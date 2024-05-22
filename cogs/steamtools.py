import aiohttp
import discord
import sqlite3
from discord.ext import commands, tasks
from discord.ext.commands import Context
from discord import app_commands

class SteamTools(commands.Cog, name="steamtools"):
    def __init__(self, bot):
        self.bot = bot

async def setup(bot) -> None:
    await bot.add_cog(SteamTools(bot))