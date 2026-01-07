import random
import datetime
import time
import json
import subprocess
import os
import requests
import logging

from lolManager import lolManager

from utils import red, endc, yellow, bold, cyan, gray, green, aendc, rankColors, abold
from utils import contains_scrambled

class Frig:
    def __init__(
        self,
        keys_path: str,
        chat_id: str,
        state_dict_path: str|None = None,
    ):
        self.logger = logging.getLogger('frigbot')
        self.last_msg_id = 0 # unique message id. Used to check if a new message has been already seen
        self.loop_delay = 2.0 # delay in seconds between checking for new mesages
        self.chat_id = chat_id

        self.max_message_length = 2_000

        self.keys_path = keys_path
        with open(keys_path) as f:
            self.keys = json.load(f)

        self.start_time = datetime.datetime.now()
        self.state_dict_path = state_dict_path

        self.id = "352226045228875786"
        self.url = "https://discordapp.com/api/v9"
        self.token = self.keys['discord']

        self.frigbot_dir = "/home/ek/wgmn/frigbot"
        self.system_prompt_path = f"{self.frigbot_dir}/frig_system_prompt.md"

        self.rps_scores = {}
        self.lol = lolManager(self.keys["riot"], "/home/ek/wgmn/frigbot/data/summonerPUUIDs.json", self.log)
        self.commands = {  # a dict of associations between commands (prefaced with a '!') and the functions they call to generate responses.
            "!help":self.help_resp,
            "!commands":self.help_resp,
            "!cmds":self.help_resp,
            "!got":self.got_resp,
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
    
    def log(self, level: str, event_type: str, message: str, data: dict = None):
        if data is None:
            data = {}
        data['event_type'] = event_type
        extra = {'data': data}
        if level == 'info':
            self.logger.info(message, extra=extra)
        elif level == 'error':
            self.logger.error(message, extra=extra)
        elif level == 'warning':
            self.logger.warning(message, extra=extra)
        elif level == 'debug':
            self.logger.debug(message, extra=extra)
        
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

    def getMessage(self, channel_id, message_id):
        url = f"{self.url}/channels/{channel_id}/messages/{message_id}"
        resp = requests.get(url, headers={"Authorization": self.token})
        return resp.json() if resp.ok else None

    def getLatestMessage(self, num_messages=1) -> dict|list[dict]:
        url = f"{self.url}/channels/{self.chat_id}/messages?limit={num_messages}"
        resp = requests.get(url, headers={"Authorization":self.token})
        if not resp.ok:
            self.log('error', 'message_error', "Message grab not successful", {'response': str(resp)})
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

    def isReplyToBot(self, msg) -> bool:
        if msg.get("referenced_message") is None: return False
        return msg["referenced_message"]["author"]["id"] == self.id

    def getResponseToNewMessage(self, msg):
        body = msg["content"].lstrip()
        if body.startswith("!"):
            command_name = body.split(" ")[0].strip()
            self.log('info', 'command_found', "Command found", {'command': command_name})
            if command_name in self.commands.keys():
                try:
                    return self.commands[command_name](msg)
                except Exception as e:
                    self.log('error', 'command_failed', "Command failed", {'command': command_name})
                    self.logger.exception("Command exception details")
                    return f"command '{command_name}' failed with exception:\n```ansi\n{e}\n```"
            else:
                self.log('warning', 'command_unknown', "Unknown command called", {'command': command_name})
                return f"command '{command_name}' not recognized"
        elif self.isReplyToBot(msg) or self.botTaggedInMessage(msg):
            self.log('info', 'chat_requested', "Chat requested via reply/mention")
            self.invoke_claude(msg)
            return None  # Claude Code handles sending via MCP tools
        elif random.random() > 0.9 and contains_scrambled(msg['content'], "itysl"):
            return self.itysl_reference_resp()
        return None

    def invoke_claude(self, msg):
        """Spawn Claude Code to handle the message."""
        import traceback

        author = msg.get("author", {}).get("global_name", "unknown")
        content = msg.get("content", "")
        msg_id = msg.get("id")

        # Parse timestamp from Discord format (ISO 8601)
        timestamp_str = msg.get("timestamp", "")
        try:
            ts = datetime.datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            formatted_time = ts.strftime("%-m/%d/%y %-I:%M %p")
        except:
            formatted_time = ""

        # Replace @mentions with usernames
        for mention in msg.get("mentions", []):
            mention_id = mention.get("id")
            mention_name = mention.get("global_name") or mention.get("username", "unknown")
            content = content.replace(f"<@{mention_id}>", f"@{mention_name}")

        # Build the prompt from the trigger message
        prompt = f"[{formatted_time}] {author}: {content}"

        cmd = [
            "claude",
            "--print",
            "--output-format", "json",
            "--verbose",
            "--dangerously-skip-permissions",
            "--system-prompt", self.system_prompt_path,
            "--mcp-config", f"{self.frigbot_dir}/.claude/settings.json",
            "-p", prompt,
        ]

        env = {
            **os.environ,
            "FRIG_DISCORD_TOKEN": self.token,
            "FRIG_CHANNEL_ID": str(self.chat_id),
            "FRIG_TRIGGER_MESSAGE_ID": str(msg_id),
        }

        self.log('info', 'claude_invoked', "Spawning Claude Code", {
            'author': author,
            'message_id': msg_id,
            'prompt': prompt,
            'cmd': cmd,
            'cwd': self.frigbot_dir,
        })

        try:
            result = subprocess.run(
                cmd,
                env=env,
                cwd=self.frigbot_dir,
                capture_output=True,
                text=True,
                timeout=120,
            )
            # Parse JSON output for detailed tool logging
            tool_calls = []
            if result.stdout:
                try:
                    output = json.loads(result.stdout)
                    messages = output if isinstance(output, list) else output.get("messages", [])

                    for msg in messages:
                        if not isinstance(msg, dict):
                            continue
                        msg_type = msg.get("type", "")

                        if msg_type == "assistant":
                            content = msg.get("message", {}).get("content", [])
                            for block in content if isinstance(content, list) else [content]:
                                if isinstance(block, dict):
                                    if block.get("type") == "tool_use":
                                        tool_name = block.get('name')
                                        tool_input = block.get('input', {})
                                        tool_calls.append({'tool': tool_name, 'input': tool_input})
                                        self.log('info', 'claude_tool_use', f"Tool: {tool_name}", {
                                            'tool': tool_name,
                                            'input': tool_input,
                                        })
                                    elif block.get("type") == "text":
                                        text = block.get('text', '')
                                        if text.strip():
                                            self.log('debug', 'claude_text', "Claude text output", {'text': text[:500]})
                        elif msg_type == "tool_result":
                            content = str(msg.get('content', ''))[:500]
                            self.log('debug', 'claude_tool_result', "Tool result", {'content': content})
                        elif msg_type == "result":
                            result_text = str(msg.get('result', ''))[:500]
                            self.log('info', 'claude_result', "Final result", {'result': result_text})
                except json.JSONDecodeError:
                    self.log('warning', 'claude_output_parse_error', "Could not parse JSON output", {
                        'stdout': result.stdout[:1000]
                    })

            self.log('info', 'claude_completed', "Claude Code finished", {
                'return_code': result.returncode,
                'tool_calls': tool_calls,
                'stderr': result.stderr[:500] if result.stderr else None,
            })
            if result.returncode != 0:
                self.log('error', 'claude_error', "Claude Code non-zero exit", {
                    'return_code': result.returncode,
                    'stdout': result.stdout[:2000] if result.stdout else None,
                    'stderr': result.stderr[:2000] if result.stderr else None,
                })
        except subprocess.TimeoutExpired as e:
            self.log('error', 'claude_timeout', "Claude Code timed out", {
                'stdout': e.stdout[:2000] if e.stdout else None,
                'stderr': e.stderr[:2000] if e.stderr else None,
            })
        except Exception as e:
            self.log('error', 'claude_exception', "Claude Code exception", {
                'error': str(e),
                'error_type': type(e).__name__,
                'traceback': traceback.format_exc(),
            })

    def runloop(self):
        self.log('info', 'bot_started', "FrigBot started", {'chat_id': self.chat_id})
        while 1:
            try:
                is_new, msg = self.getNewMessage()
                if is_new:
                    msg_author = msg.get("author", {}).get("global_name", "unknown")
                    msg_content = msg.get("content", "")
                    self.log('info', 'new_message', "New message received", {'author': msg_author, 'content': msg_content})
                    resp = self.getResponseToNewMessage(msg)
                    self.send(resp)
                self.wait()
            except Exception as e:
                self.log('error', 'bot_crashed', "Main loop crashed")
                self.logger.exception("Bot crash exception details")
                time.sleep(3)

    def poem_resp(self, *args, **kwargs):
        return ["Do not go gentle into that good juckyard.", "Tetus should burn and rave at close of day.", "Rage, rage against the dying of the gamings.", "Though wise men at their end know gaming is right,", "Becuase their plays had got no karma they", "Do not go gentle into that good juckyard"]
    def coinflip_resp(self, *args, **kwargs):
        return random.choice(['heads', 'tails'])

    def itysl_reference_resp(self, query="itysl", num=500):
        return self.randomgif(query, num)

    def help_resp(self, msg):
        command_descriptions = {
            "!help": "Displays this help message.",
            "!commands": "Alias for !help.",
            "!cmds": "Alias for !help.",
            "!rps": "Play rock-paper-scissors with the bot. Usage: `!rps [rock|paper|scissors]`.",
            "!gif": "Searches for a random GIF. Usage: `!gif [search term]`.",
            "!roll": "Rolls a random number. Usage: `!roll [max value]`.",
            "!lp": "Retrieves ranked info for a League of Legends summoner. Usage: `!lp [summoner name]`.",
            "!piggies": "Displays ranked info for the whole chat.",
            "!registeredsexoffenders": "Lists all known League of Legends summoners in Frig's database.",
            "!coin": "Flips a coin.",
            "!uptime": "Shows how long Frig has been live without stopping."
        }
        resp = "Available commands:\n(@ or reply to frig for chat)"
        for cmd, desc in command_descriptions.items():
            resp += f"\n\t{cmd} - {desc}"

        return resp

    def rps_resp(self, msg):
        rollname = msg["content"].replace("!rps", "").strip()
        authorid = msg["author"]["id"]

        win_key, draw_key, loss_key = f"{authorid}_w", f"{authorid}_d", f"{authorid}_l"

        if win_key not in self.rps_scores:
            self.log('info', 'rps_new_player', "New RPS player", {'user_id': authorid})
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
        self.log('debug', 'rps_played', "RPS game played", {'user_id': authorid, 'user_choice': opts[roll], 'bot_choice': opts[botroll]})
        
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
            self.log('error', 'lol_parse_error', "Failed to parse ranked info", {'summoner': name, 'raw_info': str(info)})
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
            "rps_scores": self.rps_scores,
            "start_time": self.start_time.isoformat(),
            "save_time": datetime.datetime.now().isoformat(),
        }
    def save_state(self):
        self.log('debug', 'state_saved', "State saved", {'file': 'state.json'})
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
        frig.rps_scores = saved_state.get("rps_scores", {})
        frig.log('info', 'state_loaded', "State loaded", {'file': path})
        frig.save_state()
        return frig
