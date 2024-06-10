import json
import logging
import os
import platform
import random
import sys

import aiosqlite
import discord
from discord.ext import commands, tasks
from discord.ext.commands import Context
from dotenv import load_dotenv

from database import DatabaseManager

if not os.path.isfile(f"{os.path.realpath(os.path.dirname(__file__))}/config.json"):
    sys.exit("'config.json' not found! Please add it and try again.")
else:
    with open(f"{os.path.realpath(os.path.dirname(__file__))}/config.json") as file:
        config = json.load(file)

"""	
Setup bot intents (events restrictions)
For more information about intents, please go to the following websites:
https://discordpy.readthedocs.io/en/latest/intents.html
https://discordpy.readthedocs.io/en/latest/intents.html#privileged-intents


Default Intents:
intents.bans = True
intents.dm_messages = True
intents.dm_reactions = True
intents.dm_typing = True
intents.emojis = True
intents.emojis_and_stickers = True
intents.guild_messages = True
intents.guild_reactions = True
intents.guild_scheduled_events = True
intents.guild_typing = True
intents.guilds = True
intents.integrations = True
intents.invites = True
intents.messages = True # `message_content` is required to get the content of the messages
intents.reactions = True
intents.typing = True
intents.voice_states = True
intents.webhooks = True

Privileged Intents (Needs to be enabled on developer portal of Discord), please use them only if you need them:
intents.members = True
intents.message_content = True
intents.presences = True
"""

intents = discord.Intents.default()

"""
Uncomment this if you want to use prefix (normal) commands.
It is recommended to use slash commands and therefore not use prefix commands.

If you want to use prefix commands, make sure to also enable the intent below in the Discord developer portal.
"""
intents.members = True
intents.message_content = True
intents.presences = True

DATABASE_DIR = "database"
ABS_PATH = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(DATABASE_DIR, "database.db")


# Setup both of the loggers
class LoggingFormatter(logging.Formatter):
    # Colors
    black = "\x1b[30m"
    red = "\x1b[31m"
    green = "\x1b[32m"
    yellow = "\x1b[33m"
    blue = "\x1b[34m"
    gray = "\x1b[38m"
    # Styles
    reset = "\x1b[0m"
    bold = "\x1b[1m"

    COLORS = {
        logging.DEBUG: gray + bold,
        logging.INFO: blue + bold,
        logging.WARNING: yellow + bold,
        logging.ERROR: red,
        logging.CRITICAL: red + bold,
    }

    def format(self, record):
        log_color = self.COLORS[record.levelno]
        format = "(black){asctime}(reset) (levelcolor){levelname:<8}(reset) (green){name}(reset) {message}"
        format = format.replace("(black)", self.black + self.bold)
        format = format.replace("(reset)", self.reset)
        format = format.replace("(levelcolor)", log_color)
        format = format.replace("(green)", self.green + self.bold)
        formatter = logging.Formatter(format, "%Y-%m-%d %H:%M:%S", style="{")
        return formatter.format(record)


logger = logging.getLogger("discord_bot")
logger.setLevel(logging.INFO)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(LoggingFormatter())
# File handler
file_handler = logging.FileHandler(filename="discord.log", encoding="utf-8", mode="w")
file_handler_formatter = logging.Formatter(
    "[{asctime}] [{levelname:<8}] {name}: {message}", "%Y-%m-%d %H:%M:%S", style="{"
)
file_handler.setFormatter(file_handler_formatter)

# Add the handlers
logger.addHandler(console_handler)
logger.addHandler(file_handler)


