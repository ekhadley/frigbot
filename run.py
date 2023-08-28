from Zenon.zenon import zenon
import time, os
from frig import *
import daemon



if __name__ == '__main__':
    #frig = Frig(chatid=551246526924455937) #kissy
    frig = Frig(chatid=972938534661009519) # eekay
    print(bold, cyan, "\nFrigBot started", endc)
    while 1:
        resp = frig.parse_last_msg()
        frig.send(resp)
        time.sleep(frig.loop_delay)
