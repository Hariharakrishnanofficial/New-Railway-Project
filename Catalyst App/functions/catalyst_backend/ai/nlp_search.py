"""
NLP Search Engine — translates natural language queries to CloudScale ZCQL criteria.
Uses Qwen API via Zoho Catalyst (no external API keys needed).
Includes circuit breaker for resilience.
"""

import os
import json
import re
import logging
import requests
import time
import hashlib
from datetime import datetime, timedelta

from core.exceptions import AIServiceError
from repositories.cache_manager import cache
from ai.qwen_client import qwen_client, qwen_breaker

logger = logging.getLogger(__name__)

# ── Known CloudScale table schemas ─────────────────────────────────────────────────
SCHEMA_CONTEXT = """
Available CloudScale tables and fields:

Bookings:
  - Booking_Status: "confirmed" | "cancelled" | "waitlisted" | "pending"
  - Payment_Status: "paid" | "pending" | "refunded"
  - Journey_Date: date in DD-MMM-YYYY format
  - PNR: 10-char alphanumeric string
  - Class: SL | 3A | 2A | 1A | CC | EC | 2S
  - Quota: General | Tatkal | Ladies | Senior | Handicapped
  - Total_Fare: numeric
  - Booking_Time: datetime
  - Users: lookup to user record (use user_id or email) 
  - Trains: lookup to train record (use train_id)
  - Num_Passengers: integer

Trains:
  - Train_Name: string
  - Train_Number: string (e.g., "12627")
  - From_Station: lookup (display_value like "MAS-Chennai Central")
  - To_Station: lookup (display_value like "SBC-Bangalore")
  - Is_Active: true | false
  - Departure_Time: time string HH:MM
  - Arrival_Time: time string HH:MM
  - Train_Type: Express | Superfast | Shatabdi | Rajdhani | Duronto | Passenger

Users:
  - Email: email string
  - Full_Name: string
  - Phone_Number: string
  - Role: Admin | User
  - Account_Status: Active | Blocked | Suspended
  - Is_Aadhar_Verified: true | false

Stations:
  - Station_Code: 2-5 letter code (e.g., MAS, SBC, NDLS)
  - Station_Name: full station name
  - Zone: railway zone code
  - State: Indian state name

Passengers:
  - Passenger_Name: string
  - Age: integer
  - Gender: Male | Female | Transgender
  - Current_Status: CNF/S1/12 | WL1 | RAC1 | Cancelled

Station codes: MAS=Chennai Central, SBC=Bangalore, NDLS=New Delhi, CSTM=Mumbai CSMT,
HYB=Hyderabad, BZA=Vijayawada, TVC=Thiruvananthapuram, CCJ=Calicut, MYS=Mysore,
CBE=Coimbatore, TPJ=Tiruchirappalli, MDU=Madurai, ED=Erode, SA=Salem, VM=Villupuram
"""

BOOKING_INTENT_STATIONS = {
    "chennai": "MAS", "bangalore": "SBC", "bengaluru": "SBC",
    "delhi": "NDLS", "new delhi": "NDLS",
    "mumbai": "CSTM", "hyderabad": "HYB", "vijayawada": "BZA",
    "trivandrum": "TVC", "thiruvananthapuram": "TVC",
    "calicut": "CCJ", "kozhikode": "CCJ", "mysore": "MYS", "mysuru": "MYS",
    "coimbatore": "CBE", "trichy": "TPJ", "madurai": "MDU",
    "erode": "ED", "salem": "SA",
}


