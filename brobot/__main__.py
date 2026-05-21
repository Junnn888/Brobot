"""Bro-bot entry point — game loop."""

import random
import time

from luma.core.render import canvas

from brobot.display import make_device
from brobot.emotions import _OVERRIDES
from brobot.face import Face

TARGET_FPS = 60
FRAME_BUDGET = 1.0 / TARGET_FPS

DEMO_PAUSE_RANGE = (4.0, 6.0)


def _shuffled_emotions():
    names = list(_OVERRIDES)
    while True:
        random.shuffle(names)
        yield from names


def main():
    device = make_device()
    face = Face()
    demo = _shuffled_emotions()
    next_switch = time.monotonic() + random.uniform(*DEMO_PAUSE_RANGE)

    try:
        while True:
            frame_start = time.monotonic()

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
