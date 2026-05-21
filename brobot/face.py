"""Face rendering — eyes, eyebrows, and mouth."""

import random
import time

from brobot.emotions import get_emotion

# --- Layout ---------------------------------------------------------------
LEFT_EYE_CENTRE = (40, 24)
RIGHT_EYE_CENTRE = (88, 24)
MOUTH_CENTRE = (64, 50)
BROW_HALF_WIDTH = 10

# --- Blink timing ---------------------------------------------------------
BLINK_BASE_MIN = 2.5
BLINK_BASE_MAX = 5.5
CLOSE_DURATION = 0.08
HOLD_DURATION = 0.05
OPEN_DURATION = 0.12

# --- Mouth polyline positions (t values) ----------------------------------
_MOUTH_T = (-1.0, -0.5, 0.0, 0.5, 1.0)
_WAVE_PATTERN = (0, -1, 1, -1, 0)


class _BlinkMachine:
    """Blink state machine.  Produces an openness multiplier (0.0–1.0)."""

    IDLE = "idle"
    CLOSING = "closing"
    CLOSED = "closed"
    OPENING = "opening"

    def __init__(self, params):
        self._params = params
        self.openness = 1.0
        self._state = self.IDLE
        self._entered_at = time.monotonic()
        self._schedule_next()

    def _schedule_next(self):
        rate = self._params["blink_rate"]
        self._next_at = time.monotonic() + random.uniform(
            BLINK_BASE_MIN * rate, BLINK_BASE_MAX * rate
        )

    def _enter(self, state):
        self._state = state
        self._entered_at = time.monotonic()

    def update(self, now):
        elapsed = now - self._entered_at

        if self._state == self.IDLE:
            self.openness = self._params["blink_openness"]
            if now >= self._next_at:
                self._enter(self.CLOSING)

        elif self._state == self.CLOSING:
            self.openness = max(
                0.0, self._params["blink_openness"] * (1.0 - elapsed / CLOSE_DURATION)
            )
            if elapsed >= CLOSE_DURATION:
                self._enter(self.CLOSED)

        elif self._state == self.CLOSED:
            self.openness = 0.0
            if elapsed >= HOLD_DURATION:
                self._enter(self.OPENING)

        elif self._state == self.OPENING:
            self.openness = min(
                self._params["blink_openness"], elapsed / OPEN_DURATION
            )
            if elapsed >= OPEN_DURATION:
                self.openness = self._params["blink_openness"]
                self._schedule_next()
                self._enter(self.IDLE)


class Face:
    """Complete face with emotion transitions and blinking."""

    def __init__(self):
        self._current = get_emotion("neutral")
        self._target = dict(self._current)
        self._origin = dict(self._current)
        self._transition_start = 0.0
        self._transition_duration = 0.0
        self._blink = _BlinkMachine(self._current)

    def set_emotion(self, name, duration=0.3):
        """Transition to a named emotion over *duration* seconds."""
        self._origin = dict(self._current)
        self._target = get_emotion(name)
        self._transition_start = time.monotonic()
        self._transition_duration = duration
        if duration <= 0.0:
            self._current.update(self._target)

    def update(self, now):
        if self._transition_duration > 0.0:
            t = (now - self._transition_start) / self._transition_duration
            t = max(0.0, min(1.0, t))
            t = t * t * (3.0 - 2.0 * t)
            for key in self._current:
                self._current[key] = (
                    self._origin[key] + (self._target[key] - self._origin[key]) * t
                )
        self._blink.update(now)

    def render(self, draw):
        p = self._current
        blink = self._blink.openness
        self._render_eyebrows(draw, p)
        self._render_eyes(draw, p, blink)
        self._render_mouth(draw, p)

    # --- Private renderers ------------------------------------------------

    @staticmethod
    def _render_eyes(draw, p, blink):
        hw = int(p["eye_half_width"])
        for side, (cx, cy) in (
            ("left", LEFT_EYE_CENTRE),
            ("right", RIGHT_EYE_CENTRE),
        ):
            hh = int(p[f"{side}_eye_half_height"] * blink)
            if hh < 1:
                draw.line(
                    (cx - hw, cy, cx + hw, cy), fill="white", width=2
                )
            else:
                draw.ellipse(
                    (cx - hw, cy - hh, cx + hw, cy + hh), fill="white"
                )

    @staticmethod
    def _render_eyebrows(draw, p):
        for side, (cx, cy) in (
            ("left", LEFT_EYE_CENTRE),
            ("right", RIGHT_EYE_CENTRE),
        ):
            if p[f"{side}_brow_show"] <= 0.5:
                continue
            brow_cy = cy - int(p[f"{side}_eye_half_height"]) - 5 + int(
                p[f"{side}_brow_y"]
            )
            angle = p[f"{side}_brow_angle"]
            inner_dy = round(angle * 0.18)

            if side == "left":
                x1, y1 = cx - BROW_HALF_WIDTH, brow_cy
                x2, y2 = cx + BROW_HALF_WIDTH, brow_cy + inner_dy
            else:
                x1, y1 = cx - BROW_HALF_WIDTH, brow_cy + inner_dy
                x2, y2 = cx + BROW_HALF_WIDTH, brow_cy

            draw.line((x1, y1, x2, y2), fill="white", width=2)

    @staticmethod
    def _render_mouth(draw, p):
        mcx, mcy = MOUTH_CENTRE
        mcx += int(p["mouth_x_offset"])
        half_w = int(20 * p["mouth_width"])

        if p["mouth_openness"] > 0.1:
            oh = max(1, int(8 * p["mouth_openness"]))
            ow = max(half_w, 6)
            draw.ellipse(
                (mcx - ow, mcy - oh, mcx + ow, mcy + oh),
                outline="white",
                width=2,
            )
            return

        curve = p["mouth_curve"]
        asym = p["mouth_asymmetry"]
        wave = p["mouth_wave"]

        points = []
        for i, t in enumerate(_MOUTH_T):
            x = mcx + int(t * half_w)
            y = mcy + int(
                curve * (1.0 - t * t) * 8.0
                + asym * t * 4.0
                + wave * _WAVE_PATTERN[i] * 3.0
            )
            points.append((x, y))

        draw.line(points, fill="white", width=2)