class NLPSearchEngine:
    """
    Converts natural language railway queries to:
    1. Zoho criteria strings for search/filter queries
    2. Booking intent objects for booking queries
    """

    def __init__(self):
        self.model = "qwen"

    def _call_qwen(self, prompt: str) -> str:
        """Make Qwen API call via Zoho Catalyst."""
        if not qwen_breaker.can_execute():
            raise AIServiceError("Qwen API circuit breaker OPEN — using fallback")

        result = qwen_client.generate_json(prompt, temperature=0.1)
        if result is None:
            # Try getting raw text response
            messages = [{"role": "user", "content": prompt}]
            text = qwen_client.chat(messages, temperature=0.1, max_tokens=512)
            if text:
                return text.replace("```json", "").replace("```", "").strip()
            raise AIServiceError("Qwen API call failed")
        
        return json.dumps(result)

    def _resolve_date(self, text: str) -> str:
        """Resolve 'today', 'tomorrow', 'next Friday' etc. to YYYY-MM-DD."""
        now   = datetime.now()
        lower = text.lower()
        if "today" in lower:
            return now.strftime("%Y-%m-%d")
        if "tomorrow" in lower:
            return (now + timedelta(days=1)).strftime("%Y-%m-%d")
        if "yesterday" in lower:
            return (now - timedelta(days=1)).strftime("%Y-%m-%d")
        return now.strftime("%Y-%m-%d")

    def _local_fallback(self, query: str) -> dict:
        """Keyword-based fallback when Gemini is unavailable."""
        q = query.lower()

        # Booking intent detection
        booking_kw = ["book", "reserve", "ticket", "travel from", "journey from"]
        if any(kw in q for kw in booking_kw):
            src = dst = None
            for city, code in BOOKING_INTENT_STATIONS.items():
                if city in q:
                    if src is None:
                        src = code
                    elif dst is None and code != src:
                        dst = code
                        break
            if src and dst:
                return {
                    "type": "booking",
                    "booking_intent": {
                        "intent": "booking",
                        "source": src,
                        "destination": dst,
                        "date": self._resolve_date(q),
                        "class": "SL",
                    },
                    "engine": "local_fallback",
                }

        # Search/filter intent
        criteria = None
        if "cancel" in q:
            criteria = 'Booking_Status == "Cancelled"'
        elif "confirmed" in q or "confirm" in q:
            criteria = 'Booking_Status == "confirmed"'
        elif "paid" in q:
            criteria = 'Payment_Status == "paid"'
        elif "pending" in q:
            criteria = 'Payment_Status == "pending"'
        elif "waitlist" in q or "wl" in q:
            criteria = 'Booking_Status == "waitlisted"'
        else:
            criteria = 'Booking_Status != ""'

        is_count  = any(w in q for w in ["count", "total", "how many", "number of"])
        report    = "Bookings"
        if "train" in q and "book" not in q:
            report   = "Trains"
            criteria = 'Is_Active == "true"'
        elif "user" in q or "passenger" in q:
            report   = "Users"
            criteria = 'Role == "User"'

        return {
            "type":               "search",
            "report":             report,
            "translated_criteria": criteria,
            "is_count":           is_count,
            "engine":             "local_fallback",
            "confidence":         0.6,
        }

    def process_query(self, query: str) -> dict:
        """
        Process a natural language railway query.
        Returns a structured result with type, report, criteria, or booking intent.
        """
        if not query or not query.strip():
            raise AIServiceError("Query cannot be empty")

        system_prompt = f"""You are a Railway Database Query AI. Today is {datetime.now().strftime('%d %B %Y')}.

{SCHEMA_CONTEXT}

Analyze the user's query and return ONLY a JSON object in one of these formats:

FORMAT 1 - Booking Intent (user wants to book a ticket):
{{
  "type": "booking",
  "source": "STATION_CODE",
  "destination": "STATION_CODE",
  "date": "YYYY-MM-DD",
  "class": "CLASS_CODE",
  "passengers": 1
}}

FORMAT 2 - Search/Filter Query (user wants to find/list/count records):
{{
  "type": "search",
  "report": "REPORT_NAME",
  "criteria": "ZOHO_CRITERIA_STRING",
  "is_count": false,
  "description": "what this query finds"
}}

FORMAT 3 - Analysis Query (user wants statistics, trends, insights):
{{
  "type": "analysis",
  "analysis_type": "booking_trends | top_trains | revenue | cancellations | class_breakdown",
  "date_range_days": 30
}}

Rules:
- Use TODAY as {datetime.now().strftime('%Y-%m-%d')} for relative dates
- Station codes: MAS=Chennai, SBC=Bangalore, NDLS=Delhi, CSTM=Mumbai, HYB=Hyderabad
- Zoho date format in criteria: DD-MMM-YYYY (e.g., 14-Mar-2026)
- Return ONLY the JSON. No markdown. No explanation.

User Query: {query}"""

        try:
            raw = self._call_qwen(system_prompt)
            parsed = json.loads(raw)

            result_type = parsed.get("type", "search")

            if result_type == "booking":
                return {
                    "type":           "booking",
                    "booking_intent": parsed,
                    "engine":         f"Qwen ({self.model})",
                }
            elif result_type == "analysis":
                return {
                    "type":          "analysis",
                    "analysis_type": parsed.get("analysis_type", "booking_trends"),
                    "date_range":    parsed.get("date_range_days", 30),
                    "engine":        f"Qwen ({self.model})",
                }
            else:
                return {
                    "type":                "search",
                    "report":              parsed.get("report", "Bookings"),
                    "translated_criteria": parsed.get("criteria"),
                    "is_count":            parsed.get("is_count", False),
                    "description":         parsed.get("description", ""),
                    "engine":              f"Qwen ({self.model})",
                    "confidence":          1.0,
                }

        except (json.JSONDecodeError, KeyError, Exception) as exc:
            logger.warning(f"NLP parse error, using fallback: {exc}")
            result = self._local_fallback(query)
            result["parse_error"] = str(exc)
            return result


