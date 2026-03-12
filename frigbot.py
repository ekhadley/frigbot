import os
import io
import random
import datetime
import base64
import json
import asyncio
import logging

import discord
from discord import app_commands
import requests

from lolManager import lolManager
from chat import ChatAssistant, generate_image
from AnthropicChat import AnthropicChatAssistant
from utils import contains_scrambled, TIER_COLORS


class FrigBot:
    OLD_BOT_ID = "352226045228875786"

    def __init__(self, channel_id: int, guild_id: int | None = None, state_dict_path: str | None = None):
        self.logger = logging.getLogger('frigbot')
        self.channel_id = channel_id
        self.guild_id = guild_id
        self.state_dict_path = state_dict_path
        self.start_time = datetime.datetime.now()
        self.max_message_length = 2000

        intents = discord.Intents.default()
        intents.message_content = True
        self.bot = discord.Client(intents=intents)
        self.tree = app_commands.CommandTree(self.bot)

        self.openrouter_key = os.environ['OPENROUTER_API_KEY']
        self.current_chat_model = "openai/gpt-5"
        self.current_image_model = "openai/gpt-image-1"
        self.asst = None  # initialized in on_ready when bot ID is known

        self.rps_scores = {}
        self.lol = lolManager(
            os.environ['RIOT_API_KEY'],
            "/home/ek/wgmn/frigbot/data/summonerPUUIDs.json",
            self.log,
        )

        self._register_events()
        self._register_commands()

    def log(self, level: str, event_type: str, message: str, data: dict = None):
        if data is None:
            data = {}
        data['event_type'] = event_type
        extra = {'data': data}
        getattr(self.logger, level, self.logger.info)(message, extra=extra)

    def _init_assistant(self):
        bot_id = str(self.bot.user.id)
        is_anthropic = "claude" in self.current_chat_model.lower()
        if is_anthropic:
            self.asst = AnthropicChatAssistant(
                chat_model_name=self.current_chat_model,
                bot_id=bot_id,
                key=os.environ['ANTHROPIC_API_KEY'],
                log_func=self.log,
                enable_web_search=True,
                enable_memory=True,
            )
        else:
            self.asst = ChatAssistant(
                chat_model_name=self.current_chat_model,
                bot_id=bot_id,
                key=self.openrouter_key,
                log_func=self.log,
                enable_web_search=False,
            )

    def _msg_to_dict(self, msg: discord.Message) -> dict:
        """Convert discord.Message to the dict format chat.py expects."""
        author_id = str(msg.author.id)
        if author_id == self.OLD_BOT_ID:
            author_id = str(self.bot.user.id)

        ref = None
        if msg.reference and isinstance(msg.reference.resolved, discord.Message):
            ref = {
                'author': {
                    'id': str(msg.reference.resolved.author.id),
                    'global_name': msg.reference.resolved.author.display_name,
                },
                'content': msg.reference.resolved.content,
            }

        return {
            'id': str(msg.id),
            'content': msg.content,
            'author': {
                'id': author_id,
                'global_name': msg.author.display_name,
            },
            'mentions': [
                {'id': str(u.id), 'global_name': u.display_name}
                for u in msg.mentions
            ],
            'referenced_message': ref,
        }

    def _register_events(self):
        @self.bot.event
        async def on_ready():
            self.log('info', 'bot_started', "FrigBot online", {
                'user': str(self.bot.user),
                'channel_id': self.channel_id,
            })
            if self.asst is None:
                self._init_assistant()
                guild = discord.Object(id=self.guild_id) if self.guild_id else None
                if guild:
                    self.tree.copy_global_to(guild=guild)
                await self.tree.sync(guild=guild)
                self.log('info', 'commands_synced', "Slash commands synced", {'guild_id': self.guild_id})

        @self.bot.event
        async def on_message(message: discord.Message):
            if message.author.bot or message.channel.id != self.channel_id:
                return

            self.log('info', 'new_message', "New message received", {
                'author': message.author.display_name,
                'content': message.content,
            })

            is_reply = (
                message.reference
                and isinstance(message.reference.resolved, discord.Message)
                and message.reference.resolved.author == self.bot.user
            )
            is_mention = self.bot.user.mentioned_in(message)

            if is_reply or is_mention:
                self.log('info', 'chat_requested', "Chat completion requested", {
                    'trigger': 'reply' if is_reply else 'mention',
                })
                history = [m async for m in message.channel.history(limit=100)]
                msgs = [self._msg_to_dict(m) for m in history]
                chat_context = self.asst.makeContext(msgs)

                async with message.channel.typing():
                    try:
                        completion = await asyncio.to_thread(self.asst.getCompletion, chat_context)
                    except Exception as e:
                        self.log('error', 'chat_failed', "Chat completion failed", {'error': str(e)})
                        self.logger.exception("Chat completion exception details")
                        status = getattr(e, 'status_code', None) or type(e).__name__
                        await message.reply(f"error: {status}")
                        return

                parts = completion.replace("\n\n", "\n").strip().split("<split>")
                final_parts = []
                for part in parts:
                    while len(part) > self.max_message_length:
                        final_parts.append(part[:self.max_message_length])
                        part = part[self.max_message_length:]
                    final_parts.append(part)

                await message.reply(final_parts[0])
                for part in final_parts[1:]:
                    await message.channel.send(part)
                self.log('info', 'chat_completed', "Chat completion sent")
                return

            if random.random() > 0.9 and contains_scrambled(message.content, "itysl"):
                gif = await asyncio.to_thread(self._random_gif, "itysl", 500)
                await message.channel.send(gif)

    def _register_commands(self):
        @self.tree.interaction_check
        async def check_channel(interaction: discord.Interaction) -> bool:
            if interaction.channel_id != self.channel_id:
                await interaction.response.send_message("Wrong channel.", ephemeral=True)
                return False
            return True

        @self.tree.command(name="help", description="List all commands")
        async def help_cmd(interaction: discord.Interaction):
            lines = [
                "`/help` — List all commands",
                "`/model` — Show current chat and image model",
                "`/setmodel` — Set the chat model",
                "`/setimgmodel` — Set the image model",
                "`/img` — Generate an image",
                "`/rps` — Play rock-paper-scissors",
                "`/gif` — Search for a random GIF",
                "`/roll` — Roll a random number",
                "`/lp` — Look up ranked League info",
                "`/piggies` — Ranked info for the whole group",
                "`/coin` — Flip a coin",
                "`/uptime` — Bot uptime",
                "`/poem` — The poem",
            ]
            await interaction.response.send_message("\n".join(lines), ephemeral=True)

        @self.tree.command(name="model", description="Show current chat and image model")
        async def model_cmd(interaction: discord.Interaction):
            await interaction.response.send_message(
                f"chat model: {self.current_chat_model}, image model: {self.current_image_model}"
            )

        @self.tree.command(name="setmodel", description="Set the chat model")
        async def setmodel_cmd(interaction: discord.Interaction, model: str):
            await interaction.response.defer()
            result = await asyncio.to_thread(self._set_chat_model, model)
            await interaction.followup.send(result)

        @self.tree.command(name="setimgmodel", description="Set the image model")
        async def setimgmodel_cmd(interaction: discord.Interaction, model: str):
            await interaction.response.defer()
            result = await asyncio.to_thread(self._set_image_model, model)
            await interaction.followup.send(result)

        @self.tree.command(name="img", description="Generate an image")
        async def img_cmd(interaction: discord.Interaction, prompt: str):
            await interaction.response.defer()
            try:
                resp = await asyncio.to_thread(
                    generate_image, prompt, self.current_image_model, self.openrouter_key, self.log
                )
                message_data = resp["choices"][0]["message"]
                if "images" in message_data:
                    for img in message_data["images"]:
                        img_b64 = img["image_url"]["url"].split(",")[1]
                        img_bytes = base64.b64decode(img_b64)
                        file = discord.File(io.BytesIO(img_bytes), filename="output.png")
                        await interaction.followup.send(prompt, file=file)
                else:
                    await interaction.followup.send(message_data['content'])
            except Exception as e:
                self.log('error', 'image_failed', "Image generation failed", {'error': str(e)})
                await interaction.followup.send(f"image generation failed: {e}")

        @self.tree.command(name="rps", description="Play rock-paper-scissors")
        @app_commands.choices(choice=[
            app_commands.Choice(name="Rock", value="rock"),
            app_commands.Choice(name="Paper", value="paper"),
            app_commands.Choice(name="Scissors", value="scissors"),
        ])
        async def rps_cmd(interaction: discord.Interaction, choice: app_commands.Choice[str] | None = None):
            uid = str(interaction.user.id)
            win_key, draw_key, loss_key = f"{uid}_w", f"{uid}_d", f"{uid}_l"

            if win_key not in self.rps_scores:
                self.log('info', 'rps_new_player', "New RPS player", {'user_id': uid})
                self.rps_scores[win_key] = 0
                self.rps_scores[draw_key] = 0
                self.rps_scores[loss_key] = 0

            if choice is None:
                await interaction.response.send_message(
                    f"Your score is {self.rps_scores[win_key]}/{self.rps_scores[draw_key]}/{self.rps_scores[loss_key]}"
                )
                return

            opts = ["rock", "paper", "scissors"]
            roll = opts.index(choice.value)
            botroll = random.randint(0, 2)

            if roll == botroll:
                report = f"We both chose {opts[botroll]}"
                self.rps_scores[draw_key] += 1
            elif (roll + 2) % 3 == botroll:
                report = f"I chose {opts[botroll]}. W"
                self.rps_scores[win_key] += 1
            else:
                report = f"I chose {opts[botroll]}. L"
                self.rps_scores[loss_key] += 1

            self.log('debug', 'rps_played', "RPS game played", {
                'user_id': uid, 'user_choice': choice.value, 'bot_choice': opts[botroll],
            })
            self.save_state()
            update = f"Your score is now {self.rps_scores[win_key]}/{self.rps_scores[draw_key]}/{self.rps_scores[loss_key]}"
            await interaction.response.send_message(f"{report}\n{update}")

        @self.tree.command(name="gif", description="Search for a random GIF")
        async def gif_cmd(interaction: discord.Interaction, query: str):
            await interaction.response.defer()
            gif = await asyncio.to_thread(self._random_gif, query)
            await interaction.followup.send(gif)

        @self.tree.command(name="roll", description="Roll a random number from 1 to max")
        async def roll_cmd(interaction: discord.Interaction, max: app_commands.Range[int, 1]):
            await interaction.response.send_message(str(random.randint(1, max)))

        @self.tree.command(name="lp", description="Look up ranked League info for a summoner")
        async def lp_cmd(interaction: discord.Interaction, summoner: str):
            await interaction.response.defer()
            result = await asyncio.to_thread(self._lp_embed, summoner.lower())
            if isinstance(result, str):
                await interaction.followup.send(result)
            else:
                await interaction.followup.send(embed=result)

        @self.tree.command(name="piggies", description="Ranked info for the whole group")
        async def piggies_cmd(interaction: discord.Interaction):
            await interaction.response.defer()
            embed = await asyncio.to_thread(self._piggies_embed)
            await interaction.followup.send(embed=embed)

        @self.tree.command(name="coin", description="Flip a coin")
        async def coin_cmd(interaction: discord.Interaction):
            await interaction.response.send_message(random.choice(["heads", "tails"]))

        @self.tree.command(name="uptime", description="Show bot uptime")
        async def uptime_cmd(interaction: discord.Interaction):
            delta = datetime.datetime.now() - self.start_time
            await interaction.response.send_message(
                f"uptime: {delta.days}d {delta.seconds // 3600}h {(delta.seconds % 3600) // 60}m {delta.seconds % 60}s"
            )

        @self.tree.command(name="poem", description="The poem")
        async def poem_cmd(interaction: discord.Interaction):
            lines = [
                "Do not go gentle into that good juckyard.",
                "Tetus should burn and rave at close of day.",
                "Rage, rage against the dying of the gamings.",
                "Though wise men at their end know gaming is right,",
                "Becuase their plays had got no karma they",
                "Do not go gentle into that good juckyard",
            ]
            await interaction.response.send_message("\n".join(lines))

    # --- Sync helpers (called via asyncio.to_thread) ---

    def _set_chat_model(self, model_name: str) -> str:
        is_anthropic = "claude" in model_name.lower()
        needs_swap = is_anthropic != isinstance(self.asst, AnthropicChatAssistant)
        bot_id = str(self.bot.user.id)

        if needs_swap:
            if is_anthropic:
                self.asst = AnthropicChatAssistant(
                    chat_model_name=model_name,
                    bot_id=bot_id,
                    key=os.environ['ANTHROPIC_API_KEY'],
                    log_func=self.log,
                    enable_web_search=True,
                    enable_memory=True,
                )
            else:
                self.asst = ChatAssistant(
                    chat_model_name=model_name,
                    bot_id=bot_id,
                    key=self.openrouter_key,
                    log_func=self.log,
                    enable_web_search=False,
                )
            self.current_chat_model = model_name
            self.log('info', 'model_changed', "Chat model changed (backend swap)", {
                'model': model_name, 'backend': 'anthropic' if is_anthropic else 'openrouter',
            })
            self.save_state()
            return f"chat model set to {model_name} ({'anthropic' if is_anthropic else 'openrouter'})"

        if self.asst.setChatModel(model_name):
            self.current_chat_model = model_name
            self.log('info', 'model_changed', "Chat model changed", {'model': model_name})
            self.save_state()
            return f"chat model set to {model_name}"
        self.log('warning', 'model_error', "Chat model not found", {'model': model_name})
        return f"no model found for {model_name} [Available chat models](<{self.asst.available_chat_models_link}>)"

    def _set_image_model(self, model_name: str) -> str:
        models = self.asst.getAvailableModels()
        for model in models["data"]:
            if model_name.strip() == model["id"].strip():
                if "image" in model["architecture"]["output_modalities"]:
                    self.current_image_model = model_name
                    self.log('info', 'model_changed', "Image model changed", {'model': model_name})
                    self.save_state()
                    return f"image model set to {model_name}"
        self.log('warning', 'model_error', "Image model not found", {'model': model_name})
        return f"no image-capable model found for {model_name} [Available image models](<{self.asst.available_image_models_link}>)"

    def _random_gif(self, query: str, num: int = 100) -> str:
        url = f"https://g.tenor.com/v2/search?q={query}&key={os.environ['TENOR_API_KEY']}&limit={num}"
        r = requests.get(url)
        urls = [g["url"] for g in r.json()["results"]]
        return random.choice(urls)

    def _lp_embed(self, name: str):
        info = self.lol.get_ranked_info(name)
        if isinstance(info, str):
            return info
        if not info:
            if "dragondude" in name.lower():
                return "ap is still a bitch (not on the ranked grind)"
            return f"{name} is not on the ranked grind"
        if 'RANKED_SOLO_5x5' not in info:
            return f"{name} has no solo queue data"

        data = info['RANKED_SOLO_5x5']
        lp = data["leaguePoints"]
        wins = int(data["wins"])
        losses = int(data["losses"])
        wr = wins / (wins + losses)
        tier = data["tier"]
        div = data["rank"]

        return discord.Embed(
            title=name,
            description=f"{tier.capitalize()} {div} — {lp} LP\n{wr:.3f} WR over {wins + losses} games",
            color=TIER_COLORS.get(tier, 0x808080),
        )

    def _piggies_embed(self):
        sumnames = ["eekay", "xylotile", "dragondude", "maestrofluff", "smolyoshi"]
        rev = {v: k for k, v in self.lol.summoner_puuids.items()}
        tier_order = {'IRON': 0, 'BRONZE': 1, 'SILVER': 2, 'GOLD': 3, 'PLATINUM': 4, 'EMERALD': 5, 'DIAMOND': 6, 'MASTER': 7, 'GRANDMASTER': 8, 'CHALLENGER': 9}
        rank_order = {'IV': 0, 'III': 1, 'II': 2, 'I': 3}

        full_infos = [self.lol.get_ranked_info(name) for name in sumnames]
        infos = [
            info["RANKED_SOLO_5x5"]
            for info in full_infos
            if info and not isinstance(info, str) and "RANKED_SOLO_5x5" in info
        ]
        infos.sort(
            key=lambda x: tier_order[x['tier']] * 1000 + rank_order[x['rank']] * 100 + x['leaguePoints'],
            reverse=True,
        )

        embed = discord.Embed(title="Ranked Solo Queue", color=0xFFD700)
        for info in infos:
            name = rev[info['puuid']]
            tier = info['tier']
            div = info['rank']
            lp = info['leaguePoints']
            wins, losses = info['wins'], info['losses']
            wr = wins / (wins + losses)
            embed.add_field(
                name=name,
                value=f"{tier.capitalize()} {div} — {lp} LP\n{wr:.3f} WR ({wins + losses} games)",
                inline=False,
            )
        return embed

    # --- State ---

    def state_dict(self):
        return {
            "current_chat_model": self.current_chat_model,
            "current_image_model": self.current_image_model,
            "rps_scores": self.rps_scores,
            "start_time": self.start_time.isoformat(),
            "save_time": datetime.datetime.now().isoformat(),
        }

    def save_state(self):
        if not self.state_dict_path:
            return
        self.log('debug', 'state_saved', "State saved", {'file': self.state_dict_path})
        with open(self.state_dict_path, "w") as f:
            json.dump(self.state_dict(), f, indent=2)

    def load_state(self):
        if not self.state_dict_path or not os.path.exists(self.state_dict_path):
            return
        with open(self.state_dict_path) as f:
            saved = json.load(f)
        self.rps_scores = saved.get("rps_scores", {})
        self.current_chat_model = saved.get("current_chat_model", self.current_chat_model)
        self.current_image_model = saved.get("current_image_model", self.current_image_model)
        self.log('info', 'state_loaded', "State loaded", {'file': self.state_dict_path})

    def run(self):
        self.bot.run(os.environ['DISCORD_TOKEN'], log_handler=None)
