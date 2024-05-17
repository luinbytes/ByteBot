from discord.ext import commands
from discord.ext.commands import Context
import discord
import aiohttp

class Images(commands.Cog, name="images"):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.hybrid_command(
        name="cat",
        description="Spawns a random cat! Big thanks to The Cat API!",
        usage="cat",
        aliases=["kitty", "car"]
    )
    async def cat(self, context: Context) -> None:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://api.thecatapi.com/v1/images/search"
            ) as request:
                print(request.status)
                if request.status == 200:
                    data = await request.json()
                    url = data[0]["url"]
                    id = data[0]["id"]
                    embed = discord.Embed(title="Random Cat!", color=0xD75BF4)
                    embed.set_image(url=url)
                    embed.add_field(name="Cat ID", value="```" + str(id) + "```", inline=False)
                    embed.add_field(name="Thanks to The Cat API!", value=f"[Open in browser]({url})", inline=False)
                    embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)

                else:
                    embed = discord.Embed(
                        title="Error!",
                        description="There is something wrong with the API, please try again later",
                        color=0xE02B2B,
                    )
                await context.send(embed=embed)

async def setup(bot) -> None:
    await bot.add_cog(Images(bot))

