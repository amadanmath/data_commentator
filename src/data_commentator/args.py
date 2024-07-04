from argparse import ArgumentParser, Namespace
from pathlib import Path
from typing import Any, Callable

import tomli


def parse_args(override_config: Callable[[dict[str, Any]], None] | None = None) -> Namespace:
    config_parser = ArgumentParser(add_help=False)
    _ = config_parser.add_argument('-c', '--config', type=Path, default='config.toml', help='config file')
    config_args, _ = config_parser.parse_known_args()
    with config_args.config.open('rb') as r:
        config = tomli.load(r)

    if override_config:
        override_config(config)

    webserver_config = config.get('webserver', {})
    parser = ArgumentParser()
    _ = parser.add_argument('-c', '--config', type=Path, default='config.toml', help='config file')
    _ = parser.add_argument('-b', '--bind', default=webserver_config.get('bind', '0.0.0.0'), help='binding address')
    _ = parser.add_argument('-p', '--port', type=int, default=webserver_config.get('port', 5007), help='binding port')
    _ = parser.add_argument('-s', '--static', type=Path, default=webserver_config.get('static'), help='static folder')
    _ = parser.add_argument('-i', '--input', type=Path, default=config.get('input'), help='JSONL path to read')
    _ = parser.add_argument('-o', '--output', type=Path, default=config.get('output'), help='JSONL path to write')
    _ = parser.add_argument('-w', '--window', type=int, default=config.get('window', 100), help='Size of the data window')
    _ = parser.add_argument('-n', '--interval', type=float, default=config.get('interval', None), help='Interval between samples')
    _ = parser.add_argument('-t', '--ts-field', type=str, default=config.get('ts_field', 'timestamp'), help='Payload field carrying timestamp')
    _ = parser.add_argument('--buffer-size', type=int, default=webserver_config.get('buffer_size', 0), help='Payload buffer size')

    # _ = parser.add_argument('rules_yml', metavar='RULES', type=Path, default=None, help='rules YAML file')

    args = parser.parse_args()

    args.payload_enhancer = config.get('payload_enhancer')
    args.priority_predictor = config.get('priority_predictor')
    args.predictor = config['predictor']
    args.synthesizer = config.get('synthesizer')
    args.speaker = config.get('speaker', {
        "name": "data_commentator.speaker.simpleaudio.SimpleAudio",
    })

    return args
