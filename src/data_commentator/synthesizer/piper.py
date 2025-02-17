from typing import Any

from pydub.audio_segment import AudioSegment
from piper import PiperVoice

from . import Synthesizer


class Piper(Synthesizer):
    is_speed_handled = True

    def __init__(
        self,
        voice: str = '',
        speaker: str | int | None = None,
        speed : float = 1.0,
    ):
        self.voice = PiperVoice.load(voice)
        self.speaker = speaker
        self.length_scale = speed is not None and 1.0 / speed
        super().__init__(speed)

    async def __call__(self, text: str) -> AudioSegment:
        query: dict[str, Any] = {
            "text": text,
        }
        if self.speaker is not None:
            query['speaker_id'] = self.speaker
        if self.speed != 1.0:
            query["length_scale"] = self.length_scale

        audio_stream = self.voice.synthesize_stream_raw(**query)
        pcm = b''.join(audio_stream)
        seg = AudioSegment(data=pcm, sample_width=2, frame_rate=22050, channels=1)
        return seg
