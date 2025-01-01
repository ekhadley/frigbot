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
        keypath = "/home/ek/Desktop/keys.json"
        configDir = "/home/ek/Desktop/wgmn/frigbot/config"
    else:
        assert 0, f"unrecognized host system: {system}"

    frig = Frig(keypath=keypath, configDir=configDir, chatid=args.chatid)
    '''
    while 1:
        try:
            frig.runloop()
        except Exception as e:
            print(f"{red}, {bold}, [FRIG] CRASHED WITH EXCEPTION:\n{e}")
            time.sleep(3)
    frig.send(f"frigbot has crashed. F for frigbot. spam @eekay")
    '''
    frig.runloop()
    #assert 0, f"reached maximum consecutive crashes. aborting bot."
