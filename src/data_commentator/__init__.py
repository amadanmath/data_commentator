try:
    import icecream
    icecream.install()
    import time
    ic.configureOutput(prefix=lambda: "%i |> " % int(time.time()))
except ImportError:
    import builtins
    from typing import TypeVar
    T = TypeVar('T')
    def ic(*a: T) -> T:
        return None if not a else (a[0] if len(a) == 1 else a)
    setattr(builtins, "ic", ic)

# TODO: move most of this into another file to avoid a circular import

import argparse

import trio
from exceptiongroup import BaseExceptionGroup, catch

from .types import Payload
from .args import parse_args
from .async_server import AsyncServer
from .collector_server import CollectorServer
from .utterance_server import UtteranceServer
from .synthesizer import Synthesizer
from .speaker import Speaker
from .priority import Priority
from .loader import load_and_instantiate, load_and_instantiate_server
from .webserver import webserver


async def run(args: argparse.Namespace) -> None:
    data_channel: tuple[trio.MemorySendChannel[Payload], trio.MemoryReceiveChannel[Payload]] = trio.open_memory_channel(args.buffer_size)

    payload_enhancer: AsyncServer | None = load_and_instantiate_server(args.payload_enhancer)
    priority_predictor: AsyncServer | None = load_and_instantiate_server(args.priority_predictor)
    predictor: AsyncServer | None = load_and_instantiate_server(args.predictor)
    synthesizer: Synthesizer | None = load_and_instantiate(args.synthesizer)
    speaker: Speaker = load_and_instantiate(args.speaker)

    if predictor is None:
        raise RuntimeError("No predictor")

    priority = Priority()
    utterance_server = UtteranceServer(predictor, synthesizer, speaker, priority)
    collector_server = CollectorServer(
        receive_channel=data_channel[1],
        utterance_server=utterance_server,
        window_size=args.window,
        ts_field=args.ts_field,
        priority=priority,
        priority_predictor=priority_predictor,
        payload_enhancer=payload_enhancer,
        output_file=args.output,
        interval=args.interval,
    )

    if args.input:
        from .data_source_server.jsonlreader import JSONLReader
        data_source_server = JSONLReader(send_channel=data_channel[0], jsonl=args.input, ts_field=args.ts_field)
        webserver_send_channel = None 
    else:
        data_source_server = None
        webserver_send_channel = data_channel[0]

    webserver.setup(args.static, webserver_send_channel, args.bind, args.port)

    def handle_stop(_: BaseExceptionGroup[KeyboardInterrupt | trio.EndOfChannel]) -> None:
        nonlocal nursery
        print("\nStopping...")
        nursery.cancel_scope.cancel()
    with catch({
        KeyboardInterrupt: handle_stop,
        trio.EndOfChannel: handle_stop,
    }):
        async with trio.open_nursery() as nursery:
            nursery.start_soon(predictor.serve)
            if priority_predictor:
                nursery.start_soon(priority_predictor.serve)
            if payload_enhancer:
                nursery.start_soon(payload_enhancer.serve)
            nursery.start_soon(utterance_server.serve)
            nursery.start_soon(collector_server.serve)
            if data_source_server:
                nursery.start_soon(data_source_server.serve)
            nursery.start_soon(webserver.serve)

def main(args: argparse.Namespace | None = None) -> None:
    if args is None:
        args = parse_args()
    trio.run(run, args)
