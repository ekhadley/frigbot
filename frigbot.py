import random
import datetime
import base64
import time
import json
import requests
import traceback

from lolManager import lolManager
from chat import ChatAssistant

from utils import red, endc, yellow, bold, cyan, gray, green, aendc, rankColors, abold
from utils import contains_scrambled

class Frig:
    def __init__(
        self,
        keys_path: str,
        chat_id: str,
        state_dict_path: str|None = None,
    ):
        self.last_msg_id = 0 # unique message id. Used to check if a new message has been already seen
        self.loop_delay = 2.0 # delay in seconds between checking for new mesages
        self.chat_id = chat_id

        self.keys_path = keys_path
        with open(keys_path) as f:
            self.keys = json.load(f)

        self.start_time = datetime.datetime.now()
        self.state_dict_path = state_dict_path

        self.bot_name = "FriggBot2000"
        self.id = "352226045228875786"
        self.url = "https://discordapp.com/api/v9"
        self.token = self.keys['discord']

        self.current_chat_model = "openai/gpt-5"
        self.current_image_model = "openai/gpt-image-1"
        self.asst = ChatAssistant(self.current_chat_model, self.current_image_model, self.id, self.bot_name, self.keys['openrouter'])
        #self.asst = ChatAssistant("anthropic/claude-opus-4.1", self.id, self.bot_name)
        #self.asst = ChatAssistant("x-ai/grok-4", self.id, self.bot_name)
        #self.asst = ChatAssistant("google/gemini-2.5-pro", self.id, self.bot_name, self.keys['openrouter'])

        self.lol = lolManager(self.keys["riot"], "summonerPUUIDs.json")

        self.commands = {
            "!help":self.help_resp, # a dict of associations between commands (prefaced with a '!') and the functions they call to generate responses.
            "!commands":self.help_resp,
            "!cmds":self.help_resp,
            "!got":self.got_resp,
            "!setmodel":self.set_chat_model,
            "!setimgmodel":self.set_image_model,
            "!img":self.img_resp,
            "!gpt_img":self.gpt_img_resp,
            "!rps":self.rps_resp,
            "!gif":self.random_gif_resp,
            "!roll":self.roll_resp,
            "!lp":self.lp_resp,
            "!piggies":self.group_lp_resp,
            "!registeredsexoffenders":self.lol.list_known_summoners,
            "!coin": self.coinflip_resp,
            "!uptime": self.uptime_resp,
            "!poem": self.poem_resp,
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

    def itysl_reference_resp(self, query="itysl", num=500):
        return self.randomgif(query, num)

    def set_chat_model(self, msg: str):
        msg_content = msg['content'] if isinstance(msg, dict) else msg
        model_name = msg_content.replace("!setmodel", "").strip()
        if self.asst.setChatModel(model_name):
            self.current_chat_model = model_name
            print(f"{bold}{gray}[FRIG]: {endc}{yellow}chat model set to '{model_name}'{endc}")
            self.save_state()
            return f"chat model set to {model_name}"
        else:
            print(f"{bold}{gray}[FRIG]: {endc}{red}no match found for chat model '{model_name}' {endc}")
            return f"no model found for {model_name} [Available chat models](<{self.asst.available_chat_models_link}>)"
    def set_image_model(self, msg: str):
        msg_content = msg['content'] if isinstance(msg, dict) else msg
        model_name = msg_content.replace("!setimgmodel", "").strip()
        if model_name == "openai/gpt-image-1" or self.asst.setImageModel(model_name):
            self.current_image_model = model_name
            print(f"{bold}{gray}[FRIG]: {endc}{yellow}image model set to '{model_name}'{endc}")
            self.save_state()
            return f"image model set to {model_name}"
        else:
            print(f"{bold}{gray}[FRIG]: {endc}{red}no match found for image model '{model_name}' {endc}")
            return f"no image-capable model found for {model_name} [Available image models](<{self.asst.available_image_models_link}>)"

    def chat_resp(self, msg):
        msg_id = msg.get("id")
        self.asst.addMessageFromChat(msg)

        print(f"{bold}{gray}[FRIG]: {endc}{yellow}chat completion requested. . .{endc}")
        completion = self.asst.getCompletion(msg_id)
        split_completion = completion.replace("\n\n", "\n").strip().split("<split>")

        resps = self.send(split_completion, reply_msg_id = msg_id)
        for comp, resp in zip(split_completion, resps):
            self.asst.addMessage("assistant", comp, resp["id"], msg_id)
    def img_resp(self, msg):
        prompt = msg['content'].replace("!img", "").strip()
        if self.current_image_model == "gpt-image-1":
            self.gpt_img_resp(msg)
        else:
            resp = self.asst.getImageGenResp(prompt)
            message = resp["choices"][0]["message"]
            self.send(message['content'])
            if "images" in message:
                for img in message["images"]:
                    img_b64 = img["image_url"]["url"].split(",")[1]
                    img_bytes = base64.b64decode(img_b64)
                    self.send("", files={"file": ("output.png", img_bytes)})

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
            "!img": "Generates an image.",
            "!gpt_img": "Generates an image using gpt-image-1.",
            "!setmodel": "Sets the chat model. Usage: `!setmodel provider/model_name`. [Available chat models](<{self.asst.available_chat_models_link}>)",
            "!setimgmodel": "Sets the image model. Usage: `!setimgmodel provider/model_name`. [Available image models](<{self.asst.available_image_models_link}>)",
            "!rps": "Play rock-paper-scissors with the bot. Usage: `!rps [rock|paper|scissors]`.",
            "!gif": "Searches for a random GIF. Usage: `!gif [search term]`.",
            "!roll": "Rolls a random number. Usage: `!roll [max value]`.",
            "!lp": "Retrieves ranked info for a League of Legends summoner. Usage: `!lp [summoner name]`.",
            "!piggies": "Displays ranked info for the whole chat.",
            "!registeredsexoffenders": "Lists all known League of Legends summoners in Frig's database.",
            "!coin": "Flips a coin.",
            "!uptime": "Shows how long Frig has been live without stopping."
        }
        resp = "Available commands:"
        for cmd, desc in command_descriptions.items():
            resp += f"\n\t{cmd} - {desc}"
        
        return resp

    def rps_resp(self, msg):
        rollname = msg["content"].replace("!rps", "").strip()
        authorid = msg["author"]["id"]

        win_key, draw_key, loss_key = f"{authorid}_w", f"{authorid}_d", f"{authorid}_l"

        if win_key not in self.rps_scores:
            print(f"{bold}{gray}[RPS]: {endc}{yellow}new RPS player found {endc}")
            self.rps_scores[draw_key] = 0
            self.rps_scores[win_key] = 0
            self.rps_scores[loss_key] = 0
        if rollname == "":
            return f"Your score is {self.rps_scores[win_key]}/{self.rps_scores[draw_key]}/{self.rps_scores[loss_key]}"

        opts = ["rock", "paper", "scissors"]
        if rollname not in opts:
            return f"{rollname} is not an option. please choose one of {opts}"
        
        roll = opts.index(rollname)
        botroll = random.randint(0, 2)
        if roll == botroll:
            report = f"We both chose {opts[botroll]}"
            self.rps_scores[draw_key] += 1
        if (roll+2)%3 == botroll:
            report = f"I chose {opts[botroll]}. W"
            self.rps_scores[win_key] += 1
        if (roll+1)%3 == botroll:
            report = f"I chose {opts[botroll]}. shitter"
            self.rps_scores[loss_key] += 1
        print(f"bot rolled: {botroll} ({opts[botroll]}), user rolled {roll} ({opts[roll]})")
        
        self.save_state()
        
        update = f"Your score is now {self.rps_scores[win_key]}/{self.rps_scores[draw_key]}/{self.rps_scores[loss_key]}"
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
            info = info['RANKED_FLEX_SR']
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
        rev = {v:k for k, v in self.lol.summoner_puuids.items()}
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
            resp += "\n"
        resp += "```"
        return resp

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

    def uptime_resp(self, *args, **kwargs):
        delta = datetime.datetime.now() - self.start_time
        return f"uptime: {delta.days}d {delta.seconds // 3600}h {(delta.seconds % 3600) // 60}m {delta.seconds % 60}s"

    def wait(self):
        time.sleep(self.loop_delay)

    def state_dict(self): 
        return {
            "keys_path": self.keys_path,
            "chat_id": self.chat_id,
            "current_chat_model": self.current_chat_model,
            "current_image_model": self.current_image_model,
            "rps_scores": self.rps_scores,
            "start_time": self.start_time.isoformat(),
            "save_time": datetime.datetime.now().isoformat(),
        }
    def save_state(self):
        with open("state.json", "w") as f:
            f.write(json.dumps(self.state_dict(), indent=2))
    
    @staticmethod
    def load_from_state_dict(
            path: str,
            keys_path: str|None = None,
            chat_id: str|None = None
        ):
        with open(path) as f:
            saved_state = json.load(f)
        frig = Frig(
            keys_path=keys_path if keys_path is not None else saved_state["keys_path"],
            chat_id=chat_id if chat_id is not None else saved_state["chat_id"],
            state_dict_path=path,
        )
        frig.rps_scores = saved_state["rps_scores"]
        frig.set_chat_model(saved_state["current_chat_model"])
        frig.set_image_model(saved_state["current_image_model"])
        print(f"{bold}{gray}[FRIG]: {endc}{yellow}loaded state dict from '{path}'{endc}")
        frig.save_state()
        return frig