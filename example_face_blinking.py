"""Bro-bot face — Phase 1: blinking eyes + stationary mouth."""

import random
import time
import os


def make_device():
    if os.environ.get("BROBOT_EMULATE"):
        from luma.emulator.device import pygame
        return pygame(width=WIDTH, height=HEIGHT, scale=4, transform="none")

    from luma.core.interface.serial import spi
    from luma.oled.device import ssd1309
    serial = spi(port=0, device=0, gpio_DC=25, gpio_RST=24, bus_speed_hz=8000000)
    return ssd1309(serial, width=WIDTH, height=HEIGHT)

from luma.core.interface.serial import spi
from luma.core.render import canvas
from luma.oled.device import ssd1309

# --- Display --------------------------------------------------------------
WIDTH, HEIGHT = 128, 64

# --- Layout ---------------------------------------------------------------
LEFT_EYE_CENTRE = (40, 24)
RIGHT_EYE_CENTRE = (88, 24)
EYE_HALF_WIDTH = 9
EYE_HALF_HEIGHT_OPEN = 9
MOUTH_BOX = (44, 42, 84, 58)   # bounding box for the smile arc

# --- Animation ------------------------------------------------------------
TARGET_FPS = 60
FRAME_BUDGET = 1.0 / TARGET_FPS

BLINK_INTERVAL_RANGE = (2.5, 5.5)   # seconds between blinks ("normal" rate)
CLOSE_DURATION = 0.08               # eyes closing
HOLD_DURATION = 0.05                # held shut
OPEN_DURATION = 0.12                # eyes opening back up


class Eyes:
    """Blink state machine. `openness` is 0.0 (closed) … 1.0 (open)."""

    IDLE = "idle"
    CLOSING = "closing"
    CLOSED = "closed"
    OPENING = "opening"

    def __init__(self):
        self.openness = 1.0
        self._enter(self.IDLE)
        self._schedule_next_blink()

    def _enter(self, state):
        self.state = state
        self.state_entered_at = time.monotonic()

    def _schedule_next_blink(self):
        self.next_blink_at = time.monotonic() + random.uniform(*BLINK_INTERVAL_RANGE)

    def update(self, now):
        elapsed = now - self.state_entered_at

        if self.state == self.IDLE:
            self.openness = 1.0
            if now >= self.next_blink_at:
                self._enter(self.CLOSING)

        elif self.state == self.CLOSING:
            self.openness = max(0.0, 1.0 - elapsed / CLOSE_DURATION)
            if elapsed >= CLOSE_DURATION:
                self._enter(self.CLOSED)

        elif self.state == self.CLOSED:
            self.openness = 0.0
            if elapsed >= HOLD_DURATION:
                self._enter(self.OPENING)

        elif self.state == self.OPENING:
            self.openness = min(1.0, elapsed / OPEN_DURATION)
            if elapsed >= OPEN_DURATION:
                self.openness = 1.0
                self._schedule_next_blink()
                self._enter(self.IDLE)

    def render(self, draw):
        for cx, cy in (LEFT_EYE_CENTRE, RIGHT_EYE_CENTRE):
            half_h = int(EYE_HALF_HEIGHT_OPEN * self.openness)
            if half_h < 1:
                # Fully closed — flat line with a tiny bit of weight
                draw.line(
                    (cx - EYE_HALF_WIDTH, cy, cx + EYE_HALF_WIDTH, cy),
                    fill="white", width=2,
                )
            else:
                draw.ellipse(
                    (cx - EYE_HALF_WIDTH, cy - half_h,
                     cx + EYE_HALF_WIDTH, cy + half_h),
                    fill="white",
                )


def render_mouth(draw):
    # Stationary smile: bottom half-arc.
    draw.arc(MOUTH_BOX, start=0, end=180, fill="white", width=2)


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
