from typing import Any

from pydub.audio_segment import AudioSegment
import pyopenjtalk
import numpy as np

from . import Synthesizer


class OpenJTalk(Synthesizer):
    is_speed_handled = False

    def __init__(
        self,
        speed: float = 1.0,
        half_tone: float = 0.0,
        run_marine: bool = False,
    ):
        self.speed = speed
        self.half_tone = half_tone
        self.run_marine = run_marine
        super().__init__(speed)

    async def __call__(self, text: str) -> AudioSegment:
        pcm, sample_rate = pyopenjtalk.tts(text, speed=self.speed, half_tone=self.half_tone, run_marine=self.run_marine)
        pcm = pcm.astype(np.int16).tobytes()
        seg = AudioSegment(data=pcm, sample_width=2, frame_rate=sample_rate, channels=1)
        seg = self.adjust_speed(seg)
        return seg
