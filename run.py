from Zenon.zenon import zenon
import time, os, sys, platform
from frig import *

def run(frig):
    print(bold, cyan, "\nFrigBot started", endc)
    while 1:
        resp = frig.parse_last_msg()
        frig.send(resp)
        time.sleep(frig.loop_delay)

if __name__ == '__main__':
    chatid = 551246526924455937 # kissy
    #chatid = 972938534661009519 # eekay
    if platform.system() == "Windows":
        keydir = "D:\\frig\\"
        configDir = "D:\\wgmn\\frigbot\\config\\"
        frig = Frig(keydir=keydir, configDir=configDir, chatid=chatid) # eekay
        run(frig)

    if platform.system() == "Linux":
        import daemon
        keydir = "/home/ek/Desktop/frigkeys/"
        configDir = "/home/ek/Desktop/wgmn/frigbot/config/"
        frig = Frig(keydir=keydir, configDir=configDir, chatid=chatid) # eekay
        with daemon.DaemonContext():
            run(frig)
