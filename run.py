import os
import argparse
from pathlib import Path
from dotenv import load_dotenv
from frigbot import FrigBot
from logger_config import setup_logging

state_dict_path = "/home/ek/wgmn/frigbot/state.json"

parser = argparse.ArgumentParser(description="Run frigbot with optional test mode.")
parser.add_argument("-t", "--test", action="store_true", help="Use test channel with instant command sync")

if __name__ == '__main__':
    load_dotenv(Path(__file__).parent / '.env')
    args = parser.parse_args()
    logger = setup_logging()

    guild_id = int(os.environ['DISCORD_GUILD_ID'])
    channel_id = int(os.environ['DISCORD_CHANNEL_ID'])
    if args.test:
        channel_id = int(os.environ.get('DISCORD_TEST_CHANNEL_ID', str(channel_id)))

    logger.info("Starting FrigBot", extra={'data': {
        'test_mode': args.test, 'channel_id': channel_id, 'guild_id': guild_id, 'event_type': 'bot_starting',
    }})

    frig = FrigBot(channel_id=channel_id, guild_id=guild_id, state_dict_path=state_dict_path)
    frig.load_state()
    frig.run()
