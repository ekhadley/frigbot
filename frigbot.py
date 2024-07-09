from utils import *

class Frig:
    def __init__(self, keypath, configDir, chatid):
        self.last_msg_id = 0 # unique message id. Used to check if a new message has been already seen
        self.loop_delay = 1.0 # delay in seconds between checking for new mesages
        self.chatid = chatid
        self.keypath = keypath
        self.configDir = configDir
        self.read_saved_state(configDir)
        
        self.client = zenon.Client(self.keys["discord"])

        self.openai_client = openai.OpenAI(api_key = self.keys['openai'])
        self.ant_client = anthropic.Anthropic(api_key=self.keys['anthropic'])

        self.lol = lolManager(self.keys["riot"], f"{self.configDir}/summonerIDs.json")
        
        self.trackedChannels = []
        self.addNewTrackedChannel("femboy fishing", "UCqq5t2vi_G753e19j6U-Ypg", "femboyFishing.json")
        self.addNewTrackedChannel("femboy physics", "UCTE3WPc1oFdNYT8SnZCQW5w", "femboyPhysics.json")
        
        self.commands = {"!help":self.help_resp, # a dict of associations between commands (prefaced with a '!') and the functions they call to generate responses.
                         "!commands":self.help_resp,
                         "!cmds":self.help_resp,
                         "!gpt":self.gpt_resp,
                         "!sonnet":self.sonnet_resp,
                         "!arcane":self.arcane_resp,
                         "!rps":self.rps_resp,
                         "!fish":self.trackedChannels[0].forceCheckAndReport,
                         "!ttfish":self.trackedChannels[0].ttcheck,
                         "!physics":self.trackedChannels[1].forceCheckAndReport,
                         "!ttphysics":self.trackedChannels[1].ttcheck,
                         "!gif":self.random_gif_resp,
                         "!lp":self.lp_resp,
                         "!piggies":self.group_lp_resp,
                         "!registeredsexoffenders":self.lol.list_known_summoners,
                         "!dalle":self.dalle_vivid_resp,
                         "!dallen":self.dalle_natural_resp}

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

    def read_saved_state(self, dirname):
        self.user_IDs = loadjson(self.configDir, "userIDs.json")
        self.rps_scores = loadjson(self.configDir, "rpsScores.json")
        self.keys = loadjson(self.keypath)
        self.botname = self.user_IDs["FriggBot2000"]

    def arcane_resp(self, msg):
        delta = datetime.datetime(2024,11,20, 21, 5, 0) - datetime.datetime.now()
        years, days, hours, minutes, seconds = delta.days//365, delta.days, delta.seconds//3600, (delta.seconds%3600)//60, delta.seconds%60
        if years < 1: return f"arcane s2 comes out in approximately {days} days, {hours} hours, {minutes} minutes, and {seconds} seconds. hang in there."
        return f"arcane s2 comes out in approximately 1 year, {days-365} days, {hours} hours, {minutes} minutes, and {seconds} seconds. hang in there."

    def arcane_reference_resp(self, query="arcane", num=500):
        phrases = ["holy shit was that an arcane reference", "literal chills", "my honest reaction to that information:", "me rn:", "this is just like arcane fr", ""]
        return [random.choice(phrases), self.randomgif(query, num)]
    def itysl_reference_resp(self, query="itysl", num=500):
        return self.randomgif(query, num)

    def gpt_resp(self, msg):
        print(f"{bold}{gray}[GPT]: {endc}{yellow}text completion requested{endc}")
        try:
            prompt = msg['content'].replace("!gpt", "").strip()
            completion = self.openai_client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}])
            resp = completion.choices[0].message.content
            if len(resp) >= 2000:
                nsplit = math.ceil(len(resp)/2000)
                interval = len(resp)//nsplit
                resp = [resp[i*interval:(i+1)*interval] for i in range(nsplit)]
            print(f"{bold}{gray}[GPT]: {endc}{green}text completion generated {endc}")
            return resp
        except Exception as e:
            print(f"{bold}{gray}[GPT]: {endc}{red}text completion failed with exception:\n{e}{endc}")
            return "https://tenor.com/view/bkrafty-bkraftyerror-bafty-error-gif-25963379"

    def sonnet_resp(self, msg):
        print(f"{bold}{gray}[SONNET]: {endc}{yellow}text completion requested{endc}")
        try:
            prompt = msg['content'].replace("!sonnet", "").strip()
            completion = self.ant_client.messages.create(
                model="claude-3-5-sonnet-20240620",
                max_tokens=2000,
                temperature=0,
                system="You are a helpful and intelligent assistant.",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ]
            )
            resp = completion.content[0].text.replace("\n\n", "\n")
            if len(resp) >= 2000:
                nsplit = math.ceil(len(resp)/2000)
                interval = len(resp)//nsplit
                resp = [resp[i*interval:(i+1)*interval] for i in range(nsplit)]
            print(f"{bold}{gray}[SONNET]: {endc}{green}text completion generated {endc}")
            return resp
        except Exception as e:
            print(f"{bold}{gray}[SONNSET]: {endc}{red}text completion failed with exception:\n{e}{endc}")
            return "https://tenor.com/view/bkrafty-bkraftyerror-bafty-error-gif-25963379"

    def get_dalle3_link(self, msg, style='vivid', quality='hd'):
        print(f"{bold}{gray}[DALLE]: {endc}{yellow}image generation requested{endc}")
        try:
            prompt = msg['content'].replace("!dalle", "").strip()
            response = self.openai_client.images.generate(model="dall-e-3", prompt=prompt, size="1024x1024", quality=quality, n=1, style=style)
            print(f"{bold}{gray}[DALLE]: {endc}{green}image generated {endc}")
            return response.data[0].url
        except Exception as e:
            print(f"{bold}{gray}[DALLE]: {endc}{red}text completion failed with exception:\n{e}{endc}")
            if e.code == 'content_policy_violation':
                return "no porn!!!"
    def dalle_vivid_resp(self, msg): return self.get_dalle3_link(msg, style='vivid')
    def dalle_natural_resp(self, msg): return self.get_dalle3_link(msg, style='natural')

    def help_resp(self, msg):
        resp = f"commands:"
        for c in self.commands: resp += f"\n{c}"
        return resp

    def rps_resp(self, msg):
        rollname = msg["content"].replace("!rps", "").strip()
        authorid = msg["author"]["id"]
        if authorid+"w" not in self.rps_scores:
            print(f"{bold}{gray}[RPS]: {endc}{yellow}new RPS player found {endc}")
            self.rps_scores[authorid+"d"] = 0
            self.rps_scores[authorid+"w"] = 0
            self.rps_scores[authorid+"l"] = 0
        if rollname == "": return f"Your score is {self.rps_scores[authorid+'w']}/{self.rps_scores[authorid+'d']}/{self.rps_scores[authorid+'l']}"

        opts = ["rock", "paper", "scissors"]
        if rollname not in opts: return f"{rollname} is not an option. please choose one of {opts}"
        
        roll = opts.index(rollname)
        if authorid == self.user_IDs["Xylotile"]: botroll = random.choice([(roll+1)%3]*6 + [(roll+2)%3, roll])
        else: botroll = random.randint(0, 2)
        if roll == botroll: report = f"We both chose {opts[botroll]}"; self.rps_scores[authorid+"d"] += 1
        if (roll+2)%3 == botroll: report = f"I chose {opts[botroll]}. W"; self.rps_scores[authorid+"w"] += 1
        if (roll+1)%3 == botroll: report = f"I chose {opts[botroll]}. shitter"; self.rps_scores[authorid+"l"] += 1
        self.write_rps_scores()
        
        update = f"Your score is now {self.rps_scores[authorid+'w']}/{self.rps_scores[authorid+'d']}/{self.rps_scores[authorid+'l']}"
        return [report, update]

    def lp_resp(self, msg):
        name = msg["content"].replace("!lp", "").strip()
        info = self.lol.get_ranked_info(name)
        
        if info == []:
            if "dragondude" in name.lower(): return "ap is still a bitch (not on the ranked grind)"
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
        sumnames = ["eekay", "xylotile", "dragondude", "maestrofluff"]
        rev = {v:k for k, v in self.lol.summonerIDs.items()}
        tierOrder = {'IRON':0, 'BRONZE':1, 'SILVER':2, 'GOLD':3, 'PLATINUM':4, 'EMERALD':5, 'DIAMOND':6, 'MASTER':7, 'GRANDMASTER':8, 'CHALLENGER':9}
        rankColors = {'IRON':agray, 'BRONZE':ared, 'SILVER':awhite, 'GOLD':ayellow, 'PLATINUM':acyan, 'EMERALD':alime, 'DIAMOND':ablue, 'MASTER':red, 'GRANDMASTER':apink, 'CHALLENGER':apurple}
        rankOrder = {'IV':0, 'III':1, 'II':2, "I":3}

        infos = [self.lol.get_ranked_info(name) for name in sumnames]
        infos = [x[0] for x in infos if x != []]
        infos.sort(key = lambda x: tierOrder[x['tier']]*1000 + rankOrder[x['rank']]*100 + x['leaguePoints'], reverse=True)

        names = [f"{abold}{rev[info['summonerId']]}{aendc}" for info in infos]
        ranks = [f"{rankColors[info['tier']]}{info['tier'].lower().capitalize()} {info['rank']}{aendc} " for info in infos]
        winrates = [f"[{info['wins']/(info['wins'] + info['losses']):.3f} over {info['wins']+info['losses']} games]\n" for info in infos]

        namepad = max([len(name) for name in sumnames]) + 2
        rankpad = max([len(info['tier']+info['rank']) for info in infos])

        resp = "```ansi\n"
        for i, info in enumerate(infos):
            resp += names[i] + " "*(namepad-len(rev[info['summonerId']])) + ranks[i] + " "*(rankpad-len(info['tier']+info['rank'])) + f"{info['leaguePoints']} LP " + winrates[i]
            #resp +=  name + " "*(pad-len(name)) + f"{info['tier'].lower().capitalize()} {info['rank']} {info['leaguePoints']} LP. {info['wins']/(info['wins'] + info['losses']):.3f} over {info['wins']+info['losses']} games\n"
        resp += "```"
        return resp

    def send(self, msg): # sends a string or list of strings as a message/messages in the chat
        if isinstance(msg, list):
            for m in msg: self.send(m)
        elif isinstance(msg, str) and msg != "":
            self.client.send_message(self.chatid, msg)

    def get_last_msg(self): # reads the most recent message in the chat, returns a json
        try:
            msg = self.client.get_message(self.chatid)
            return msg
        except Exception as e:
            print(f"{bold}{gray}[FRIG]: {endc}{red}message read failed with exception:\n{e}{endc}")
            return None
    
    def get_self_msg(self): # determines what the bot needs to send at any given instance based on new messages and timed messages
        msg = self.get_last_msg()
        if msg["id"] != self.last_msg_id and msg["author"]["id"] != self.botname:
            try:
                author = self.user_IDs[msg["author"]["global_name"]]
            except KeyError:
                print(f"{bold}{gray}[FRIG]: {endc}{yellow}new username '{msg['author']['global_name']}' detected. storing their ID. {endc}")
                self.user_IDs[msg["author"]["global_name"]] = msg["author"]["id"]
                with open(f"{self.configDir}/userIDs.json", "w") as f:
                    f.write(json.dumps(self.user_IDs, indent=4))
            
            self.last_msg_id = msg["id"]
            return self.get_response_to_new_msg(msg)
        return self.get_timed_messages()

    def get_timed_messages(self): # checks for messages triggered by timing or external events
        reports = []
        for channel in self.trackedChannels:
            if channel.checkLatestUpload():
                reports.append(channel.reportVid()) # broken in the case where this loop should report multiple new videos. ugh.
        if len(reports) == 0: return "" 
        return reports

    def get_response_to_new_msg(self, msg): # determines how to respond to a newly detected message. 
        body = msg["content"].lstrip()
        if body.startswith("!"):
            try:
                command = body.split(" ")[0]
                print(f"{bold}{gray}[FRIG]: {endc}{yellow} command found: {command}{endc}")
                #self.client.typing_action(self.chatid, msg)
                return self.commands[command](msg)
            except Exception as e:
                print(f"{bold}{gray}[FRIG]: {endc}{red} command '{command}' failed with exception:\n{e}{endc}")
                return f"command '{command}' not recognized"
        else:
            return self.echo_resp(body)

    def echo_resp(self, body, reference_gif_prob=0.1): # determines which, if any, (non command) response to respond with. first checks phrases then other conditionals
        bsplit = body.split(" ")
        for e in self.echoes:
            if e in bsplit:
                print(f"{bold}{gray}[FRIG]: {endc}{gray} issuing echo for '{e}'{endc}")
                return self.echoes[e]
        gifs = []
        if random.uniform(0, 1) < reference_gif_prob:
            if contains_scrambled(body, "itysl"): gifs.append(self.itysl_reference_resp())
        if random.uniform(0, 1) < reference_gif_prob / 10:
            if contains_scrambled(body, "arcane"): gifs.append(self.arcane_reference_resp())
        if len(gifs) > 0: return gifs
        return ""

    def runloop(self):
        print(bold, cyan, "\nFrigBot started!", endc)
        while 1:
            try:
                resp = self.get_self_msg()
                self.send(resp)
                self.wait()
            except Exception as e:
                print(f"{red}, {bold}, [FRIG] CRASHED WITH EXCEPTION:\n{e}")
                time.sleep(3)

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

    def wait(self):
        time.sleep(self.loop_delay)


