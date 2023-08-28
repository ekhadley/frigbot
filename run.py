from Zenon.zenon import zenon
import time, os, sys, platform
from frig import *

def run(frig):
    print(bold, cyan, "\nFrigBot started", endc)
    while 1:
        resp = bot.parse_last_msg()
        bot.send(resp)
        time.sleep(bot.loop_delay)

if __name__ == '__main__':
    #chatid = 551246526924455937 # kissy
    chatid = 972938534661009519 # eekay
    if platform.system() == "Windows":
        keydir = "D:\\frig"
        frig = Frig(keydir, chatid=chatid) # eekay
        run(frig)

    if platform.system() == "Linux":
        import daemon
        keydir = "home/ek/Desktop/frigkeys/"
        frig = Frig(keydir, chatid=chatid) # eekay
        with daemon.DaemonContext():
            run(frig)
