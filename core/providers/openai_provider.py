"""OpenAI-compatible provider for the AI Development Agent System.

Supports OpenAI, DeepSeek, and any OpenAI-compatible API endpoints.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

import httpx

from core.llm_interface import LLMProvider


class OpenAIProvider(LLMProvider):
    """Provider for OpenAI-compatible APIs (OpenAI, DeepSeek, etc.).
    
    Configuration via environment variables:
    - OPENAI_API_KEY: Your API key (required)
    - OPENAI_BASE_URL: API base URL (default: https://api.deepseek.com)
    - OPENAI_MODEL: Model name (default: gpt-4o)
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
    ):
        """Initialize the OpenAI provider.
        
        Args:
            api_key: API key. If None, reads from OPENAI_API_KEY env var.
            base_url: API base URL. If None, reads from OPENAI_BASE_URL env var
                     or defaults to https://api.deepseek.com.
            model: Model name. If None, reads from OPENAI_MODEL env var
                   or defaults to gpt-4o.
        """
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.base_url = (base_url or os.environ.get("OPENAI_BASE_URL", "https://api.deepseek.com")).rstrip("/")
        self.model = model or os.environ.get("OPENAI_MODEL", "deepseek-chat")
        
        if not self.api_key:
            raise ValueError(
                "OpenAI API key not found. Set OPENAI_API_KEY environment variable "
                "or pass api_key to the constructor."
            )

    def _get_headers(self) -> Dict[str, str]:
        """Get HTTP headers for API requests."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def generate(self, prompt: str, **kwargs) -> str:
        """Generate a response from the LLM.
        
        Args:
            prompt: The prompt to send
            **kwargs: Additional parameters (temperature, max_tokens, etc.)
            
        Returns:
            Generated text response
        """
        messages = [{"role": "user", "content": prompt}]
        return self.chat(messages, **kwargs)

    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Send a chat conversation to the LLM.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            **kwargs: Additional parameters (temperature, max_tokens, etc.)
            
        Returns:
            Generated text response
        """
        temperature = kwargs.get("temperature", 0.7)
        max_tokens = kwargs.get("max_tokens", 4096)

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        response = httpx.post(
            f"{self.base_url}/chat/completions",
            headers=self._get_headers(),
            json=payload,
            timeout=120.0,
        )

        if response.status_code != 200:
            raise RuntimeError(
                f"API request failed (status {response.status_code}): {response.text}"
            )

        result = response.json()
        return result["choices"][0]["message"]["content"]
