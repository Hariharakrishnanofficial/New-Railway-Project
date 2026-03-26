"""
gemini_agent.py — Gemini-powered Railway AI Agent.
Uses prompts.py for all system and skill prompts.
Supports intent detection, skill routing, and multi-turn conversation.
"""

import os
import json
import logging
import requests
from datetime import datetime, timedelta
from ai.prompts import (
    AGENT_SYSTEM_PROMPT,
    INTENT_DETECTION_PROMPT,
    ENTITY_EXTRACTION_PROMPT,
    SKILL_SEARCH_TRAINS,
    SKILL_BOOK_TICKET,
    SKILL_PNR_STATUS,
    SKILL_CANCEL_BOOKING,
    SKILL_SEAT_AVAILABILITY,
    SKILL_FARE_CALCULATOR,
    SKILL_TRAVEL_RECOMMENDATIONS,
    SKILL_TRAIN_SCHEDULE,
    SKILL_ADMIN_ANALYTICS,
)

logger = logging.getLogger(__name__)

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
GEMINI_URL   = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"

# Map intent name → skill prompt
SKILL_MAP = {
    "search_trains":      SKILL_SEARCH_TRAINS,
    "book_ticket":        SKILL_BOOK_TICKET,
    "pnr_status":         SKILL_PNR_STATUS,
    "cancel_booking":     SKILL_CANCEL_BOOKING,
    "seat_availability":  SKILL_SEAT_AVAILABILITY,
    "fare_calculator":    SKILL_FARE_CALCULATOR,
    "travel_recommend":   SKILL_TRAVEL_RECOMMENDATIONS,
    "train_schedule":     SKILL_TRAIN_SCHEDULE,
    "admin_analytics":    SKILL_ADMIN_ANALYTICS,
}


