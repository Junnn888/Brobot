"""Emotion parameter definitions — pure data, no rendering logic."""

DEFAULTS: dict[str, float] = {
    "eye_half_width": 9.0,
    "left_eye_half_height": 9.0,
    "right_eye_half_height": 9.0,
    "left_brow_show": 0.0,
    "right_brow_show": 0.0,
    "left_brow_y": 0.0,
    "right_brow_y": 0.0,
    "left_brow_angle": 0.0,
    "right_brow_angle": 0.0,
    "mouth_x_offset": 0.0,
    "mouth_curve": 0.3,
    "mouth_width": 0.6,
    "mouth_openness": 0.0,
    "mouth_asymmetry": 0.0,
    "mouth_wave": 0.0,
    "blink_rate": 1.0,
    "blink_openness": 1.0,
}

_OVERRIDES: dict[str, dict[str, float]] = {
    "neutral": {},
    "happy": {
        "left_eye_half_height": 10.0,
        "right_eye_half_height": 10.0,
        "mouth_curve": 0.8,
        "mouth_width": 0.8,
        "blink_rate": 0.7,
    },
    "sad": {
        "left_eye_half_height": 7.0,
        "right_eye_half_height": 7.0,
        "left_brow_show": 1.0,
        "right_brow_show": 1.0,
        "left_brow_angle": -12.0,
        "right_brow_angle": -12.0,
        "mouth_curve": -0.5,
        "mouth_width": 0.5,
        "blink_rate": 1.5,
    },
    "angry": {
        "left_eye_half_height": 6.0,
        "right_eye_half_height": 6.0,
        "left_brow_show": 1.0,
        "right_brow_show": 1.0,
        "left_brow_angle": 18.0,
        "right_brow_angle": 18.0,
        "left_brow_y": 0.0,
        "right_brow_y": 0.0,
        "mouth_curve": -0.5,
        "mouth_width": 0.6,
        "blink_openness": 0.7,
        "blink_rate": 2.0,
    },
    "surprised": {
        "eye_half_width": 11.0,
        "left_eye_half_height": 12.0,
        "right_eye_half_height": 12.0,
        "left_brow_show": 1.0,
        "right_brow_show": 1.0,
        "left_brow_y": -3.0,
        "right_brow_y": -3.0,
        "left_brow_angle": -8.0,
        "right_brow_angle": -8.0,
        "mouth_curve": 0.0,
        "mouth_openness": 0.6,
        "mouth_width": 0.3,
    },
    "smug": {
        "right_eye_half_height": 7.0,
        "right_brow_show": 1.0,
        "right_brow_y": -2.0,
        "right_brow_angle": -6.0,
        "mouth_x_offset": -6.0,
        "mouth_curve": 0.4,
        "mouth_asymmetry": 0.5,
        "mouth_width": 0.5,
        "blink_openness": 0.85,
    },
    "unsure": {
        "left_eye_half_height": 8.0,
        "right_eye_half_height": 8.0,
        "left_brow_show": 1.0,
        "right_brow_show": 1.0,
        "left_brow_angle": -5.0,
        "right_brow_angle": 5.0,
        "mouth_curve": 0.0,
        "mouth_wave": 1.0,
        "mouth_width": 0.5,
        "blink_rate": 1.2,
    },
    "rock-eyebrow": {
        "left_brow_show": 1.0,
        "right_brow_show": 1.0,
        "left_brow_angle": 4.0,
        "right_brow_y": -5.0,
        "right_brow_angle": -8.0,
        "mouth_x_offset": -5.0,
        "mouth_curve": 0.3,
        "mouth_asymmetry": 0.3,
    },
}


def list_emotions() -> list[str]:
    """Return all available emotion names."""
    return list(_OVERRIDES)


def get_emotion(name: str) -> dict[str, float]:
    """Return full parameter set for the named emotion."""
    return {**DEFAULTS, **_OVERRIDES[name]}
