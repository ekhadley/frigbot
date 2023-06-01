import selenium, time, random, requests, openai, numpy as np
from bs4 import BeautifulSoup as bs4
from selenium.webdriver.common.keys import Keys
class bot:
    def __init__(self, driver):
        self.driver = driver
        self.lastSeen = msg()
        self.name = "FriggBot2000"
        self.online = self.getOnline()

        self.altGCName = "EK kissy kissy femboys mega fax no joke straight calculator no printer on a stack yo"
#        self.desiredGCName = u"\u2764 \u1F48 \u1F46 EK kissy kissy femboys mega fax no joke straight calculator no printer on a stack yo"
        self.desiredGCName = "👨❤💋👨 EK kissy kissy femboys mega fax no joke straight calculator no printer on a stack yo"

        self.c4games = []
        self.c4challenges = []

        self.responses = {
            "fdghdfghdfghdfghdfghdfghdfghdfghdfghdf":"GÅMING!",
            "lith":"https://cdn.discordapp.com/attachments/785014933758410796/785032262206226442/image0.jpg",
            "nefarious":"This computer is shared with others including parents. This is a parent speaking to you to now. Not sure what this group is up to. I have told my son that role playing d and d games are absolutely forbidden in out household. We do not mind him having online friendships with local people that he knows for legitimate purposes. Perhaps this is an innocent group. But, we expect transparency in our son's friendships and acquaintances. If you would like to identify yourself now and let me know what your purpose for this platform is this is fine. You are welcome to do so.",
            "avatars":"This computer is shared with others including parents. This is a parent speaking to you to now. Not sure what this group is up to. I have told my son that role playing d and d games are absolutely forbidden in out household. We do not mind him having online friendships with local people that he knows for legitimate purposes. Perhaps this is an innocent group. But, we expect transparency in our son's friendships and acquaintances. If you would like to identify yourself now and let me know what your purpose for this platform is this is fine. You are welcome to do so.",
            "cringe":"https://media.discordapp.net/attachments/551246526924455937/776278020507959296/image0.jpg?width=248&height=330",
            "patrick":"https://cdn.discordapp.com/attachments/785014933758410796/785218539350523944/nyooo.mp4",
            "weirdchamp":"https://cdn.discordapp.com/attachments/785015097927139348/785219023654354964/lmao.png",
            "nog":"https://cdn.discordapp.com/attachments/785014933758410796/785258888478851082/eggy.png",
            "wgmn":"https://cdn.discordapp.com/attachments/551246526924455937/783217821776740352/image0.gif",
        }
        self.introductions = {
            "eekay":"https://tenor.com/view/kinoplex-ethan-gif-24282665",
            "CaMelon":"https://tenor.com/view/camel-go-camel-go-go-ark-never-gonna-break-my-stride-walk-gif-20059775",
            "Xylotile":"https://tenor.com/view/william-william-gaming-clownzy-clownzy-buddy-gif-22541192",
            "ErfBundy":"https://tenor.com/view/gavin-discord-gif-22590938",
            "Joguitaro":"https://tenor.com/view/cat-spin-taylor-gif-19203154",
            "ASlowFatHorsey":"https://tenor.com/view/ap-down-revue-starlight-gif-22390985",
            "jakecrewa":"https://tenor.com/view/silent-gift-tr-the-realness-gif-14030327"
        }
        self.intros = {
            "eekay":"https://cdn.discordapp.com/attachments/551246526924455937/976967172364570754/IMG_2090.gif",
            "CaMelon":"https://media.discordapp.net/attachments/551246526924455937/976959442845335632/IMG_2085.gif",
            "Xylotile":"https://cdn.discordapp.com/attachments/972938534661009519/976969584907272263/sadf.gif",
            "ErfBundy":"https://cdn.discordapp.com/attachments/972938534661009519/976968856423772180/sdfg.gif",
            "Joguitaro":"https://cdn.discordapp.com/attachments/972938534661009519/976968624524906496/asdf.gif",
            "ASlowFatHorsey":"https://cdn.discordapp.com/attachments/972938534661009519/976968254478245998/aps.gif",
            "jakecrewa":"https://cdn.discordapp.com/attachments/972938534661009519/976970039318179840/asdfasdfasdf.gif"
        }

    def readLast(self):
        incoming = msg()
        while True:
            try:
                incoming.content = self.driver.find_elements_by_css_selector(".messageContent-2t3eCI")[-1].text
                incoming.sender = self.driver.find_elements_by_css_selector(".username-h_Y3Us")[-1].text
                incoming.time = self.driver.find_elements_by_css_selector("[datetime]")[-1].get_attribute("datetime")
                break
            #except selenium.common.exceptions.StaleElementReferenceException:
            except:
                time.sleep(.01)
        if incoming != self.lastSeen and incoming.sender != self.name:
            self.lastSeen.copy(incoming)
            self.onMessage()

    def send(self, msg):
        print("typing . . .")
        self.driver.find_element_by_css_selector('[role=textbox]').send_keys(msg)
        time.sleep(.1)
        self.driver.find_element_by_css_selector('[role=textbox]').send_keys(Keys.ENTER)
        print("response finished . . .")

    def onMessage(self):
        m = self.lastSeen.content

        for i, e in enumerate(self.responses):
            if e == m.lower():
                self.send(self.responses[e])

        if "cemb cemb" in m.lower():
            self.send(random.choice(["yes", "no", "c'est possible"]))

        if "!challenge " in m:
            n = m.replace("@", "")
            challenged = n.replace("!challenge ", "")
            if self.isChallenged(self.lastSeen.sender, challenged):
                self.send("You have already challenged that user")
            elif self.isChallenged(challenged, self.lastSeen.sender):
                self.send("That user has already challenged you. Accept the challenge with !accept [USERNAME]")
            elif challenged == self.lastSeen.sender:
                self.send("You can't play yourself moron why are you trying to break friggbot?")
            else:
                self.send(f"Connect4 challenge created vs {challenged}")
                self.c4challenges.append([self.lastSeen.sender, challenged])
        if '!accept ' in m:
            n = m.replace("@", "")
            challenger = n.replace("!accept ", "")
            if not self.isChallenged(challenger, self.lastSeen.sender):
                self.send("You have not been challenged by that user")
            elif self.isInGame(self.lastSeen.sender):
                self.send('You are already in a game')
            elif self.isInGame(challenger):
                self.send('That user is currently in a game')
            else:
                self.c4challenges.remove([challenger, self.lastSeen.sender])
                new = connect4(challenger, self.lastSeen.sender)
                self.c4games.append(new)
                self.send(f"Game started between @{new.p1} and @{new.p2}. {new.p1} goes first:")
                self.send(new.show())
        if "!c4 " in m:
            validMove = False
            try:
                move = int(m.replace("!c4 ", ""))
                validMove = True
            except:
                self.send("Invalid move. choose a number [1-7] for your piece")
            if validMove:
                if not self.isInGame(self.lastSeen.sender):
                    self.send("You are not in a game")
                elif move > 7 or move < 1:
                    self.send(f"Invalid move. Choose a column [1-7] to drop your piece")
                else:
                    g = self.gameOf(self.lastSeen.sender)
                    resp = g.move(self.lastSeen.sender, move)
                    if resp == "not their move":
                        self.send(f"It's {(g.p1 if self.lastSeen.sender != g.p1 else g.p2)}'s move")
                    elif resp == "column full":
                        self.send("That column is full.")
                    else:
                        self.send(g.show())
                        res = g.checkEnd()
                        if res == 'p1 win':
                            self.send(f"{g.p1} wins. wpyiyi!")
                            self.c4games.remove(g)
                        if res == 'p2 win':
                            self.send(f"{g.p2} wins. wpyiyi!")
                            self.c4games.remove(g)
                        if res == 'draw':
                            self.send(f"{g.p1} wins. wpyiyi!")
                            self.c4games.remove(g)
        if "!abort" in m:
            if self.isInGame(self.lastSeen.sender):
                g = self.gameOf(self.lastSeen.sender)
                self.send(f"{self.lastSeen.sender}'s game with {(g.p1 if self.lastSeen.sender != g.p1 else g.p2)} has been aborted.")
                self.c4games.remove(g)
            else:
                self.send("You are not currently in a game")
        if "!decline " in m:
            challenger = m.replace("!decline ", "").replace("@", "")
            if self.isChallenged(challenger, self.lastSeen.sender):
                self.send(f"{challenger}'s challenge vs {self.lastSeen.sender} has been declined")
                self.c4challenges.remove([challenger, self.lastSeen.sender])
            else:
                self.send(f"You have not been challenged by {challenger}")


        if "!lp" in m.lower():
            self.send(self.getLP(m))

        if "!gpt3" in m.lower():
            self.send(self.genGPT(m))

    def intro(self):
        old = self.online
        new = self.getOnline()
        for e in new:
            if e not in old:
                self.send(self.intros[e])
        if old != new:
            self.online = new 

    def gameOf(self, user):
        for i in self.c4games:
            if i.p1 == self.lastSeen.sender or i.p2 == self.lastSeen.sender:
                return i

    def isInGame(self, user):
        for i in self.c4games:
            if i.p1 == self.lastSeen.sender or i.p2 == self.lastSeen.sender:
                return True
        return False

    def isChallenged(self, challenger, challenged):
        return [challenger, challenged] in self.c4challenges

    def gcName(self):
        currentName = self.driver.find_element_by_css_selector(".container-1bg4pR").text
        return currentName

    def enforceName(self):
        name = self.gcName()
        if name not in [self.altGCName, self.desiredGCName]:
            nameBox = self.driver.find_element_by_css_selector(".input-1nrc5P")
            nameBox.click()
            #nameBox.clear()
            nameBox.send_keys(Keys.CONTROL + "a", Keys.DELETE)
            nameBox.send_keys(self.altGCName, Keys.ENTER)

    def getOnline(self):
        ppl = self.driver.find_elements_by_css_selector(".layout-1qmrhw")
        online = [e.find_element_by_css_selector(".name-3Vmqxm") for e in ppl if len(e.find_elements_by_css_selector(".pointerEvents-9SZWKj")) > 0]
        onPC = set([e.text for e in online])
        return onPC

    def genGPT(self, prompt):
        print("gpt request received. . .")
        openai.api_key = open("C:\\Users\\ekhad\\Desktop\\frig\\openaikey.txt").readline()
        resp = openai.Completion.create(
            prompt=prompt.replace("!gpt3 ",""),
            temperature=.5,
            engine="text-davinci-002",
            max_tokens=250,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0)
        print("request processed. . .")
        return resp.choices[0].text

    def getLP(self, m):
        try:
            region = m[0:m.index(" ")].replace("!lp", "")
        except ValueError:
            return "use the command right you stupid fuck"
        name = m.replace(f"!lp{region} ", "")
        regions = ["na", "euw", "eun", "kr", "br", "jp", "ru", "oc", "tr", "la"]
        region = "na" if region not in regions else region
        region = region if region in ['kr', 'ru'] else region+'1'
        try:
            addr = f"https://u.gg/lol/profile/{region}/{name}/overview"
            page = bs4(requests.get(addr).text, 'html.parser')
            lp = page.find("div", class_="rank-text").text
            rank = page.find("span", class_="rank-title").text

            report = f'{name} is in {rank} at {lp.replace(rank, "")}'
            if "Unranked" in report:
                report = f"{name} is not on the ranked grind"
        except AttributeError:
            if region not in regions:
                report = f"region not recognized. Recognized regions: {regions[:]}"
            else:
                report = 'https://tenor.com/view/who-dat-snoop-gif-15116696'
        return report

