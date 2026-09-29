from .hardware_interface import HardwareIO


def build_hardware_io(config) -> HardwareIO:
    """The one place that branches on platform. Everything downstream
    (orchestrator, server) talks to the returned object only through the
    HardwareIO interface."""
    if config.device == "laptop":
        from .laptop_io import LaptopHardwareIO

        return LaptopHardwareIO(mute_key=config.raw.get("mute_key", "f9"))

    if config.device == "raspberrypi":
        from .pi_gpio import PiHardwareIO

        gpio = config.raw["gpio"]
        return PiHardwareIO(
            mute_button_pin=gpio["mute_button_pin"],
            listening_led_pin=gpio["listening_led_pin"],
            online_led_pin=gpio["online_led_pin"],
        )

    raise ValueError(f"Unsupported device: {config.device}")
