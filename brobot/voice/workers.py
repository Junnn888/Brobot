"""Conversation thread — orchestrates input → brain → output.

Runs in its own daemon thread so the main game loop keeps rendering the
face at 60Hz while stdin and the API are blocking.

The shared `VoiceState` is the bridge to the main loop: it reads the
current state each tick and maps it to a face emotion.
"""

import sys
import threading

from brobot.voice.brain import Brain
from brobot.voice.io import InputSource, OutputSink


class VoiceState:
    """Shared state read by the main game loop to drive face emotion.

    Simple attribute writes are atomic under the GIL, so no lock is needed
    for the single-field case.
    """

    WAITING = "waiting"    # awaiting user input
    THINKING = "thinking"  # API call in flight
    SPEAKING = "speaking"  # streaming reply

    def __init__(self):
        self.state = self.WAITING


class ConversationWorker(threading.Thread):
    """Drives the input → brain → output loop in its own thread."""

    def __init__(
        self,
        input_source: InputSource,
        output_sink: OutputSink,
        brain: Brain,
        state: VoiceState,
    ):
        super().__init__(daemon=True, name="conversation")
        self._input = input_source
        self._output = output_sink
        self._brain = brain
        self._state = state
        self._stop = threading.Event()

    def stop(self) -> None:
        self._stop.set()

    def run(self) -> None:
        while not self._stop.is_set():
            self._state.state = VoiceState.WAITING

            try:
                user_text = self._input.get_next_message()
            except (KeyboardInterrupt, EOFError):
                self._stop.set()
                break

            if not user_text:
                continue

            self._state.state = VoiceState.THINKING

            try:
                chunks = self._brain.respond(user_text)

                # Wrap the iterator so we can flip THINKING -> SPEAKING on the
                # first chunk arriving from the model.
                def tracking(chunks=chunks):
                    first = True
                    for chunk in chunks:
                        if first:
                            self._state.state = VoiceState.SPEAKING
                            first = False
                        yield chunk

                self._output.speak(tracking())
            except Exception as exc:  # noqa: BLE001 — keep the chat alive on transient errors
                print(f"\n[brain error] {exc}", file=sys.stderr)
