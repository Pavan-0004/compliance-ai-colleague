from pynput import keyboard

from .hardware_interface import HardwareIO


class LaptopHardwareIO(HardwareIO):
    """Laptop backend: a keyboard hotkey stands in for the physical mute
    switch. set_indicator() is a no-op here — the React dashboard's status
    light is the visible listening indicator for this platform."""

    def __init__(self, mute_key: str = "f9"):
        super().__init__()
        self.mute_key = mute_key
        self._listener = None

    def start(self):
        self._listener = keyboard.GlobalHotKeys({f"<{self.mute_key}>": self.toggle_mute})
        self._listener.start()

    def stop(self):
        if self._listener:
            self._listener.stop()

    def toggle_mute(self):
        self._set_muted(not self._muted)

    def set_indicator(self, stage: str):
        pass
