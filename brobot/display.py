"""Device factory — the sole platform-aware module."""

import os

WIDTH = 128
HEIGHT = 64


def make_device():
    if os.environ.get("BROBOT_EMULATE"):
        from luma.emulator.device import pygame

        return pygame(width=WIDTH, height=HEIGHT, scale=6, transform="identity")

    from luma.core.interface.serial import spi
    from luma.oled.device import ssd1309

    serial = spi(port=0, device=0, gpio_DC=25, gpio_RST=24, bus_speed_hz=8000000)
    return ssd1309(serial, width=WIDTH, height=HEIGHT)
