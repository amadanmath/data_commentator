import trio
from pydub.audio_segment import AudioSegment
from simpleaudio import play_buffer

from . import Speaker


class SimpleAudio(Speaker):
    async def __call__(self, seg: AudioSegment | None, text: str) -> None:
        if seg:
            playback = play_buffer(
                seg.raw_data,
                num_channels=seg.channels,
                bytes_per_sample=seg.sample_width,
                sample_rate=seg.frame_rate
            )
            while playback.is_playing():
                await trio.sleep(0.05)


if __name__ == "__main__":
    from ..synthesizer.voicevox import Voicevox

    async def main():
        voicevox = Voicevox(speed=1.0)
        speaker = SimpleAudio()
        text = "こんにちは！これはタイムアウトのテストです。"
        seg = await voicevox(text)
        with trio.move_on_after(2):
            _ = await speaker(seg, text)
        text = "つづきます"
        seg = await voicevox(text)
        _ = await speaker(seg, text)

    trio.run(main)
