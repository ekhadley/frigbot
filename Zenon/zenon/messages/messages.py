import requests
import re
import json
import random

class Messages(object):
    def __init__(self, token, Discord = "https://discordapp.com/api/v9/"):
        self.token = token
        self.discord = Discord

    def send_message(self, chatid, content, proxy): # it can also be use as a private message
        url = f"{self.discord}channels/{chatid}/messages"
        nonce = random.randint(10000000, 99999999)
        return requests.post(url, proxies=proxy, data={"content":str(content), "nonce":str(nonce)}, headers={"Authorization":self.token}).text
        #self.discord+"channels/"+str(chatid)+"/messages#"
        #proxies=proxy,data={"content":str(content),"nonce":str(random.randint(10000000, 99999999))}
        #headers={"Authorization":self.token}).text

    
    def send_message_with_tts(self, chatid, content, proxy):
        return requests.post(self.discord + "channels/" + str(chatid) + "/messages#", proxies=proxy, data={"content":str(content), "nonce":str(chatid), "tts":True}, headers={"Authorization":self.token}).text
        
    def typing_action(self, chatid, proxy):
        return requests.post(self.discord + "channels/" + str(chatid) + "/typing", proxies=proxy, headers={"Authorization":self.token}).text
    
    def pinMessage(self, chatid, msgid, proxy):
        return requests.post(self.discord + "channels/" + str(chatid) + "/pins/" + str(msgid), proxies=proxy, headers={"Authorization":self.token}).text
    
    def deleteMessage(self, chatid, messageid, proxy):
        return requests.delete(self.discord + "channels/" + str(chatid) + "/messages/" + str(messageid), proxies=proxy, headers={"Authorization":self.token}).text
    
    def editMessage(self, chatid, messageid, text, proxy):
        return requests.patch(self.discord + "channels/" + str(chatid) + "/messages/" + str(messageid), proxies=proxy, headers={"Authorization":self.token}, data={"content":text}).text
        
    def sendFile(self, chatid, file, content, proxy):
        return requests.post(self.discord + "channels/" + str(chatid) + "/messages", proxies=proxy, headers={"Authorization":self.token, "content":str(content)}, files={"file":open(file, 'rb')}).text

    def get_message(self, chatid, proxy):
        url = f"{self.discord}channels/{chatid}/messages?limit=1"
        res = requests.get(url, proxies=proxy, headers={"Authorization":self.token}).json()
        return res[0] if isinstance(res, list) else res

#    def get_author(self, chatid, proxy):
#        res = requests.get(self.discord + "channels/" + str(chatid) + "/messages?limit=1", proxies=proxy, headers={"Authorization":self.token}).text
#        return json.loads(res)
#        #return res.split('"username": "')[1].split('"')[0]

#    def get_author_id(self, chatid, proxy):
#        res = requests.get(self.discord + "channels/" + str(chatid) + "/messages?limit=1", proxies=proxy, headers={"Authorization":self.token}).text
#        return res.split('"id": "')[1].split('"')[0]
