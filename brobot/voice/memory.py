"""Reaction memory — tracks what lands and what doesn't.

Detects positive/negative reactions in user messages, attributes them to
the previous assistant reply, and surfaces recent examples for prompt
injection. Persists to ~/.brobot/memory.json.

Detection is keyword-based: cheap, predictable, easy to tune. Both
positive and negative signals are tracked so the feedback loop has a
correction signal, not just amplification.
"""

import json
from datetime import datetime
from pathlib import Path

POSITIVE_MARKERS = (
    "lol", "lmao", "haha", "hehe", "ha!", "good one", "i like that",
    "i love that", "that's funny", "that's good", "that's great", "nice",
    "love it", "love that", "amazing", "you're funny", "you're great",
    "brilliant", "fair",
)

NEGATIVE_MARKERS = (
    "not funny", "shut up", "lame", "boring", "weird", "bad bot",
    "stop it", "stop that", "don't", "that's not", "that wasn't",
    "cringe",
)

# How many of each to surface in prompt context.
CONTEXT_WINS = 4
CONTEXT_LOSSES = 3

DEFAULT_PATH = Path.home() / ".brobot" / "memory.json"


def _detect_reaction(text: str) -> str | None:
    """Return 'positive', 'negative', or None for ambiguous/no signal."""
    lowered = text.lower()
    has_pos = any(marker in lowered for marker in POSITIVE_MARKERS)
    has_neg = any(marker in lowered for marker in NEGATIVE_MARKERS)
    if has_pos and not has_neg:
        return "positive"
    if has_neg and not has_pos:
        return "negative"
    return None


class Memory:
    """Reaction memory. Stores tagged examples; surfaces them in prompts."""

    def __init__(self, path: Path | None = None):
        self._path = Path(path) if path else DEFAULT_PATH
        self._reactions: list[dict] = []
        self._pending_reply: str | None = None
        self._load()

    def _load(self) -> None:
        if not self._path.exists():
            return
        try:
            data = json.loads(self._path.read_text())
            self._reactions = data.get("reactions", [])
        except (json.JSONDecodeError, OSError):
            # Corrupted file — start fresh rather than crash brobot.
            self._reactions = []

    def _save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(
            json.dumps({"reactions": self._reactions}, indent=2)
        )

    def process_user_message(self, user_text: str) -> None:
        """Detect a reaction and attribute it to the pending reply if any.

        Called once per user turn, before generating brobot's response.
        """
        if self._pending_reply is None:
            return
        reaction = _detect_reaction(user_text)
        if reaction is None:
            return
        self._reactions.append({
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "user_msg": user_text,
            "bot_reply": self._pending_reply,
            "reaction": reaction,
        })
        self._pending_reply = None
        self._save()

    def record_reply(self, bot_reply: str) -> None:
        """Mark this reply as awaiting feedback from the next user message."""
        self._pending_reply = bot_reply

    def get_context(self) -> str:
        """Return formatted 'wins / losses' string for prompt injection.

        Empty string when nothing has been recorded yet.
        """
        wins = [
            r["bot_reply"] for r in reversed(self._reactions)
            if r["reaction"] == "positive"
        ][:CONTEXT_WINS]
        losses = [
            r["bot_reply"] for r in reversed(self._reactions)
            if r["reaction"] == "negative"
        ][:CONTEXT_LOSSES]

        if not wins and not losses:
            return ""

        parts = ["# Feedback memory"]
        if wins:
            parts.append("\nThese replies of yours landed well recently:")
            parts.extend(f"- {w}" for w in wins)
        if losses:
            parts.append("\nThese didn't land:")
            parts.extend(f"- {l}" for l in losses)
        parts.append("\nFind what works. Vary your approach. Don't just repeat what landed.")
        return "\n".join(parts)

    def reset(self) -> None:
        """Wipe all stored reactions. For debugging."""
        self._reactions = []
        self._pending_reply = None
        self._save()
