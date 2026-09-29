import queue

import numpy as np
import sounddevice as sd


class AudioCapture:
    """Mic -> simple energy-based voice-activity segmentation -> utterance
    generator. While hardware.muted is True, incoming blocks are dropped in
    the audio callback itself — no audio is buffered or written anywhere,
    which is what makes the mute switch a real guarantee and not just a UI
    state."""

    def __init__(
        self,
        hardware,
        samplerate: int = 16000,
        block_duration: float = 0.5,
        silence_threshold: float = 0.01,
        silence_blocks: int = 2,
    ):
        self.hardware = hardware
        self.samplerate = samplerate
        self.block_size = int(samplerate * block_duration)
        self.silence_threshold = silence_threshold
        self.silence_blocks = silence_blocks
        self._q: "queue.Queue[np.ndarray]" = queue.Queue()

    def _callback(self, indata, frames, time_info, status):
        if self.hardware.muted:
            return
        self._q.put(indata.copy())

    def stream_utterances(self):
        buffer = []
        silence_count = 0
        speaking = False

        with sd.InputStream(
            samplerate=self.samplerate,
            channels=1,
            blocksize=self.block_size,
            callback=self._callback,
        ):
            while True:
                try:
                    block = self._q.get(timeout=1.0)
                except queue.Empty:
                    continue

                energy = float(np.abs(block).mean())

                if energy > self.silence_threshold:
                    buffer.append(block)
                    speaking = True
                    silence_count = 0
                elif speaking:
                    silence_count += 1
                    buffer.append(block)
                    if silence_count >= self.silence_blocks:
                        segment = np.concatenate(buffer, axis=0).flatten()
                        buffer = []
                        speaking = False
                        silence_count = 0
                        yield segment
