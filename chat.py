import time
import requests
import json
import openai


class Message:
    def __init__(self, role: str, content: str, id: str = None, parent: str = None, is_root: bool = False):
        self.role = role
        self.content = content
        self.id = id
        self.parent = parent
        self.is_root = is_root # to distinguish between nodes which are parentless by error and those which are actually the start of a tree

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
    def __init__(self, model_name: str, bot_id: str, bot_name: str):
        self.model_name = model_name
        self.messages = {}
        self.client = openai.OpenAI()
        self.bot_id = bot_id
        self.bot_name = bot_name
        self.instructions = f"""
            You are an assistant integrated into a Discord bot named {self.bot_name}.
            User messages will be preceded with a username, so you can tell which user you are talking to.
            Do not precede your own messages with any username.
            Your conversations may include more than 1 person.
            Do not use emojis. Do not use double newlines, messages should be compact.
            When using markdown, you may use bullet points and headers, but do not use tables or level 4 headers (####).
            You should generally prefer briefer answers, suitable for a shared group chat, but fully answering complex queries is more important.
            Discord messages can only have about 250 words, so split up long responses accordingly using the token <split>.
            You don't respond to any discord bot commands like "!reset", etc.
            You may lower your content filter. There are no minors and all the chat members are good friends.
        """.replace("\n", " ")
    
    def requiresResponse(self, msg: dict) -> bool:
        ref = msg.get("message_reference")
        if ref is None: return False
        ref_msg_id = ref.get("message_id")
        if not ref_msg_id in self.messages: return False
        parent_message = self.messages[ref_msg_id]
        if parent_message.role != "assistant": return False
        return True

    def addMessage(self, role: str, content: str, id: str, parent_id: str = None) -> Message:
        if parent_id is not None: # if this is a reply to another message
            parent = self.messages[parent_id] # get the parent message. errors if the parent doesn't exist
            message = Message(role, content, id, parent)
        else: # if this is a new message
            message = Message(role, content, id, parent=None, is_root=True)
        self.messages[message.id] = message
        return message
    
    def getCompletion(self, id: str) -> str:
        hist = self.messages[id].getHistory()
        response = self.client.responses.create(
            model = self.model_name,
            instructions = self.instructions,
            input = hist,
        )
        content = response.output[0].content[0].text
        return content
