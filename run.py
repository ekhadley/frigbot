"""
import sys
import platform
import argparse
from frigbot import Frig

key_path = "/home/ek/frigkeys.json"
config_path = "/home/ek/wgmn/frigbot/config"

eekay_dms_id = 551246526924455937
kissy_chat_id = 972938534661009519

parser = argparse.ArgumentParser()
parser.add_argument('chat_id', help="channel id. defaults to kissy", nargs="?", type=int, default=kissy_chat_id)
if __name__ == '__main__':
    nargs = len(sys.argv) - 1
    assert nargs <= 2, f"expected 1 or 0 arguments. got {nargs}:\n{sys.argv}"

    args = parser.parse_args()

    frig = Frig(keypath=key_path, configDir=config_path, chatid=args.chat_id)
    frig.runloop()
"""
import sys
import argparse
from frigbot import Frig

key_path = "/home/ek/frigkeys.json"
config_path = "/home/ek/wgmn/frigbot/config"

eekay_dms_id = 972938534661009519
kissy_chat_id = 551246526924455937


parser = argparse.ArgumentParser(description="Run frigbot with optional test and quiet modes.")
parser.add_argument("-t", "--test", action="store_true", help="Use test chat ID (eekay_dms_id)")

if __name__ == '__main__':
    args = parser.parse_args()
    chat_id = eekay_dms_id if args.test else kissy_chat_id
    frig = Frig(keypath=key_path, configDir=config_path, chatid=chat_id)
    frig.runloop()
