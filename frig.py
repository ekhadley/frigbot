import datetime, random, math, json, requests, time, os, numpy as np
from Zenon.zenon import zenon
import openai
from utils import *

class Frig:
    def __init__(self, keydir, configDir, chatid=551246526924455937):
        self.chatid = chatid
        self.keydir = keydir
        self.configDir = configDir
        self.token = open(f"{keydir}frigtoken.txt").readline().strip()
        self.openaikey = open(f"{keydir}openai_key.txt").readline().strip()
        self.riotkey = open(f"{keydir}riotapi.txt").readline().strip()
        self.lastfap =  self.load_lastfap()
        
        self.lol = lolManager(self.riotkey, self.configDir)
        openai.api_key = self.openaikey
        self.client = zenon.Client(self.token)

        self.user_IDs = self.load_user_ids()

        self.botname = self.user_IDs["FriggBot2000"]

        self.commands = {"!help":self.help_resp, # a dict of associations between commands (prefaced with a '!') and the functions they call to generate responses.
                         "!commands":self.help_resp,
                         "!cmds":self.help_resp,
                         "!gpt4":self.gpt_resp,
                         "!gpt":self.gpt_resp,
                         "!arcane":self.arcane_resp,
                         "!faptime":self.faptime_resp,
                         "!lastfap":self.lastfap_resp,
                         "!fapfail":self.fapfail_resp,
                         "!lostfap":self.fapfail_resp,
                         "!lp":self.lp_resp}

        self.echo_resps = [ # the static repsonse messages for trigger words which I term "echo" responses
                "This computer is shared with others including parents. This is a parent speaking to you to now. Not sure what this group is up to. I have told my son that role playing d and d games are absolutely forbidden in out household. We do not mind him having online friendships with local people that he knows for legitimate purposes. Perhaps this is an innocent group. But, we expect transparency in our son's friendships and acquaintances. If you would like to identify yourself now and let me know what your purpose for this platform is this is fine. You are welcome to do so.",
                           
                ["Do not go gentle into that good juckyard.", "Tetus should burn and rave at close of day.", "Rage, rage against the dying of the gamings.", "Though wise men at their end know gaming is right,", "Becuase their plays had got no karma they", "Do not go gentle into that good juckyard"]
                           ]

        self.echoes = {"nefarious":self.echo_resps[0], # these are the trigger words and their associated echo
                       "avatars":self.echo_resps[0],
                       "poem":self.echo_resps[1],
                       "poetry":self.echo_resps[1],
                       "tetus":self.echo_resps[1],
                       "juckyard":self.echo_resps[1]
                       }


        self.last_msg_id = 0 # unique message id. Used to check if a new message has appeared
        self.loop_delay = 0.3 # delay in seconds between checking for new mesages

    def arcane_resp(self, msg):
        delta = datetime.datetime(2024,12,25, 21, 5, 0) - datetime.datetime.now()
        days, hours, minutes, seconds = delta.days, delta.seconds//3600, (delta.seconds%3600)//60, delta.seconds%60
        return f"arcane s2 comes out in approximately {days} days, {hours} hours, {minutes} minutes, and {seconds} seconds. hang in there."

    def gpt_resp(self, msg):
        print(f"{bold}{gray}[GPT]: {endc}{lemon}text completion requested{endc}")
        try:
            completion = openai.ChatCompletion.create(model="gpt-4", messages=[{"role": "user", "content": msg["content"]}])
            resp = completion.choices[0].message.content
            print(f"{bold}{gray}[GPT]: {endc}{green}text completion generated {endc}")
            return resp
        except Exception as e:
            print(f"{bold}{gray}[GPT]: {endc}{red}text completion failed with exception:\n{e}{endc}")
            return "https://tenor.com/view/bkrafty-bkraftyerror-bafty-error-gif-25963379"

    def help_resp(self, msg):
        resp = f"commands:"
        for c in self.commands: resp += f"\n{c}"
        return resp

    def lp_resp(self, msg):
        summ = msg["content"].replace("!lp", "").strip()
        return self.lol.ranked_info(summ)

    def send(self, msg): # sends a string or list of strings as a message/messages in the chat
        if isinstance(msg, list):
            for m in msg: self.send(m)
        elif isinstance(msg, str) and msg != "":
            self.client.send_message(self.chatid, msg)

    def get_last_msg(self) -> str: # reads the most recent message in the chat, returns a json
        try:
            msg = self.client.get_message(self.chatid)
            return msg
        except Exception as e:
            print(f"{bold}{gray}[FRIG]: {endc}{red}message read failed with exception:\n{e}{endc}")
            return None
    
    def parse_last_msg(self): # reads most recent msg, determines if it has been previously seen, and what command to respond with, if any
        msg = self.get_last_msg()
        if msg["id"] != self.last_msg_id and msg["author"]["id"] != self.botname:
            try:
                author = self.user_IDs[msg["author"]["global_name"]]
            except KeyError:
                print(f"{bold}{gray}[FRIG]: {endc}{lemon}new username '{msg['author']['global_name']}' detected. storing their ID. {endc}")
                self.user_IDs[msg["author"]["global_name"]] = msg["author"]["id"]
                with open(f"{self.configDir}userIDs.json", "w") as f:
                    f.write(json.dumps(self.user_IDs, indent=4))
            
            self.last_msg_id = msg["id"]
            return self.get_response(msg)
        return ""

    def get_response(self, msg): # determines how to respond to a newly detected message. 
        body = msg["content"].lstrip()
        if body.startswith("!"):
            try:
                command = body.split(" ")[0]
                print(f"{bold}{gray}[FRIG]: {endc}{lemon} command found: {command}{endc}")
                return self.commands[command](msg)
            except KeyError as e:
                print(f"{bold}{gray}[FRIG]: {endc}{red} detected command '{command}' but type was unrecognized{endc}")
                return f"command: '{command}' was not recognized"
        else:
            for e in self.echoes:
                if e in body.split(" "):
                    print(f"{bold}{gray}[FRIG]: {endc}{gray} issuing echo for '{e}'{endc}")
                    return self.echoes[e]
        return ""

    def load_user_ids(self):
        with open(f"{self.configDir}userIDs.json", 'r') as f:
            return json.load(f)

    def load_lastfap(self):
        try:
            return dateload(f"{self.configDir}lastfap.txt")
        except Exception as e:
            print(e)
            return None

    def faptime(self):
        delta = datetime.datetime.now() - self.lastfap
        days, hours, minutes, seconds = delta.days, delta.seconds//3600, (delta.seconds%3600)//60, delta.seconds%60
        return days, hours, minutes, seconds
    def faptime_resp(self, msg):
        days, hours, minutes, seconds = self.faptime()
        return f"Xylotile has not nutted in {days} days, {hours} hours, {minutes} minutes, and {seconds} seconds. stay strong."
    def lastfap_resp(self, msg):
        return f"Xylotile's last nut was on {self.lastfap.strftime('%B %d %Y at %I:%M%p')}"
    def fapfail_resp(self, msg):
        authorid = msg["author"]["id"]
        try:
            if int(authorid) != int(self.user_IDs["Xylotile"]): return f"You are not authorized to make Xylotile nut."
            else:
                days, hours, minutes, seconds = self.faptime()
                self.set_last_fap()
                return ["https://tenor.com/view/ambatukam-ambasing-ambadeblow-gif-25400729", f"Xylotile has just lost their nofap streak of {days} days, {hours} hours, {minutes} minutes, and {seconds} seconds."]
        except KeyError:
            print(bold, red, f"Xylotile's userID could not be found, so the fapstreak update could not be verified. thats not good! spam @eekay")
    def set_last_fap(self):
        datesave(datetime.datetime.now(), f"{self.configDir}lastfap.txt")
        self.lastfap = self.load_lastfap()

