import logging
import anthropic
from chat import ChatAssistant, fixLinks
from memory_tool import LocalMemoryTool

class AnthropicChatAssistant(ChatAssistant):
    def __init__(
        self,
        chat_model_name: str,
        image_model_name: str,
        context_mode: str,
        bot_id: str,
        key: str,
        log_func: callable = None,
        system_prompt: str = None,
        enable_web_search: bool = True,
        enable_memory: bool = True,
    ):
        super().__init__(
            chat_model_name=chat_model_name,
            image_model_name=image_model_name,
            context_mode=context_mode,
            bot_id=bot_id,
            key=key,
            log_func=log_func,
            system_prompt=system_prompt,
            enable_web_search=False,  # don't use OpenRouter's web search plugin
        )
        self.client = anthropic.Anthropic(api_key=key)
        self.tools = []
        if enable_web_search:
            self.tools.append({"type": "web_search_20250305", "name": "web_search"})
        self.memory_tool = LocalMemoryTool() if enable_memory else None
        if self.memory_tool:
            self.tools.append(self.memory_tool)

    def setChatModel(self, model_name: str) -> bool:
        self.chat_model_name = model_name
        self.log('info', 'model_changed', "Chat model changed", {'model': model_name, 'model_type': 'chat'})
        return True

    def makeConversationHistory(self, chat_context: str) -> list[dict]:
        return [{"role": "user", "content": chat_context}]

    def getModelResponse(self, chat_context: str):
        hist = self.makeConversationHistory(chat_context)
        self.log('info', 'chat_api_request', "Anthropic chat request", {'backend': 'anthropic', 'model': self.chat_model_name, 'message_count': len(hist)})

        if self.memory_tool:
            response = self.client.beta.messages.tool_runner(
                model=self.chat_model_name,
                max_tokens=4096,
                system=self.system_prompt,
                messages=hist,
                tools=self.tools,
                betas=["context-management-2025-06-27"],
            ).until_done()
        else:
            response = self.client.messages.create(
                model=self.chat_model_name,
                max_tokens=4096,
                system=self.system_prompt,
                messages=hist,
                tools=self.tools if self.tools else anthropic.NOT_GIVEN,
            )

        self.log('info', 'chat_api_response', "Anthropic chat response", {'backend': 'anthropic', 'model': self.chat_model_name, 'stop_reason': response.stop_reason})
        return response

    def getCompletion(self, chat_context: str) -> str:
        response = self.getModelResponse(chat_context)
        text_parts = [block.text for block in response.content if block.type == "text"]
        text_content = "\n".join(text_parts)
        text_content = fixLinks(text_content)

        self.log('info', 'chat_usage', "Completion usage", {
            'backend': 'anthropic',
            'prompt_tokens': response.usage.input_tokens,
            'completion_tokens': response.usage.output_tokens,
            'total_tokens': response.usage.input_tokens + response.usage.output_tokens,
        })
        return text_content