class lolManager: # this handles requests to the riot api
    def __init__(self, riotkey, savePath):
        self.savePath = savePath
        self.riotkey = riotkey
        self.summonerIDs = loadjson(savePath)
        #self.match_history('eekay')

    def load_player_ids(self):
        with open(self.savePath, 'r') as f:
            return json.load(f)
    
    def get_summoner_id(self, summonerName, region=None):
        try:
            return self.summonerIDs[str(summonerName)]
        except KeyError:
            print(f"{gray}{bold}[LOL]:{endc} {yellow}requested summonerID for new name: '{summonerName}'{endc}")
            url = f"https://{region}.api.riotgames.com/lol/summoner/v4/summoners/by-name/{summonerName}?api_key={self.riotkey}"
            get = requests.get(url)
            print(f"{blue+bold} getting summoner id for {summonerName}{endc}")
            if get.status_code == 200:
                self.summonerIDs[str(summonerName)] = get.json()["id"]
                print(f"{gray}{bold}[LOL]:{endc} {yellow}stored summonerID for new username: '{summonerName}'{endc}")
                self.store_player_ids()
                return self.summonerIDs[str(summonerName)]
            else:
                print(f"{gray}{bold}[LOL]:{endc} {red}summonerID for new username: '{summonerName}' could not be located{endc}")
                return None
    def store_player_ids(self):
        with open(self.savePath, "w") as f:
            f.write(json.dumps(self.summonerIDs, indent=4))

    def get_ranked_info(self, summonerName, region=None):
        region = "na1" if region is None else region
        summonerID = self.get_summoner_id(summonerName, region)
        url = f"https://{region}.api.riotgames.com/lol/league/v4/entries/by-summoner/{summonerID}?api_key={self.riotkey}"
        get = requests.get(url)
        if get.status_code == 200:
            print(f"{gray}{bold}[LOL]: {endc}{green}ranked info acquired for '{summonerName}'{endc}")
            return get.json(parse_float=float, parse_int=int)
        elif get.status_code == 403:
            print(f"{gray}{bold}[LOL]: {endc}{red}got 403 for name '{summonerName}'. key is probably expired. {endc}")
            return f"got 403 for name '{summonerName}'. key is probably expired. blame riot request url:\n{url}"
        else:
            print(f"{gray}{bold}[LOL]: {endc}{red}attempted ID for '{summonerName}' got: {get}. request url:\n{url}'{endc}")
            return "https://tenor.com/view/snoop-dog-who-what-gif-14541222"

    #ugh:
    # https://developer.riotgames.com/apis#summoner-v4/GET_getBySummonerId to get the puuid from the encrypted summoner id (which is whats stored by frig)
    # https://developer.riotgames.com/apis#match-v5/GET_getMatchIdsByPUUID to get the match ids of whatever games from the summoner's puuid
    # https://developer.riotgames.com/apis#match-v5/GET_getMatch to get info about the game from the id from the match id
    def match_history(self, summonerName, region=None):
        region = "americas" if region is None else region
        summonerID = self.get_summoner_id(summonerName, region)
        url = f"https://{region}.api.riotgames.com/lol/match/v5/matches/NA1_5004846015?api_key={self.riotkey}"
        print(bold, purple, url, endc)
        get = requests.get(url)
        
        with open('data.json', 'w', encoding='utf-8') as f:
            json.dump(get.json(), f, ensure_ascii=False, indent=4)
        
        if get.status_code == 200:
            print(f"{gray}{bold}[LOL]: {endc}{green}ranked info acquired for '{summonerName}'{endc}")
            print(get.json())
        elif get.status_code == 403:
            print(f"{gray}{bold}[LOL]: {endc}{red}got 403 for name '{summonerName}'. key is probably expired. {endc}")
            return f"got 403 for name '{summonerName}'. key is probably expired. blame riot"
        else:
            print(f"{gray}{bold}[LOL]: {endc}{red}attempted ID for '{summonerName}' got: {get}. request url:\n{url}'{endc}")
            return "https://tenor.com/view/snoop-dog-who-what-gif-14541222"


    def list_known_summoners(self, *args, **kwargs):
        return "".join([f"{k}\n" for k, v in self.summonerIDs.items()])

