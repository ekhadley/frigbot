from Zenon.zenon import zenon
import time, os, sys, platform
from frig import *

print(platform.system())

if __name__ == '__main__':
    #chatid = 551246526924455937 # kissy
    chatid = 972938534661009519 # eekay
    if platform.system() == "Windows":
        keydir = "D:\\frig"
        frig = Frig(keydir, chatid=chatid) # eekay
        print(bold, cyan, "\nFrigBot started", endc)
        while 1:
            resp = frig.parse_last_msg()
            frig.send(resp)
            time.sleep(frig.loop_delay)
    
