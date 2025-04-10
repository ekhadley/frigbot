import datetime
import json

purple  = "\033[38;2;255;0;255m"
blue    = "\033[38;2;0;0;255m"
brown   = "\033[38;2;128;128;0m"
cyan    = "\033[38;2;0;255;255m"
lime    = "\033[38;2;0;255;0m"
yellow  = "\033[38;2;255;255;0m"
red     = "\033[38;2;255;0;0m"
pink    = "\033[38;2;255;95;215m"
orange  = "\033[38;2;255;95;0m"
green   = "\033[38;2;0;175;0m"
gray    = "\033[38;2;127;127;127m"
magenta = "\033[38;2;128;0;128m"
bold = '\033[1m'
underline = '\033[4m'
endc = '\033[0m'

ared = "[31m"
#agreen = "[32m"
alime = '[32m'
ayellow = '[33m'
ablue = '[34m'
apurple = '[35m'
acyan = '[36m'
awhite = '[37m'
agray = '[30m'

abrown = '[33m'
apink = "[38;5;206m"
aorange = "[38;5;202m"
agray = "[38;5;8m"
abold = '[1m'
aunderline = '[4m'
aendc = '[0m'
rankColors = {'IRON':agray, 'BRONZE':ared, 'SILVER':awhite, 'GOLD':ayellow, 'PLATINUM':acyan, 'EMERALD':alime, 'DIAMOND':ablue, 'MASTER':red, 'GRANDMASTER':apink, 'CHALLENGER':apurple}

def contains_scrambled(msg, key):
    state = 0
    for c in msg:
        if c.lower() == key[state]:
            state += 1
        if state == len(key):
            return True
    return False

def daterep(dat):
    return dat.strftime("%Y-%b-%d (%H:%M:%S)")

def strptime(dstr): return datetime.datetime.strptime(dstr, "%Y-%b-%d (%H:%M:%S)")

def dateload(*args):
    assert 0 < (nargs:=len(args)) and nargs < 3, f"{red}found {len(args)} args{endc}. Expected 2 args (dir, name) or 1 (path)"
    if len(args) == 1:
        path = args[0]
    else:
        path = f"{args[0]}/{args[1]}"
    path += "" if path.endswith('.txt') else '.txt'
    with open(path) as f:
        return strptime(f.readline().strip())

def datesave(date, pth):
    with open(pth, mode='w+') as f:
        f.write(daterep(date))

def loadjson(*args):
    assert 0 < (nargs:=len(args)) and nargs < 3, f"{red}found {len(args)} args{endc}. Expected 2 args (dir, name) or 1 (path)"
    if len(args) == 1:
        path = args[0]
    else:
        path = f"{args[0]}/{args[1]}"
    path += "" if path.endswith('.json') else '.json'
    with open(path) as f:
        return json.load(f)
