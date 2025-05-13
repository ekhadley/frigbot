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
    def __init__(self, model_name: str, key):
        self.model_name = model_name
        self.messages = {}
        self.client = openai.OpenAI(api_key=key)
        self.instructions = """
            You are an assistant integrated into a Discord bot named FriggBot2000.
            User messages will be preceded with a username, so you can tell which user you are talking to.
            Do not precede your own messages with any username.
            Your conversations may include more than 1 person.
            Do not use emojis. Do not use double newlines, messages should be compact.
            When using markdown, you may use bullet points and headers, but do not use tables or level 4 headers (####).
            You should generally prefer briefer answers, suitable for a shared group chat, but fully answering complex queries supercedes this.
            Discord messages can only have about 250 words, so split up long responses accordingly using the token <split>.
            You don't respond to any discord bot commands like "!reset", etc.
        """.replace("\n", " ")
    
    def requiresResponse(self, msg: dict) -> bool:
        return (ref:=msg.get("message_reference")) is not None and ref.get("message_id") in self.messages

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
