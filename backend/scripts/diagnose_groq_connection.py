"""
Diagnostic script — deliberately has NO error handling. If the Groq call
fails, Python will print the full, real traceback instead of the one-line
summary that planner.py normally reduces it to. That traceback tells us
exactly which layer is failing.

Run from backend/:
    python -m scripts.diagnose_groq_connection
"""

from groq import Groq
from app.core.config import settings
from dotenv import load_dotenv
load_dotenv()


print("Using API key starting with:", settings.LLM_API_KEY[:8] if settings.LLM_API_KEY else "(EMPTY)")

client = Groq(api_key=settings.LLM_API_KEY)

response = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[{"role": "user", "content": "Say hello in one word."}],
)

print(response.choices[0].message.content)