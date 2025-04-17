import math
import random
import datetime
import time
import json
import requests
import openai
import pyicloud

from ytTracker import ytChannelTracker
from lolManager import lolManager
from chat import ChatManager, OpenAIRunner

from utils import red, endc, yellow, bold, cyan, gray, green, aendc, rankColors, abold, purple
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
        
        self.url = "https://discordapp.com/api/v9"
        self.token = self.keys['discord']

        self.openai_client = openai.OpenAI(api_key = self.keys['openai'])
        #self.openai_runner = OpenAIRunner(model_name = "gpt-4o", tools = ["web_search_preview"], client=self.openai_client, text_output_callback=self.editLastMessage)
        self.openai_runner = OpenAIRunner(model_name = "chatgpt-4o-latest", tools = [], client=self.openai_client, text_output_callback=self.editLastMessage)

        self.lol = lolManager(self.keys["riot"], f"{self.configDir}/summonerIDs.json")

        self.chatter = ChatManager(self.keys['runpod'])

        self.trackedChannels = []
        self.addNewTrackedChannel("femboy fishing", "UCqq5t2vi_G753e19j6U-Ypg", "femboyFishing.json")
        self.addNewTrackedChannel("femboy physics", "UCTE3WPc1oFdNYT8SnZCQW5w", "femboyPhysics.json")

        self.commands = {
            "!help":self.help_resp, # a dict of associations between commands (prefaced with a '!') and the functions they call to generate responses.
            "!commands":self.help_resp,
            "!cmds":self.help_resp,
            "!gpt":self.gpt_resp,
            "!dune":self.dune_resp,
            "!rps":self.rps_resp,
            "!fish":self.trackedChannels[0].forceCheckAndReport,
            "!ttfish":self.trackedChannels[0].ttcheck,
            "!physics":self.trackedChannels[1].forceCheckAndReport,
            "!ttphysics":self.trackedChannels[1].ttcheck,
            "!gif":self.random_gif_resp,
            "!roll":self.roll_resp,
            "!lp":self.lp_resp,
            "!piggies":self.group_lp_resp,
            "!registeredsexoffenders":self.lol.list_known_summoners,
            "!dallen":self.dalle_natural_resp,
            "!dalle":self.dalle_vivid_resp,
            "!coin": self.coinflip_resp,
            "!coinflip": self.coinflip_resp,
            "!sus": self.sus_resp,
            "!imposter": self.imposter_resp,
            #"!locate_xylotile": self.locate_xylotile_resp
        }

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
        
    def send(self, msg): # sends a string/list of strings as a message/messages in the chat
        if isinstance(msg, list):
            for m in msg:
                self.send(m)
        elif isinstance(msg, str) and msg != "":
            send_resp = requests.post(
                f"{self.url}/channels/{self.chat_id}/messages",
                data={"content":str(msg)},
                headers={"Authorization":self.token}
            ).text
            resp_info = json.loads(send_resp)
            self.last_self_msg_id = resp_info['id']
    def editMessage(self, message_id, new_content):
        resp = requests.patch(
            f"{self.url}/channels/{self.chat_id}/messages/{message_id}",
            data={"content": new_content},
            headers={"Authorization": self.token}
        )
        return resp
    def editLastMessage(self, new_content): return self.editMessage(self.last_self_msg_id, new_content)
    def getLatestMsg(self, num_messages=1):
        url = f"{self.url}/channels/{self.chat_id}/messages?limit={num_messages}"
        res = requests.get(url, headers={"Authorization":self.token}).json()
        return res[0] if len(res) == 1 else res
    def getSelfMsg(self): # determines what the bot needs to send at any given moment based on new messages and timed messages
        try:
            msg = self.getLatestMsg()
        except Exception as e:
            print(f"{bold}{gray}[FRIG]: {endc}{red}message read failed with exception:\n{e}{endc}")
            return None
        msg_id, msg_author_id = msg["id"], msg["author"]["id"] 
        if msg_id != self.last_msg_id and msg_author_id != self.botname:
            author_global = msg["author"]["global_name"]
            if author_global not in self.user_IDs:
                print(f"{bold}{gray}[FRIG]: {endc}{yellow}new username '{msg['author']['global_name']}' detected. storing their ID. {endc}")
                self.user_IDs[msg["author"]["global_name"]] = msg_author_id
                with open(f"{self.configDir}/userIDs.json", "w") as f:
                    f.write(json.dumps(self.user_IDs, indent=4))
            
            self.last_msg_id = msg_id
            return self.getResponseToNewMsg(msg)
        return self.getTimedMessages()
    def getTimedMessages(self): # checks for messages triggered by timing or external events
        reports = []
        for channel in self.trackedChannels:
            if channel.checkLatestUpload():
                reports.append(channel.reportVid()) # broken in the case where this loop should report multiple new videos. ugh.
        if len(reports) == 0:
            return "" 
        return reports
    def getResponseToNewMsg(self, msg): # determines how to respond to a newly detected message. 
        body = msg["content"].lstrip()
        if body.startswith("!"):
            command_name = body.split(" ")[0]
            print(f"{bold}{gray}[FRIG]: {endc}{yellow} command found: {command_name}{endc}")
            if command_name in self.commands.keys():
                try:
                    return self.commands[command_name](msg)
                except Exception as e:
                    print(f"{bold}{gray}[FRIG]: {endc}{red} known command '{command_name}' failed with exception:\n{e}{endc}")
                    return f"command '{command_name}' failed with exception:\n```ansi\n{e}\n```"
            else:
                print(f"{bold}{gray}[FRIG]: {endc}{red} unknown command '{command_name}' was called:\n{e}{endc}")
                return f"command '{command_name}' not recognized"
        else:
            return self.echo_resp(body)
    def echo_resp(self, body, reference_gif_prob=0.1): # determines which, if any, (non command) response to respond with. first checks phrases then other conditionals
        bsplit = body.split(" ")
        for e in self.echoes:
            if e in bsplit:
                print(f"{bold}{gray}[FRIG]: {endc}{gray} issuing echo for '{e}'{endc}")
                return self.echoes[e]
        if (random.uniform(0, 1) < reference_gif_prob) and contains_scrambled(body, "itysl"):
                return self.itysl_reference_resp()
        return ""
    def runloop(self):
        print(bold, cyan, "\nFrigBot started!", endc)
        while 1:
            try:
                resp = self.getSelfMsg()
                self.send(resp)
                self.wait()
            except Exception as e:
                print(f"{red}, {bold}, [FRIG] CRASHED WITH EXCEPTION:\n{e}")
                time.sleep(3)


    def coinflip_resp(self, *args, **kwargs):
        return random.choice(['heads', 'tails'])

    def read_saved_state(self):
        self.user_IDs = loadjson(self.configDir, "userIDs.json")
        self.rps_scores = loadjson(self.configDir, "rpsScores.json")
        self.keys = loadjson(self.keypath)
        self.botname = self.user_IDs["FriggBot2000"]

    def dune_resp(self, msg):
        delta = datetime.datetime(2025, 12, 18, 20, 0, 0) - datetime.datetime.now()
        year, days, hours, minutes, seconds = delta.days//365, delta.days%365, delta.seconds//3600, (delta.seconds%3600)//60, delta.seconds%60
        print(delta.days, delta.days//365, year, year==1)
        if year == 1:
            return [self.randomgif("dune", 300), f"1 year, {days} days, {hours} hours, {minutes} minutes, and {seconds} seconds"]
        return [self.randomgif("dune", 300), f"{days} days, {hours} hours, {minutes} minutes, and {seconds} seconds."]

    def itysl_reference_resp(self, query="itysl", num=500):
        return self.randomgif(query, num)

    def sus_resp(self, msg, **kwargs):
        try:
            history_len = int(msg['content'].split(" ")[1])
        except Exception:
            history_len = 50
        print(f"{bold}{gray}[SUS]: {endc}{yellow}ai continuation requested{endc}")
        history_len = min(max(2, history_len), 100)
        chat_history = self.getLatestMsg(num_messages=history_len)
        chat_history = [msg for msg in chat_history if msg['author']['global_name'] != 'FriggBot2000' and "!sus" not in msg['content']]
        print(f"{bold}{gray}[SUS]: {endc}{yellow}chat history succesfully recorded{endc}")
        chat_ctx = self.chatter.formatMessages(chat_history)
        print(f"completing on chat context: '{repr(chat_ctx)}'")
        print(f"{bold}{gray}[SUS]: {endc}{yellow}chat history formatted{endc}")
        completion = self.chatter.getCompletion(chat_ctx)
        print(f"{bold}{gray}[SUS]: {endc}{green}continuation succesfully generated{endc}")
        return completion.split("\n")
    def imposter_resp(self, msg, **kwargs):
        try:
            imposter = msg['content'].split(" ")[1]
        except Exception:
            imposter = ""
        print(f"{bold}{gray}[SUS]: {endc}{yellow}ai continuation requested{endc}")
        chat_history = self.getLatestMsg(num_messages=25)
        chat_history = [msg for msg in chat_history if msg['author']['global_name'] != 'FriggBot2000' and "!imposter" not in msg['content'] and "!sus" not in msg['content']]
        print(f"{bold}{gray}[SUS]: {endc}{yellow}chat history succesfully recorded{endc}")
        chat_ctx = self.chatter.formatMessages(chat_history, tail=f"{imposter}: ")
        print(f"completing on chat context: '{repr(chat_ctx)}'")
        print(f"{bold}{gray}[SUS]: {endc}{yellow}chat history formatted{endc}")
        completion = f"{imposter}: " + self.chatter.getCompletion(chat_ctx)
        print(f"{bold}{gray}[SUS]: {endc}{green}continuation succesfully generated{endc}")
        return completion.split("\n")

    def openai_resp(self, model, msg):
         print(f"{bold}{gray}[{model}]: {endc}{yellow}text completion requested{endc}")
         prompt = msg['content'].replace("!gpt", "").strip()
         try:
             completion = self.openai_client.chat.completions.create(model=model, messages=[{"role": "user", "content": prompt}])
             resp = completion.choices[0].message.content.replace("\n\n", "\n")
             if len(resp) >= 2000:
                 nsplit = math.ceil(len(resp)/2000)
                 interval = len(resp)//nsplit
                 resp = [resp[i*interval:(i+1)*interval] for i in range(nsplit)]
             print(f"{bold}{gray}[{model}]: {endc}{green}text completion generated {endc}")
             return resp
         except Exception as e:
             print(f"{bold}{gray}[{model}]: {endc}{red}text completion failed with exception:\n{e}{endc}")
             return "https://tenor.com/view/bkrafty-bkraftyerror-bafty-error-gif-25963379"
    def gpt_resp(self, msg):
        self.send('. . .')
        return self.openai_resp("chatgpt-4o-latest", msg)

    def _gpt_resp(self, msg):
        self.send('. . .')
        input = msg['content'].replace("!gpt", "")
        self.openai_runner.addUserMessage(input)
        last_blocked = 0
        with self.openai_runner.getStream() as stream:
            for i, event in enumerate(stream):
                if event.type == "response.output_text.delta":
                    content = event.snapshot
                    if i%10 == 0:
                        self.editLastMessage(content)
        while not self.editLastMessage(content).ok:
            time.sleep(0.3)
        self.openai_runner.clearMessages()
        return ""


    def get_dalle3_link(self, msg, style='vivid', quality='hd'):
        print(f"{bold}{gray}[DALLE]: {endc}{yellow}image generation requested{endc}")
        self.send('. . .')
        try:
            prompt = msg['content'].replace("!dalle", "").strip()
            response = self.openai_client.images.generate(model="dall-e-3", prompt=prompt, size="1024x1024", quality=quality, n=1, style=style)
            print(f"{bold}{gray}[DALLE]: {endc}{green}image generated {endc}")
            #print(bold, purple, response.data[0].revised_prompt, endc)
            return response.data[0].url
        except Exception as e:
            print(f"{bold}{gray}[DALLE]: {endc}{red}text completion failed with exception:\n{e}{endc}")
            if e.code == 'content_policy_violation':
                return "no porn!!!"
    def dalle_vivid_resp(self, msg): return self.get_dalle3_link(msg, style='vivid')
    def dalle_natural_resp(self, msg): return self.get_dalle3_link(msg, style='natural')

    def help_resp(self, msg):
        command_descriptions = {
            "!help": "Displays this help message.",
            "!commands": "Alias for !help.",
            "!cmds": "Alias for !help.",
            "!gpt": "Generates a response using GPT-4o.",
            "!o1": "Generates a response using OpenAI's O1-preview model.",
            "!dune": "Shows countdown to Dune: Part Two release.",
            "!rps": "Play rock-paper-scissors with the bot. Usage: `!rps [rock|paper|scissors]`.",
            "!fish": "Checks for a new video from 'Femboy Fishing'.",
            "!ttfish": "Shows time remaining until the next check for 'Femboy Fishing'.",
            "!physics": "Checks for a new video from 'Femboy Physics'.",
            "!ttphysics": "Shows time remaining until the next check for 'Femboy Physics'.",
            "!gif": "Searches for a random GIF. Usage: `!gif [search term]`.",
            "!roll": "Rolls a random number. Usage: `!roll [max value]`.",
            "!lp": "Retrieves ranked info for a League of Legends summoner. Usage: `!lp [summoner name]`.",
            "!piggies": "Displays ranked info for a group of predefined League of Legends players.",
            "!registeredsexoffenders": "Lists all known League of Legends summoners in Frig's database.",
            "!dallen": "Generates an image using DALL-E in 'natural' style.",
            "!dalle": "Generates an image using DALL-E in 'vivid' style.",
            "!coin": "Flips a coin.",
            "!coinflip": "Alias for !coin.",
            "!sus": "based on the last ~100 messages, generate an ai continuation of the conversation"
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

        infos = [self.lol.get_ranked_info(name) for name in sumnames]
        infos = [x[0] for x in infos if x != []]
        infos.sort(key = lambda x: tierOrder[x['tier']]*1000 + rankOrder[x['rank']]*100 + x['leaguePoints'], reverse=True)

        names = [f"{abold}{rev[info['summonerId']]}{aendc}" for info in infos]
        ranks = [f"{rankColors[info['tier']]}{info['tier'].lower().capitalize()} {info['rank']}{aendc} " for info in infos]
        winrates = [f"[{info['wins']/(info['wins'] + info['losses']):.3f} over {info['wins']+info['losses']} games]" for info in infos]

        namepad = max([len(name) for name in sumnames]) + 2
        rankpad = max([len(info['tier']+info['rank']) for info in infos]) if len(infos) > 0 else 10

        resp = "```ansi\n"
        for i, info in enumerate(infos):
            resp += names[i] + " "*(namepad-len(rev[info['summonerId']])) + ranks[i] + " "*(rankpad-len(info['tier']+info['rank'])) + f"{info['leaguePoints']} LP " + winrates[i]
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
    
    def addNewTrackedChannel(self, channelName, channelID, saveFileName):
        fname = saveFileName if saveFileName.endswith(".json") else saveFileName+".json"
        tracker = ytChannelTracker(channelName, self.keys["youtube"], channelID, f"{self.configDir}/{fname}")
        self.trackedChannels.append(tracker)

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

    def wait(self):
        time.sleep(self.loop_delay)