class connect4:
    def __init__(self, p1, p2):
        self.p1 = p1
        self.p2 = p2
        self.board = [['.' for j in range(0, 6)] for i in range(0, 7)]
        self.movenum = 0
        self.live = True

    def move(self, player, col):
        if player not in [self.p1, self.p2]:
            return 'invalid player'
        if player == self.p1 and self.movenum%2 == 1:
            return 'not their move'
        if player == self.p2 and self.movenum%2 == 0:
            return 'not their move'

        for i, e in enumerate(self.board[col-1]):
            if e == '.':
                if player == self.p1:
                    self.board[col-1][i] = 'x'
                if player == self.p2:
                    self.board[col-1][i] = 'o'
                self.movenum += 1
                return 'accepted'
        return 'column full'

    def show(self):
        rep = '```'
        t = np.ndarray.tolist(np.transpose(self.board))
        t.reverse()
        for i in t:
            for j in i:
                rep += j + ' '
            rep += '\n'
        return rep + '```'

    def checkEnd(self):
        for i in self.board:
            if sublist(i, ['x', 'x', 'x', 'x']):
                return 'p1 win'
            if sublist(i, ['o', 'o', 'o', 'o']):
                return 'p2 win'
        for i in np.ndarray.tolist(np.transpose(self.board)):
            if sublist(i, ['x', 'x', 'x', 'x']):
                return 'p1 win'
            if sublist(i, ['o', 'o', 'o', 'o']):
                return 'p2 win'
        for i in diags(self.board):
            if sublist(i, ['x', 'x', 'x', 'x']):
                return 'p1 win'
            if sublist(i, ['o', 'o', 'o', 'o']):
                return 'p2 win'
        o = [e[:] for e in self.board]
        [e.reverse() for e in o]
        for i in diags(o):
            if sublist(i, ['x', 'x', 'x', 'x']):
                return 'p1 win'
            if sublist(i, ['o', 'o', 'o', 'o']):
                return 'p2 win'
        for e in self.board:
            if '.' in e:
                return 'no end condition'
        return 'draw'
            

class msg:
    def __init__(self):
        self.content = None
        self.sender = None
        self.time = None

    def __eq__(self, __o: object) -> bool:
        return (self.content == __o.content) and (self.sender == __o.sender) and (self.time == __o.time)

    def copy(self, new):
        self.content, self.sender, self.time = new.content, new.sender, new.time

    def clear(self):
        self.content = None
        self.sender = None
        self.time = None
        
def sublist(a, b):
    for i in range(0, len(a)-len(b)+1):
        if a[i:i+len(b)] == b:
            return True
    return False

def diags(a):
    n = len(a[0]) + len(a) - 1
    b = [np.ndarray.tolist(np.diag(a, k=i)) for i in range(-n, n)]
    return [e for e in b if e != []]

