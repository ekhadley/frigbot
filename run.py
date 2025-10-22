import json
import argparse
from frigbot import Frig

keys_path = "/home/ek/frigkeys.json"
#data_path = "/home/ek/wgmn/frigbot/config"
state_dict_path = "/home/ek/wgmn/frigbot/state.json"

eekay_dms_id = 972938534661009519
kissy_chat_id = 551246526924455937

parser = argparse.ArgumentParser(description="Run frigbot with optional test mode.")
parser.add_argument("-t", "--test", action="store_true", help="Use test chat ID (eekay_dms_id)")

if __name__ == '__main__':
    args = parser.parse_args()
    chat_id = eekay_dms_id if args.test else kissy_chat_id
    #frig = Frig(keys_path=keys_path, chat_id=chat_id)
    frig = Frig.load_from_state_dict(state_dict_path, chat_id=chat_id)
    frig.runloop()
