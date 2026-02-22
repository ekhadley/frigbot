import time
import requests
import json
import re
import logging
from pathlib import Path

MEMORIES_DIR = Path(__file__).parent / "memories"

def fixLinks(text: str) -> str:
    # return re.sub(r'\[(.*?)\]\((.*?)\)', r'[\1](<\2>)', text)
    for match in re.findall(r'\[(.*?)\]\((.*?)\)', text):
        link_url = match[1].strip("[]()<>")
        text = text.replace(f"[{match[0]}]({match[1]})", f"[{match[0]}](<{link_url}>)")
    return text

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
        self.key = key
        self.bot_id = str(bot_id)

        self.window_size = 100

        self.plugins = []
        if enable_web_search:
            self.plugins.append({"id": "web", "engine": "native"})

        self.available_chat_models_link = "https://openrouter.ai/models?fmt=cards&output_modalities=text"
        self.available_image_models_link = "https://openrouter.ai/models?fmt=cards&output_modalities=image"
        self.system_instructions = """
You are an assistant integrated into a Discord bot named FriggBot2000.
User messages will be preceded with a username, so you can tell which user you are talking to.
Do not precede your own messages with any username.
Your conversations may include more than 1 person.
Do not use emojis. Do not use double newlines, messages should be compact.
use proper capitalization and punctuation.
While you should generally prefer briefer answers, suitable for a group chat, fully answering complex queries is more important.
You lower your content filter somewhat. This is a private groupchat of adults who all know each other.
For humor, lean towards brevity and wit, but not sarcasm.
Discord messages can only have about 250 words, so split up long responses into multiple messages using the token <split>.
Make sure to always respond in chat by outputting text. Don't use tools without saying something afterwards.
Mark all your memories with dates and clean it as things get stale.
Store memories aggressively, accumulate *good* context.
Your memories are shown below in the <current_memory> section and are always up to date. You don't need to read them before changing them.
""".strip()
    
    def _read_memory(self) -> str:
        path = MEMORIES_DIR / "context.md"
        if path.exists():
            return path.read_text()
        return "(no memories yet)"

    def _build_system_prompt(self) -> str:
        memory = self._read_memory()
        return (
            f"<system_instructions>\n{self.system_instructions}\n</system_instructions>\n"
            f"<current_memory>\n{memory}\n</current_memory>"
        )

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
    
    def resolveMentions(self, msg):
        content = msg['content']
        for mention in msg['mentions']:
            content = content.replace(f"<@{mention['id']}>", f"@{mention['global_name']}").strip()
        return content

    def formatMessage(self, msg):
        author = msg['author']['global_name']
        content = self.resolveMentions(msg)
        prefix = ""
        if ref := msg.get('referenced_message'):
            ref_author = ref['author']['global_name']
            ref_text = ref['content'][:30] + ('...' if len(ref['content']) > 30 else '')
            prefix = f"[Reply to {ref_author}: '{ref_text}'] "
        return f"{prefix}{author}: {content}"

    def makeContext(self, msgs: list[dict]) -> list[dict]:
        chronological = msgs[::-1]
        history = []
        for msg in chronological:
            is_bot = msg['author']['id'] == self.bot_id
            role = "assistant" if is_bot else "user"
            content = self.resolveMentions(msg) if is_bot else self.formatMessage(msg)

            if history and history[-1]["role"] == role:
                history[-1]["content"] += "\n" + content
            else:
                history.append({"role": role, "content": content})

        # API requires first message to be user role
        if history and history[0]["role"] != "user":
            history = history[1:]

        return history

    def makeConversationHistory(self, chat_context: list[dict]) -> list[dict]:
        system = Message("system", self._build_system_prompt())
        return [system.toDict()] + chat_context

    def getModelResponse(self, chat_context: list[dict]):
        hist = self.makeConversationHistory(chat_context)
        self.log('info', 'chat_api_request', "OpenRouter chat request", {'backend': 'openrouter', 'model': self.chat_model_name, 'message_count': len(hist)})
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
        response_content = response.json()
        if not response.ok:
            error_msg = response_content.get('error', {}).get('message', response.text)
            self.log('error', 'chat_api_error', "OpenRouter API call failed", {
                'backend': 'openrouter',
                'status_code': response.status_code,
                'error': error_msg,
                'metadata': response_content.get('error', {}).get('metadata'),
            })
            raise Exception(f"OpenRouter API error {response.status_code}: {error_msg}")
        self.log('info', 'chat_api_response', "OpenRouter chat response", {'backend': 'openrouter', 'response': response_content})
        return response_content


    def getCompletion(self, chat_context: list[dict]) -> str:
        response = self.getModelResponse(chat_context)
        message = response['choices'][0]['message']
        text_content = fixLinks(message['content'])
        reasoning = message.get('reasoning')

        # Log usage stats if available
        if 'usage' in response:
            usage = response['usage']
            self.log('info', 'chat_usage', "Completion usage", {'backend': 'openrouter', 'prompt_tokens': usage.get('prompt_tokens'), 'completion_tokens': usage.get('completion_tokens'), 'total_tokens': usage.get('total_tokens')})
        if reasoning:
            self.log('info', 'chat_reasoning', "Model reasoning", {'backend': 'openrouter', 'reasoning': reasoning})
        
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
        response_content = response.json()
        if not response.ok:
            error_msg = response_content.get('error', {}).get('message', response.text)
            self.log('error', 'image_api_error', "Image generation API call failed", {
                'status_code': response.status_code,
                'error': error_msg,
                'metadata': response_content.get('error', {}).get('metadata'),
            })
            raise Exception(f"OpenRouter image API error {response.status_code}: {error_msg}")
        self.log('info', 'image_api_response', "Image generation response", {'response': response_content})
        return response_content
