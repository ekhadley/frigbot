import os
import time
import requests
import json
from frigbot import Frig


def formatMessage(msg):
    if isinstance(msg, list): return "".join([formatMessage(m)+"\n" for m in msg])
    return f"{msg['author']['global_name']}: {msg['content']}"


key_path = "/home/ek/frigkeys.json"
config_path = "/home/ek/wgmn/frigbot/config"
chatid = 972938534661009519 # eekay
#chatid = 551246526924455937 # kissy
if __name__ == '__main__':
    frig = Frig(keypath=key_path, configDir=config_path, chatid=chatid)


    msg = frig.getLatestMessage(num_messages = 2)
    print(msg)
    print()
    print()
    print()
    print()
    fmt = formatMessage(msg)
    print(fmt)
    


request_url = "https://api.runpod.ai/v2/j7y37sji59fax1/run"
return_base_url =  "https://api.runpod.ai/v2/j7y37sji59fax1/status/"
RUNPOD_API_KEY = os.environ.get("RUNPOD_API_KEY")
payload = {
    "input": {
        "prompt": "Xylotile: Nvda right now\nJoguitaro: Hold\nJoguitaro: https://tenor.com/view/braveheart-hold-shouts-gif-13268605\nXylotile: Started a call that lasted 30 minutes.\nXylotile: @Joguitaro\neekay: lol no shot\neekay: my teacher was talking about CPUs in my computer architecture class\neekay: and told everybody about the Intel guy on wab who bet his grandma's inheritance\neekay: wsb*\nXylotile: lol\nASlowFatHorsey: Guh\nASlowFatHorsey: Who?\neekay: \neekay: this guy lol\neekay: who put in his grandmas entire inheritance the day ebfore intel absolutely tanked\nXylotile: He deserves it\nXylotile: Absolute retard\neekay: yea intel wasnt looking so hot before the tank\neekay: not sure why he tryna get fancy\nXylotile: Besides that he didn’t diversify\nJoguitaro: bro did not know what people meant when they said invest lol\nXylotile: People in the comments said he prolly comes from money and that 700k doesn’t mean much\neekay: yeah neither do any of the gainporn screenshots on wsb\neekay: i mean if 700k is the entire inheritance you know about how much money they have\nASlowFatHorsey: Ain’t no way\nASlowFatHorsey: lol\nASlowFatHorsey: Why he doing that tho\nASlowFatHorsey: That’s so free if he just puts that in vug\nASlowFatHorsey: Def a upvote content goblin\neekay: he spent too much time on wallstreetbets\neekay: saw too manys creenshots of 1000% return portfolios\nXylotile: @eekay\nXylotile: @eekay\nXylotile: @eekay\nXylotile: @eekay\nXylotile: clasic\nXylotile: wait u playing or just have it up\nXylotile: Started a call that lasted 0 minutes.\neekay: im in zoom class rn lol\nXylotile: lol\nXylotile: @eekay can we discccc\neekay: Started a call that lasted 35 minutes.\neekay: @ASlowFatHorsey tonite?\neekay: we should br eady for barrens 10d4y\nJoguitaro: Most autistic way to say today\neekay: u clearly dont know hacking lingo\neekay: man we gotta climb step on the gas\nXylotile: he's prolly trying to find another girl to bring to our place\neekay: true i bet he ab to cancel\nASlowFatHorsey: https://tenor.com/view/panda-lonely-sad-pain-rain-gif-9594547216369692740\nASlowFatHorsey: Noodles\nASlowFatHorsey: Don’t noodles\nASlowFatHorsey: Quit\nASlowFatHorsey: Don’t quit\nASlowFatHorsey: Too worried about where dez were and where they will be\nASlowFatHorsey: Just enjoy them for where they are\nASlowFatHorsey: On ur chin\nASlowFatHorsey: !sonnet dez poem pls\nASlowFatHorsey: Erm\nASlowFatHorsey: @piggypatrol\nASlowFatHorsey: What’s the problem buddy\nErfBundy: Schizophrenia\nASlowFatHorsey: Yea\nASlowFatHorsey: Classic\nXylotile: Classic drunk ap\nXylotile: I’m gonna sod my pants\neekay: this shitty ass apartment xylotile chose for us is ddosing frigbot\neekay: wont let him connect or smthn\n",
        "max_new_tokens": 250
    }
}
headers = {
    "Authorization": f"Bearer {RUNPOD_API_KEY}",
    "Content-Type": "application/json"
}
response = requests.post(request_url, headers=headers, data=json.dumps(payload))

if response.ok:
    result = response.json()
    print("RunPod result:", result)
else:
    print("Error:", response.text)

return_url = return_base_url + result['id']
print(f"checking status from url: {return_url}")
while 1:
    completion_request = requests.get(return_url, headers=headers)
    if completion_request.ok:
        completion_result = completion_request.json()
        if completion_result['status'] == 'COMPLETED':
            break
    time.sleep(1)

print(completion_result)