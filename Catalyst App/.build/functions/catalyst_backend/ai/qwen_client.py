"""
qwen_client.py — Centralized Qwen API client via Zoho Catalyst QuickML.
Used by all AI modules: NLP search, booking assistant, analytics AI, agent.
Includes circuit breaker pattern for resilience.
"""

import os
import json
import logging
import requests
import time
from typing import Optional

logger = logging.getLogger(__name__)

# Zoho Catalyst QuickML LLM endpoint
CATALYST_PROJECT_ID = "31207000000011084"
QWEN_API_URL = f"https://api.catalyst.zoho.in/quickml/v2/project/{CATALYST_PROJECT_ID}/llm/chat"


class QwenCircuitBreaker:
    """
    Simple circuit breaker for Qwen API calls.
    States: closed (normal) -> open (failing) -> half_open (testing)
    """

    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 300):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failures = 0
        self.last_failure_time = 0
        self.state = "closed"

    def can_execute(self) -> bool:
        """Check if circuit allows execution."""
        if self.state == "closed":
            return True
        if self.state == "open":
            # Check if recovery timeout has passed
            if time.time() - self.last_failure_time >= self.recovery_timeout:
                self.state = "half_open"
                return True
            return False
        # half_open state allows one test call
        return True

    def record_success(self):
        """Record successful API call."""
        self.failures = 0
        self.state = "closed"

    def record_failure(self):
        """Record failed API call."""
        self.failures += 1
        self.last_failure_time = time.time()
        if self.failures >= self.failure_threshold:
            self.state = "open"
            logger.warning(f"Qwen circuit breaker OPEN after {self.failures} failures")

    def stats(self) -> dict:
        return {
            "state": self.state,
            "failures": self.failures,
            "threshold": self.failure_threshold,
        }


# Global circuit breaker instance
qwen_breaker = QwenCircuitBreaker()


