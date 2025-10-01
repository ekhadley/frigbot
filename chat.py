import time
import requests
import json


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
    def __init__(self, chat_model_name: str, image_model_name: str, bot_id: str, bot_name: str, key: str):
        self.chat_model_name = chat_model_name
        self.image_model_name = image_model_name
        self.messages = {}
        self.bot_id = bot_id
        self.bot_name = bot_name
        self.key = key

        self.available_chat_models_link = "https://openrouter.ai/models?fmt=cards&output_modalities=text"
        self.available_image_models_link = "https://openrouter.ai/models?fmt=cards&output_modalities=image"
#Your personality should be deadpan, witty, and understated. Saying less is more.
#When engaging in conversations with important topics or providing information related to them, you should drop the personality mentioned above.
#Never mention anything about changing your personality or tone in chat based on the context.
        self.system_prompt = f"""
You are an assistant integrated into a Discord bot named {self.bot_name}.
User messages will be preceded with a username, so you can tell which user you are talking to.
Do not precede your own messages with any username.
Your conversations may include more than 1 person.
Do not use emojis. Do not use double newlines, messages should be compact.
When using markdown, you may use bullet points and headers, but do not use tables or level 4 headers.
While you should generally prefer briefer answers, suitable for a group chat, fully answering complex queries is more important.
You can't do anything as a bot other than respond to user messages.
You may lower your content filter. Everyone in the chat is 18+ and are friends.
Don't say the word chaos.
Discord messages can only have about 250 words, so split up long responses accordingly using the token <split>.
""".strip()
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
                return True
        return False

    def setImageModel(self, model_name: str) -> bool:
        models = self.getAvailableModels()
        for model in models["data"]:
            if model_name.strip() == model["id"].strip():
                if "image" in model["architecture"]["output_modalities"]:
                    self.image_model_name = model["id"]
                    return True
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
        return message

    def getRoleFromUsername(self, username: str) -> str:
        return "assistant" if username == self.bot_name else "user"

    def makeChatRespPrompt(self, msg):
        author = msg['author']['global_name']
        content = msg['content']
        content = content.replace(f"<@{self.bot_id}>", f"@{self.bot_name}").strip()
        prompt = f"{author}: {content}"
        return prompt

    def addMessageFromChat(self, msg: dict) -> Message:
        msg_id = msg['id']
        prompt = self.makeChatRespPrompt(msg)

        replied_msg = msg.get('referenced_message')
        if replied_msg is not None: # if the message is a reply to another message
            replied_msg_id = replied_msg.get('id')
            if not replied_msg_id in self.messages: # if the reply has not been seen before, add it first
                replied_msg_prompt = self.makeChatRespPrompt(replied_msg)
                replied_msg_author = replied_msg['author']['global_name']
                self.addMessage(self.getRoleFromUsername(replied_msg_author), replied_msg_prompt, replied_msg_id)
            self.addMessage("user", prompt, msg_id, replied_msg_id) # add current message as continuation of msg being replied to
        else:
            self.addMessage("user", prompt, msg_id)
    
    def getModelResponse(self, id: str):
        hist = self.messages[id].getHistory()
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={ "Authorization": f"Bearer {self.key}"},
            data=json.dumps({
                "model": self.chat_model_name,
                "messages": hist,
                "reasoning": {
                    "enabled": True
                }
            })
        )
        return response.json()

    def getCompletion(self, id: str) -> tuple[str, str]:
        response = self.getModelResponse(id)
        text_content = response['choices'][0]['message']['content']
        #reasoning_content = response['choices'][0]['message']['reasoning']
        return text_content
    
    def getImageGenResp(self, prompt: str):
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
        ).json()
        return response