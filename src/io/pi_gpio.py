"""Raspberry Pi hardware backend (GPIO mute button + LED).

Placeholder for the Raspberry Pi build phase — see plan.md Section 7,
Phase 6. It implements the same HardwareIO interface as LaptopHardwareIO
so orchestrator.py and server.py need zero changes once this is filled
in: only DEVICE=raspberrypi in .env plus this file.
"""
from .hardware_interface import HardwareIO


class PiHardwareIO(HardwareIO):
    def __init__(self, mute_button_pin: int, listening_led_pin: int, online_led_pin: int):
        super().__init__()
        self.mute_button_pin = mute_button_pin
        self.listening_led_pin = listening_led_pin
        self.online_led_pin = online_led_pin
        raise NotImplementedError(
            "Raspberry Pi GPIO backend is implemented in the Raspberry Pi build phase "
            "(plan.md Phase 6)."
        )

    def start(self):
        raise NotImplementedError

    def stop(self):
        raise NotImplementedError

    def toggle_mute(self):
        raise NotImplementedError

    def set_indicator(self, stage: str):
        raise NotImplementedError