class DiscordBot(commands.Bot):
    def __init__(self) -> None:
        self.status_message = None

        async def get_prefix(bot, message: discord.Message) -> list[str]:
            async with aiosqlite.connect(DB_PATH) as db:
                async with db.cursor() as cursor:
                    guild_id = message.guild.id if message.guild else None
                    if isinstance(guild_id, int) or guild_id is None:
                        prefix = await self.guild_prefix(guild_id)
                        return commands.when_mentioned_or(prefix)(bot, message)
                    else:
                        raise TypeError(f"guild_id should be of type int or None, not {type(guild_id)}")

        super().__init__(
            command_prefix=get_prefix,
            intents=intents,
            help_command=None,
        )
        self.logger = logger
        self.config = config
        self.database = None
        self.wavelink = None

    async def guild_prefix(self, guild_id, prefix=None):
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.cursor() as cursor:
                if prefix is not None:
                    # Write to the table
                    await cursor.execute("INSERT INTO GuildPrefix (guild_id, prefix) VALUES (?, ?)", (guild_id, prefix))
                    await db.commit()
                else:
                    # Read from the table
                    await cursor.execute("SELECT prefix FROM GuildPrefix WHERE guild_id = ?", (guild_id,))
                    row = await cursor.fetchone()
                    return row[0] if row else None

    async def guild_autoroles(self, guild_id, role_id=None):
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.cursor() as cursor:
                if role_id is not None:
                    # Write to the table
                    await cursor.execute("INSERT INTO GuildAutoroles (guild_id, role_id) VALUES (?, ?)",
                                         (guild_id, role_id))
                    await db.commit()
                else:
                    # Read from the table
                    await cursor.execute("SELECT role_id FROM GuildAutoroles WHERE guild_id = ?", (guild_id,))
                    row = await cursor.fetchone()
                    return row[0] if row else None

    async def init_db(self) -> None:
        async with aiosqlite.connect(
                f"{os.path.realpath(os.path.dirname(__file__))}/database/database.db"
        ) as db:
            with open(
                    f"{os.path.realpath(os.path.dirname(__file__))}/database/schema.sql"
            ) as file:
                await db.executescript(file.read())
            await db.commit()

    async def load_cogs(self) -> None:
        """
        The code in this function is executed whenever the bot will start.
        """
        for file in os.listdir(f"{os.path.realpath(os.path.dirname(__file__))}/cogs"):
            if file.endswith(".py"):
                extension = file[:-3]
                try:
                    await self.load_extension(f"cogs.{extension}")
                    self.logger.info(f"Loaded extension '{extension}'")
                except Exception as e:
                    exception = f"{type(e).__name__}: {e}"
                    self.logger.error(
                        f"Failed to load extension {extension}\n{exception}"
                    )

    @tasks.loop(minutes=5.0)
    async def status_task(self) -> None:
        """
        Set up the game status task of the bot.
        """
        if os.getenv("IS_DEV_CONTAINER") == "True":
            statuses = ["Reading discord.py docs...", "VSCode! (not good help me)", "Coding and Crying :)",
                        "DEV MODE = [ON] >B)", "Something is probably broken rn", "Don't expect me to work rn! :D",
                        "Thanks GitHub Copilot <3", "LLM's took my job."]
        else:
            statuses = ["with knives rn", "Counter-Strike 2", "with firearms.", "Vote for me on top.gg!",
                        "You should gamble...", "Lunar Client (ew)", "He actually remembered...",
                        "League of Leg... Nope nvm.", "Minecraft 2", "Grand Theft Auto 7", "Half-Life 2.9 D:",
                        "That fucking dota card game lmao", "Overwatch 1 season 3 (good times)",
                        "0x6c75 smells really bad.", "add @iconize for free v-bucks :3"]
        await self.change_presence(activity=discord.Game(random.choice(statuses)))
        # channel = self.get_channel(1240624554544726037)
        # random_message = random.choice(
        #     ["Meine Wurstnudel tut weh! Bitte, oh bitte reiben Sie sie!", "Ich bin ein kleiner, dummer Bot!", "Gott, du riechst so gut......", "Ich mag es, wie du mich benutzt, um deine Ersparnisse zu verspielen. Das macht mich wirklich an.", "Du solltest wetten :)", "BLACKJACK JETZT SPIELEN", "Ich hoffe wirklich, dass Sie von einer hohen Klippe fallen."]
        # )
        # await channel.send(random_message)

    @status_task.before_loop
    async def before_status_task(self) -> None:
        """
        Before starting the status changing task, we make sure the bot is ready
        """
        await self.wait_until_ready()

    async def setup_hook(self) -> None:
        """
        This will just be executed when the bot starts the first time.
        """
        self.logger.info(f"Logged in as {self.user.name}")
        self.logger.info(f"discord.py API version: {discord.__version__}")
        self.logger.info(f"Python version: {platform.python_version()}")
        self.logger.info(
            f"Running on: {platform.system()} {platform.release()} ({os.name})"
        )
        self.logger.info("-------------------")
        await self.init_db()
        await self.load_cogs()
        self.status_task.start()
        self.database = DatabaseManager(
            connection=await aiosqlite.connect(
                f"{os.path.realpath(os.path.dirname(__file__))}/database/database.db"
            )
        )

    async def on_ready(self):
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.cursor() as cursor:
                for guild in self.guilds:
                    guild_id = guild.id
                    prefix = await self.guild_prefix(guild_id)
                    if prefix is None:
                        await self.guild_prefix(guild_id, '>')
                        self.logger.error(f"Prefix for guild {guild.id} is not set, setting it to default prefix '>'")

        self.wavelink = await self.wavelink.initiate_node(
            host='lavalink',
            port=2333,
            password='youshallnotpass',
            identifier='MAIN',
            region='us_central'
        )

    async def on_message(self, message: discord.Message) -> None:
        """
        The code in this event is executed every time someone sends a message, with or without the prefix

        :param message: The message that was sent.
        """
        if message.author == self.user or message.author.bot:
            return
        await self.process_commands(message)

    async def on_command_completion(self, context: Context) -> None:
        """
        The code in this event is executed every time a normal command has been *successfully* executed.

        :param context: The context of the command that has been executed.
        """
        full_command_name = context.command.qualified_name
        split = full_command_name.split(" ")
        executed_command = str(split[0])
        if context.guild is not None:
            self.logger.info(
                f"Executed {executed_command} command in {context.guild.name} (ID: {context.guild.id}) (ChannelID: {context.channel.id}) by {context.author} (ID: {context.author.id})"
            )
        else:
            self.logger.info(
                f"Executed {executed_command} command by {context.author} (ID: {context.author.id}) in DMs"
            )
        try:
            await context.message.delete()
        except discord.NotFound:
            pass

    async def on_command_error(self, context: Context, error) -> None:
        """
        The code in this event is executed every time a normal valid command catches an error.

        :param context: The context of the normal command that failed executing.
        :param error: The error that has been faced.
        """
        if isinstance(error, commands.CommandOnCooldown):
            minutes, seconds = divmod(error.retry_after, 60)
            hours, minutes = divmod(minutes, 60)
            hours = hours % 24
            embed = discord.Embed(
                description=f"**Please slow down** - You can use this command again in {f'{round(hours)} hours' if round(hours) > 0 else ''} {f'{round(minutes)} minutes' if round(minutes) > 0 else ''} {f'{round(seconds)} seconds' if round(seconds) > 0 else ''}.",
                color=0xE02B2B,
            )
            await context.send(embed=embed)
            await context.message.delete()
        elif isinstance(error, commands.NotOwner):
            embed = discord.Embed(
                description="You are not the owner of the bot!", color=0xE02B2B
            )
            await context.send(embed=embed)
            await context.message.delete()
            if context.guild:
                self.logger.warning(
                    f"{context.author} (ID: {context.author.id}) tried to execute an owner only command in the guild {context.guild.name} (ID: {context.guild.id}), but the user is not an owner of the bot."
                )
            else:
                self.logger.warning(
                    f"{context.author} (ID: {context.author.id}) tried to execute an owner only command in the bot's DMs, but the user is not an owner of the bot."
                )
        elif isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(
                description="You are missing the permission(s) `"
                            + ", ".join(error.missing_permissions)
                            + "` to execute this command!",
                color=0xE02B2B,
            )
            await context.send(embed=embed)
            await context.message.delete()
        elif isinstance(error, commands.BotMissingPermissions):
            embed = discord.Embed(
                description="I am missing the permission(s) `"
                            + ", ".join(error.missing_permissions)
                            + "` to fully perform this command!",
                color=0xE02B2B,
            )
            await context.send(embed=embed)
            await context.message.delete()
        elif isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(
                title="Error!",
                # We need to capitalize because the command arguments have no capital letter in the code and they are the first word in the error message.
                description=str(error).capitalize(),
                color=0xE02B2B,
            )
            await context.send(embed=embed)
            await context.message.delete()
        elif isinstance(error, commands.CommandInvokeError) and isinstance(error.original, AttributeError) and \
                error.original.args[0] == "'NoneType' object has no attribute 'mention'":
            embed = discord.Embed(
                title="Error!",
                description="You need to mention a user!",
                color=0xE02B2B,
            )
            await context.send(embed=embed)
            await context.message.delete()
        elif isinstance(error, commands.CommandNotFound):
            embed = discord.Embed(
                title="Error!",
                description="Command not found!",
                color=0xE02B2B,
            )
            embed.add_field(name="Failed Command: ", value=f"`{context.message.content}`", inline=False)
            embed.add_field(name="Hint",
                            value="Use `help` to see all available categories. Use `help <category>` to see all commands in a category.",
                            inline=False)
            await context.send(embed=embed)
            await context.message.delete()
            raise (error)
        else:
            raise error


load_dotenv()

bot = DiscordBot()
bot.run(os.getenv("TOKEN"))
