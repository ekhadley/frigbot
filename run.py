import sys
import platform
import argparse
from frigbot import Frig

chatid = 551246526924455937 # kissy
eekayid = 972938534661009519 # eekay
parser = argparse.ArgumentParser()
parser.add_argument('chatid', help="channel id. defaults to kissy", nargs="?", type=int, default=chatid)
if __name__ == '__main__':
    nargs = len(sys.argv) - 1
    assert nargs <= 2, f"expected 1 or 0 arguments. got {nargs}:\n{sys.argv}"
    args = parser.parse_args()
    
    system = platform.system()
    if system == "Windows":
        keypath = "D:\\frig\\keys.json"
        configDir = "D:\\wgmn\\frigbot\\config"
    elif system == "Linux":
        keypath = "/home/ek/frigkeys.json"
        configDir = "/home/ek/wgmn/frigbot/config"
    else:
        assert 0, f"unrecognized host system: {system}"
        exit()

    frig = Frig(keypath=keypath, configDir=configDir, chatid=args.chatid)
    frig.runloop()
