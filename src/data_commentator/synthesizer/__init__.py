from abc import abstractmethod

from pydub.audio_segment import AudioSegment
from pydub.effects import speedup
from audio_effects import speed_down


class Synthesizer:
    is_speed_handled = False

    def __init__(
        self,
        speed: float = 1.0,
        chunk_size: int = 50,
        crossfade: int = 25,
        merge_crossfade: int = 25,
        crossfade_threshold: int = 10,
    ) -> None:
        self.speed = speed
        self.chunk_size = chunk_size
        self.crossfade = crossfade
        self.merge_crossfade = merge_crossfade
        self.crossfade_threshold = crossfade_threshold
        super().__init__()

    @abstractmethod
    async def __call__(self, text: str) -> AudioSegment:
        return AudioSegment.empty()

    def adjust_speed(self, seg: AudioSegment) -> AudioSegment:
        if self.speed == 1.0 or self.is_speed_handled:
            return seg
        if self.speed > 1.0:
            seg = speedup(seg, self.speed, self.chunk_size, self.crossfade)
        else:
            seg = speed_down(seg, self.speed, self.chunk_size, self.crossfade, self.merge_crossfade, self.crossfade_threshold)
        return seg
