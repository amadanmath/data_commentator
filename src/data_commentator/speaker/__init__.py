from abc import abstractmethod

from pydub.audio_segment import AudioSegment


class Speaker:
    @abstractmethod
    async def __call__(self, seg: AudioSegment | None, text: str) -> None:
        pass
