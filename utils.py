import datetime, random, math, json, requests, time, os, numpy as np
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


def dateload(pth):
    with open(pth) as f:
        dstr = f.readline().strip()
    return datetime.datetime.strptime(dstr, "%Y-%b-%d (%H:%M:%S)")

def datesave(date, pth):
    with open(pth, mode='w+') as f:
        f.write(daterep(date))
        f.close()


