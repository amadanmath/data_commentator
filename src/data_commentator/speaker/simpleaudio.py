import trio
from pydub.audio_segment import AudioSegment
from simpleaudio import play_buffer

from . import Speaker


class SimpleAudio(Speaker):
    def __init__(self, console: bool = False):
        self.console = console

    async def __call__(self, seg: AudioSegment | None, text: str) -> None:
        if self.console:
            print(text)
        if seg:
            playback = play_buffer(
                seg.raw_data,
                num_channels=seg.channels,
                bytes_per_sample=seg.sample_width,
                sample_rate=seg.frame_rate
            )
            try:
                while playback.is_playing():
                    await trio.sleep(0.05)
            except trio.Cancelled:
                if playback.is_playing():
                    playback.stop()
                    playback.wait_done()
                raise
