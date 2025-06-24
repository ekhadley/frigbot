import json
import requests
from utils import gray, bold, endc, yellow, blue, green, red
from utils import loadjson

class lolManager: # this handles requests to the riot api
    def __init__(self, riotkey, savePath):
        self.savePath = savePath
        self.riotkey = riotkey
        self.summonerIDs = loadjson(savePath)

        """
        puuids = {}
        for name, sumid in self.summonerIDs.items():
            url = f"https://americas.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{name}/NA1?api_key=RGAPI-825a3730-5b92-4667-b7e9-992d43bb0658"
            get = requests.get(url)
            if get.status_code == 200:
                raw_info = get.json(parse_float=float, parse_int=int)
                puuid = raw_info["puuid"]
                puuids[name] = puuid
                print(f"puuid for {name}#NA1 found: '{puuid}'")
            else:
                print(f"no puuid found for {name}")

        with open("/home/ek/wgmn/frigbot/config/puuids.json", "w+") as f:
            f.write(json.dumps(puuids, indent=4))
        """

    def load_player_ids(self):
        with open(self.savePath, 'r') as f:
            return json.load(f)
    
    def store_player_ids(self):
        with open(self.savePath, "w") as f:
            f.write(json.dumps(self.summonerIDs, indent=4))

    def get_ranked_info(self, sum_name, region=None):
        region = "na1" if region is None else region
        puuid = self.summonerIDs[sum_name]
        url = f"https://{region}.api.riotgames.com/lol/league/v4/entries/by-puuid/{puuid}?api_key={self.riotkey}"
        get = requests.get(url)
        if get.status_code == 200:
            print(f"{gray}{bold}[LOL]: {endc}{green}ranked info acquired for '{sum_name}'{endc}")
            raw_info = get.json(parse_float=float, parse_int=int)
            full_info = {}
            for specific_queue_info in raw_info:
                full_info[specific_queue_info["queueType"]] = specific_queue_info
            return full_info
        elif get.status_code == 403:
            print(f"{gray}{bold}[LOL]: {endc}{red}got 403 for name '{sum_name}'. key is probably expired. {endc}")
            return f"got 403 for name '{sum_name}'. key is probably expired. blame riot request url:\n{url}"
        else:
            print(f"{gray}{bold}[LOL]: {endc}{red}attempted ID for '{sum_name}' got: {get}. request url:\n{url}'{endc}")
            return "https://tenor.com/view/snoop-dog-who-what-gif-14541222"

    #ugh:
    # https://developer.riotgames.com/apis#summoner-v4/GET_getBySummonerId to get the puuid from the encrypted summoner id (which is whats stored by frig)
    # https://developer.riotgames.com/apis#match-v5/GET_getMatchIdsByPUUID to get the match ids of whatever games from the summoner's puuid
    # https://developer.riotgames.com/apis#match-v5/GET_getMatch to get info about the game from the id from the match id
    def match_history(self, summonerName, region=None):
        region = "americas" if region is None else region
        #summonerID = self.get_summoner_id(summonerName, region)
        url = f"https://{region}.api.riotgames.com/lol/match/v5/matches/NA1_5004846015?api_key={self.riotkey}"
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
