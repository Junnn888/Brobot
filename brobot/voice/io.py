"""Input/output abstractions for the voice pipeline.

The `InputSource` yields user messages; the `OutputSink` renders bro-bot's
replies as a stream of chunks. Both have stdin/stdout impls for dev; mic
and speaker impls will land alongside the audio hardware.

Selection is driven by the `BROBOT_VOICE_IO` env var:
    text  -> StdinInputSource / StdoutOutputSink  (default)
    audio -> not implemented yet
"""

import os
import sys
from abc import ABC, abstractmethod
from typing import Iterator


class InputSource(ABC):
    @abstractmethod
    def get_next_message(self) -> str:
        """Block until the user provides a message; return the text."""


class OutputSink(ABC):
    @abstractmethod
    def speak(self, chunks: Iterator[str]) -> None:
        """Render bro-bot's reply. `chunks` yields text fragments as they
        stream from the brain."""


class StdinInputSource(InputSource):
    PROMPT = "you > "

    def get_next_message(self) -> str:
        try:
            return input(self.PROMPT).strip()
        except EOFError:
            # Ctrl-D — translate to KeyboardInterrupt so the main loop exits cleanly
            raise KeyboardInterrupt


class StdoutOutputSink(OutputSink):
    PREFIX = "bro > "

    def speak(self, chunks: Iterator[str]) -> None:
        sys.stdout.write(self.PREFIX)
        sys.stdout.flush()
        for chunk in chunks:
            sys.stdout.write(chunk)
            sys.stdout.flush()
        sys.stdout.write("\n")
        sys.stdout.flush()


def make_io() -> tuple[InputSource, OutputSink]:
    """Pick I/O implementations based on `BROBOT_VOICE_IO`."""
    mode = os.environ.get("BROBOT_VOICE_IO", "text")
    if mode == "text":
        return StdinInputSource(), StdoutOutputSink()
    if mode == "audio":
        raise NotImplementedError("Audio I/O not yet implemented")
    raise ValueError(f"Unknown BROBOT_VOICE_IO mode: {mode!r}")
