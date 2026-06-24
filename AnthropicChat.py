import logging
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
import anthropic
from chat import ChatAssistant, fixLinks
from memory_tool import LocalMemoryTool

TOOL_LOOP_TIMEOUT = 120  # seconds
CACHE_DIAGNOSTICS_BETA = "cache-diagnosis-2026-04-07"

class AnthropicChatAssistant(ChatAssistant):
    def __init__(
        self,
        chat_model_name: str,
        bot_id: str,
        key: str,
        log_func: callable = None,
        system_prompt: str = None,
        enable_web_search: bool = True,
        enable_memory: bool = True,
    ):
        super().__init__(
            chat_model_name=chat_model_name,
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
        self.memory_tool = LocalMemoryTool(log_func=log_func) if enable_memory else None
        if self.memory_tool:
            self.tools.append(self.memory_tool)
        self._prev_message_id = None  # last response id, for cache diagnostics

    def setChatModel(self, model_name: str) -> bool:
        self.chat_model_name = model_name
        self.log('info', 'model_changed', "Chat model changed", {'model': model_name, 'model_type': 'chat'})
        return True

    def makeConversationHistory(self, chat_context: list[dict]) -> list[dict]:
        return chat_context

    def getModelResponse(self, chat_context: list[dict]):
        hist = self.makeConversationHistory(chat_context)
        self.log('info', 'chat_api_request', "Anthropic chat request", {'backend': 'anthropic', 'model': self.chat_model_name, 'message_count': len(hist), 'messages': hist})
        sent_prev_message_id = self._prev_message_id  # captured before this call overwrites it

        is_adaptive = "4-7" in self.chat_model_name or "4.7" in self.chat_model_name
        if is_adaptive:
            thinking_config = {"type": "adaptive"}
            extra_kwargs = {"output_config": {"effort": "high"}}
        else:
            thinking_config = {"type": "enabled", "budget_tokens": 12_000}
            extra_kwargs = {}

        if self.memory_tool:
            self.memory_tool.set_context(hist)
            runner = self.client.beta.messages.tool_runner(
                model=self.chat_model_name,
                max_tokens=16_000,
                system=self._build_system_prompt(),
                messages=hist,
                tools=self.tools,
                thinking=thinking_config,
                cache_control={"type": "ephemeral", "ttl": "1h"},  # auto-caches last cacheable block, moves forward each turn
                diagnostics={"previous_message_id": self._prev_message_id},
                betas=["context-management-2025-06-27", CACHE_DIAGNOSTICS_BETA],
                **extra_kwargs,
            )
            start_time = time.time()
            self.log('info', 'tool_runner_started', "Tool runner started", {'timeout': TOOL_LOOP_TIMEOUT})

            def collect_all_turns():
                all_text = []
                all_thinking = []
                last_msg = None
                for message in runner:
                    for block in message.content:
                        if block.type == "thinking":
                            all_thinking.append(block.thinking)
                        elif block.type == "text" and block.text.strip():
                            all_text.append(block.text)
                    last_msg = message
                return last_msg, all_text, all_thinking

            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(collect_all_turns)
                try:
                    response, all_text_parts, all_thinking_parts = future.result(timeout=TOOL_LOOP_TIMEOUT)
                except FuturesTimeoutError:
                    elapsed = time.time() - start_time
                    self.log('error', 'chat_timeout', "Tool runner timed out", {'timeout': TOOL_LOOP_TIMEOUT, 'elapsed': round(elapsed, 2)})
                    raise TimeoutError(f"Tool runner timed out after {elapsed:.1f}s")
            elapsed = time.time() - start_time
            self.log('info', 'tool_runner_done', "Tool runner completed", {'elapsed': round(elapsed, 2)})
        else:
            response = self.client.beta.messages.create(
                model=self.chat_model_name,
                max_tokens=16_000,
                system=self._build_system_prompt(),
                messages=hist,
                tools=self.tools if self.tools else anthropic.NOT_GIVEN,
                thinking=thinking_config,
                cache_control={"type": "ephemeral", "ttl": "1h"},  # auto-caches last cacheable block
                diagnostics={"previous_message_id": self._prev_message_id},
                betas=[CACHE_DIAGNOSTICS_BETA],
                timeout=TOOL_LOOP_TIMEOUT,
                **extra_kwargs,
            )
            all_text_parts = [block.text for block in response.content if block.type == "text"]
            all_thinking_parts = [block.thinking for block in response.content if block.type == "thinking"]

        content_types = [block.type for block in response.content]
        has_web_search = any(t in ('server_tool_use', 'web_search_tool_result') for t in content_types)
        self.log('info', 'chat_api_response', "Anthropic chat response", {
            'backend': 'anthropic',
            'model': self.chat_model_name,
            'stop_reason': response.stop_reason,
            'content_block_types': content_types,
            'has_text': bool(all_text_parts),
            'has_web_search': has_web_search,
            'messages': hist,
            'text': all_text_parts,
        })
        if all_thinking_parts:
            self.log('info', 'chat_reasoning', "Model reasoning", {'backend': 'anthropic', 'reasoning': all_thinking_parts})
        if has_web_search:
            self.log('info', 'web_search_used', "Web search was used in response")

        diagnostics = response.diagnostics
        cache_missed_input_tokens = None
        if sent_prev_message_id is None:
            cache_diagnostics_state = "first_turn"
        elif diagnostics is None:
            cache_diagnostics_state = "no_divergence"
        elif diagnostics.cache_miss_reason is None:
            cache_diagnostics_state = "pending"
        else:
            cache_diagnostics_state = diagnostics.cache_miss_reason.type
            cache_missed_input_tokens = getattr(diagnostics.cache_miss_reason, 'cache_missed_input_tokens', None)
        self._prev_message_id = response.id

        cache_diagnostics = {
            'cache_diagnostics_state': cache_diagnostics_state,
            'cache_missed_input_tokens': cache_missed_input_tokens,
        }
        return response, all_text_parts, cache_diagnostics

    def getCompletion(self, chat_context: list[dict]) -> str:
        response, text_parts, cache_diagnostics = self.getModelResponse(chat_context)
        text_content = "".join(text_parts)

        if not text_content.strip():
            self.log('warning', 'chat_empty_response', "Response contained no text content", {
                'stop_reason': response.stop_reason,
                'content_block_types': [block.type for block in response.content],
            })
            text_content = "(I processed your request but generated no text response)"

        text_content = fixLinks(text_content)

        self.log('info', 'chat_usage', "Completion usage", {
            'backend': 'anthropic',
            'prompt_tokens': response.usage.input_tokens,
            'completion_tokens': response.usage.output_tokens,
            'total_tokens': response.usage.input_tokens + response.usage.output_tokens,
            'cache_creation_tokens': response.usage.cache_creation_input_tokens,
            'cache_read_tokens': response.usage.cache_read_input_tokens,
            **cache_diagnostics,
        })
        return text_content
