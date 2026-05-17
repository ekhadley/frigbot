import os
import asyncio
import argparse
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / '.env')

import uvicorn

from frigbot import FrigBot
from logger_config import setup_logging
import streaks_db
from puzzles_api import app as fastapi_app

state_dict_path = "/home/ek/wgmn/frigbot/state.json"

parser = argparse.ArgumentParser(description="Run frigbot with optional test mode.")
parser.add_argument("-t", "--test", action="store_true", help="Use test channel with instant command sync")


async def main():
    args = parser.parse_args()
    logger = setup_logging()

    guild_id = int(os.environ['DISCORD_GUILD_ID'])
    channel_id = int(os.environ['DISCORD_CHANNEL_ID'])
    if args.test:
        channel_id = int(os.environ.get('DISCORD_TEST_CHANNEL_ID', str(channel_id)))

    logger.info("Starting FrigBot", extra={'data': {
        'test_mode': args.test, 'channel_id': channel_id, 'guild_id': guild_id, 'event_type': 'bot_starting',
    }})

    streaks_db.init_db()

    frig = FrigBot(channel_id=channel_id, guild_id=guild_id, state_dict_path=state_dict_path)
    frig.load_state()

    config = uvicorn.Config(fastapi_app, host="127.0.0.1", port=8001, log_level="info")
    server = uvicorn.Server(config)

    await asyncio.gather(frig.start(), server.serve())


if __name__ == '__main__':
    asyncio.run(main())
