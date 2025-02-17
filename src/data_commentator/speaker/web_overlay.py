import base64
import wave
from io import BytesIO

import trio
from pydub.audio_segment import AudioSegment
try:
    import audioop
except ImportError:
    import pydub.pyaudioop as audioop

from . import Speaker
from ..webserver import webserver


# From https://github.com/jiaaro/pydub/blob/996cec42e9621701edb83354232b2c0ca0121560/pydub/audio_segment.py#L824
# to avoid creating a temporary file (which `seg.export` does)
def seg_to_wav(seg: AudioSegment) -> bytes:
    pcm_for_wav = seg.raw_data
    if seg.sample_width == 1:
        # convert to unsigned integers for wav
        pcm_for_wav = audioop.bias(pcm_for_wav, 1, 128) # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType, reportAttributeAccessIssue]

    data = BytesIO()
    with wave.open(data, 'wb') as wave_data:
        wave_data.setnchannels(seg.channels)
        wave_data.setsampwidth(seg.sample_width)
        wave_data.setframerate(seg.frame_rate)
        # For some reason packing the wave header struct with
        # a float in python 2 doesn't throw an exception
        wave_data.setnframes(int(seg.frame_count()))
        wave_data.writeframesraw(pcm_for_wav)

    return data.getvalue()


class WebOverlay(Speaker):
    async def __call__(self, seg: AudioSegment | None, text: str) -> None:
        data = {
            "text": text,
        }
        if seg:
            speech_data = seg_to_wav(seg)
            data["speech"] = base64.b64encode(speech_data).decode()

        await webserver.broadcast(data)
        await trio.sleep(len(seg) / 1000.0)
