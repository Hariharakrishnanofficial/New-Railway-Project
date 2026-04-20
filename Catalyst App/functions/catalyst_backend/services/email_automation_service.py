"""
Email automation service for MailBot.

Stores settings and thread state in the existing Settings table so the feature
works without a schema migration. Thread state is persisted as JSON blobs under
distinct Type_field values.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import requests

from config import TABLES
from repositories.cloudscale_repository import CriteriaBuilder, cloudscale_repo

logger = logging.getLogger(__name__)


SETTINGS_TYPE = "EmailAutomationSettings"
THREAD_TYPE = "EmailAutomationThread"

DEFAULT_SETTINGS: Dict[str, Any] = {
    "enabled": False,
    "openai_model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
    "temperature": 0.3,
    "max_tokens": 220,
    "max_turns": 4,
    "from_address": os.getenv("EMAIL_FROM_ADDRESS", ""),
    "system_prompt": (
        "You are MailBot, a professional email assistant. "
        "Reply concisely, helpfully, and with a calm tone. "
        "Use the provided thread context only. "
        "If the message is ambiguous, ask one clear follow-up question. "
        "Keep replies under 120 words unless the user explicitly asks for more detail."
    ),
    "signature": "",
    "review_keywords": [
        "refund",
        "chargeback",
        "legal",
        "lawyer",
        "fraud",
        "scam",
        "abuse",
        "angry",
        "cancel my account",
        "complaint",
        "lawsuit",
        "privacy",
        "data breach",
    ],
    "no_reply_patterns": [
        "no-reply",
        "noreply",
        "do-not-reply",
        "do_not_reply",
        "donotreply",
    ],
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_json_load(value: Any, fallback: Any) -> Any:
    if value is None:
        return fallback
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(str(value))
    except Exception:
        return fallback


def _safe_json_dump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def _normalize_email(email: str) -> str:
    return (email or "").strip().lower()


class EmailAutomationService:
    def get_thread(self, thread_key: str) -> Dict[str, Any]:
        """Fetch a single persisted thread state by its Settings.Key."""
        return self._load_thread_record(thread_key) or {}

    def load_settings(self) -> Dict[str, Any]:
        criteria = CriteriaBuilder().eq("Type_field", SETTINGS_TYPE).eq("Key", "GLOBAL").build()
        rows = cloudscale_repo.get_records(TABLES["settings"], criteria=criteria, limit=1)
        if not rows:
            return {**DEFAULT_SETTINGS, "record_id": None}

        row = rows[0]
        persisted = _safe_json_load(row.get("Value"), {})
        merged = {**DEFAULT_SETTINGS, **(persisted or {})}
        # Normalize list-based fields (older rows may not have arrays).
        merged["review_keywords"] = (
            merged["review_keywords"] if isinstance(merged.get("review_keywords"), list) else DEFAULT_SETTINGS["review_keywords"]
        )
        merged["no_reply_patterns"] = (
            merged["no_reply_patterns"] if isinstance(merged.get("no_reply_patterns"), list) else DEFAULT_SETTINGS["no_reply_patterns"]
        )
        merged["record_id"] = row.get("ID")
        return merged

    def save_settings(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        current = self.load_settings()
        merged = {**current, **payload}

        # Persist only the automation payload, not helper keys.
        persisted = dict(merged)
        persisted.pop("record_id", None)

        row_payload = {
            "Type_field": SETTINGS_TYPE,
            "Key": "GLOBAL",
            "Value": _safe_json_dump(persisted),
            "Description": "MailBot automation settings",
            "Is_Active": "true" if bool(persisted.get("enabled")) else "false",
        }

        if current.get("record_id"):
            result = cloudscale_repo.update_record(TABLES["settings"], current["record_id"], row_payload)
        else:
            result = cloudscale_repo.create_record(TABLES["settings"], row_payload)

        if not result.get("success"):
            raise RuntimeError(result.get("error", "Unable to save settings"))

        return self.load_settings()

    def list_threads(self, limit: int = 50, status: Optional[str] = None) -> Dict[str, Any]:
        criteria = CriteriaBuilder().eq("Type_field", THREAD_TYPE).build()
        rows = cloudscale_repo.get_records(TABLES["settings"], criteria=criteria, limit=limit)

        threads: List[Dict[str, Any]] = []
        for row in rows:
            state = _safe_json_load(row.get("Value"), {})
            if not isinstance(state, dict):
                continue
            if status and str(state.get("status", "")).lower() != status.lower():
                continue
            state["record_id"] = row.get("ID")
            threads.append(state)

        threads.sort(key=lambda t: str(t.get("updated_at", "")), reverse=True)

        stats = {
            "total_threads": len(threads),
            "auto_replied": sum(1 for t in threads if t.get("status") == "auto_replied"),
            "manual_review": sum(1 for t in threads if t.get("status") == "manual_review"),
            "paused": sum(1 for t in threads if t.get("status") == "paused"),
            "errors": sum(1 for t in threads if t.get("status") == "error"),
        }

        return {"threads": threads, "stats": stats}

    def _load_thread_record(self, thread_key: str) -> Dict[str, Any]:
        criteria = CriteriaBuilder().eq("Type_field", THREAD_TYPE).eq("Key", thread_key).build()
        rows = cloudscale_repo.get_records(TABLES["settings"], criteria=criteria, limit=1)
        if not rows:
            return {}

        row = rows[0]
        state = _safe_json_load(row.get("Value"), {})
        if not isinstance(state, dict):
            state = {}
        state["record_id"] = row.get("ID")
        return state

    def _save_thread_state(self, thread_key: str, state: Dict[str, Any]) -> Dict[str, Any]:
        payload = dict(state)
        payload.pop("record_id", None)
        row_payload = {
            "Type_field": THREAD_TYPE,
            "Key": thread_key,
            "Value": _safe_json_dump(payload),
            "Description": f"{payload.get('sender_email', '')} | {payload.get('subject', '')}",
            "Is_Active": "true" if payload.get("status") not in {"paused", "manual_review", "error"} else "false",
        }

        existing_id = state.get("record_id")
        if existing_id:
            result = cloudscale_repo.update_record(TABLES["settings"], existing_id, row_payload)
        else:
            result = cloudscale_repo.create_record(TABLES["settings"], row_payload)

        if not result.get("success"):
            raise RuntimeError(result.get("error", "Unable to save thread state"))

        return self._load_thread_record(thread_key)

    def build_thread_key(self, thread_id: Optional[str], sender_email: str, subject: str) -> str:
        if thread_id:
            return f"thread:{thread_id}"
        basis = f"{_normalize_email(sender_email)}|{(subject or '').strip().lower()}"
        digest = hashlib.sha1(basis.encode("utf-8")).hexdigest()[:16]
        return f"thread:{digest}"

    def is_no_reply_sender(self, sender_email: str, sender_name: str, settings: Dict[str, Any]) -> bool:
        text = f"{sender_email} {sender_name}".lower()
        patterns = settings.get("no_reply_patterns") or DEFAULT_SETTINGS["no_reply_patterns"]
        if not isinstance(patterns, list):
            patterns = DEFAULT_SETTINGS["no_reply_patterns"]
        return any(str(pattern).lower() in text for pattern in patterns)

    def classify_risk(self, text: str, settings: Dict[str, Any]) -> Dict[str, Any]:
        content = (text or "").strip().lower()
        reasons: List[str] = []

        if not content:
            reasons.append("empty message")

        if len(content) < 18:
            reasons.append("very short message")

        review_keywords = settings.get("review_keywords") or DEFAULT_SETTINGS["review_keywords"]
        if not isinstance(review_keywords, list):
            review_keywords = DEFAULT_SETTINGS["review_keywords"]

        if any(str(word).lower() in content for word in review_keywords):
            reasons.append("review keyword hit")

        if any(word in content for word in ("angry", "furious", "terrible", "awful", "worst", "useless", "idiot")):
            reasons.append("negative sentiment")

        if any(word in content for word in ("cancel my account", "delete my data", "lawsuit", "chargeback")):
            reasons.append("high-risk request")

        if content.count("?") >= 3:
            reasons.append("ambiguous question stream")

        should_escalate = bool(reasons)
        severity = "high" if any(reason in reasons for reason in ("sensitive topic", "high-risk request")) else ("medium" if reasons else "low")
        return {
            "should_escalate": should_escalate,
            "severity": severity,
            "reasons": reasons,
        }

    def _build_messages(self, state: Dict[str, Any], payload: Dict[str, Any], settings: Dict[str, Any]) -> List[Dict[str, str]]:
        system_prompt = settings.get("system_prompt") or DEFAULT_SETTINGS["system_prompt"]
        history = state.get("history") or []

        messages: List[Dict[str, str]] = [{"role": "system", "content": system_prompt}]

        for item in history[-12:]:
            role = item.get("role")
            content = item.get("content")
            if role in {"user", "assistant"} and content:
                messages.append({"role": role, "content": str(content)})

        inbound_lines = [
            f"Sender: {payload.get('sender_name') or payload.get('sender_email') or 'Customer'}",
            f"Subject: {payload.get('subject') or ''}".strip(),
            f"Thread context: {payload.get('thread_id') or payload.get('thread_key') or 'unknown'}",
            "",
            (payload.get("body") or "").strip(),
        ]
        messages.append({"role": "user", "content": "\n".join(line for line in inbound_lines if line is not None).strip()})
        return messages

    def generate_reply(self, messages: List[Dict[str, str]], settings: Dict[str, Any]) -> Dict[str, Any]:
        api_key = os.getenv("OPENAI_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is not configured")

        model = (settings.get("openai_model") or os.getenv("OPENAI_MODEL") or "gpt-4o-mini").strip()
        temperature = float(settings.get("temperature", 0.3))
        max_tokens = int(settings.get("max_tokens", 220))

        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
            timeout=60,
        )

        if response.status_code >= 400:
            raise RuntimeError(f"OpenAI request failed ({response.status_code}): {response.text}")

        data = response.json()
        reply = (
            data.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
            .strip()
        )
        if not reply:
            raise RuntimeError("OpenAI returned an empty reply")

        return {
            "reply": reply,
            "model": model,
            "usage": data.get("usage", {}),
            "raw_response": data,
        }

    def send_reply_adapter(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send the generated reply through an adapter.

        If the deployment has a Zoho Mail/MCP bridge configured, this method can
        forward the payload there. Otherwise it returns a dry-run success so the
        rest of the automation pipeline remains testable.
        """

        send_url = (
            os.getenv("EMAIL_SEND_ADAPTER_URL", "").strip()
            or os.getenv("ZOHO_MAIL_SEND_URL", "").strip()
            or os.getenv("ZOHO_MCP_URL", "").strip()
        )

        if send_url:
            response = requests.post(send_url, json=payload, timeout=30)
            if response.status_code >= 400:
                raise RuntimeError(f"Send adapter failed ({response.status_code}): {response.text}")
            try:
                return response.json()
            except Exception:
                return {"success": True, "raw_response": response.text}

        return {
            "success": True,
            "dry_run": True,
            "message": "No outbound mail adapter configured; stored as a simulated send.",
        }

    def process_inbound_reply(self, payload: Dict[str, Any], force: bool = False) -> Dict[str, Any]:
        settings = self.load_settings()
        if not settings.get("enabled") and not force:
            return {
                "success": True,
                "status": "paused",
                "should_reply": False,
                "reason": "Auto-response is disabled",
                "settings": settings,
            }

        sender_email = _normalize_email(payload.get("sender_email") or payload.get("from_email"))
        sender_name = (payload.get("sender_name") or "").strip()
        subject = (payload.get("subject") or "").strip()
        body = (payload.get("body") or payload.get("content") or "").strip()
        thread_id = (payload.get("thread_id") or payload.get("threadId") or "").strip() or None
        message_id = (payload.get("message_id") or payload.get("messageId") or "").strip() or None

        thread_key = self.build_thread_key(thread_id, sender_email, subject)
        state = self._load_thread_record(thread_key) or {
            "thread_key": thread_key,
            "thread_id": thread_id,
            "sender_email": sender_email,
            "sender_name": sender_name,
            "subject": subject,
            "status": "active",
            "turn_count": 0,
            "processed_message_ids": [],
            "history": [],
            "manual_review_reasons": [],
            "created_at": _utc_now(),
            "updated_at": _utc_now(),
            "last_inbound_message_id": None,
            "last_reply_text": "",
            "last_error": "",
            "needs_human_review": False,
        }

        processed_message_ids = list(state.get("processed_message_ids") or [])
        if message_id and message_id in processed_message_ids:
            state["status"] = "duplicate"
            state["updated_at"] = _utc_now()
            self._save_thread_state(thread_key, state)
            return {
                "success": True,
                "status": "duplicate",
                "should_reply": False,
                "thread": state,
            }

        if self.is_no_reply_sender(sender_email, sender_name, settings):
            state["status"] = "ignored"
            state["last_error"] = "No-reply/system sender"
            state["updated_at"] = _utc_now()
            self._save_thread_state(thread_key, state)
            return {
                "success": True,
                "status": "ignored",
                "should_reply": False,
                "reason": "No-reply/system sender",
                "thread": state,
            }

        risk = self.classify_risk(body, settings)
        max_turns = int(settings.get("max_turns", 4))
        if risk["should_escalate"] and not force:
            state["status"] = "manual_review"
            state["needs_human_review"] = True
            state["manual_review_reasons"] = risk["reasons"]
            state["last_error"] = "; ".join(risk["reasons"])
            state["updated_at"] = _utc_now()
            self._save_thread_state(thread_key, state)
            return {
                "success": True,
                "status": "manual_review",
                "should_reply": False,
                "risk": risk,
                "thread": state,
            }

        if int(state.get("turn_count", 0)) >= max_turns and not force:
            state["status"] = "paused"
            state["last_error"] = f"Max turns reached ({max_turns})"
            state["updated_at"] = _utc_now()
            self._save_thread_state(thread_key, state)
            return {
                "success": True,
                "status": "paused",
                "should_reply": False,
                "reason": state["last_error"],
                "thread": state,
            }

        messages = self._build_messages(
            state,
            {
                **payload,
                "sender_email": sender_email,
                "sender_name": sender_name,
                "subject": subject,
                "body": body,
                "thread_id": thread_id,
                "thread_key": thread_key,
            },
            settings,
        )

        llm_result = self.generate_reply(messages, settings)
        reply_text = llm_result["reply"]

        if settings.get("signature"):
            signature = str(settings.get("signature")).strip()
            if signature:
                reply_text = f"{reply_text}\n\n{signature}"

        adapter_result = self.send_reply_adapter(
            {
                "from_address": settings.get("from_address") or payload.get("from_address") or os.getenv("EMAIL_FROM_ADDRESS", ""),
                "to_address": sender_email,
                "thread_id": thread_id,
                "message_id": message_id,
                "subject": subject,
                "content": reply_text,
                "action": "reply",
            }
        )

        history = list(state.get("history") or [])
        history.append(
            {
                "role": "user",
                "message_id": message_id,
                "content": body,
                "created_at": _utc_now(),
            }
        )
        history.append(
            {
                "role": "assistant",
                "message_id": adapter_result.get("message_id") or None,
                "content": reply_text,
                "created_at": _utc_now(),
            }
        )
        history = history[-20:]

        if message_id:
            processed_message_ids.append(message_id)

        state.update(
            {
                "thread_id": thread_id,
                "sender_email": sender_email,
                "sender_name": sender_name,
                "subject": subject,
                "status": "auto_replied",
                "needs_human_review": False,
                "manual_review_reasons": [],
                "turn_count": int(state.get("turn_count", 0)) + 1,
                "processed_message_ids": processed_message_ids[-50:],
                "history": history,
                "last_inbound_message_id": message_id,
                "last_reply_text": reply_text,
                "last_error": "",
                "last_model": llm_result.get("model"),
                "updated_at": _utc_now(),
                "last_delivery": adapter_result,
            }
        )

        saved = self._save_thread_state(thread_key, state)
        return {
            "success": True,
            "status": "auto_replied",
            "should_reply": True,
            "reply_text": reply_text,
            "thread": saved,
            "risk": risk,
            "adapter_result": adapter_result,
            "llm_usage": llm_result.get("usage", {}),
        }


email_automation_service = EmailAutomationService()
