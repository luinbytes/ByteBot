import aiohttp
import discord
from discord.ext import commands
from discord.ext.commands import Context
from discord import app_commands

class Utilities(commands.Cog, name="utilities"):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.hybrid_command(
        name="bitcoin",
        description="Get the current price of bitcoin.",
    )
    async def bitcoin(self, context: Context) -> None:
        """
        Get the current price of bitcoin.

        :param context: The hybrid command context.
        """
        # This will prevent your bot from stopping everything when doing a web request - see: https://discordpy.readthedocs.io/en/stable/faq.html#how-do-i-make-a-web-request
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://api.coindesk.com/v1/bpi/currentprice/BTC.json"
            ) as request:
                if request.status == 200:
                    data = await request.json(
                        content_type="application/javascript"
                    )  # For some reason the returned content is of type JavaScript
                    embed = discord.Embed(
                        title="Bitcoin price",
                        description=f"The current price is {data['bpi']['USD']['rate']} :dollar:",
                        color=0xBEBEFE,
                    )
                else:
                    embed = discord.Embed(
                        title="Error!",
                        description="There is something wrong with the API, please try again later",
                        color=0xE02B2B,
                    )
                await context.send(embed=embed)

    @commands.hybrid_command(
        name="userinfo",
        description="Get information about a user"
    )
    async def userinfo(self, context: Context, user: discord.Member = None) -> None:
        """
        Get information about a user.

        :param context: The hybrid command context.
        :param user: The user to get the info from.
        """
        if user is None:
            user = context.author
        
        embed = discord.Embed(
            title=f"{user.name}",
            description=f"ID: {user.id}",
            color=0xBEBEFE,
        )
        embed.add_field(name="Joined", value=user.joined_at.strftime("%d/%m/%Y %H:%M:%S"), inline=True)
        embed.add_field(name="Created", value=user.created_at.strftime("%d/%m/%Y %H:%M:%S"))
        embed.add_field(name="Roles", value=", ".join([role.name for role in user.roles]), inline=False)
        embed.add_field(name="Status", value=user.status, inline=True)
        embed.add_field(name="Highest Role", value=user.top_role.name, inline=True)
        embed.add_field(name="Bot", value=user.bot, inline=True)   
        embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
        embed.set_thumbnail(url=user.avatar)
        await context.send(embed=embed)


    @commands.hybrid_command(
        name="avatar",
        description="Get the avatar of a user"
    )
    @app_commands.describe(
        user="The user to get the avatar of."
    )
    async def avatar(self, context: Context, user: discord.Member = None) -> None:
        """
        Gets a users avatar.

        :param context: The hybrid command context.
        :param user: The user to get the avatar of.
        """
        embed = discord.Embed(color=0xBEBEFE)
        
        if user:
            embed.title = f"{user.name}'s avatar"
            embed.add_field(name="", value=f"[Open in browser]({user.avatar.url})", inline=False)
            embed.set_image(url=user.avatar)
            embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
        else:
            embed.title = "Your Avatar"
            embed.add_field(name="", value=f"[Open in browser]({context.author.avatar.url})", inline=False)
            embed.set_image(url=context.author.avatar)
            embed.set_footer(text="Requested by yourself", icon_url=context.author.avatar)

        await context.send(embed=embed)


async def setup(bot) -> None:
    await bot.add_cog(Utilities(bot))
