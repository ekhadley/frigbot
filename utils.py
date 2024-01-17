import datetime, random, math, json, requests, time, os, numpy as np
from googleapiclient.discovery import build
from Zenon.zenon import zenon
import openai

purple = '\033[95m'
blue = '\033[94m'
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

def daterep(dat):
    return dat.strftime("%Y-%b-%d (%H:%M:%S)")

def strptime(dstr): return datetime.datetime.strptime(dstr, "%Y-%b-%d (%H:%M:%S)")

#def dateload(dir_, name):
#    return strptime(loadtxt(dir_, name).readline().strip())

#def loadtxt(*args):
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

'''
def reporter(func):
    def report(*args, **kwargs):
        print(args)
        print(kwargs)
        return func(*args, **kwargs)
    return report

@reporter
def mult(a, b):
    print(a*b)
    return a*b

mult(4, 23)
'''
