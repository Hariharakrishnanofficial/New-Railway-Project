"""
booking_conversation.py — Conversational booking flow with intent-first routing.

Features:
- Intent-first routing: Every message passes through intent detector first
- Stage-based booking flow: Collects information one step at a time
- Menu handling: Proper support for numbered menu selections
- State preservation: Maintains booking state across messages

Stages: from → to → date → class → [search] → select_train → pax_count →
        pax_name → pax_age → pax_gender → (loop for each passenger) →
        confirm → [create_booking] → done
"""

import json
import logging
import re
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple

from ai.qwen_client import qwen_client
from ai.booking_prompts import (
    INTENT_DETECTOR_PROMPT,
    STAGE_FROM_PROMPT, STAGE_TO_PROMPT, STAGE_DATE_PROMPT,
    STAGE_CLASS_PROMPT, STAGE_SELECT_TRAIN_PROMPT, STAGE_PAX_COUNT_PROMPT,
    STAGE_PAX_NAME_PROMPT, STAGE_PAX_AGE_PROMPT, STAGE_PAX_GENDER_PROMPT,
    STAGE_CONFIRM_PROMPT, MENU_REPLY_PROMPT, RESTART_HANDLER_PROMPT,
    TRAIN_FORMATTER_PROMPT, BOOKING_SUMMARY_TEMPLATE,
    STATION_MAP, CLASS_MAP, CLASS_FARE_KEY, CLASS_SEAT_KEY,
    AI_ASSISTANT_SYSTEM_PROMPT, MCP_QUERY_PROMPT, QUESTION_CLASSIFIER_PROMPT,
)

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════
#  DATA CLASSES
# ══════════════════════════════════════════════════════════════════

@dataclass
class PassengerInfo:
    """Single passenger details."""
    name: str = ""
    age: int = 0
    gender: str = ""


@dataclass
class BookingState:
    """
    Complete booking state, serialized to/from frontend on each message.
    """
    # Current conversation stage
    stage: str = "from"

    # Journey details
    from_station: Optional[str] = None
    to_station: Optional[str] = None
    date: Optional[str] = None  # YYYY-MM-DD format
    date_display: Optional[str] = None  # Human readable
    travel_class: Optional[str] = None  # SL, 3A, 2A, 1A, CC
    class_display: Optional[str] = None  # Full name

    # Selected train
    train_id: Optional[str] = None
    train_name: Optional[str] = None
    train_number: Optional[str] = None

    # Passengers
    pax_count: int = 0
    passengers: List[Dict[str, Any]] = field(default_factory=list)
    current_pax_index: int = 0
    pax_field: str = "name"  # name → age → gender rotation

    # Search results (for train selection)
    trains_list: List[Dict[str, Any]] = field(default_factory=list)

    # Current menu context
    menu_type: Optional[str] = None  # no_trains_found, change_menu, class_select, train_select

    # Fare calculation
    fare_per_person: float = 0.0
    total_fare: float = 0.0

    def reset(self) -> 'BookingState':
        """Reset to initial state."""
        return BookingState()

    def reset_passengers(self) -> None:
        """Reset passenger collection."""
        self.passengers = []
        self.current_pax_index = 0
        self.pax_field = "name"


@dataclass
class ConversationResponse:
    """Response from the conversation processor."""
    reply: str
    state: BookingState
    trigger: Optional[str] = None  # search_trains, show_confirm, create_booking, change_menu, booking_complete


# ══════════════════════════════════════════════════════════════════
#  HELPER FUNCTIONS
# ══════════════════════════════════════════════════════════════════

def match_station(user_input: str) -> Optional[str]:
    """
    Match user input to a known station name.
    Returns the standardized station name or None if no match.
    """
    if not user_input:
        return None

    normalized = user_input.lower().strip()

    # Direct match
    if normalized in STATION_MAP:
        return STATION_MAP[normalized]

    # Partial match
    for key, value in STATION_MAP.items():
        if normalized in key or key in normalized:
            return value

    return None


def match_class(user_input: str) -> Optional[Tuple[str, str]]:
    """
    Match user input to a travel class.
    Returns (code, display_name) or None if no match.
    """
    if not user_input:
        return None

    normalized = user_input.lower().strip()

    if normalized in CLASS_MAP:
        return CLASS_MAP[normalized]

    return None


