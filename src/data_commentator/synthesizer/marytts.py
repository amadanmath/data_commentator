from typing import Any

from pydub.audio_segment import AudioSegment
import httpx

from . import Synthesizer

class MaryTTS(Synthesizer):
    is_speed_handled = True

    def __init__(
        self,
        base_uri: str = "http://localhost:59125",
        voice: int = 1, 
        locale: str = 'en',
        speed : float = 1.0,
    ):
        self.voice = voice
        self.base_uri = base_uri
        self.locale = locale
        super().__init__(speed)

    async def __call__(self, text: str) -> AudioSegment:
        # from datetime import datetime; now = datetime.now() # XXX: remove
        query: dict[str, Any] = {
            "INPUT_TEXT": text,
            "INPUT_TYPE": "TEXT",
            "LOCALE": self.locale,
            "VOICE": self.voice,
            "OUTPUT_TYPE": "AUDIO",
            "AUDIO": "WAVE",
        }
        if self.speed != 1.0:
            query["SPEED"] = self.speed

        async with httpx.AsyncClient(base_url=self.base_uri, timeout=20) as client:
            req = await client.post('/process', data=query)
            pcm = await req.aread()
        seg = AudioSegment(data=pcm)
        # synth_time = (datetime.now() - now).total_seconds(); per_character = synth_time / len(text); ic(synth_time, per_character)
        return seg


if __name__ == "__main__":
    import trio
    from pydub.playback import play

    synthesizer = MaryTTS(speed=0.7)
    seg = trio.run(synthesizer, "Hello, world!")
    play(seg)
