"""Script to run benchmarks."""
import asyncio
import argparse
from contextlib import suppress
import logging
import time

from homeassistant import core

BENCHMARKS = {}


def run(args):
    """Handle ensure config commandline script."""
    # Disable logging
    logging.getLogger('homeassistant.core').setLevel(logging.CRITICAL)

    parser = argparse.ArgumentParser(
        description=("Run a Home Assistant benchmark."))
    parser.add_argument('name', choices=BENCHMARKS)
    parser.add_argument('--script', choices=['benchmark'])

    args = parser.parse_args()

    benchmark = BENCHMARKS[args.name]

    print('Using event loop:', asyncio.get_event_loop_policy().__module__)

    with suppress(KeyboardInterrupt):
        while True:
            loop = asyncio.new_event_loop()
            hass = core.HomeAssistant(loop)
            hass.async_stop_track_tasks()
            runtime = loop.run_until_complete(benchmark(hass))
            print('Benchmark {} done in {}s'.format(
                benchmark.__name__, runtime))
            loop.run_until_complete(hass.async_stop())
            loop.close()

    return 0


def benchmark(func):
    """Decorator to mark a benchmark."""
    BENCHMARKS[func.__name__] = func
    return func


@benchmark
@asyncio.coroutine
def async_million_events(hass):
    """Run a million events."""
    count = 0
    event_name = 'benchmark_event'
    event = asyncio.Event(loop=hass.loop)

    @core.callback
    def listener(_):
        """Handle event."""
        nonlocal count
        count += 1

        if count == 10**6:
            event.set()

    hass.bus.async_listen(event_name, listener)

    start = time.time()

    for _ in range(10**6):
        hass.bus.async_fire(event_name)

    yield from event.wait()

    return time.time() - start
