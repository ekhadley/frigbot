from frigbot import Frig



def formatMessage(msg):
    if isinstance(msg, list): return "".join([formatMessage(m)+"\n" for m in msg])
    return f"{msg['author']['global_name']}: {msg['content']}"


key_path = "/home/ek/frigkeys.json"
config_path = "/home/ek/wgmn/frigbot/config"
chatid = 972938534661009519 # eekay
#chatid = 551246526924455937 # kissy
if __name__ == '__main__':
    frig = Frig(keypath=key_path, configDir=config_path, chatid=chatid)


    msg = frig.getLatestMessage(num_messages = 2)
    print(msg)
    print()
    print()
    print()
    print()
    fmt = formatMessage(msg)
    print(fmt)
    
