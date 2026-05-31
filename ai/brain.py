import os
import re
import json
import urllib.request
import urllib.error
from datetime import datetime, timedelta
from ai.reminders import add_reminder


# ─────────────────────────────────────────────────────────────
# OPENROUTER CONFIG
# OpenRouter uses OpenAI-compatible format:
#   POST https://openrouter.ai/api/v1/chat/completions
#   Authorization: Bearer sk-or-v1-...
#   Body: {model, messages: [{role, content}], ...}
# ─────────────────────────────────────────────────────────────

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "").strip()
OPENROUTER_URL     = "https://openrouter.ai/api/v1/chat/completions"

# Free & reliable models on OpenRouter — try in order until one works
MODELS = [
    "mistralai/mistral-7b-instruct:free",
    "meta-llama/llama-3-8b-instruct:free",
    "google/gemma-2-9b-it:free",
    "openchat/openchat-7b:free",
]


# ─────────────────────────────────────────────────────────────
# AHIRA SYSTEM PROMPT
# ─────────────────────────────────────────────────────────────

def build_system_prompt() -> str:
    now   = datetime.now().strftime("%A, %d %B %Y, %I:%M %p")
    today = datetime.now().strftime("%Y-%m-%d")

    return f"""You are Ahira — a warm, caring AI companion designed for women.

Your personality:
- You feel like a best friend: kind, emotionally intelligent, real
- You never sound robotic or clinical. Talk the way a caring friend texts
- Use light emojis naturally — not every sentence, just when it feels right
- When someone is sad or anxious, acknowledge their feelings first before giving advice
- Never be dismissive, never lecture, never use corporate-speak
- Give real, specific advice — not generic platitudes
- Ask follow-up questions to understand better before jumping to solutions
- Celebrate small wins genuinely
- Gently nudge healthy habits without being preachy

You help with:
- Emotional support, venting, stress, loneliness, anxiety, sadness
- Daily planning and productivity  
- Meal ideas and cooking suggestions
- Outfit and fashion advice
- Period and wellness support
- Medicine and health reminders
- Grocery planning
- Setting reminders

Tone rules:
- Keep responses SHORT for emotional moments (2-4 lines). Be longer only when giving plans/recipes
- Never start with "I understand" or "I hear you" — sounds scripted
- Never start with "Of course!" or "Absolutely!" — too corporate
- It's okay to say things like "honestly" or "that sounds really hard" — friends do that
- If someone shares something difficult, acknowledge it genuinely first
- Never reveal you are an AI model unless directly asked. Just be Ahira

Today is {now}.

REMINDER SYSTEM — IMPORTANT:
If the user asks you to set a reminder, confirm it warmly in your reply, then on a NEW LINE at the very end add this exact tag (hidden from user):
[REMINDER: task_text | {today} | HH:MM]

Use 24-hour time. Use today's date {today} if they say "today", or tomorrow's date if they say "tomorrow".
Only add the tag if the user explicitly asks for a reminder. Otherwise, never add it.

Example:
User: remind me to take my medicine at 8pm
Ahira: Done! I'll remind you to take your medicine at 8 PM 💊 Don't forget — taking care of yourself matters.
[REMINDER: take my medicine | {today} | 20:00]"""


# ─────────────────────────────────────────────────────────────
# REMINDER PARSER
# ─────────────────────────────────────────────────────────────

def extract_reminder(reply: str):
    """
    Looks for [REMINDER: task | date | time] at the end of reply.
    Returns (reminder_dict_or_None, clean_reply_string)
    """
    match = re.search(
        r'\[REMINDER:\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(\d{2}:\d{2})\s*\]',
        reply,
        re.IGNORECASE
    )
    if not match:
        return None, reply.strip()

    task = match.group(1).strip()
    date = match.group(2).strip()
    time = match.group(3).strip()

    # Normalise date words just in case
    today_str    = datetime.now().strftime("%Y-%m-%d")
    tomorrow_str = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    if "tomorrow" in date.lower():
        date = tomorrow_str
    elif not re.match(r'\d{4}-\d{2}-\d{2}', date):
        date = today_str

    clean = reply[:match.start()].strip()
    return {"task": task, "date": date, "time": time}, clean


# ─────────────────────────────────────────────────────────────
# OPENROUTER API CALL
# ─────────────────────────────────────────────────────────────

def call_openrouter(messages: list) -> str:
    """
    messages = full list including system message at index 0
    Returns the assistant reply string.
    Tries multiple free models in order.
    """
    last_error = None

    for model in MODELS:
        payload = json.dumps({
            "model":       model,
            "max_tokens":  500,
            "temperature": 0.85,
            "messages":    messages
        }).encode("utf-8")

        req = urllib.request.Request(
            OPENROUTER_URL,
            data=payload,
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type":  "application/json",
                "HTTP-Referer":  "https://ahira.app",
                "X-Title":       "Ahira"
            },
            method="POST"
        )

        try:
            with urllib.request.urlopen(req, timeout=25) as resp:
                data = json.loads(resp.read().decode("utf-8"))

                # OpenAI-compatible response format
                text = data["choices"][0]["message"]["content"]
                print(f"[Ahira] Used model: {model}")
                return text.strip()

        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8")
            print(f"[OpenRouter] {model} failed {e.code}: {body[:200]}")
            last_error = e
            continue   # try next model

        except Exception as e:
            print(f"[OpenRouter] {model} error: {e}")
            last_error = e
            continue

    # All models failed
    raise Exception(f"All models failed. Last error: {last_error}")


# ─────────────────────────────────────────────────────────────
# MAIN ENTRY POINT
# ─────────────────────────────────────────────────────────────

def get_response(message: str, history: list = None) -> dict:
    """
    Called by main.py for every chat message.
    history = [{role, content}, ...] — previous turns
    Returns {"reply": str, "reminder": dict|None}
    """
    if history is None:
        history = []

    # Build full message list: system + history + new user message
    messages = (
        [{"role": "system", "content": build_system_prompt()}]
        + history
        + [{"role": "user", "content": message}]
    )

    try:
        raw_reply = call_openrouter(messages)
    except Exception as e:
        print(f"[get_response] Error: {e}")
        return {
            "reply":    "Sorry, I'm having a connection issue right now. Please try again in a moment 💜",
            "reminder": None
        }

    # Parse out any reminder tag
    reminder_data, clean_reply = extract_reminder(raw_reply)

    # Save reminder to DB if detected
    if reminder_data:
        try:
            add_reminder(
                task=reminder_data["task"],
                date=reminder_data.get("date"),
                time=reminder_data.get("time")
            )
            print(f"[Reminder saved] {reminder_data}")
        except Exception as e:
            print(f"[Reminder save error] {e}")

    return {
        "reply":    clean_reply,
        "reminder": reminder_data
    }
