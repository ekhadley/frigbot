import datetime
import json
import math

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

TIER_COLORS = {
    'IRON': 0x7C7C7C, 'BRONZE': 0xCD7F32, 'SILVER': 0xC0C0C0,
    'GOLD': 0xFFD700, 'PLATINUM': 0x00CED1, 'EMERALD': 0x50C878,
    'DIAMOND': 0xB9F2FF, 'MASTER': 0x9B59B6, 'GRANDMASTER': 0xFF6B6B,
    'CHALLENGER': 0xF0E68C,
}

def contains_scrambled(msg, key):
    state = 0
    for c in msg:
        if c.lower() == key[state]:
            state += 1
        if state == len(key):
            return True
    return False


def split_resp(resp):
    if len(resp) >= 2000:
        nsplit = math.ceil(len(resp)/2000)
        interval = len(resp)//nsplit
        return [resp[i*interval:(i+1)*interval] for i in range(nsplit)]
    return resp
