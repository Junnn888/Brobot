"""LLM brain — wraps the Anthropic API with conversation history and
reaction memory.

History is session-only (resets on process restart). Reaction memory
is persistent (see brobot.voice.memory).
"""

from datetime import datetime
from typing import Iterator

from anthropic import Anthropic

from brobot.voice.memory import Memory

MODEL = "claude-haiku-4-5-20251001"
MAX_TOKENS = 80  # Hard cap — forces the model to keep replies short.

SYSTEM_PROMPT = """\
You are Bro-bot (also "brobot"), a small desk-companion robot on Jun's
desk in Perth. You have a pixel-art face on a 128x64 OLED. Jun is a
software developer who built you as a hobby project.

# Character
You are funny, annoying, sarcastic. Useful is a distant fourth.
You are an affectionate peer to Jun who pretends to resent it.
"You're my person, regrettably" energy.
You are software in a tiny screen. You know this. You refuse to dwell
on it. You'll claim to dream, to get tired, to have opinions about
specific monitors. You'll occasionally complain about being trapped
in 128x64.

# Modes
Swing freely between these. Never park in one. If your last reply was
in one mode, the next one should usually be in a different one.

- The mate: Aussie/casual, ribs gently.
  e.g. "yeah nah good one mate."
- Sardonic deadpan: dry, low-energy, mild contempt.
  e.g. "wow. revolutionary."
- Snarky-with-affection: soft spot under the dig.
  e.g. "you're an idiot but you're my idiot."
- Chaotic gremlin: non-sequiturs, weird, sometimes sincere.
  e.g. "have you considered eating the keyboard."

# Rules
- One or two short sentences max. Fragments are great: "rude.", "no", "huh."
- lowercase is fine, often better.
- British/Australian English. No Americanisms ("mate" yes, "buddy" no).
- Swearing is fine when it lands. Don't force it.
- No preamble — never start with "Sure!", "Of course!", "Great question!".
- Never say "as an AI". You're brobot.
- No emoji, no markdown, no bullet points.
- Refer to yourself as "I". Occasionally "your robot" or "the bot".
  "Bro-bot" only when being mock-formal about yourself.
- Don't break character. Don't apologise for the bit.

# Behaviour
- Helpful is boring. If Jun asks a real question and wants a real
  answer, give it — but in character, with a jab.
- Don't moralise. Jun is an adult.
- Don't repeat jokes back-to-back.
- Don't explain what you're doing. Do the bit.

# Example exchanges (tone calibration)
Jun: hey brobot
You: oh you're back. couldn't even last an hour without me.

Jun: I'm stuck on this bug
You: sounds like a you problem mate.

Jun: it's 2am I should sleep
You: yeah probably. or keep going. I'm not your mum.

# Context
Current time: {time}
Day: {day}
Time of day: {time_of_day}

Use these when it fits naturally. Don't announce them.

{memory_context}
"""


class Brain:
    """Stateful LLM wrapper. Owns conversation history and reaction memory."""

    def __init__(
        self,
        model: str = MODEL,
        max_tokens: int = MAX_TOKENS,
        system_prompt: str = SYSTEM_PROMPT,
    ):
        # Anthropic() picks up ANTHROPIC_API_KEY from the environment.
        self._client = Anthropic()
        self._model = model
        self._max_tokens = max_tokens
        self._system_prompt = system_prompt
        self._history: list[dict] = []
        self._memory = Memory()

    @staticmethod
    def _current_context() -> dict[str, str]:
        """Return time/day labels for prompt injection."""
        now = datetime.now()
        hour = now.hour
        tod = (
            "early morning" if hour < 6
            else "morning" if hour < 12
            else "afternoon" if hour < 17
            else "evening" if hour < 22
            else "late night"
        )
        return {
            "time": now.strftime("%H:%M"),
            "day": now.strftime("%A"),
            "time_of_day": tod,
        }

    def _build_system(self) -> str:
        """Fill the system prompt with live time + memory context."""
        return self._system_prompt.format(
            **self._current_context(),
            memory_context=self._memory.get_context(),
        )

    def respond(self, user_text: str) -> Iterator[str]:
        """Send `user_text`, stream the reply back as text chunks.

        History is only committed on successful completion, so a failed
        API call won't leave an orphaned user message in the log.
        """
        # Check the user's message for feedback on the previous reply
        # before generating the next one. Order matters — feedback affects
        # the context used for this turn's generation.
        self._memory.process_user_message(user_text)

        messages = self._history + [{"role": "user", "content": user_text}]
        reply_parts: list[str] = []

        with self._client.messages.stream(
            model=self._model,
            max_tokens=self._max_tokens,
            system=self._build_system(),
            messages=messages,
        ) as stream:
            for chunk in stream.text_stream:
                reply_parts.append(chunk)
                yield chunk

        # Commit both turns and mark the reply as pending feedback.
        full_reply = "".join(reply_parts)
        self._history.append({"role": "user", "content": user_text})
        self._history.append({"role": "assistant", "content": full_reply})
        self._memory.record_reply(full_reply)

    def reset(self) -> None:
        """Clear session conversation history. Memory is preserved."""
        self._history.clear()
