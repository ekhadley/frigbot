import datetime, random, math, json, requests, time, os, openai
from googleapiclient.discovery import build
from Zenon.zenon import zenon

purple = '\033[95m'
blue = '\033[94m'
brown = '\033[33m'
cyan = '\033[96m'
lime = '\033[92m'
yellow = '\033[93m'
red = "\033[38;5;196m"
pink = "\033[38;5;206m"
orange = "\033[38;5;202m"
green = "\033[38;5;34m"
gray = "\033[38;5;8m"
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

def contains_scrambled(msg, key):
    state = 0
    for c in msg:
        if c.lower() == key[state]: state += 1
        if state == len(key): return True
    return False


def daterep(dat):
    return dat.strftime("%Y-%b-%d (%H:%M:%S)")

def strptime(dstr): return datetime.datetime.strptime(dstr, "%Y-%b-%d (%H:%M:%S)")

def dateload(*args):
    assert 0 < (nargs:=len(args)) and nargs < 3, f"{red}found {len(args)} args{endc}. Expected 2 args (dir, name) or 1 (path)"
    if len(args) == 1: path = args[0]
    else: path = f"{args[0]}/{args[1]}"
    path += "" if path.endswith('.txt') else '.txt'
    with open(path) as f:
        return strptime(f.readline().strip())

def datesave(date, pth):
    with open(pth, mode='w+') as f:
        f.write(daterep(date))

def loadjson(*args):
    assert 0 < (nargs:=len(args)) and nargs < 3, f"{red}found {len(args)} args{endc}. Expected 2 args (dir, name) or 1 (path)"
    if len(args) == 1: path = args[0]
    else: path = f"{args[0]}/{args[1]}"
    path += "" if path.endswith('.json') else '.json'
    with open(path) as f:
        return json.load(f)