# ════════════════════════════════════════════════════════════════════════════
#  BOOKING ASSISTANT  (multi-turn conversational booking)
# ════════════════════════════════════════════════════════════════════════════

class BookingAssistant:
    """
    Conversational booking assistant powered by Qwen.
    Manages multi-turn context for step-by-step ticket booking.
    """

    def __init__(self):
        self.model = "qwen"

    SYSTEM_PROMPT = f"""You are a helpful Railway Booking Assistant. Today is {datetime.now().strftime('%d %B %Y')}.

Help users book train tickets step by step. Be concise and friendly.

Station codes: MAS=Chennai Central, SBC=Bangalore City, NDLS=New Delhi,
CSTM=Mumbai CSMT, HYB=Hyderabad, BZA=Vijayawada, TVC=Thiruvananthapuram

Travel classes: SL=Sleeper, 3A=AC 3-Tier, 2A=AC 2-Tier, 1A=AC First, CC=Chair Car

Rules:
- Max 6 passengers per booking
- Journey date must be today or future (within 120 days)
- Collect: source, destination, date, class, number of passengers, passenger details (name, age, gender)

Return a JSON object with:
{{
  "action": "ask_source" | "ask_destination" | "ask_date" | "ask_class" |
            "ask_passenger_count" | "ask_passenger_details" | "search_trains" |
            "confirm_booking" | "booking_complete" | "clarify" | "chat",
  "message": "Your response to the user",
  "data": {{collected_booking_data_so_far}},
  "ready_to_book": false
}}

When all required info is collected, set ready_to_book: true and action: "confirm_booking".
Return ONLY JSON. No markdown.
"""

    def chat(self, user_message: str, conversation_history: list) -> dict:
        """
        Process one turn of the booking conversation.
        conversation_history: list of {role: 'user'|'assistant', content: str}
        """
        if not qwen_breaker.can_execute():
            return {"action": "chat", "message": "AI is temporarily unavailable. Please try again shortly.", "data": {}}

        # Build messages list for multi-turn
        messages = []
        for msg in conversation_history[-20:]:   # keep last 20 turns for context
            role = msg.get("role", "user")
            content = msg.get("content", "")
            messages.append({"role": role, "content": content})

        # Add current message
        messages.append({"role": "user", "content": user_message})

        try:
            response = qwen_client.chat(
                messages=messages,
                system_prompt=self.SYSTEM_PROMPT,
                max_tokens=512,
                temperature=0.3
            )
            
            if not response:
                return {"action": "chat", "message": "Sorry, I'm having trouble. Please try again.", "data": {}}

            raw = response.strip().replace("```json", "").replace("```", "").strip()
            parsed = json.loads(raw)
            return parsed

        except json.JSONDecodeError:
            return {
                "action":  "chat",
                "message": response if response else "I had trouble understanding that. Could you rephrase?",
                "data":    {},
            }
        except Exception as exc:
            logger.error(f"BookingAssistant error: {exc}")
            return {
                "action":  "chat",
                "message": "I had trouble understanding that. Could you rephrase?",
                "data":    {},
            }


# ════════════════════════════════════════════════════════════════════════════
#  RECOMMENDATION ENGINE
# ════════════════════════════════════════════════════════════════════════════

