import aiohttp
import discord
import sqlite3
from discord.ext import commands, tasks
from discord.ext.commands import Context
from discord import app_commands

class SteamTools(commands.Cog, name="steamtools"):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="steamid",
        description="Scrape info from a users steam account via their steamID.",
        usage="steamid <steamID>",
        aliases=["sid"]
    )
    @app_commands.describe(
        steamID="The steamID of the user to scrape info from."
    )
    async def steamid(self, context: Context, steamID: str) -> None:
        async with aiohttp.ClientSession() as session:
            async with session.get(f'https://api.snaz.in/v2/steam/user-profile/{steamID}') as r:
                if r.status == 200:
                    data = await r.json()
                    embed = discord.Embed(
                        title=data['username'],
                        url=f"https://steamcommunity.com/id/{data['custom_url']}",
                        description=data['summary']['text'],
                        color=discord.Color.blue()
                    )
                    embed.set_thumbnail(url=data['avatar'])
                    embed.set_image(url=data['background_url'])
                    embed.add_field(name="Bans", value=f"Community: {data['bans']['community']}\nGame: {data['bans']['game']}\nTrade: {data['bans']['trade']}\nVAC: {data['bans']['vac']}", inline=False)
                    embed.add_field(name="Level", value=data['level']['formatted'], inline=True)
                    embed.add_field(name="Member Since", value=data['badge']['meta'], inline=True)
                    friends = data['counts']['friends']['formatted'] if data['counts']['friends'] else 'None/Private'
                    embed.add_field(name="Friends", value=friends, inline=True)
                    embed.add_field(name="Games", value=data['counts']['games']['formatted'], inline=True)
                    embed.add_field(name="Badges", value=data['counts']['badges']['formatted'], inline=True)
                    embed.add_field(name="Artwork", value=data['counts']['artwork']['formatted'], inline=True)
                    embed.add_field(name="Screenshots", value=data['counts']['screenshots']['formatted'], inline=True)
                    embed.add_field(name="Workshop Files", value=data['counts']['workshop_files']['formatted'], inline=True)
                    embed.add_field(name="Primary Group", value=data['primary_group']['name'], inline=True)
                    embed.set_footer(text="Data provided by Snaz API")
                    await context.send(embed=embed)
                else:
                    await context.send('Could not fetch data from Steam API.')

async def setup(bot) -> None:
    await bot.add_cog(SteamTools(bot))