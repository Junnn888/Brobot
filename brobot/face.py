"""Face rendering — eyes and mouth."""

import random
import time

# --- Layout ---------------------------------------------------------------
LEFT_EYE_CENTRE = (40, 24)
RIGHT_EYE_CENTRE = (88, 24)
EYE_HALF_WIDTH = 9
EYE_HALF_HEIGHT_OPEN = 9
MOUTH_BOX = (44, 42, 84, 58)

# --- Animation ------------------------------------------------------------
BLINK_INTERVAL_RANGE = (2.5, 5.5)
CLOSE_DURATION = 0.08
HOLD_DURATION = 0.05
OPEN_DURATION = 0.12


class Eyes:
    """Blink state machine. `openness` is 0.0 (closed) ... 1.0 (open)."""

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
                draw.line(
                    (cx - EYE_HALF_WIDTH, cy, cx + EYE_HALF_WIDTH, cy),
                    fill="white",
                    width=2,
                )
            else:
                draw.ellipse(
                    (
                        cx - EYE_HALF_WIDTH,
                        cy - half_h,
                        cx + EYE_HALF_WIDTH,
                        cy + half_h,
                    ),
                    fill="white",
                )


def render_mouth(draw):
    draw.arc(MOUTH_BOX, start=0, end=180, fill="white", width=2)