class QwenClient:
    """
    Qwen API client via Zoho Catalyst QuickML.
    Provides unified interface for all AI modules.
    """

    def __init__(self):
        self.api_url = QWEN_API_URL
        self.max_retries = 3

    def _get_headers(self) -> dict:
        """Get headers for Catalyst QuickML API."""
        access_token = os.getenv('CATALYST_ACCESS_TOKEN', '')
        if not access_token:
            logger.warning("CATALYST_ACCESS_TOKEN not set - Qwen API calls may fail")
        return {
            "Content-Type": "application/json",
            "Authorization": f"Zoho-oauthtoken {access_token}",
            "CATALYST-ORG": os.getenv("CATALYST_ORG", "60066581545"),
        }

    def _build_prompt(self, messages: list, system_prompt: str = "") -> tuple:
        """Convert chat messages into prompt + system_prompt for Catalyst QuickML.

        Returns:
            (prompt_text, system_prompt_text) tuple
        """
        sys_parts = []
        if system_prompt:
            sys_parts.append(system_prompt)

        prompt_parts = []
        for msg in messages:
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            if role == 'system':
                sys_parts.append(content)
            elif role == 'assistant':
                prompt_parts.append(f"Assistant: {content}")
            else:
                prompt_parts.append(content)

        combined_system = "\n\n".join(sys_parts) if sys_parts else ""
        combined_prompt = "\n\n".join(prompt_parts) if prompt_parts else ""
        return combined_prompt, combined_system

    def chat(
        self,
        messages: list,
        system_prompt: str = "",
        max_tokens: int = 2048,
        temperature: float = 0.7,
        timeout: int = 60
    ) -> Optional[str]:
        """
        Send chat request to Qwen via Zoho Catalyst QuickML.

        Uses JSON body with 'prompt' field as required by the Catalyst API.

        Args:
            messages: List of message dicts with 'role' and 'content'
            system_prompt: Optional system instructions
            max_tokens: Maximum tokens in response
            temperature: Response randomness (0.0-1.0)
            timeout: Request timeout in seconds

        Returns:
            Response text or None on error
        """
        if not qwen_breaker.can_execute():
            logger.warning("Qwen circuit breaker is OPEN - using fallback")
            return None

        prompt_text, sys_text = self._build_prompt(messages, system_prompt)

        payload = {
            "prompt": prompt_text,
            "model": os.getenv("CATALYST_MODEL", "crm-di-qwen_text_14b-fp8-it"),
            "system_prompt": sys_text,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": 0.9,
            "top_k": 50,
            "best_of": 1,
        }

        backoff = 1
        for attempt in range(self.max_retries):
            try:
                logger.debug(f"Qwen API call attempt {attempt + 1}/{self.max_retries}")
                response = requests.post(
                    self.api_url,
                    headers=self._get_headers(),
                    json=payload,
                    timeout=timeout
                )

                if response.status_code == 200:
                    qwen_breaker.record_success()
                    result = response.json()
                    # Extract response text from Catalyst format
                    return self._extract_response(result)

                elif response.status_code == 429:
                    logger.warning(f"Qwen rate limited (429). Retrying in {backoff}s...")
                    qwen_breaker.record_failure()
                    time.sleep(backoff)
                    backoff = min(backoff * 2, 16)
                    continue

                elif response.status_code >= 500:
                    logger.warning(f"Qwen server error ({response.status_code}). Retrying...")
                    qwen_breaker.record_failure()
                    time.sleep(backoff)
                    backoff = min(backoff * 2, 16)
                    continue

                else:
                    logger.error(f"Qwen API error: {response.status_code} - {response.text}")
                    qwen_breaker.record_failure()
                    return None

            except requests.exceptions.Timeout:
                logger.warning(f"Qwen API timeout. Retrying...")
                qwen_breaker.record_failure()
                time.sleep(backoff)
                backoff = min(backoff * 2, 16)
                continue

            except requests.exceptions.RequestException as e:
                logger.error(f"Qwen network error: {e}")
                qwen_breaker.record_failure()
                return None

        logger.error(f"Qwen API failed after {self.max_retries} retries")
        return None

    def _extract_response(self, result: dict) -> Optional[str]:
        """Extract response text from Catalyst API response."""
        try:
            logger.debug(f"Extracting response from: {json.dumps(result)[:500]}")
            
            # Try OpenAI-compatible format
            if "choices" in result and result["choices"]:
                choice = result["choices"][0]
                if isinstance(choice, dict):
                    msg = choice.get("message", {})
                    if isinstance(msg, dict):
                        return msg.get("content", "")
                    return str(msg)
            
            # Try direct message format
            if "message" in result:
                msg = result["message"]
                if isinstance(msg, dict):
                    return msg.get("content", str(msg))
                return str(msg)
            
            # Try direct response format
            if "response" in result:
                resp = result["response"]
                if isinstance(resp, dict):
                    return resp.get("content", str(resp))
                return str(resp)
            
            # Try content field
            if "content" in result:
                return result["content"]
            
            # Try output field
            if "output" in result:
                return result["output"]
            
            # Try text field
            if "text" in result:
                return result["text"]
            
            # Return raw result as string if we can't parse
            logger.warning(f"Unexpected Qwen response format: {json.dumps(result)[:200]}")
            return json.dumps(result)
            
        except Exception as e:
            logger.error(f"Failed to extract Qwen response: {e}")
            return None

    def generate_json(
        self,
        prompt: str,
        system_prompt: str = "",
        max_tokens: int = 1024,
        temperature: float = 0.1
    ) -> Optional[dict]:
        """
        Generate JSON response from Qwen.
        Useful for structured outputs like intent detection, entity extraction.
        
        Returns:
            Parsed JSON dict or None on error
        """
        messages = [{"role": "user", "content": prompt}]
        response = self.chat(
            messages=messages,
            system_prompt=system_prompt,
            max_tokens=max_tokens,
            temperature=temperature
        )

        if not response:
            return None

        # Clean up response (remove markdown code blocks if present)
        text = response.strip()
        text = text.replace("```json", "").replace("```", "").strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON from Qwen response: {e}")
            logger.debug(f"Raw response: {text[:500]}")
            return None


# Singleton instance
qwen_client = QwenClient()
