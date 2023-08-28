import random, math, json, requests, time, os, numpy as np
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

class Frig:
    def __init__(self, keydir, configDir, chatid=551246526924455937):
        self.chatid = chatid
        self.keydir = keydir
        self.configDir = configDir
        self.token = open(f"{keydir}frigtoken.txt").readline().strip()
        print(self.token)
        self.openaikey = open(f"{keydir}openai_key.txt").readline().strip()
        self.riotkey = open(f"{keydir}riotapi.txt").readline().strip()
        
        self.lol = lolManager(self.riotkey, self.configDir)
        openai.api_key = self.openaikey
        self.client = zenon.Client(self.token)

        self.user_IDs = self.load_user_ids()


        self.commands = {"!help":self.help_resp,
                         "!commands":self.help_resp,
                         "!cmds":self.help_resp,
                         "!gpt4":self.gpt_resp,
                         "!gpt":self.gpt_resp,
                         "!lp":self.lp_resp}

        self.echoes = {"nefarious":"This computer is shared with others including parents. This is a parent speaking to you to now. Not sure what this group is up to. I have told my son that role playing d and d games are absolutely forbidden in out household. We do not mind him having online friendships with local people that he knows for legitimate purposes. Perhaps this is an innocent group. But, we expect transparency in our son's friendships and acquaintances. If you would like to identify yourself now and let me know what your purpose for this platform is this is fine. You are welcome to do so."}

        self.last_msg_id = 0
        self.loop_delay = 0.05

    def gpt_resp(self, msg):
        print(f"{bold}{gray}[GPT]: {endc}{yellow}text completion requested{endc}")
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

    def send(self, msg):
        if msg != "": self.client.send_message(self.chatid, msg)
    def get_last_msg(self) -> str:
        msg = self.client.get_message(self.chatid)
        return msg
    
    def parse_last_msg(self):
        msg = self.get_last_msg()
        if msg["id"] != self.last_msg_id and msg["author"]["id"] != self.user_IDs["FriggBot2000"]:
            try:
                author = self.user_IDs[msg["author"]["global_name"]]
            except KeyError:
                print(f"{bold}{gray}[FRIG]: {endc}{yellow}new username '{msg['author']['global_name']}' detected. storing their ID. {endc}")
                self.user_IDs[msg["author"]["global_name"]] = msg["author"]["id"]
                with open(f"{self.configDir}userIDs.json", "w") as f:
                    f.write(json.dumps(self.user_IDs, indent=4))
            
            self.last_msg_id = msg["id"]
            return self.parse(msg)
        return ""

    def parse(self, msg):
        body = msg["content"].lstrip()
        if body.startswith("!"):
            try:
                command = body.split(" ")[0]
                print(f"{bold}{gray}[FRIG]: {endc}{yellow} command found: {command}{endc}")
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


class lolManager:
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
            print(f"{gray}{bold}[LOL]:{endc} {yellow}requested summonerID for new name:' {summonerName}'{endc}")
            url = f"https://{region}.api.riotgames.com/lol/summoner/v4/summoners/by-name/{summonerName}?api_key={self.riotkey}"
            get = requests.get(url)
            if get.status_code == 200:
                self.summonerIDs[str(summonerName)] = get.json()["id"]
                print(f"{gray}{bold}[LOL]:{endc} {yellow}stored new summonerID for '{summonerName}'{endc}")
                self.store_player_ids()
                return self.summonerIDs[str(summonerName)]
            else:
                print(f"{gray}{bold}[LOL]:{endc} {red}new summonerID for '{summonerName}' could not be located{endc}")
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
            print(f"{gray}{bold}[LOL]:{endc} {green}ranked info acquired for '{summonerName}'{endc}")
            return report
        print(f"{gray}{bold}[LOL]: {endc}{red}get request got: {get} for name '{summonerName}'{endc}")
        return "https://tenor.com/view/snoop-dog-who-what-gif-14541222"
    
    def parse_ranked_info(self, info, name):
        if info == []:
            if name.lower() == "dragondude": "@ASlowFatHorsey play ranked bitch"
            return f"{name} is not on the ranked grind"
        try:
            summinfo = info[0]
            name = summinfo["summonerName"]
            lp = summinfo["leaguePoints"]
            wins = int(summinfo["wins"])
            losses = int(summinfo["losses"])
            winrate = wins/(wins+losses)
            if len(info) > 1:
                rankedinfo = info[1]
                tier = rankedinfo["tier"].lower().capitalize()
                div = rankedinfo["rank"]
                rankrep = f"in {tier} {div} at {lp} lp"
            else:
                div = "unranked"
                tier = "unranked"
                rankrep = f"unranked at {lp} lp"

            rep = f"{name} is {rankrep} with a {winrate:.3f} wr over {wins+losses} games"
            return rep
        except ValueError: print(info); return f"got ranked info:\n'{info}',\n but failed to parse. (spam @eekay)"
    