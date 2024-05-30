import os
from io import BytesIO

import ONNXVITS_infer
import torch
from torch import no_grad, LongTensor
import commons
import utils
from text import text_to_sequence, _clean_text

import soundfile as sf

from flask import Flask, request, Response
from asgiref.wsgi import WsgiToAsgi


class Synthesizer:
    def __init__(self, config_path, model_path, onnx_dir, lang):
        self.lang = lang
        self.hps = utils.get_hparams_from_file(config_path)
        self.model = ONNXVITS_infer.SynthesizerTrn(
            len(self.hps.symbols),
            self.hps.data.filter_length // 2 + 1,
            self.hps.train.segment_size // self.hps.data.hop_length,
            n_speakers=self.hps.data.n_speakers,
            ONNX_dir=onnx_dir,
            **self.hps.model)
        utils.load_checkpoint(model_path, self.model, None)
        self.model.eval()

    def get_text(self, text, is_symbol):
        cleaners = [] if is_symbol else self.hps.data.text_cleaners
        text_norm = text_to_sequence(text, self.hps.symbols, cleaners)
        if self.hps.data.add_blank:
            text_norm = commons.intersperse(text_norm, 0)
        text_norm = LongTensor(text_norm)
        return text_norm

    def __call__(
            self, text, speaker_id=0, speaker=None, language=None, speed=1.0, is_symbol=False
    ):
        language = language or self.lang
        if language is not None:
            language_mark = f"[{language[:2].upper()}]"
            text = language_mark + text + language_mark
        if speaker is not None:
            speaker_id = self.hps.speakers[speaker]
        stn_tst = self.get_text(text, is_symbol)
        with no_grad():
            x_tst = stn_tst.unsqueeze(0)
            x_tst_lengths = LongTensor([stn_tst.size(0)])
            sid = LongTensor([speaker_id])
            audio = self.model.infer(
                x_tst, x_tst_lengths, sid=sid,
                noise_scale=.667, noise_scale_w=0.8,
                length_scale=1.0 / speed
            )[0][0, 0].data.cpu().float().numpy()
        return self.hps.data.sampling_rate, audio


config = os.environ.get("CONFIG", "configs/uma_trilingual.json")
model = os.environ.get("MODEL", "pretrained_models/G_trilingual.pth")
onnx = os.environ.get("ONNX", "ONNX_net/G_trilingual/")
language = os.environ.get("LANGUAGE", "ja")

engine = Synthesizer(config, model, onnx, language)

app = Flask(__name__)
asgi_app = WsgiToAsgi(app)


@app.route("/process", methods=['POST'])
def post_process():
    text = request.form['INPUT_TEXT']
    language = request.form.get('LOCALE')
    speaker = request.form.get('VOICE')
    speed = request.form.get('SPEED')

    try:
        speaker_id = int(speaker)
        speaker = None
    except (ValueError, TypeError):
        speaker_id = None

    try:
        speed = float(speed)
    except (ValueError, TypeError):
        speed = 1.0

    sampling_rate, data = engine(text, speaker_id=speaker_id, speaker=speaker, language=language, speed=speed)
    with BytesIO() as w:
        sf.write(w, data, sampling_rate, format="WAV")
        data = w.getvalue()
    return Response(data, mimetype='audio/wav')
