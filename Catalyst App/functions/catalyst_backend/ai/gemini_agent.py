"""
gemini_agent.py — Qwen-powered Railway AI Agent (via Zoho Catalyst).
Uses prompts.py for all system and skill prompts.
Supports intent detection, skill routing, and multi-turn conversation.
Implements resilience patterns: circuit breaker and exponential backoff.
"""

import os
import json
import logging
import time
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
    SKILL_TRAVEL_RECOMMENDATIONS,
    SKILL_FARE_CALCULATOR,
    SKILL_ADMIN_ANALYTICS,
    SKILL_TRAIN_SCHEDULE
)

from ai.qwen_client import qwen_client, qwen_breaker

logger = logging.getLogger(__name__)

# Map intent name → skill prompt
SKILL_MAP = {
    "search_trains":      SKILL_SEARCH_TRAINS,
    "book_ticket":        SKILL_BOOK_TICKET,
    "pnr_status":         SKILL_PNR_STATUS,
    "cancel_booking":     SKILL_CANCEL_BOOKING,
    "seat_availability":   SKILL_SEAT_AVAILABILITY,
    "fare_calculator":     SKILL_FARE_CALCULATOR,
    "travel_recommend":   SKILL_TRAVEL_RECOMMENDATIONS,
    "train_schedule":     SKILL_TRAIN_SCHEDULE,
    "admin_analytics":    SKILL_ADMIN_ANALYTICS,
}


class GeminiRailwayAgent:
    """
    Qwen-based Railway AI Agent with skill routing and resilience patterns.
    (Class name kept for backward compatibility)
    
    Features:
    - Circuit breaker to prevent cascading failures
    - Exponential backoff retry logic
    - Multi-turn conversation support
    - Intent detection and skill routing
    """

    def __init__(self):
        """Initialize the Railway Agent."""
        logger.info("Railway AI Agent initialized with Qwen via Zoho Catalyst")

    # ── Core API call ─────────────────────────────────────────────────────────

    def _call_qwen(
        self,
        system_prompt: str,
        history: list,
        user_message: str,
        max_tokens: int = 1024,
        temperature: float = 0.3,
    ) -> str:
        """
        Call Qwen via Zoho Catalyst with circuit breaker and retry logic.
        
        Args:
            system_prompt: System instructions for the model
            history: Conversation history (list of dicts with 'role' and 'content')
            user_message: Current user message
            max_tokens: Maximum tokens in response
            temperature: Temperature for response generation
        
        Returns:
            str: Model response or fallback message if service unavailable
        """
        # Check if circuit breaker allows execution
        if not qwen_breaker.can_execute():
            logger.warning(f"Qwen circuit breaker is {qwen_breaker.state} - using fallback")
            return self._get_fallback_response()

        # Build messages list
        messages = []
        
        # Add conversation history (last 20 messages to fit within token limits)
        for msg in history[-20:]:
            role = msg.get("role", "user")
            content = msg.get("content", "").strip()
            if not content:
                continue
            messages.append({"role": role, "content": content})
        
        # Add current user message
        messages.append({"role": "user", "content": user_message})

        response = qwen_client.chat(
            messages=messages,
            system_prompt=system_prompt,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        if response:
            return response
        else:
            return self._get_fallback_response()

    def _get_fallback_response(self) -> str:
        """Return a fallback response when circuit breaker is open."""
        state = qwen_breaker.state
        if state == "open":
            return "AI service is currently unavailable due to high load or repeated errors. Please try again in a few minutes."
        elif state == "half_open":
            return "AI service is recovering from a recent issue. Please try again shortly."
        else:
            return "AI service is temporarily unavailable. Please try again later."

    def get_breaker_stats(self) -> dict:
        """Get circuit breaker statistics for monitoring."""
        return qwen_breaker.stats()

    # ── Intent Detection ──────────────────────────────────────────────────────

    def detect_intent(self, user_message: str) -> str:
        """Detect user intent from their message."""
        response = self._call_qwen(
            INTENT_DETECTION_PROMPT,
            [],
            user_message,
            max_tokens=50
        )
        
        # Extract intent from response (typically one word)
        intent = response.strip().lower().split()[0] if response else "unknown"
        logger.debug(f"Detected intent: {intent}")
        return intent

    def extract_entities(self, user_message: str) -> dict:
        """Extract entities from user message."""
        response = self._call_qwen(
            ENTITY_EXTRACTION_PROMPT,
            [],
            user_message,
            max_tokens=200
        )
        
        try:
            # Clean up response
            text = response.strip().replace("```json", "").replace("```", "").strip()
            entities = json.loads(text)
            logger.debug(f"Extracted entities: {entities}")
            return entities
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse entities from response: {response}")
            return {}

    # ── Main conversation method ──────────────────────────────────────────────

    def chat(self, user_message: str, history: list = None, user_role: str = "User") -> dict:
        """
        Main chat interface for the user.
        
        Args:
            user_message: The user's message
            history: Conversation history (optional)
            user_role: User's role (User/Admin)
        
        Returns:
            dict: Response with intent, message, and other data
        """
        if history is None:
            history = []
        
        # Detect intent
        intent = self.detect_intent(user_message)
        
        # Select skill prompt based on intent
        skill_prompt = SKILL_MAP.get(intent, AGENT_SYSTEM_PROMPT)
        
        # Get response from Qwen
        response = self._call_qwen(
            skill_prompt,
            history,
            user_message,
            max_tokens=1024
        )
        
        return {
            "intent": intent,
            "response": response,
            "message": response,
        }


# Singleton instance
gemini_agent = GeminiRailwayAgent()
