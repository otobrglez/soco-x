#!/usr/bin/env python

import asyncio
import logging
import soco
from soco import SoCo


class BaseConfig(object):
    PLAYER_NAME = None
    DESIRED_VOLUME = 20
    SLEEP_INTERVAL = 5
    SOCO_DISCOVER_TIMEOUT = 5


class WorkConfig(BaseConfig):
    PLAYER_NAME = "Main"


CONFIG = WorkConfig


class NoDeviceFound(Exception): pass


def find_player(player_name: str) -> SoCo:
    device = None
    try:
        device = [zone for zone in soco.discover(timeout=CONFIG.SOCO_DISCOVER_TIMEOUT) if
                  zone and zone.player_name == player_name][0]
    except:
        raise NoDeviceFound("No device {} found".format(player_name))

    return device


current_track: dict = {}


def current_track_hash() -> int:
    return hash('' + ''.join(current_track.values()))


def normalize_volume():
    global current_track
    player = find_player(CONFIG.PLAYER_NAME)
    track_dict = dict(player.get_current_track_info())
    track = {'artist': track_dict['artist'], 'title': track_dict['title']}
    track_hash = hash('' + ''.join(track.values()))
    if track_hash != current_track_hash():
        current_track = track
        logging.info("{} - {}".format(track['artist'], track['title']))

    if player.volume > CONFIG.DESIRED_VOLUME:
        logging.info("Volume is too loud {}. Reducing.".format(player.volume))
        player.volume -= 2


async def loop_set_device(event_loop: asyncio.BaseEventLoop):
    try:
        while event_loop.is_running():
            normalize_volume()
            await asyncio.sleep(CONFIG.SLEEP_INTERVAL)
    except asyncio.CancelledError:
        await asyncio.sleep(0)


def main():
    logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(message)s')
    logging.getLogger('soco').setLevel(logging.ERROR)

    loop = asyncio.get_event_loop()

    task = loop.create_task(loop_set_device(loop))

    future = asyncio.gather(task)

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        future.cancel()
        loop.run_until_complete(future)
        loop.close()


if __name__ == '__main__':
    main()