def parse_date(user_input: str, today: datetime) -> Optional[Tuple[str, str]]:
    """
    Parse user date input to a date.
    Returns (YYYY-MM-DD, display_format) or None if invalid.
    """
    if not user_input:
        return None

    normalized = user_input.lower().strip()

    # Handle relative dates
    if normalized == "today":
        return (today.strftime("%Y-%m-%d"), today.strftime("%d-%b-%Y"))

    if normalized == "tomorrow":
        tomorrow = today + timedelta(days=1)
        return (tomorrow.strftime("%Y-%m-%d"), tomorrow.strftime("%d-%b-%Y"))

    if normalized == "day after tomorrow" or normalized == "day after":
        day_after = today + timedelta(days=2)
        return (day_after.strftime("%Y-%m-%d"), day_after.strftime("%d-%b-%Y"))

    # Handle "next monday", "next friday", etc.
    weekdays = {
        "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
        "friday": 4, "saturday": 5, "sunday": 6
    }
    for day_name, day_num in weekdays.items():
        if f"next {day_name}" in normalized:
            days_ahead = day_num - today.weekday()
            if days_ahead <= 0:
                days_ahead += 7
            target = today + timedelta(days=days_ahead)
            return (target.strftime("%Y-%m-%d"), target.strftime("%d-%b-%Y"))

    # Try various date formats
    formats = [
        ("%d %B %Y", "%d-%b-%Y"),    # 18 March 2026
        ("%d %b %Y", "%d-%b-%Y"),     # 18 Mar 2026
        ("%d %B", "%d-%b-%Y"),        # 18 March (assume current year)
        ("%d %b", "%d-%b-%Y"),        # 18 Mar
        ("%d/%m/%Y", "%d-%b-%Y"),     # 18/03/2026
        ("%d-%m-%Y", "%d-%b-%Y"),     # 18-03-2026
        ("%Y-%m-%d", "%d-%b-%Y"),     # 2026-03-18
    ]

    # Remove ordinal suffixes
    cleaned = re.sub(r'(\d)(st|nd|rd|th)', r'\1', normalized)

    for parse_fmt, display_fmt in formats:
        try:
            parsed = datetime.strptime(cleaned, parse_fmt)
            # If year not in format, use current year
            if "%Y" not in parse_fmt:
                parsed = parsed.replace(year=today.year)
                # If the date has passed this year, use next year
                if parsed < today:
                    parsed = parsed.replace(year=today.year + 1)
            return (parsed.strftime("%Y-%m-%d"), parsed.strftime("%d-%b-%Y"))
        except ValueError:
            continue

    return None


def validate_date(date_str: str, today: datetime) -> Tuple[bool, str]:
    """
    Validate a date for booking.
    Returns (is_valid, error_message).
    """
    try:
        date = datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return (False, "Invalid date format.")

    # Check if in the past
    if date.date() < today.date():
        return (False, "That date is in the past. Please choose a future date.")

    # Check if more than 120 days ahead
    max_date = today + timedelta(days=120)
    if date > max_date:
        return (False, "Maximum advance booking is 120 days. Please choose an earlier date.")

    return (True, "")


def parse_number(user_input: str) -> Optional[int]:
    """Extract a number from user input."""
    if not user_input:
        return None

    # Try direct integer
    try:
        return int(user_input.strip())
    except ValueError:
        pass

    # Extract digits
    digits = re.findall(r'\d+', user_input)
    if digits:
        return int(digits[0])

    # Word to number mapping
    word_map = {
        "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
        "just me": 1, "only me": 1, "myself": 1,
        "me and my wife": 2, "me and wife": 2, "couple": 2,
    }
    normalized = user_input.lower().strip()
    for word, num in word_map.items():
        if word in normalized:
            return num

    return None


def parse_gender(user_input: str) -> Optional[str]:
    """Parse gender from user input."""
    if not user_input:
        return None

    normalized = user_input.lower().strip()

    male_keywords = ["m", "male", "boy", "man", "gents"]
    female_keywords = ["f", "female", "girl", "woman", "ladies"]
    other_keywords = ["other", "third", "o"]

    if normalized in male_keywords:
        return "Male"
    if normalized in female_keywords:
        return "Female"
    if normalized in other_keywords:
        return "Other"

    return None

def extract_json(text: str) -> Optional[Dict]:
    """Extract JSON from LLM response text."""
    if not text:
        return None

    # Clean up markdown code blocks
    text = text.strip()
    text = re.sub(r'^```json\s*', '', text)
    text = re.sub(r'^```\s*', '', text)
    text = re.sub(r'\s*```$', '', text)

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Try to find JSON in the text
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass

    logger.warning(f"Failed to parse JSON from: {text[:200]}")
    return None


# ══════════════════════════════════════════════════════════════════
#  BOOKING CONVERSATION CLASS
# ══════════════════════════════════════════════════════════════════

