"""Smoke test for Gemini via LiteLLM."""
import os

from litellm import completion
from dotenv import load_dotenv

load_dotenv()

response = completion(
    model="gemini/gemini-1.0-pro",
    messages=[{"role": "user", "content": "Explain LiteLLM in one sentence"}],
    api_key=os.getenv("GEMINI_API_KEY"),
)

print(f"Response from Gemini: {response.choices[0].message.content}")