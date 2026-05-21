"""Bro-bot entry point — game loop."""

import time

from luma.core.render import canvas

from brobot.display import make_device
from brobot.face import Eyes, render_mouth

TARGET_FPS = 60
FRAME_BUDGET = 1.0 / TARGET_FPS


def main():
    device = make_device()
    eyes = Eyes()

    try:
        while True:
            frame_start = time.monotonic()
            eyes.update(frame_start)

            with canvas(device) as draw:
                eyes.render(draw)
                render_mouth(draw)

            elapsed = time.monotonic() - frame_start
            time.sleep(max(0.0, FRAME_BUDGET - elapsed))
    except KeyboardInterrupt:
        device.clear()


if __name__ == "__main__":
    main()