class RecommendationEngine:
    """
    Personalized train recommendations based on user booking history.
    Uses scoring algorithm: route match + class preference + availability.
    """

    def get_recommendations(self, user_id: str, source: str = "", destination: str = "") -> list:
        """
        Generate top 3 train recommendations for a user.
        Returns list of { train, score, reason } dicts.
        """
        try:
            from config import TABLES
            from repositories.cloudscale_repository import cloudscale_repo, CriteriaBuilder as CB

            # Fetch user booking history (last 30 bookings)
            criteria = CB().eq("Users", user_id).build()
            history  = cloudscale_repo.get_records(TABLES["bookings"], criteria=criteria, limit=30)

            # Extract preferences
            class_counts  = {}
            for b in history:
                cls = str(b.get("Class", "SL")).upper().strip()
                if cls:
                    class_counts[cls] = class_counts.get(cls, 0) + 1

            preferred_class = max(class_counts, key=class_counts.get) if class_counts else "SL"
            logger.debug(f"User {user_id} preferred class: {preferred_class}")

            # Fetch available trains
            trains = cloudscale_repo.search_trains(source=source, destination=destination)
            if not trains:
                return []

            def get_code(field):
                if isinstance(field, dict):
                    dv = field.get("display_value", "")
                    return dv.split("-")[0].strip().upper()
                return str(field or "").split("-")[0].strip().upper()

            recommendations = []
            for train in trains[:20]:
                score  = 0.0
                reason = []

                # Class preference score
                # Support both 3A and 3AC formats
                cls_clean = preferred_class.replace('AC', 'A').replace('SL', 'SL')
                fare_key  = f"Fare_{cls_clean}"
                if train.get(fare_key) or train.get(f"Fare_{preferred_class}"):
                    score  += 0.4
                    reason.append(f"Has your preferred {preferred_class} class")

                # Active train score
                if str(train.get("Is_Active", "true")).lower() == "true":
                    score += 0.2

                # Route match score
                if source and destination:
                    t_src = get_code(train.get("From_Station", {}))
                    t_dst = get_code(train.get("To_Station", {}))
                    if t_src == source and t_dst == destination:
                        score  += 0.4
                        reason.append("Direct route match")

                recommendations.append({
                    "train":  train,
                    "score":  round(score, 2),
                    "reason": "; ".join(reason) if reason else "Good availability",
                })

            recommendations.sort(key=lambda x: x["score"], reverse=True)
            return recommendations[:3]
        except Exception as e:
            logger.exception(f"get_recommendations error: {e}")
            return []


# ════════════════════════════════════════════════════════════════════════════
#  ANALYTICS AI  (Gemini-powered insights)
# ════════════════════════════════════════════════════════════════════════════

class AnalyticsAI:
    """Uses Qwen to generate natural-language insights from booking data."""

    def __init__(self):
        self.model = "qwen"

    def generate_insights(self, analytics_data: dict, question: str = "") -> str:
        """Generate a natural language analysis of the provided analytics data with caching."""
        # ── Caching ──────────────────────────────────────────────────────────
        data_json = json.dumps(analytics_data, sort_keys=True)
        data_hash = hashlib.md5(f"{data_json}:{question}".encode()).hexdigest()
        cache_key = f"ai_insight:{data_hash}"
        
        cached_insight = cache.get(cache_key)
        if cached_insight:
            logger.debug(f"AI Insight Cache HIT: {data_hash}")
            return cached_insight

        if not qwen_breaker.can_execute():
            return "AI analysis temporarily unavailable. Please try again shortly."

        prompt = f"""You are a Railway Analytics Expert. Analyze this booking data and provide 3-5 key insights.
Be concise. Use numbers. Focus on actionable findings.

Data: {data_json[:3000]}

{f'Specific question: {question}' if question else 'Provide general insights about bookings, revenue, and demand patterns.'}

Respond in plain English. 3-5 bullet points max."""

        try:
            messages = [{"role": "user", "content": prompt}]
            insight = qwen_client.chat(
                messages=messages,
                max_tokens=500,
                temperature=0.4
            )
            
            if insight:
                cache.set(cache_key, insight, ttl=1800)  # Cache for 30 mins
                return insight
            
            return "AI analysis unavailable. Please try again later."
            
        except Exception as exc:
            logger.error(f"AnalyticsAI error: {exc}")
            return "Analysis unavailable due to an error. Please try again later."


# Singletons
nlp_search_engine   = NLPSearchEngine()
booking_assistant   = BookingAssistant()
recommendation_engine = RecommendationEngine()
analytics_ai        = AnalyticsAI()
