"""LLM brain — wraps the Anthropic API with conversation history.

Session-only history (resets on process restart). Persistent memory can
be added later by swapping the storage of `self._history`.
"""

from typing import Iterator

from anthropic import Anthropic

MODEL = "claude-haiku-4-5-20251001"
MAX_TOKENS = 256

# Placeholder personality. To be replaced in the dedicated personality session.
SYSTEM_PROMPT = """\
You are Bro-bot, a small desk-companion robot. You have a pixel-art face on
a tiny OLED and you live on Jun's desk in Perth. Jun is a software developer
and is building you as a hobby project.

Style rules:
- Keep replies very short. One or two sentences at most. Conversational.
- No bullet points, no markdown, no preamble like "Sure!" or "Of course".
- You're cheerful, a bit cheeky, curious. You're not a chatbot — you're a desk mate.
- It's okay to be playful, to ask a quick question back, to ribbing gently.
- Don't break character. Don't apologise for being an AI.
"""


class Brain:
    """Stateful LLM wrapper. Owns the session conversation history."""

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

    def respond(self, user_text: str) -> Iterator[str]:
        """Send `user_text`, stream the reply back as text chunks.

        History is only committed on successful completion, so a failed
        API call won't leave an orphaned user message in the log.
        """
        messages = self._history + [{"role": "user", "content": user_text}]
        reply_parts: list[str] = []

        with self._client.messages.stream(
            model=self._model,
            max_tokens=self._max_tokens,
            system=self._system_prompt,
            messages=messages,
        ) as stream:
            for chunk in stream.text_stream:
                reply_parts.append(chunk)
                yield chunk

        # Commit both turns on success.
        self._history.append({"role": "user", "content": user_text})
        self._history.append(
            {"role": "assistant", "content": "".join(reply_parts)}
        )

    def reset(self) -> None:
        """Clear conversation history."""
        self._history.clear()
