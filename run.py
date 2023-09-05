from Zenon.zenon import zenon
import time, os, sys, platform
from frig import *

def run(frig):
    print(bold, cyan, "\nFrigBot started!", endc)
    while 1:
        resp = frig.parse_last_msg()
        frig.send(resp)
        time.sleep(frig.loop_delay)

if __name__ == '__main__':
    system = platform.system()
    #chatid = 551246526924455937 # kissy
    chatid = 972938534661009519 # eekay
    if system == "Windows":
        keydir = "D:\\frig\\"
        configDir = "D:\\wgmn\\frigbot\\config\\"
    elif system == "Linux":
        keydir = "/home/ek/Desktop/frigkeys/"
        configDir = "/home/ek/Desktop/wgmn/frigbot/config/"
    else: assert 0, f"unrecognized host system: {system}"
    
    Frig = Frig(keydir=keydir, configDir=configDir, chatid=chatid) # eekay
    i = 0
    while i < 5:
        try:
            run(Frig)
            i = 0
        except Exception as e:
            i += 1
            print(f"{bold}crashed with exception:\n{e}\n This is the {i}'th/4 consecutive crash.{endc}")
    Frig.send(f"frigbot has crashed. F for frigbot. spam @.eekay")
    assert 0, f"reached maximum consecutive crashes. aborting bot."