class GeminiRailwayAgent:
    """
    Gemini-based Railway AI Agent with skill routing.

    Flow:
      1. Detect intent from user message
      2. Extract entities (stations, dates, class etc.)
      3. Build full prompt = system prompt + skill prompt + conversation history
      4. Send to Gemini API
      5. Return structured response
    """

    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY", "")
        self.model   = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
        self.url     = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
        if not self.api_key:
            logger.warning("GEMINI_API_KEY not set — Gemini agent disabled")

    # ── Core API call ─────────────────────────────────────────────────────────

    def _call_gemini(
        self,
        system_prompt: str,
        history: list,
        user_message: str,
        max_tokens: int = 1024,
        temperature: float = 0.3,
    ) -> str:
        """
        Call Gemini generateContent endpoint.

        Gemini does not have a dedicated 'system' role like Claude.
        We prepend the system prompt as the very first user turn,
        followed by a model acknowledgement, then the real conversation.
        This is the standard pattern for Gemini multi-turn with a system prompt.
        """
        if not self.api_key:
            return "Gemini API key not configured. Set GEMINI_API_KEY in your .env file."

        # Build contents list
        # Format: system injected as first user+model pair, then real history, then current message
        contents = []

        # Inject system prompt as first exchange
        contents.append({
            "role": "user",
            "parts": [{"text": f"[SYSTEM INSTRUCTIONS]\n{system_prompt}"}],
        })
        contents.append({
            "role": "model",
            "parts": [{"text": "Understood. I am RailwayAI and will follow these instructions."}],
        })

        # Add conversation history (last 20 turns)
        for msg in history[-20:]:
            role    = msg.get("role", "user")
            content = msg.get("content", "").strip()
            if not content:
                continue
            # Gemini uses "model" not "assistant"
            gemini_role = "model" if role == "assistant" else "user"
            contents.append({
                "role":  gemini_role,
                "parts": [{"text": content}],
            })

        # Add current user message
        contents.append({
            "role":  "user",
            "parts": [{"text": user_message}],
        })

        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature":     temperature,
                "maxOutputTokens": max_tokens,
            },
        }

        try:
            resp = requests.post(
                f"{self.url}?key={self.api_key}",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30,
            )

            if resp.status_code != 200:
                logger.error(f"Gemini API error {resp.status_code}: {resp.text[:300]}")
                return f"Gemini API error: HTTP {resp.status_code}"

            data = resp.json()

            # Extract text from response
            candidates = data.get("candidates", [])
            if not candidates:
                return "No response from Gemini."

            parts = candidates[0].get("content", {}).get("parts", [])
            if not parts:
                return "Empty response from Gemini."

            return parts[0].get("text", "").strip()

        except requests.exceptions.Timeout:
            return "Request timed out. Please try again."
        except Exception as exc:
            logger.exception(f"Gemini call failed: {exc}")
            return "AI service unavailable. Please try again."

    # ── Intent detection ──────────────────────────────────────────────────────

    def detect_intent(self, user_message: str) -> str:
        """Classify user message into one of the defined intents."""
        result = self._call_gemini(
            system_prompt = INTENT_DETECTION_PROMPT,
            history       = [],
            user_message  = user_message,
            max_tokens    = 20,
            temperature   = 0.0,   # deterministic for classification
        )
        intent = result.strip().lower().replace(" ", "_").replace("-", "_")

        # Validate — fall back to general_chat if unrecognised
        if intent not in SKILL_MAP and intent != "general_chat":
            logger.debug(f"Unrecognised intent '{intent}' — falling back to general_chat")
            return "general_chat"

        return intent

    # ── Entity extraction ─────────────────────────────────────────────────────

    def extract_entities(self, user_message: str) -> dict:
        """Extract structured entities (stations, date, class etc.) from user message."""
        today  = datetime.now()
        prompt = ENTITY_EXTRACTION_PROMPT.format(
            today      = today.strftime("%Y-%m-%d"),
            tomorrow   = (today + timedelta(days=1)).strftime("%Y-%m-%d"),
            day_after  = (today + timedelta(days=2)).strftime("%Y-%m-%d"),
        )

        raw = self._call_gemini(
            system_prompt = prompt,
            history       = [],
            user_message  = user_message,
            max_tokens    = 300,
            temperature   = 0.0,
        )

        # Strip markdown fences if Gemini added them
        clean = raw.replace("```json", "").replace("```", "").strip()

        try:
            return json.loads(clean)
        except Exception:
            logger.debug(f"Entity extraction JSON parse failed: {clean[:100]}")
            return {}

    # ── Main chat entry point ─────────────────────────────────────────────────

    def chat(
        self,
        user_message: str,
        history: list = [],
        user_role: str = "User",
    ) -> dict:
        """
        Main entry point for agent conversation.

        Args:
            user_message : Current user input text
            history      : List of {role, content} dicts from previous turns
            user_role    : "User" or "Admin" — controls admin skill access

        Returns:
            {
              "response":   "...",
              "intent":     "search_trains",
              "entities":   { "source_station": "MAS", ... },
              "skill_used": "search_trains"
            }
        """
        # 1. Detect intent
        intent = self.detect_intent(user_message)

        # 2. Block admin-only skills from regular users
        if intent == "admin_analytics" and user_role != "Admin":
            return {
                "response":   "That feature is only available to administrators.",
                "intent":     intent,
                "entities":   {},
                "skill_used": None,
            }

        # 3. Get matching skill prompt
        skill_prompt = SKILL_MAP.get(intent, "")

        # 4. Build combined system prompt
        system = AGENT_SYSTEM_PROMPT
        if skill_prompt:
            system += f"\n\n---\nACTIVE SKILL:\n{skill_prompt}"

        # 5. Extract entities in parallel (reuse same message)
        entities = self.extract_entities(user_message)

        # 6. Call Gemini with full conversation history
        response = self._call_gemini(
            system_prompt = system,
            history       = history,
            user_message  = user_message,
            max_tokens    = 1024,
            temperature   = 0.3,
        )

        return {
            "response":   response,
            "intent":     intent,
            "entities":   entities,
            "skill_used": intent if skill_prompt else None,
        }


# Singleton — import this in routes
gemini_agent = GeminiRailwayAgent()