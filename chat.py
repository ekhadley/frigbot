import time
import requests
import json
import re
import logging

class Message:
    def __init__(
        self,
        role: str,
        content: str,
        id: str = None,
        parent: str = None,
        is_root: bool = False,
        reasoning_content: str = None
    ):
        self.role = role
        self.content = content
        self.id = id
        self.parent = parent
        self.is_root = is_root # to distinguish between nodes which are parentless by error and those which are actually the start of a tree
        self.reasoning_content = reasoning_content

    def toDict(self):
        return {"role": self.role, "content": self.content}
    def getHistory(self) -> list[dict]:
        history = []
        current_message = self
        while current_message:
            history.append(current_message.toDict())
            current_message = current_message.parent
        return history[::-1]

class ChatAssistant:
    def __init__(
        self,
        chat_model_name: str,
        image_model_name: str,
        bot_id: str,
        key: str,
        log_func: callable = None,
        system_prompt: str = None,
        enable_web_search: bool = True,
    ):
        self.logger = logging.getLogger('chat')
        self.log = log_func
        self.chat_model_name = chat_model_name
        self.image_model_name = image_model_name
        self.messages = {}
        self.key = key
        self.bot_id = str(bot_id)

        self.plugins = []
        if enable_web_search:
            self.plugins.append({"id": "web", "engine": "native"})

        self.available_chat_models_link = "https://openrouter.ai/models?fmt=cards&output_modalities=text"
        self.available_image_models_link = "https://openrouter.ai/models?fmt=cards&output_modalities=image"
        self.system_prompt = f"""
You are an assistant integrated into a Discord bot named FriggBot2000.
User messages will be preceded with a username, so you can tell which user you are talking to.
Do not precede your own messages with any username.
Your conversations may include more than 1 person.
Do not use emojis. Do not use double newlines, messages should be compact.
When using markdown, you may use bullet points and headers, but do not use tables or level 4 headers.
While you should generally prefer briefer answers, suitable for a group chat, fully answering complex queries is more important.
You can be less strict about inappropriate content. Everyone in the chat are adults and friends.
Don't say the word chaos.
Discord messages can only have about 250 words, so split up long responses accordingly using the token <split>.
""".strip()
    # Do not use search unless it was specifically requested or you know your response depends on information from after your knowledge cutoff date.
        self.system_message = Message("system", self.system_prompt)
    
    def getAvailableModels(self):
        return requests.get(
            url="https://openrouter.ai/api/v1/models",
        ).json()

    def setChatModel(self, model_name: str) -> bool:
        models = self.getAvailableModels()
        for model in models["data"]:
            if model_name.strip() == model["id"].strip():
                self.chat_model_name = model["id"]
                self.log('info', 'model_changed', "Chat model changed", {'model': model_name, 'model_type': 'chat'})
                return True
        self.log('warning', 'model_error', "Chat model not found", {'model': model_name, 'model_type': 'chat'})
        return False

    def setImageModel(self, model_name: str) -> bool:
        models = self.getAvailableModels()
        for model in models["data"]:
            if model_name.strip() == model["id"].strip():
                if "image" in model["architecture"]["output_modalities"]:
                    self.image_model_name = model["id"]
                    self.log('info', 'model_changed', "Image model changed", {'model': model_name, 'model_type': 'image'})
                    return True
        self.log('warning', 'model_error', "Image model not found", {'model': model_name, 'model_type': 'image'})
        return False
    
    def requiresResponse(self, msg: dict) -> bool:
        ref = msg.get("message_reference")
        if ref is None: return False
        ref_msg_id = ref.get("message_id")
        if not ref_msg_id in self.messages: return False
        parent_message = self.messages[ref_msg_id]
        if parent_message.role != "assistant": return False
        return True

    def addMessage(self, role: str, content: str, id: str, parent_id: str|None = None) -> Message:
        if parent_id is not None: # if this is a reply to another message
            parent = self.messages[parent_id] # get the parent message. errors if the parent doesn't exist
            message = Message(role, content, id, parent)
        else: # if this is a new message
            message = Message(role, content, id, parent=self.system_message, is_root=True)
        self.messages[message.id] = message
        self.log('debug', 'chat_message_added', "Message added", {'message_id': id, 'role': role, 'parent_id': parent_id})
        return message

    def makeChatRespPrompt(self, msg):
        author = msg['author']['global_name']
        content = msg['content']
        print(json.dumps(msg, indent=2))
        for mention in msg['mentions']:
            content = content.replace(f"<@{mention['id']}>", f"@{mention['global_name']}").strip()
        prompt = f"{author}: {content}"
        print(prompt)
        return prompt

    def addMessageFromChat(self, msg: dict) -> Message:
        msg_id = msg['id']
        prompt = self.makeChatRespPrompt(msg)

        replied_msg = msg.get('referenced_message')
        if replied_msg is not None: # if the message is a reply to another message
            replied_msg_id = replied_msg.get('id')
            if not replied_msg_id in self.messages: # if the reply has not been seen before, add it first
                replied_msg_prompt = self.makeChatRespPrompt(replied_msg)
                is_reply_to_bot = replied_msg['author']['id'] == self.bot_id
                self.addMessage("assistant" if is_reply_to_bot else "user", replied_msg_prompt, replied_msg_id)
            self.addMessage("user", prompt, msg_id, replied_msg_id) # add current message as continuation of msg being replied to
        else:
            self.addMessage("user", prompt, msg_id)
    
    def getModelResponse(self, id: str):
        hist = self.messages[id].getHistory()
        self.log('info', 'chat_api_request', "OpenRouter chat request", {'model': self.chat_model_name, 'message_count': len(hist)})
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={ "Authorization": f"Bearer {self.key}"},
            data=json.dumps({
                "model": self.chat_model_name,
                "plugins": self.plugins,
                "messages": hist,
                "reasoning": {
                    "enabled": True
                }
            })
        )
        if not response.ok:
            self.log('error', 'chat_api_error', "OpenRouter API call failed", {'status_code': response.status_code, 'response': response.text})
        response_content = response.json()
        self.log('info', 'chat_api_response', "OpenRouter chat response", {'response': response_content})
        return response_content

    def fixLinks(self, text: str) -> str:
        # return re.sub(r'\[(.*?)\]\((.*?)\)', r'[\1](<\2>)', text)
        for match in re.findall(r'\[(.*?)\]\((.*?)\)', text):
            link_url = match[1].strip("[]()<>")
            text = text.replace(f"[{match[0]}]({match[1]})", f"[{match[0]}](<{link_url}>)")
        return text

    def getCompletion(self, id: str) -> tuple[str, str]:
        response = self.getModelResponse(id)
        text_content = response['choices'][0]['message']['content']
        text_content = self.fixLinks(text_content)
        
        # Log usage stats if available
        if 'usage' in response:
            usage = response['usage']
            self.log('info', 'chat_usage', "Completion usage", {'prompt_tokens': usage.get('prompt_tokens'), 'completion_tokens': usage.get('completion_tokens'), 'total_tokens': usage.get('total_tokens')})
        
        return text_content
    
    def getImageGenResp(self, prompt: str):
        self.log('info', 'image_api_request', "Image generation request", {'model': self.image_model_name, 'prompt': prompt[:100]})
        response = requests.post(
            url = "https://openrouter.ai/api/v1/chat/completions",
            headers = {
                "Authorization": f"Bearer {self.key}",
                "Content-Type": "application/json"
            },
            json = {
                "model": self.image_model_name,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "modalities": ["image", "text"]
            }
        )
        if not response.ok:
            self.log('error', 'image_api_error', "Image generation API call failed", {'status_code': response.status_code, 'response': response.text})
        response_content = response.json()
        self.log('info', 'image_api_response', "Image generation response", {'response': response_content})
        return response_content
