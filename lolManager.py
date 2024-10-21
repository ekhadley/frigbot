from utils import *

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