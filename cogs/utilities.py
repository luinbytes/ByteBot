import aiohttp
import discord
import sqlite3
import os
from discord.ext import commands
from discord.ext.commands import Context
from discord import app_commands
from xml.etree import ElementTree as ET

DATABASE_DIR = "database"
ABS_PATH = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(DATABASE_DIR, "database.db")

def guild_prefix(db, guild_id, prefix=None):
    db_conn = sqlite3.connect(DB_PATH)
    db = db_conn.cursor()
    if prefix is not None:
        # Write to the table
        try:
            db.execute("INSERT INTO GuildPrefix (guild_id, prefix) VALUES (?, ?)", (guild_id, prefix))
        except sqlite3.IntegrityError:
            db.execute("UPDATE GuildPrefix SET prefix = ? WHERE guild_id = ?", (prefix, guild_id))
        db_conn.commit()
    else:
        # Read from the table
        cursor = db.execute("SELECT prefix FROM GuildPrefix WHERE guild_id = ?", (guild_id,))
        row = cursor.fetchone()
        return row[0] if row else None
    db.close()

class Utilities(commands.Cog, name="utilities"):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.hybrid_command(
        name="bitcoin",
        description="Get the current price of bitcoin.",
        aliases=["btc"]
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
        description="Get information about a user",
        usage="userinfo <@user>",
        aliases=["user"]
    )
    @app_commands.describe(
        user="The user to get the info from."
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
        description="Get the avatar of a user",
        usage="avatar <@user>",
        aliases=["av"]
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

    @commands.hybrid_command(
        name="joinedat",
        description="Get the date a user joined the server.",
        usage="joinedat <@user>",
        aliases=["joined", "joindate"]
    )
    @app_commands.describe(
        user="The user to get the join date of."
    )
    async def joinedat(self, context: Context, user: discord.Member = None) -> None:
        """
        Get the date a user joined the server.

        :param context: The hybrid command context.
        :param user: The user to get the join date of.
        """
        if user is None:
            user = context.author

        embed = discord.Embed(
            title=f"{user.name}",
            description=f"Joined at {user.joined_at.strftime('%d/%m/%Y %H:%M:%S')}",
            color=0xBEBEFE,
        )
        embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
        embed.set_thumbnail(url=user.avatar)
        await context.send(embed=embed)

    @commands.hybrid_command(
        name="userid",
        description="Get the ID of a user.",
        usage="userid <@user>",
        aliases=["uid", "id"]
    )
    @app_commands.describe(
        user="The user to get the ID of."
    )
    async def userid(self, context: Context, user: discord.Member = None) -> None:
        """
        Get the ID of a user.

        :param context: The hybrid command context.
        :param user: The user to get the ID of.
        """
        if user is None:
            user = context.author

        embed = discord.Embed(
            title=f"{user.name}",
            description=f"ID: {user.id}",
            color=0xBEBEFE,
        )
        embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
        embed.set_thumbnail(url=user.avatar)
        await context.send(embed=embed)

    @commands.hybrid_command(
        name="listaliases",
        description="List all available aliases for a command.",
        usage="listaliases <command>",
        aliases=["aliases"]
    )
    @app_commands.describe(
        command="The command to list aliases for."
    )
    async def listaliases(self, context: Context, command: str) -> None:
        """
        List all available aliases for a command.

        :param context: The hybrid command context.
        :param command: The command to list aliases for.
        """
        cmd = self.bot.get_command(command)

        if cmd is None:
            await context.send(f"Command '{command}' not found.")
            return

        aliases = cmd.aliases

        if not aliases:
            await context.send(f"No aliases found for command '{command}'.")
            return

        embed = discord.Embed(
            title=f"Aliases for '{command}'",
            description=" - ".join(f"`{alias}`" for alias in aliases),
            color=0xBEBEFE
        )
        embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
        await context.send(embed=embed)

    @commands.hybrid_command(
        name="prefix",
        description="Get the current prefix for the server.",
    )
    async def display_prefix(self, context: Context) -> None:
        """
        Get the current prefix for the server.

        :param context: The hybrid command context.
        """
        prefix = guild_prefix(self, context.guild.id)
        if prefix is None:
            prefix = "!"

        embed = discord.Embed(
            title="Prefix",
            description=f"The current prefix for this server is `{prefix}`",
            color=0xBEBEFE,
        )
        embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
        await context.send(embed=embed)

async def setup(bot) -> None:
    await bot.add_cog(Utilities(bot))
