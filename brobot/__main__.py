"""Bro-bot entry point — game loop + optional voice."""

import os
import random
import time

from dotenv import load_dotenv
from luma.core.render import canvas

from brobot.display import make_device
from brobot.emotions import list_emotions
from brobot.face import Face

# Load .env at startup so ANTHROPIC_API_KEY is available before Brain() is constructed.
load_dotenv()

TARGET_FPS = 60
FRAME_BUDGET = 1.0 / TARGET_FPS

DEMO_PAUSE_RANGE = (4.0, 6.0)

# Map conversation state to a face emotion. Tune freely.
VOICE_EMOTIONS = {
    "waiting": "neutral",
    "thinking": "unsure",
    "speaking": "happy",
}


def _shuffled_emotions():
    names = list_emotions()
    while True:
        random.shuffle(names)
        yield from names


def main():
    device = make_device()
    face = Face()

    voice_enabled = "BROBOT_VOICE_IO" in os.environ
    voice_state = None
    last_voice_state = None

    if voice_enabled:
        # Imported lazily so the demo-only path doesn't need the anthropic SDK.
        from brobot.voice.brain import Brain
        from brobot.voice.io import make_io
        from brobot.voice.workers import ConversationWorker, VoiceState

        input_src, output_sink = make_io()
        brain = Brain()
        voice_state = VoiceState()
        conversation = ConversationWorker(input_src, output_sink, brain, voice_state)
        conversation.start()
        print("(bro-bot is alive. type to chat. ctrl-c to quit.)")

    demo = _shuffled_emotions()
    next_switch = time.monotonic() + random.uniform(*DEMO_PAUSE_RANGE)

    try:
        while True:
            frame_start = time.monotonic()

            if voice_enabled:
                # Face follows conversation state.
                if voice_state.state != last_voice_state:
                    face.set_emotion(VOICE_EMOTIONS[voice_state.state])
                    last_voice_state = voice_state.state
            else:
                # Demo mode: cycle through random emotions.
                if frame_start >= next_switch:
                    face.set_emotion(next(demo))
                    next_switch = frame_start + random.uniform(*DEMO_PAUSE_RANGE)

            face.update(frame_start)

            with canvas(device) as draw:
                face.render(draw)

            elapsed = time.monotonic() - frame_start
            time.sleep(max(0.0, FRAME_BUDGET - elapsed))
    except KeyboardInterrupt:
        device.clear()


if __name__ == "__main__":
    main()