class ytChannelTracker:
    def __init__(self, name, ytkey, channelID, savePath, checkInterval=10800):
        self.channelName = name
        self.checkInterval = checkInterval
        self.savePath = savePath # where on disk do we keep most recent video ID (not rly a log, just the most recent)
        self.channelID = channelID # the channelid (not the visible one) of the channel we are monitoring
        self.mostRecentVidId, self.lastCheckTime = self.readSave() # read the most recent video ID and time of last api request
        self.yt = build('youtube', 'v3', developerKey=ytkey) # initialize our client

    def getLatestVidId(self): # uses ytv3 api to get the time and id of most recent video upload from channel
        print(f"{bold}{gray}[YT]: {endc}{yellow}checking latest video from channel: {self.channelName}{endc}")
        try:
            request = self.yt.channels().list(part='contentDetails', id=self.channelID)
            response = request.execute()
            playlist_id = response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
            
            playlist = self.yt.playlistItems().list(part='contentDetails', playlistId=playlist_id, maxResults=1)
            plresp = playlist.execute()
            videoId = plresp['items'][0]['contentDetails']['videoId'].strip()
            changed = self.mostRecentVidId != videoId
            self.mostRecentVidId = videoId
            print(f"{bold}{gray}[YT]: {endc}{green} successfully retreived id of latest video from channel: {self.channelName} {endc}")
            return changed, videoId, True
        except Exception as e:
            print(f"{bold}{gray}[YT]: {endc}{red}upload retreival for channel: '{self.channelName}' failed with exception:\n{e}{endc}")
            return None, None, False

    def checkLatestUpload(self): # limits rate of checks, returns wether a new vid has been found, updates saved state
        if self.shouldCheck():
            changed, newest, succeeded = self.getLatestVidId()
            self.recordNewRead(videoId=newest)
            if not succeeded: return False
            return changed
        return False

    def reportVid(self): return f"new video from {self.channelName}:\nhttps://youtube.com/watch?v={self.mostRecentVidId}"
    def forceCheckAndReport(self, *args): # forces check, and just gives link
        changed, newest, _ = self.getLatestVidId()
        self.recordNewRead(videoId=newest)
        return f"https://youtube.com/watch?v={self.mostRecentVidId}"

    def readSave(self): # reads stored videoID of most recent 
        with open(self.savePath, 'r') as f:
            save = json.load(f)
            videoId, lastread = save["videoId"], self.str2dt(save["lastCheckTime"])
        return videoId, lastread
    def recordNewRead(self, videoId=None): # writes the current most recent upload to disk
        self.lastCheckTime = datetime.datetime.now()
        try:
            with open(self.savePath, "r") as f:
                saved = json.load(f)
            saved["lastCheckTime"] = self.now()
            if videoId is not None: saved["videoId"] = videoId
            with open(self.savePath, "w") as f:
                f.write(json.dumps(saved, indent=4))
        except Exception as e:
            print(f"{red} recordNewRead for channel: '{self.channelName}' failed with exception:\n{e}")

    def timeSinceCheck(self): # returns the amount of time since last 
        delta = datetime.datetime.now() - self.lastCheckTime
        sec = delta.days*24*60*60 + delta.seconds
        #print(f"{sec} sec since last check. check interval is {self.checkInterval} sec. checking in {self.checkInterval - sec}")
        return delta.days*24*60*60 + delta.seconds

    def shouldCheck(self): return self.timeSinceCheck() >= self.checkInterval
    def ttcheck(self, *args, **kwargs):
        delta = self.checkInterval - self.timeSinceCheck()
        hours, minutes, seconds = delta//3600, (delta%3600)//60, delta%60
        return f"checking in {hours}h, {minutes}m, {seconds}s seconds" 

    def now(self): return datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    def str2dt(self, dstr): return datetime.datetime.strptime(dstr, "%Y-%m-%dT%H:%M:%SZ")
