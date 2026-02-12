import argparse
from pathlib import Path
from dotenv import load_dotenv
from frigbot import Frig
from logger_config import setup_logging

state_dict_path = "/home/ek/wgmn/frigbot/state.json"

eekay_dms_id = 972938534661009519
kissy_chat_id = 551246526924455937

parser = argparse.ArgumentParser(description="Run frigbot with optional test mode.")
parser.add_argument("-t", "--test", action="store_true", help="Use test chat ID (eekay_dms_id)")

if __name__ == '__main__':
    load_dotenv(Path(__file__).parent / '.env')
    args = parser.parse_args()

    # Setup logging
    logger = setup_logging()

    chat_id = eekay_dms_id if args.test else kissy_chat_id
    logger.info(f"Starting FrigBot (test_mode={args.test})", extra={'data': {'test_mode': args.test, 'chat_id': chat_id, 'event_type': 'bot_starting'}})

    frig = Frig.load_from_state_dict(state_dict_path, chat_id=chat_id)

    logger.info("Entering main message loop", extra={'data': {'chat_id': chat_id, 'event_type': 'entering_main_loop'}})
    frig.runloop()
