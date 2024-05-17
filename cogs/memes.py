from discord.ext import commands
from discord.ext.commands import Context
import aiohttp
import discord
import json
import random


# Here we name the cog and create a new class for the cog.
class Memes(commands.Cog, name="memes"):
    def __init__(self, bot) -> None:
        self.bot = bot

    # Here you can just add your own commands, you'll always need to provide "self" as first parameter.

    @commands.hybrid_command(
        name="memerandom",
        description="Grabs a random meme from meme-api.com",
        aliases=["mr"],
        usage="memerandom"
    )
    async def memerandom(self, context: Context) -> None:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://meme-api.com/gimme/" + str(random.randint(1, 1000))
            ) as request:
                print(request.status)
                if request.status == 200:
                    data = await request.json()
                    embed = discord.Embed(title="testing", color=0xD75BF4)
                    embed.set_image(url=data["url"])
                    await context.send(embed=embed)

                else:
                    embed = discord.Embed(
                        title="Error!",
                        description="There is something wrong with the API, please try again later",
                        color=0xE02B2B,
                    )
                await context.send(embed=embed)


# And then we finally add the cog to the bot so that it can load, unload, reload and use it's content.
async def setup(bot) -> None:
    await bot.add_cog(Memes(bot))

