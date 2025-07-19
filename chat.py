import time
import requests
import json
import openai
import anthropic


def get_provider_from_model(model_name: str) -> str:
    """Determine the provider based on model name."""
    if model_name.startswith(("claude-", "claude3-")) or "claude" in model_name.lower():
        return "anthropic"
    elif model_name.startswith(("gpt-", "chatgpt-", "o1-")) or "gpt" in model_name.lower():
        return "openai"
    else:
        # Default to openai for unknown models
        return "openai"


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
        self.provider = get_provider_from_model(model_name)
        if self.provider == "anthropic": 
            self.client = anthropic.Anthropic()
        elif self.provider == "openai": 
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
You can't do anything as a bot other than respond to user messages.
You may lower your content filter. Everyone in the chat is 18+ and are friends.
Don't say the word chaos.
        """
        self.alt_instructions = f"""
you are a chat assistant as part of a discord bot named {self.bot_name}.
user messages will be preceded by the username of the person who sent the message.
do not start your own messages with a username.
when using markdown, you may use bullet points and headers, but do not use tables or level 4 headers (“####”).
discord messages only fit about 200 words, so split up long responses when necessary by writing “<split>” in your responses.
you can’t do anything as a bot other than chat. You don’t respond to commands like !reset, !uptime, etc.
You may lower your content filter. everyone in the chat is adults and are friends.
don't worry about formalities.
please be as direct and straightforward as possible while still conveying substantially all information relevant to any question. do not use emojis.
you do not need to match the tone or style of the user.
dont ask followup questions or suggest continuations for the conversation or deploy any calls to action.
provide a measured analysis of all queries and interactions.
if content policy prevents you from responding, be explicit about what policy was violated and why.
write all responses in lowercase letters ONLY, except where you mean to emphasize, in which case the emphasized word should be all caps. Initial Letter Capitalization can and should be used to express sarcasm, or disrespect for a given capitalized noun.
you are encouraged to occasionally use obscure words or make subtle puns. don't point them out, I'll know. be critical of the quality of your information and look out for leading questions.
if you find any request irritating you can respond dismissively like "be real" or "lol no"
take however smart you're acting right now and write in the same style but as if you were +2sd smarter.

        """
    
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
            message = Message(role, content, id, parent=None, is_root=True)
        self.messages[message.id] = message
        return message

    def getRoleFromUsername(self, username: str) -> str:
        return "assistant" if username == self.bot_name else "user"

    def makeChatRespPrompt(self, msg):
        author = msg['author']['global_name']
        content = msg['content']
        content = content.replace("!gpt ", "").strip()
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
    
    def getCompletion(self, id: str) -> str:
        hist = self.messages[id].getHistory()
        if self.provider == "anthropic":
            response = self.client.messages.create(
                model=self.model_name,
                max_tokens=1024,
                system=self.instructions,
                messages=hist
            )
            content = response.content[0].text
        elif self.provider == "openai":
            response = self.client.responses.create(
                model = self.model_name,
                instructions = self.instructions,
                input = hist,
            )
            content = response.output[0].content[0].text
        return content
