import googleapiclient
from googleapiclient.discovery import build

import json
import datetime
from utils import bold, gray, endc, yellow, green, red

class ytChannelTracker:
    def __init__(self, name, ytkey, channelID, savePath, checkInterval=10800):
        self.channelName = name
        self.checkInterval = checkInterval
        self.savePath = savePath # where on disk do we keep most recent video ID (not rly a log, just the most recent)
        self.channelID = channelID # the channelid (not the visible one) of the channel we are monitoring
        self.mostRecentVidId, self.lastCheckTime = self.readSave() # read the most recent video ID and time of last api request
        print(googleapiclient.__dict__)
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
            if not succeeded:
                return False
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
            if videoId is not None:
                saved["videoId"] = videoId
            with open(self.savePath, "w") as f:
                f.write(json.dumps(saved, indent=4))
        except Exception as e:
            print(f"{red} recordNewRead for channel: '{self.channelName}' failed with exception:\n{e}")

    def timeSinceCheck(self): # returns the amount of time since last 
        delta = datetime.datetime.now() - self.lastCheckTime
        #print(f"{sec} sec since last check. check interval is {self.checkInterval} sec. checking in {self.checkInterval - sec}")
        return delta.days*24*60*60 + delta.seconds

    def shouldCheck(self): return self.timeSinceCheck() >= self.checkInterval
    def ttcheck(self, *args, **kwargs):
        delta = self.checkInterval - self.timeSinceCheck()
        hours, minutes, seconds = delta//3600, (delta%3600)//60, delta%60
        return f"checking in {hours}h, {minutes}m, {seconds}s seconds" 

    def now(self): return datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    def str2dt(self, dstr): return datetime.datetime.strptime(dstr, "%Y-%m-%dT%H:%M:%SZ")
