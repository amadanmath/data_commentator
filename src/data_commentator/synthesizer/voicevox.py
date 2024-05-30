import json

from pydub.audio_segment import AudioSegment
import httpx

from . import Synthesizer

class Voicevox(Synthesizer):
    def __init__(
        self,
        base_uri: str = "http://localhost:50021",
        voice: int = 1, 
        enable_interrogative_upspeak: bool = False,
        speed : float = 1.0,
    ):
        self.voice = voice
        self.base_uri = base_uri
        self.enable_interrogative_upspeak = enable_interrogative_upspeak
        super().__init__(speed)

    async def __call__(self, text: str) -> AudioSegment:
        # from datetime import datetime; now = datetime.now() # XXX: remove
        async with httpx.AsyncClient(base_url=self.base_uri, timeout=20) as client:
            req = await client.post('audio_query', params={
                "text": text,
                "speaker": self.voice,
            })
            audio_query = req.json()

            req = await client.post('synthesis', params={
                "speaker": self.voice,
                "enable_interrogative_upspeak": json.dumps(self.enable_interrogative_upspeak),
            }, json=audio_query)
            pcm = await req.aread()
        seg = AudioSegment(data=pcm)
        # synth_time = (datetime.now() - now).total_seconds(); per_character = synth_time / len(text); ic(synth_time, per_character)
        seg = self.adjust_speed(seg)
        return seg


if __name__ == "__main__":
    import trio
    from pydub.playback import play

    voicevox = Voicevox(speed=0.7)
    seg = trio.run(voicevox, "こんにちは！")
    play(seg)
