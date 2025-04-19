import time
import requests
import json

from collections.abc import Callable
import openai





def formatMsg(msg):
    #if isinstance(msg, list): return "".join([formatMsg(m)+"\n" for m in msg[::-1]])
    return f"{msg['author']['global_name']}: {msg['content']}"

class ChatManager:
    def __init__(self, api_key):
        self.api_key = api_key
        self.avg_char_per_token = 3
        # we want to give the model about 1024 tokens, but we dont want to tokenize the context before we send it just to check the length. we just use this to get in the ballpark.
        self.ctx_tok_len_target = 1024
        self.ctx_str_len_max = self.ctx_tok_len_target * self.avg_char_per_token

        self.url_base = "https://api.runpod.ai/v2/j7y37sji59fax1"
        self.request_url = self.url_base + "/run"
        self.return_url_base = self.url_base + "/status/"

        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def getCompletion(self, prompt:str, max_new_tokens:int = 100) -> str:
        payload = { "input": { "prompt": prompt, "max_new_tokens": max_new_tokens } }
        request_response = requests.post(self.request_url, headers=self.headers, data=json.dumps(payload))
        if request_response.ok:
            request = request_response.json()
            return_url = self.return_url_base + request['id']

            while 1:
                completion_response = requests.get(return_url, headers=self.headers)
                if completion_response.ok:
                    completion = completion_response.json()

                    if completion['status'] == 'COMPLETED':
                        return completion['output']
                    elif completion['status'] == 'FAILED':
                        break
                time.sleep(1)
        return f"Completion failed."

    def formatMessages(self, ChatCtx:str, tail:str = "") -> str: # given a list of messages, we format them and include as many as possible while remaining under the maximum.
        ctx = "\n"
        for msg in ChatCtx:
            fmt = formatMsg(msg)
            if len(fmt) + len(ctx) <= self.ctx_str_len_max:
                ctx = fmt + "\n" + ctx
            else:
                return ctx + tail
        return ctx + tail