class BookingConversation:
    """
    Main conversational booking handler.
    Implements intent-first routing and stage-based value collection.
    """

    def __init__(self):
        self.qwen = qwen_client

    def process_message(
        self,
        message: str,
        state: Optional[BookingState] = None,
        history: Optional[List[Dict]] = None
    ) -> ConversationResponse:
        """
        Process a user message through the conversational booking flow.

        Args:
            message: User's message text
            state: Current booking state (from frontend)
            history: Conversation history

        Returns:
            ConversationResponse with reply, updated state, and optional trigger
        """
        if state is None:
            state = BookingState()
        if history is None:
            history = []

        message = message.strip()
        if not message:
            return ConversationResponse(
                reply="Please type a message.",
                state=state
            )

        # Step 1: Detect intent
        intent_result = self._detect_intent(message, state.stage)
        intent = intent_result.get("intent", "UNCLEAR")
        extracted = intent_result.get("extracted", message)

        logger.info(f"Detected intent: {intent}, extracted: {extracted}, stage: {state.stage}")

        # Step 2: Route based on intent
        if intent == "RESTART":
            return self._handle_restart(message, extracted, state)

        elif intent == "MENU_SELECT":
            return self._handle_menu_select(extracted, state)

        elif intent == "PROVIDE_VALUE":
            return self._handle_provide_value(extracted, state)

        elif intent == "PNR_CHECK":
            return self._handle_pnr_check(extracted, state)

        elif intent == "CANCEL_BOOKING":
            return self._handle_cancel_booking(extracted, state)

        elif intent == "QUESTION":
            return self._handle_question(message, history, state)

        else:  # UNCLEAR
            return self._handle_unclear(message, state)

    # ─── Intent Detection ────────────────────────────────────────────

    def _detect_intent(self, message: str, current_stage: str) -> Dict:
        """Detect user intent using Prompt 1."""
        prompt = INTENT_DETECTOR_PROMPT.format(
            CURRENT_STAGE=current_stage,
            USER_MESSAGE=message
        )

        response = self.qwen.chat(
            messages=[{"role": "user", "content": prompt}],
            system_prompt="You are an intent classifier. Output ONLY valid JSON.",
            max_tokens=150,
            temperature=0.1
        )

        result = extract_json(response)
        if result and "intent" in result:
            return result

        # Fallback: heuristic detection
        return self._heuristic_intent(message, current_stage)

    def _heuristic_intent(self, message: str, stage: str) -> Dict:
        """Heuristic fallback for intent detection."""
        msg_lower = message.lower().strip()

        # RESTART triggers
        restart_keywords = [
            "book train", "new booking", "start over", "book ticket",
            "i want to book", "let me book", "restart"
        ]
        if any(kw in msg_lower for kw in restart_keywords):
            # Check for route
            if " to " in msg_lower:
                return {"intent": "RESTART", "extracted": message}
            return {"intent": "RESTART", "extracted": ""}

        # PNR check
        if "pnr" in msg_lower or re.match(r'^[a-z0-9]{10}$', msg_lower):
            pnr_match = re.search(r'[a-z0-9]{10}', msg_lower, re.IGNORECASE)
            return {"intent": "PNR_CHECK", "extracted": pnr_match.group() if pnr_match else ""}

        # Cancel booking
        if "cancel" in msg_lower and ("booking" in msg_lower or "ticket" in msg_lower):
            return {"intent": "CANCEL_BOOKING", "extracted": message}

        # Question
        question_keywords = ["what is", "how do", "what are", "help", "?"]
        if any(kw in msg_lower for kw in question_keywords):
            return {"intent": "QUESTION", "extracted": message}

        # Menu selection (single digits or common options)
        if msg_lower in ["1", "2", "3", "4", "5"]:
            return {"intent": "MENU_SELECT", "extracted": msg_lower}
        menu_phrases = [
            "try a different", "change the", "sleeper", "ac 3", "ac 2",
            "first class", "chair car", "yes", "no", "confirm", "proceed"
        ]
        if any(phrase in msg_lower for phrase in menu_phrases):
            return {"intent": "MENU_SELECT", "extracted": message}

        # Default to PROVIDE_VALUE
        return {"intent": "PROVIDE_VALUE", "extracted": message}

    # ─── Intent Handlers ─────────────────────────────────────────────

    def _handle_restart(self, message: str, extracted: str, state: BookingState) -> ConversationResponse:
        """Handle RESTART intent - start a new booking."""
        new_state = BookingState()

        # Try to extract route from message
        if " to " in extracted.lower():
            parts = extracted.lower().split(" to ")
            if len(parts) >= 2:
                from_input = parts[0].strip()
                to_input = parts[1].strip()

                from_station = match_station(from_input)
                to_station = match_station(to_input)

                if from_station and to_station:
                    new_state.from_station = from_station
                    new_state.to_station = to_station
                    new_state.stage = "date"
                    return ConversationResponse(
                        reply=f"Starting fresh!\n\nFrom: {from_station}\nTo: {to_station}\n\nWhich date would you like to travel?\n(e.g. '18 March', 'tomorrow', '25/03/2026')",
                        state=new_state
                    )
                elif from_station:
                    new_state.from_station = from_station
                    new_state.stage = "to"
                    return ConversationResponse(
                        reply=f"Starting fresh!\n\nFrom: {from_station}\n\nWhere are you travelling to?",
                        state=new_state
                    )
                elif to_station:
                    new_state.to_station = to_station
                    new_state.stage = "from"
                    return ConversationResponse(
                        reply=f"Starting fresh! I understand you want to go to {to_station}.\n\nWhere are you travelling from?",
                        state=new_state
                    )

        # No route extracted - start fresh
        new_state.stage = "from"
        return ConversationResponse(
            reply="Let's book your train!\n\nWhere are you travelling from?",
            state=new_state
        )

    def _handle_menu_select(self, selection: str, state: BookingState) -> ConversationResponse:
        """Handle MENU_SELECT intent."""
        menu_type = state.menu_type
        sel_lower = selection.lower().strip()

        # No trains found menu
        if menu_type == "no_trains_found":
            if sel_lower in ["1", "try a different date", "different date"]:
                state.stage = "date"
                state.menu_type = None
                return ConversationResponse(
                    reply="Sure! Which date would you like to try instead?",
                    state=state
                )
            elif sel_lower in ["2", "try a different class", "different class"]:
                state.stage = "class"
                state.menu_type = None
                return ConversationResponse(
                    reply="Which class would you like to try?\n1. Sleeper (SL)\n2. AC 3 Tier (3A)\n3. AC 2 Tier (2A)\n4. AC First Class (1A)\n5. Chair Car (CC)",
                    state=state
                )
            elif sel_lower in ["3", "change the route", "change route"]:
                state.stage = "from"
                state.menu_type = None
                state.from_station = None
                state.to_station = None
                return ConversationResponse(
                    reply="Let's change the route. Where would you like to travel from?",
                    state=state
                )

        # Change menu (after declining booking confirmation)
        elif menu_type == "change_menu":
            if sel_lower in ["1", "source", "from"]:
                state.stage = "from"
                state.menu_type = None
                return ConversationResponse(
                    reply="Where would you like to travel from?",
                    state=state
                )
            elif sel_lower in ["2", "destination", "to"]:
                state.stage = "to"
                state.menu_type = None
                return ConversationResponse(
                    reply="Where would you like to travel to?",
                    state=state
                )
            elif sel_lower in ["3", "date"]:
                state.stage = "date"
                state.menu_type = None
                return ConversationResponse(
                    reply="Which date would you like to travel?",
                    state=state
                )
            elif sel_lower in ["4", "class"]:
                state.stage = "class"
                state.menu_type = None
                return ConversationResponse(
                    reply="Which class?\n1. Sleeper (SL)\n2. AC 3 Tier (3A)\n3. AC 2 Tier (2A)\n4. AC First Class (1A)\n5. Chair Car (CC)",
                    state=state
                )
            elif sel_lower in ["5", "passenger", "passengers"]:
                state.stage = "pax_count"
                state.menu_type = None
                state.reset_passengers()
                return ConversationResponse(
                    reply="How many passengers will be travelling?",
                    state=state
                )

        # Class selection menu
        elif menu_type == "class_select" or state.stage == "class":
            class_result = match_class(selection)
            if class_result:
                code, display = class_result
                state.travel_class = code
                state.class_display = display
                state.menu_type = None
                return ConversationResponse(
                    reply=f"Class: {display}\n\nSearching trains from {state.from_station} to {state.to_station} on {state.date_display}...",
                    state=state,
                    trigger="search_trains"
                )

        # Train select menu
        elif menu_type == "train_select":
            return self._handle_train_selection(selection, state)

        # Confirmation (yes/no)
        if sel_lower in ["yes", "y", "ok", "confirm", "proceed", "book it", "go ahead", "sure"]:
            return ConversationResponse(
                reply="Booking your tickets now...",
                state=state,
                trigger="create_booking"
            )
        elif sel_lower in ["no", "n", "cancel", "change", "wrong", "go back"]:
            state.menu_type = "change_menu"
            return ConversationResponse(
                reply="No problem! What would you like to change?\n1. Source station\n2. Destination station\n3. Travel date\n4. Travel class\n5. Passenger details",
                state=state,
                trigger="change_menu"
            )

        # Unclear selection
        return ConversationResponse(
            reply="Please type a number (1, 2, 3, etc.) or the option name.",
            state=state
        )

    def _handle_provide_value(self, value: str, state: BookingState) -> ConversationResponse:
        """Handle PROVIDE_VALUE intent based on current stage."""
        stage = state.stage

        if stage == "from":
            return self._handle_stage_from(value, state)
        elif stage == "to":
            return self._handle_stage_to(value, state)
        elif stage == "date":
            return self._handle_stage_date(value, state)
        elif stage == "class":
            return self._handle_stage_class(value, state)
        elif stage == "select_train":
            return self._handle_train_selection(value, state)
        elif stage == "pax_count":
            return self._handle_stage_pax_count(value, state)
        elif stage == "pax_name":
            return self._handle_stage_pax_name(value, state)
        elif stage == "pax_age":
            return self._handle_stage_pax_age(value, state)
        elif stage == "pax_gender":
            return self._handle_stage_pax_gender(value, state)
        elif stage == "confirm":
            return self._handle_stage_confirm(value, state)
        else:
            # Unknown stage - restart
            return self._handle_restart(value, "", state)

    def _handle_pnr_check(self, pnr: str, state: BookingState) -> ConversationResponse:
        """Handle PNR_CHECK intent."""
        # Extract PNR if not clean
        pnr_match = re.search(r'[a-z0-9]{10}', pnr, re.IGNORECASE)
        pnr_number = pnr_match.group().upper() if pnr_match else pnr.upper()

        return ConversationResponse(
            reply=f"Checking PNR status for {pnr_number}...",
            state=state,
            trigger="pnr_check"
        )

    def _handle_cancel_booking(self, message: str, state: BookingState) -> ConversationResponse:
        """Handle CANCEL_BOOKING intent."""
        # Extract PNR if present
        pnr_match = re.search(r'[a-z0-9]{10}', message, re.IGNORECASE)

        if pnr_match:
            return ConversationResponse(
                reply=f"Starting cancellation for PNR {pnr_match.group().upper()}...",
                state=state,
                trigger="cancel_booking"
            )
        else:
            return ConversationResponse(
                reply="Please provide the PNR number of the booking you want to cancel.",
                state=state
            )

    def _handle_question(self, message: str, history: List[Dict], state: BookingState) -> ConversationResponse:
        """Handle QUESTION intent with intelligent response and MCP database access."""

        # Step 1: Classify if the question needs database access
        needs_db = self._check_needs_database(message)

        if needs_db:
            # Step 2: Generate MCP query and execute
            mcp_result = self._execute_mcp_query(message)
            if mcp_result:
                # Format the database results into a helpful response
                reply = self._format_mcp_response(message, mcp_result)
                return ConversationResponse(reply=reply, state=state)

        # Step 3: For general questions, use AI with enhanced system prompt
        messages = history[-10:] if history else []
        messages.append({"role": "user", "content": message})

        response = self.qwen.chat(
            messages=messages,
            system_prompt=AI_ASSISTANT_SYSTEM_PROMPT,
            max_tokens=512,
            temperature=0.7
        )

        reply = response.strip() if response else "I can help you search trains, book tickets, check PNR status, or cancel bookings. What would you like to do?"

        return ConversationResponse(
            reply=reply,
            state=state
        )

    def _check_needs_database(self, message: str) -> bool:
        """Check if the question requires database access."""
        # Quick keyword-based check first (faster than LLM)
        db_keywords = [
            "show", "find", "search", "list", "get", "check", "lookup",
            "trains from", "trains to", "station", "pnr", "booking",
            "fare", "schedule", "availability", "how many", "all"
        ]
        msg_lower = message.lower()
        if any(kw in msg_lower for kw in db_keywords):
            return True

        # For ambiguous cases, use LLM classifier
        try:
            prompt = QUESTION_CLASSIFIER_PROMPT.format(USER_QUESTION=message)
            response = self.qwen.chat(
                messages=[{"role": "user", "content": prompt}],
                system_prompt="You are a query classifier. Output ONLY valid JSON.",
                max_tokens=100,
                temperature=0.1
            )
            result = extract_json(response)
            return result.get("needs_db", False) if result else False
        except Exception as e:
            logger.warning(f"Classification failed: {e}")
            return False

    def _execute_mcp_query(self, message: str) -> Optional[Dict]:
        """Generate and execute MCP query from natural language using dynamic schema."""
        try:
            # Import schema discovery for dynamic module detection
            from services.schema_discovery import schema_discovery

            # Generate dynamic MCP prompt based on discovered schema
            dynamic_prompt = schema_discovery.build_mcp_prompt()
            prompt = dynamic_prompt.replace("{USER_QUERY}", message)

            response = self.qwen.chat(
                messages=[{"role": "user", "content": prompt}],
                system_prompt="You are a database query generator. Output ONLY valid JSON.",
                max_tokens=200,
                temperature=0.1
            )

            mcp_query = extract_json(response)
            if not mcp_query or mcp_query.get("method") == "NONE":
                logger.info(f"No MCP query generated for: {message}")
                return None

            # Execute the query via Zoho
            from services.zoho_service import zoho

            module = mcp_query.get("module", "")
            filters = mcp_query.get("filters", {})

            # Use schema discovery to find the report for this module
            report = schema_discovery.get_report_for_module(module)

            if not report:
                # Fallback: try hardcoded mapping for backward compatibility
                from config import TABLES
                module_map = {
                    "Stations": "stations",
                    "Trains": "trains",
                    "Bookings": "bookings",
                    "Users": "users",
                    "Fares": "fares",
                    "Passengers": "passengers",
                    "Train_Routes": "train_routes",
                    "Route_Stops": "route_stops",
                    "Inventory": "train_inventory",
                    "Quotas": "quotas",
                    "Coach_Layouts": "coach_layouts",
                    "Announcements": "announcements",
                }
                config_key = module_map.get(module)
                if config_key:
                    report = TABLES.get(config_key)

            if not report:
                logger.warning(f"No report found for module: {module}")
                return None

            logger.info(f"MCP Query: module={module}, report={report}, filters={filters}")

            # Fetch records
            result = zoho.get_all_records(report, criteria=None, limit=50)
            if not result.get("success"):
                logger.warning(f"Zoho query failed: {result.get('error')}")
                return None

            records = result.get("data", {}).get("data", []) or []

            # Apply local filtering
            if filters:
                filtered = []
                for rec in records:
                    match = True
                    for field, value in filters.items():
                        rec_val = rec.get(field, "")
                        if isinstance(rec_val, dict):
                            rec_val = rec_val.get("display_value", "")
                        if str(value).lower() not in str(rec_val).lower():
                            match = False
                            break
                    if match:
                        filtered.append(rec)
                records = filtered

            return {
                "module": module,
                "report": report,
                "filters": filters,
                "count": len(records),
                "records": records[:20]  # Limit to 20 for display
            }

        except Exception as e:
            logger.exception(f"MCP query execution failed: {e}")
            return None

    def _format_mcp_response(self, question: str, mcp_result: Dict) -> str:
        """Format MCP query results into a human-readable response."""
        module = mcp_result.get("module", "")
        records = mcp_result.get("records", [])
        count = mcp_result.get("count", 0)

        if count == 0:
            return f"No {module.lower()} found matching your query."

        # Format based on module type
        lines = [f"Found {count} result(s):\n"]

        if module == "Trains":
            for i, rec in enumerate(records[:10], 1):
                num = rec.get("Train_Number", "N/A")
                name = rec.get("Train_Name", "Unknown")
                from_st = rec.get("From_Station", {})
                to_st = rec.get("To_Station", {})
                from_disp = from_st.get("display_value", from_st) if isinstance(from_st, dict) else from_st
                to_disp = to_st.get("display_value", to_st) if isinstance(to_st, dict) else to_st
                dep = rec.get("Departure_Time", "")
                arr = rec.get("Arrival_Time", "")
                lines.append(f"{i}. {num} — {name}")
                lines.append(f"   {from_disp} → {to_disp}")
                lines.append(f"   Departs: {dep} | Arrives: {arr}")
                lines.append("")

        elif module == "Stations":
            for i, rec in enumerate(records[:15], 1):
                code = rec.get("Station_Code", "")
                name = rec.get("Station_Name", "")
                city = rec.get("City", "")
                state = rec.get("State", "")
                lines.append(f"{i}. {code} — {name} ({city}, {state})")

        elif module == "Bookings":
            for i, rec in enumerate(records[:10], 1):
                pnr = rec.get("PNR", "N/A")
                status = rec.get("Booking_Status", "N/A")
                date = rec.get("Journey_Date", "N/A")
                fare = rec.get("Total_Fare", 0)
                lines.append(f"{i}. PNR: {pnr} | Status: {status}")
                lines.append(f"   Date: {date} | Fare: ₹{fare}")
                lines.append("")

        elif module == "Announcements":
            for i, rec in enumerate(records[:5], 1):
                title = rec.get("Title", "")
                msg = rec.get("Message", "")
                priority = rec.get("Priority", "")
                lines.append(f"{i}. [{priority}] {title}")
                lines.append(f"   {msg[:100]}{'...' if len(msg) > 100 else ''}")
                lines.append("")

        else:
            # Generic formatting for other modules
            for i, rec in enumerate(records[:10], 1):
                items = []
                for k, v in list(rec.items())[:5]:
                    if k != "ID" and v:
                        if isinstance(v, dict):
                            v = v.get("display_value", str(v))
                        items.append(f"{k}: {v}")
                lines.append(f"{i}. {' | '.join(items)}")

        if count > len(records):
            lines.append(f"\n... and {count - len(records)} more results.")

        return "\n".join(lines)

    def _handle_unclear(self, message: str, state: BookingState) -> ConversationResponse:
        """Handle UNCLEAR intent."""
        stage = state.stage

        prompts = {
            "from": "Which city or station are you travelling from?",
            "to": "Which city or station are you travelling to?",
            "date": "Which date would you like to travel? (e.g., 'tomorrow', '18 March')",
            "class": "Which class would you prefer? Type 1-5:\n1. Sleeper (SL)\n2. AC 3 Tier (3A)\n3. AC 2 Tier (2A)\n4. AC First Class (1A)\n5. Chair Car (CC)",
            "select_train": "Please type the train number from the list to select it.",
            "pax_count": "How many passengers will be travelling? (1 to 6)",
            "pax_name": f"What is passenger {state.current_pax_index + 1}'s full name?",
            "pax_age": f"How old is the passenger?",
            "pax_gender": "What is the passenger's gender? (Male / Female / Other)",
            "confirm": "Please type YES to confirm the booking or NO to make changes.",
        }

        reply = prompts.get(stage, "I didn't understand that. Would you like to book a train? Type 'book train' to start.")

        return ConversationResponse(
            reply=reply,
            state=state
        )

    # ─── Stage Handlers ──────────────────────────────────────────────

    def _handle_stage_from(self, value: str, state: BookingState) -> ConversationResponse:
        """Handle 'from' stage - source station."""
        station = match_station(value)

        if station:
            state.from_station = station
            state.stage = "to"
            return ConversationResponse(
                reply=f"From: {station}\n\nGreat! And where are you travelling to?",
                state=state
            )
        else:
            return ConversationResponse(
                reply="I didn't recognise that station. Try typing a city name like Chennai, Bangalore, Mumbai, Delhi, or Madurai.",
                state=state
            )

    def _handle_stage_to(self, value: str, state: BookingState) -> ConversationResponse:
        """Handle 'to' stage - destination station."""
        station = match_station(value)

        if station:
            # Check if same as source
            if station == state.from_station:
                return ConversationResponse(
                    reply="Destination cannot be the same as source. Please choose a different station.",
                    state=state
                )

            state.to_station = station
            state.stage = "date"
            return ConversationResponse(
                reply=f"To: {station}\n\nWhich date would you like to travel?\nYou can say: '18 March', 'tomorrow', '25/03/2026', or 'next Monday'",
                state=state
            )
        else:
            return ConversationResponse(
                reply="I didn't recognise that station. Try typing a city name like Chennai, Bangalore, Mumbai, Delhi, or Madurai.",
                state=state
            )

    def _handle_stage_date(self, value: str, state: BookingState) -> ConversationResponse:
        """Handle 'date' stage - journey date."""
        today = datetime.now()
        result = parse_date(value, today)

        if result:
            date_iso, date_display = result
            is_valid, error_msg = validate_date(date_iso, today)

            if not is_valid:
                return ConversationResponse(
                    reply=error_msg,
                    state=state
                )

            state.date = date_iso
            state.date_display = date_display
            state.stage = "class"
            return ConversationResponse(
                reply=f"Date: {date_display}\n\nWhich class would you prefer?\n1. Sleeper (SL) — cheapest\n2. AC 3 Tier (3A)\n3. AC 2 Tier (2A)\n4. AC First Class (1A) — premium\n5. Chair Car (CC) — for day trains",
                state=state
            )
        else:
            return ConversationResponse(
                reply="I couldn't parse that date. Try saying '18 March', 'tomorrow', or '25/03/2026'.",
                state=state
            )

    def _handle_stage_class(self, value: str, state: BookingState) -> ConversationResponse:
        """Handle 'class' stage - travel class selection."""
        class_result = match_class(value)

        if class_result:
            code, display = class_result
            state.travel_class = code
            state.class_display = display
            return ConversationResponse(
                reply=f"Class: {display}\n\nSearching trains from {state.from_station} to {state.to_station} on {state.date_display}...",
                state=state,
                trigger="search_trains"
            )
        else:
            return ConversationResponse(
                reply="Please choose a class by typing 1, 2, 3, 4, or 5.\n1. Sleeper (SL)\n2. AC 3 Tier (3A)\n3. AC 2 Tier (2A)\n4. AC First Class (1A)\n5. Chair Car (CC)",
                state=state
            )

    def _handle_train_selection(self, value: str, state: BookingState) -> ConversationResponse:
        """Handle train selection from results."""
        trains = state.trains_list
        if not trains:
            return ConversationResponse(
                reply="No trains available to select. Please search again.",
                state=state,
                trigger="search_trains"
            )

        val_lower = value.lower().strip()

        # Try to match by number or name
        for train in trains:
            train_num = str(train.get("Train_Number", "")).lower()
            train_name = str(train.get("Train_Name", "")).lower()

            if val_lower == train_num or val_lower in train_num:
                state.train_id = train.get("ID")
                state.train_number = train.get("Train_Number")
                state.train_name = train.get("Train_Name")
                state.stage = "pax_count"
                state.menu_type = None

                # Get fare
                fare_key = CLASS_FARE_KEY.get(state.travel_class, "Fare_SL")
                state.fare_per_person = float(train.get(fare_key, 0))

                return ConversationResponse(
                    reply=f"Selected: {state.train_number} — {state.train_name}\n\nHow many passengers will be travelling? (1 to 6)",
                    state=state
                )

            if val_lower in train_name:
                state.train_id = train.get("ID")
                state.train_number = train.get("Train_Number")
                state.train_name = train.get("Train_Name")
                state.stage = "pax_count"
                state.menu_type = None

                fare_key = CLASS_FARE_KEY.get(state.travel_class, "Fare_SL")
                state.fare_per_person = float(train.get(fare_key, 0))

                return ConversationResponse(
                    reply=f"Selected: {state.train_number} — {state.train_name}\n\nHow many passengers will be travelling? (1 to 6)",
                    state=state
                )

        return ConversationResponse(
            reply="I didn't find that train. Please type the train number from the list above, like '12639'.",
            state=state
        )

    def _handle_stage_pax_count(self, value: str, state: BookingState) -> ConversationResponse:
        """Handle passenger count input."""
        count = parse_number(value)

        if count is None:
            return ConversationResponse(
                reply="How many passengers? Please enter a number from 1 to 6.",
                state=state
            )

        if count < 1:
            return ConversationResponse(
                reply="You need at least 1 passenger. How many will be travelling?",
                state=state
            )

        if count > 6:
            return ConversationResponse(
                reply="Maximum 6 passengers per booking. How many will be travelling?",
                state=state
            )

        state.pax_count = count
        state.passengers = []
        state.current_pax_index = 0
        state.pax_field = "name"
        state.stage = "pax_name"
        state.total_fare = state.fare_per_person * count

        return ConversationResponse(
            reply=f"{count} passenger(s).\n\nWhat is passenger 1's full name?",
            state=state
        )

    def _handle_stage_pax_name(self, value: str, state: BookingState) -> ConversationResponse:
        """Handle passenger name input."""
        name = value.strip().title()

        if not name or len(name) < 2:
            return ConversationResponse(
                reply="Please enter a valid name.",
                state=state
            )

        # Initialize or update current passenger
        if state.current_pax_index >= len(state.passengers):
            state.passengers.append({"name": name, "age": 0, "gender": ""})
        else:
            state.passengers[state.current_pax_index]["name"] = name

        state.stage = "pax_age"
        return ConversationResponse(
            reply=f"How old is {name}?",
            state=state
        )

    def _handle_stage_pax_age(self, value: str, state: BookingState) -> ConversationResponse:
        """Handle passenger age input."""
        age = parse_number(value)

        if age is None or age < 1 or age > 120:
            pax_name = state.passengers[state.current_pax_index]["name"]
            return ConversationResponse(
                reply=f"Please enter a valid age for {pax_name}. (1 to 120)",
                state=state
            )

        state.passengers[state.current_pax_index]["age"] = age
        state.stage = "pax_gender"
        pax_name = state.passengers[state.current_pax_index]["name"]

        return ConversationResponse(
            reply=f"What is {pax_name}'s gender? (Male / Female / Other)",
            state=state
        )

    def _handle_stage_pax_gender(self, value: str, state: BookingState) -> ConversationResponse:
        """Handle passenger gender input."""
        gender = parse_gender(value)

        if not gender:
            pax_name = state.passengers[state.current_pax_index]["name"]
            return ConversationResponse(
                reply=f"Please say Male, Female, or Other for {pax_name}.",
                state=state
            )

        state.passengers[state.current_pax_index]["gender"] = gender
        state.current_pax_index += 1

        # Check if more passengers needed
        if state.current_pax_index < state.pax_count:
            state.stage = "pax_name"
            return ConversationResponse(
                reply=f"What is passenger {state.current_pax_index + 1}'s full name?",
                state=state
            )
        else:
            # All passengers collected - show summary
            state.stage = "confirm"
            summary = self._build_booking_summary(state)
            return ConversationResponse(
                reply=f"All passengers collected.\n\n{summary}",
                state=state,
                trigger="show_confirm"
            )

    def _handle_stage_confirm(self, value: str, state: BookingState) -> ConversationResponse:
        """Handle booking confirmation."""
        val_lower = value.lower().strip()

        if val_lower in ["yes", "y", "ok", "confirm", "proceed", "book it", "go ahead", "sure", "correct"]:
            return ConversationResponse(
                reply="Booking your tickets now...",
                state=state,
                trigger="create_booking"
            )
        elif val_lower in ["no", "n", "cancel", "change", "wrong", "go back"]:
            state.menu_type = "change_menu"
            return ConversationResponse(
                reply="No problem! What would you like to change?\n1. Source station\n2. Destination station\n3. Travel date\n4. Travel class\n5. Passenger details",
                state=state,
                trigger="change_menu"
            )
        else:
            return ConversationResponse(
                reply="Please type YES to confirm the booking or NO to make changes.",
                state=state
            )

    # ─── Helper Methods ──────────────────────────────────────────────

    def _build_booking_summary(self, state: BookingState) -> str:
        """Build the booking summary message."""
        passengers_list = ""
        for i, pax in enumerate(state.passengers):
            passengers_list += f"   {i+1}. {pax['name']} — {pax['age']} yrs, {pax['gender']}\n"

        return BOOKING_SUMMARY_TEMPLATE.format(
            from_station=state.from_station,
            to_station=state.to_station,
            date_display=state.date_display,
            train_number=state.train_number,
            train_name=state.train_name,
            class_display=state.class_display,
            passengers_list=passengers_list.rstrip(),
            total_fare=int(state.total_fare)
        )

    def format_train_results(self, trains: List[Dict], state: BookingState) -> str:
        """Format train search results for display."""
        if not trains:
            return f"No trains found from {state.from_station} to {state.to_station} on {state.date_display} in {state.class_display} class.\n\nWould you like to:\n1. Try a different date\n2. Try a different class\n3. Change the route"

        fare_key = CLASS_FARE_KEY.get(state.travel_class, "Fare_SL")
        seat_key = CLASS_SEAT_KEY.get(state.travel_class, "Total_Seats_SL")

        lines = [f"Found {len(trains)} train(s):\n"]

        for i, train in enumerate(trains[:5], 1):
            train_num = train.get("Train_Number", "N/A")
            train_name = train.get("Train_Name", "Unknown")
            dep_time = train.get("Departure_Time", "N/A")
            arr_time = train.get("Arrival_Time", "N/A")
            fare = train.get(fare_key, 0)
            seats = train.get(seat_key, 0)
            status = "Available" if seats > 0 else "Limited"

            lines.append(f"{i}. {train_num} — {train_name}")
            lines.append(f"   Departs {dep_time} → Arrives {arr_time}")
            lines.append(f"   Fare: ₹{int(fare)} | Seats: {status}")
            lines.append("")

        lines.append("Type a train number to select it.")

        return "\n".join(lines)


# ══════════════════════════════════════════════════════════════════
#  SINGLETON INSTANCE
# ══════════════════════════════════════════════════════════════════

booking_conversation = BookingConversation()


# ══════════════════════════════════════════════════════════════════
#  UTILITY FUNCTIONS FOR ROUTES
# ══════════════════════════════════════════════════════════════════

def state_to_dict(state: BookingState) -> Dict:
    """Convert BookingState to dictionary for JSON serialization."""
    return asdict(state)


def dict_to_state(data: Dict) -> BookingState:
    """Convert dictionary to BookingState."""
    if not data:
        return BookingState()

    # Handle nested passengers list
    passengers = data.get("passengers", [])
    if passengers:
        data["passengers"] = [dict(p) for p in passengers]

    # Handle nested trains_list
    trains_list = data.get("trains_list", [])
    if trains_list:
        data["trains_list"] = [dict(t) for t in trains_list]

    # Remove any unknown fields
    known_fields = {f.name for f in BookingState.__dataclass_fields__.values()}
    clean_data = {k: v for k, v in data.items() if k in known_fields}

    return BookingState(**clean_data)
