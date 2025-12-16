from __future__ import annotations
from typing import Dict, List, Optional
import os
import requests


class LLM:
    def __init__(self) -> None:
        self.enabled = os.getenv("LLM_ENABLED", "false").lower() == "true"
        self.api_key = os.getenv("OPENAI_API_KEY", "")
        self.base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
        self.model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
        self.max_tokens = int(os.getenv("LLM_MAX_TOKENS", "350"))

    def explain_plan(self, mission_id: str, operator_intent: Optional[str], tasks: List[Dict]) -> Optional[str]:
        if not self.enabled or not self.api_key:
            return None

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "You are assisting a mission operator. Summarize the tasking plan.\n"
                        "Be concise. Explain why these tasks are prioritized. Mention tradeoffs if relevant.\n\n"
                        f"Mission: {mission_id}\n"
                        f"Intent: {operator_intent or 'not provided'}\n"
                        f"Tasks: {tasks}\n"
                    ),
                }
            ],
            "max_tokens": self.max_tokens,
        }

        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        r = requests.post(f"{self.base_url}/chat/completions", json=payload, headers=headers, timeout=20)
        r.raise_for_status()
        data = r.json()
        return data["choices"][0]["message"]["content"].strip()