class lolManager: # this handles requests to the riot api
    def __init__(self, riotkey, saveDir):
        self.saveDir = saveDir
        self.riotkey = riotkey
        self.summonerIDs = self.load_player_ids()

    def load_player_ids(self):
        with open(f"{self.saveDir}summonerIDs.json", 'r') as f:
            return json.load(f)
    
    def get_summoner_id(self, summonerName, region=None):
        try:
            return self.summonerIDs[str(summonerName)]
        except KeyError:
            print(f"{gray}{bold}[LOL]:{endc} {lemon}requested summonerID for new name:' {summonerName}'{endc}")
            url = f"https://{region}.api.riotgames.com/lol/summoner/v4/summoners/by-name/{summonerName}?api_key={self.riotkey}"
            get = requests.get(url)
            if get.status_code == 200:
                self.summonerIDs[str(summonerName)] = get.json()["id"]
                print(f"{gray}{bold}[LOL]:{endc} {lemon}stored summonerID for new username: '{summonerName}'{endc}")
                self.store_player_ids()
                return self.summonerIDs[str(summonerName)]
            else:
                print(f"{gray}{bold}[LOL]:{endc} {red}summonerID for new username: '{summonerName}' could not be located{endc}")
                return None
    def store_player_ids(self):
        with open(f"{self.saveDir}summonerIDs.json", "w") as f:
            f.write(json.dumps(self.summonerIDs, indent=4))

    def ranked_info(self, summonerName, region=None):
        region = "na1" if region is None else region
        summonerID = self.get_summoner_id(summonerName, region)
        url = f"https://{region}.api.riotgames.com/lol/league/v4/entries/by-summoner/{summonerID}?api_key={self.riotkey}"
        get = requests.get(url)
        if get.status_code == 200:
            report = self.parse_ranked_info(get.json(), summonerName)
            print(f"{gray}{bold}[LOL]: {endc}{green}ranked info acquired for '{summonerName}'{endc}")
            return report
        elif get.status_code == 403:
            print(f"{gray}{bold}[LOL]: {endc}{red}got 403 for name '{summonerName}'. key is probably expired. request url:\n{url}{endc}")
            return f"got 403 for name '{summonerName}'. key is probably expired. blame riot"
        else:
            print(f"{gray}{bold}[LOL]: {endc}{red}attempted ID for '{summonerName}' got: {get}. request url:\n{url}'{endc}")
            return "https://tenor.com/view/snoop-dog-who-what-gif-14541222"
    
    def parse_ranked_info(self, info, name):
        if info == []:
            if "dragondude" in name.lower(): return "ap is still a bitch (not on the ranked grind)"
            return f"{name} is not on the ranked grind"
        try:
            info = info[0]
            name = info["summonerName"]
            lp = info["leaguePoints"]
            wins = int(info["wins"])
            losses = int(info["losses"])
            winrate = wins/(wins+losses)

            tier = info["tier"].lower().capitalize()
            div = info["rank"]
            rankrep = f"in {tier} {div} at {lp} lp"

            rep = f"{name} is {rankrep} with a {winrate:.3f} wr over {wins+losses} games"
            return rep
        except ValueError: print(info); return f"got ranked info:\n'{info}',\n but failed to parse. (spam @eekay)"
    
