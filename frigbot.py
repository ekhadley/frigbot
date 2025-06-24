import random
import datetime
import base64
import time
import json
import requests
import openai
import pyicloud
import traceback
from typing import Literal

from lolManager import lolManager
from chat import ChatAssistant
from completions import CompletionManager

from utils import red, endc, yellow, bold, cyan, gray, green, aendc, rankColors, abold
from utils import loadjson, contains_scrambled

class Frig:
    def __init__(self, keypath, configDir, chat_id):
        self.last_msg_id = 0 # unique message id. Used to check if a new message has been already seen
        self.last_self_msg_id = 0
        self.loop_delay = 1.0 # delay in seconds between checking for new mesages
        self.chat_id = chat_id
        self.keypath = keypath
        self.configDir = configDir
        self.read_saved_state()

        self.start_time = datetime.datetime.now()

        self.bot_name = "FriggBot2000"
        self.id = "352226045228875786"
        
        self.url = "https://discordapp.com/api/v9"
        self.token = self.keys['discord']

        self.openai_client = openai.OpenAI()
        self.asst = ChatAssistant("chatgpt-4o-latest", self.id, self.bot_name)
        #self.asst = ChatAssistant("claude-sonnet-4-20250514", self.id, self.bot_name)

        self.lol = lolManager(self.keys["riot"], f"{self.configDir}/summonerPUUIDs.json")

        self.completer = CompletionManager(self.keys['runpod'])
        self.commands = {
            "!help":self.help_resp, # a dict of associations between commands (prefaced with a '!') and the functions they call to generate responses.
            "!commands":self.help_resp,
            "!cmds":self.help_resp,
            "!got":self.got_resp,
            "!img":self.gpt_img_resp,
            #"!gpt":self.gpt_resp,
            "!gpt":self.chat_resp,
            #"!gpts":self.gpt_search_resp,
            "!rps":self.rps_resp,
            "!gif":self.random_gif_resp,
            "!roll":self.roll_resp,
            "!lp":self.lp_resp,
            "!piggies":self.group_lp_resp,
            "!registeredsexoffenders":self.lol.list_known_summoners,
            "!coin": self.coinflip_resp,
            "!coinflip": self.coinflip_resp,
            "!sus": self.sus_resp,
            "!imposter": self.imposter_resp,
            "!uptime": self.uptime_resp,
            "!poem": self.poem_resp,
            #"!locate_xylotile": self.locate_xylotile_resp
        }

        self.echo_resps = [ # the static repsonse messages for trigger words which I term "echo" responses (deprecated, i just keep these here cuz its good pasta)
            "This computer is shared with others including parents. This is a parent speaking to you to now. Not sure what this group is up to. I have told my son that role playing d and d games are absolutely forbidden in out household. We do not mind him having online friendships with local people that he knows for legitimate purposes. Perhaps this is an innocent group. But, we expect transparency in our son's friendships and acquaintances. If you would like to identify yourself now and let me know what your purpose for this platform is this is fine. You are welcome to do so.",
        ]
        
    def send(self, msg, reply_msg_id = None, files=None): # sends a string/list of strings as a message/messages in the chat. optionally replies to a previous message.
        if isinstance(msg, list): return [self.send(m, reply_msg_id) for m in msg]
        elif msg is not None or files is not None:
            if reply_msg_id is None:
                post_data = { "content": str(msg) }
            else:
                post_data = { 'content': str(msg), 'message_reference': { 'message_id':reply_msg_id, 'channel_id':self.chat_id }}

            send_resp = requests.post(
                f"{self.url}/channels/{self.chat_id}/messages",
                json = post_data,
                headers = { "Authorization":self.token },
                files = files
            ).json()
            return send_resp
    def editMessage(self, message_id, new_content):
        resp = requests.patch(
            f"{self.url}/channels/{self.chat_id}/messages/{message_id}",
            data={"content": new_content},
            headers={"Authorization": self.token}
        )
        return resp
    def getLatestMessage(self, num_messages=1) -> dict|list[dict]:
        url = f"{self.url}/channels/{self.chat_id}/messages?limit={num_messages}"
        resp = requests.get(url, headers={"Authorization":self.token})
        if not resp.ok:
            print(f"{bold}{gray}[FRIG]: {endc}{red} message grab not successful: {resp}{endc}")
            return None
        data = resp.json()
        return data[0] if len(data) == 1 else data
    def getNewMessage(self):
        msg = self.getLatestMessage()
        if msg:
            msg_id, msg_author_id = msg["id"], msg["author"]["id"] 
            if msg_id != self.last_msg_id and msg_author_id != self.id:
                self.last_msg_id = msg_id
                return True, msg
        return False, msg
    def botTaggedInMessage(self, msg) -> bool:
        return f"<@{self.id}>" in msg["content"]
    def getResponseToNewMessage(self, msg):
        body = msg["content"].lstrip()
        if body.startswith("!"):
            command_name = body.split(" ")[0].strip()
            print(f"{bold}{gray}[FRIG]: {endc}{yellow} command found: {command_name}{endc}")
            if command_name in self.commands.keys():
                try:
                    return self.commands[command_name](msg)
                except Exception as e:
                    print(f"{bold}{gray}[FRIG]: {endc}{red} known command '{command_name}' failed")
                    traceback.print_exc()
                    print(endc)
                    return f"command '{command_name}' failed with exception:\n```ansi\n{e}\n```"
            else:
                print(f"{bold}{gray}[FRIG]: {endc}{red} unknown command '{command_name}' was called:\n{endc}")
                return f"command '{command_name}' not recognized"
        elif self.asst.requiresResponse(msg) or self.botTaggedInMessage(msg):
            print(f"{bold}{gray}[FRIG]: {endc}{yellow} chat completion requested via reply{endc}")
            return self.chat_resp(msg)
        elif random.random() > 0.9 and contains_scrambled(msg['content'], "itysl"):
            return self.itysl_reference_resp()
        return None

    def runloop(self):
        print(bold, cyan, "\nFrigBot started!", endc)
        while 1:
            try:
                is_new, msg = self.getNewMessage()
                if is_new:
                    resp = self.getResponseToNewMessage(msg)
                    self.send(resp)
                self.wait()
            except Exception as e:
                print(f"{red}, {bold}, [FRIG] crashed with exception:\n{e}")
                traceback.print_exc()
                time.sleep(3)

    def poem_resp(self, *args, **kwargs):
        return ["Do not go gentle into that good juckyard.", "Tetus should burn and rave at close of day.", "Rage, rage against the dying of the gamings.", "Though wise men at their end know gaming is right,", "Becuase their plays had got no karma they", "Do not go gentle into that good juckyard"]
    def coinflip_resp(self, *args, **kwargs):
        return random.choice(['heads', 'tails'])

    def read_saved_state(self):
        self.user_IDs = loadjson(self.configDir, "userIDs.json")
        self.rps_scores = loadjson(self.configDir, "rpsScores.json")
        self.keys = loadjson(self.keypath)

    def itysl_reference_resp(self, query="itysl", num=500):
        return self.randomgif(query, num)

    def sus_resp(self, msg, **kwargs):
        try:
            history_len = int(msg['content'].split(" ")[1])
        except Exception:
            history_len = 50
        print(f"{bold}{gray}[SUS]: {endc}{yellow}ai continuation requested{endc}")
        history_len = min(max(2, history_len), 100)
        chat_history = self.getLatestMessage(num_messages=history_len)
        chat_history = [msg for msg in chat_history if msg['author']['global_name'] != 'FriggBot2000' and "!sus" not in msg['content']]
        print(f"{bold}{gray}[SUS]: {endc}{yellow}chat history succesfully recorded{endc}")
        chat_ctx = self.completer.formatMessages(chat_history)
        print(f"completing on chat context: '{repr(chat_ctx)}'")
        print(f"{bold}{gray}[SUS]: {endc}{yellow}chat history formatted{endc}")
        completion = self.completer.getCompletion(chat_ctx)
        print(f"{bold}{gray}[SUS]: {endc}{green}continuation succesfully generated{endc}")
        return completion.split("\n")
    def imposter_resp(self, msg, **kwargs):
        try:
            imposter = msg['content'].split(" ")[1]
        except Exception:
            imposter = ""
        print(f"{bold}{gray}[SUS]: {endc}{yellow}ai continuation requested{endc}")
        chat_history = self.getLatestMessage(num_messages=25)
        chat_history = [msg for msg in chat_history if msg['author']['global_name'] != 'FriggBot2000' and "!imposter" not in msg['content'] and "!sus" not in msg['content']]
        print(f"{bold}{gray}[SUS]: {endc}{yellow}chat history succesfully recorded{endc}")
        chat_ctx = self.completer.formatMessages(chat_history, tail=f"{imposter}: ")
        print(f"completing on chat context: '{repr(chat_ctx)}'")
        print(f"{bold}{gray}[SUS]: {endc}{yellow}chat history formatted{endc}")
        completion = f"{imposter}: " + self.completer.getCompletion(chat_ctx)
        print(f"{bold}{gray}[SUS]: {endc}{green}continuation succesfully generated{endc}")
        return completion.split("\n")

    def chat_resp(self, msg):
        msg_id = msg.get("id")
        self.asst.addMessageFromChat(msg)

        print(f"{bold}{gray}[FRIG]: {endc}{yellow}chat completion requested. . .{endc}")
        completion = self.asst.getCompletion(msg_id)
        split_completion = completion.replace("\n\n", "\n").strip().split("<split>")

        resps = self.send(split_completion, reply_msg_id = msg_id)
        for comp, resp in zip(split_completion, resps):
            self.asst.addMessage("assistant", comp, resp["id"], msg_id)

    def gpt_img_resp(self, msg):
        prompt = msg['content'].replace("!img", "").strip()
        self.send(f"image gen started: '{prompt if len(prompt) < 15 else prompt[:15]+'...'}'")
        try:
            resp = self.openai_client.images.generate(
                    model="gpt-image-1",
                    prompt=prompt,
                    moderation="low",
                    quality="high",
                )
        except Exception as e:
            if e.code == "moderation_blocked":
                return "no porn!!!"
            return f"error while generating: '{e.code}'"

        img_b64 = resp.data[0].b64_json
        img_bytes = base64.b64decode(img_b64)
        self.send("", files={"file": ("output.png", img_bytes)})

    def help_resp(self, msg):
        command_descriptions = {
            "!help": "Displays this help message.",
            "!commands": "Alias for !help.",
            "!cmds": "Alias for !help.",
            "!gpt": "Generates a response using GPT-4o.",
            "!img": "Generates an image using gpt-image-1.",
            "!rps": "Play rock-paper-scissors with the bot. Usage: `!rps [rock|paper|scissors]`.",
            "!gif": "Searches for a random GIF. Usage: `!gif [search term]`.",
            "!roll": "Rolls a random number. Usage: `!roll [max value]`.",
            "!lp": "Retrieves ranked info for a League of Legends summoner. Usage: `!lp [summoner name]`.",
            "!piggies": "Displays ranked info for a group of predefined League of Legends players.",
            "!registeredsexoffenders": "Lists all known League of Legends summoners in Frig's database.",
            "!coin": "Flips a coin.",
            "!coinflip": "Alias for !coin.",
            "!sus": "based on the last ~100 messages, generate an ai continuation of the conversation",
            "!uptime": "Shows how long Frig has been live without stopping."
        }
        resp = "Available commands:"
        for cmd, desc in command_descriptions.items():
            resp += f"\n\t{cmd} - {desc}"
        
        return resp

    def rps_resp(self, msg):
        rollname = msg["content"].replace("!rps", "").strip()
        authorid = msg["author"]["id"]
        if authorid+"w" not in self.rps_scores:
            print(f"{bold}{gray}[RPS]: {endc}{yellow}new RPS player found {endc}")
            self.rps_scores[authorid+"d"] = 0
            self.rps_scores[authorid+"w"] = 0
            self.rps_scores[authorid+"l"] = 0
        if rollname == "":
            return f"Your score is {self.rps_scores[authorid+'w']}/{self.rps_scores[authorid+'d']}/{self.rps_scores[authorid+'l']}"

        opts = ["rock", "paper", "scissors"]
        if rollname not in opts:
            return f"{rollname} is not an option. please choose one of {opts}"
        
        roll = opts.index(rollname)
        if authorid == self.user_IDs["Xylotile"]:
            botroll = random.choice([(roll+1)%3]*6 + [(roll+2)%3, roll])
        else:
            botroll = random.randint(0, 2)
        if roll == botroll:
            report = f"We both chose {opts[botroll]}"
            self.rps_scores[authorid+"d"] += 1
        if (roll+2)%3 == botroll:
            report = f"I chose {opts[botroll]}. W"
            self.rps_scores[authorid+"w"] += 1
        if (roll+1)%3 == botroll:
            report = f"I chose {opts[botroll]}. shitter"
            self.rps_scores[authorid+"l"] += 1
        print(f"bot rolled: {botroll} ({opts[botroll]}), user rolled {roll} ({opts[roll]})")
        self.write_rps_scores()
        
        update = f"Your score is now {self.rps_scores[authorid+'w']}/{self.rps_scores[authorid+'d']}/{self.rps_scores[authorid+'l']}"
        return [report, update]

    def lp_resp(self, msg):
        name = msg["content"].replace("!lp", "").strip().lower()
        info = self.lol.get_ranked_info(name)
        if isinstance(info, str):
            return info
        
        if info == []:
            if "dragondude" in name.lower():
                return "ap is still a bitch (not on the ranked grind)"
            return f"{name} is not on the ranked grind"
        try:
            info = info[0]
            #name = info["summonerName"]
            lp = info["leaguePoints"]
            wins = int(info["wins"])
            losses = int(info["losses"])
            winrate = wins/(wins+losses)

            tier = info["tier"].lower().capitalize()
            div = info["rank"]
            rankrep = f"in {tier} {div} at {lp} lp"

            rep = f"{name} is {rankrep} with a {winrate:.3f} wr over {wins+losses} games"
            return rep
        
        except ValueError:
            print(info)
            return f"got ranked info:\n'{info}',\n but failed to parse. (spam @eekay)"

    def group_lp_resp(self, *args, **kwargs):
        sumnames = ["eekay", "xylotile", "dragondude", "maestrofluff", "smolyoshi"]
        rev = {v:k for k, v in self.lol.summonerIDs.items()}
        tierOrder = {'IRON':0, 'BRONZE':1, 'SILVER':2, 'GOLD':3, 'PLATINUM':4, 'EMERALD':5, 'DIAMOND':6, 'MASTER':7, 'GRANDMASTER':8, 'CHALLENGER':9}
        rankOrder = {'IV':0, 'III':1, 'II':2, "I":3}

        full_infos = [self.lol.get_ranked_info(name) for name in sumnames]
        infos = [info["RANKED_SOLO_5x5"] for info in full_infos if len(info) > 0  and "RANKED_SOLO_5x5" in info]
        infos.sort(key = lambda x: tierOrder[x['tier']]*1000 + rankOrder[x['rank']]*100 + x['leaguePoints'], reverse=True)

        names = [f"{abold}{rev[info['puuid']]}{aendc}" for info in infos]
        ranks = [f"{rankColors[info['tier']]}{info['tier'].lower().capitalize()} {info['rank']}{aendc} " for info in infos]
        winrates = [f"[{info['wins']/(info['wins'] + info['losses']):.3f} over {info['wins']+info['losses']} games]" for info in infos]

        namepad = max([len(name) for name in sumnames]) + 2
        rankpad = max([len(info['tier']+info['rank']) for info in infos]) if len(infos) > 0 else 10

        resp = "```ansi\n"
        for i, info in enumerate(infos):
            resp += names[i] + " "*(namepad-len(rev[info['puuid']])) + ranks[i] + " "*(rankpad-len(info['tier']+info['rank'])) + f"{info['leaguePoints']} LP " + winrates[i]
            if 'xylotile' in names[i]:
                resp += " (0/1 vs ap)"
            elif 'dragondude' in names[i]:
                resp += " (1/0 vs xylotile)"
            resp += "\n"
        resp += "```"
        return resp

    def write_rps_scores(self):
        with open(f"{self.configDir}/rpsScores.json", "w") as f:
            f.write(json.dumps(self.rps_scores, indent=4))

    def got_resp(self, *args, **kwargs):
        return "https://tenor.com/view/sosig-gif-9357588"
    def gifsearch(self, query, num):
        url = f"https://g.tenor.com/v2/search?q={query}&key={self.keys['tenor']}&limit={num}"
        r = requests.get(url)
        gets = json.loads(r.content)["results"]
        urls = [g["url"] for g in gets]
        return urls
    def randomgif(self, query, num):
        return random.choice(self.gifsearch(query, num))
    def random_gif_resp(self, msg, num=100):
        query = msg['content'].replace("!gif", "").strip()
        return self.randomgif(query, num)
    def roll_resp(self, msg):
        try:
            m = int(msg['content'].replace("!roll", "").strip())
            assert m > 0
            return str(random.randint(1, m))
        except Exception:
            return "choose an int > 0"

    def locate_xylotile_resp(self, *args, **kwargs):
        icloud = pyicloud.PyiCloudService("william.carrillo0415@icloud.com", self.keys['xylotile_icloud'])
        phone = icloud.iphone
        location = phone.location()
        link = f"https://maps.google.com/?q={location['latitude']},{location['longitude']}"
        return ["Xylotile is currently here:", link]
    
    def uptime_resp(self, *args, **kwargs):
        delta = datetime.datetime.now() - self.start_time
        return f"uptime: {delta.days}d {delta.seconds // 3600}h {(delta.seconds % 3600) // 60}m {delta.seconds % 60}s"

    def wait(self):
        time.sleep(self.loop_delay)
