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

    @commands.hybrid_command(
        name="setwelcomechannel",
        description="Set the welcome channel for the server.",
        usage="setwelcomechannel <#channel>",
        aliases=["swc"]
    )
    @app_commands.describe(
        channel="The channel to set as the welcome channel."
    )
    async def set_welcome_channel(self, context: Context, channel: discord.TextChannel = None) -> None:
        """
        Set the welcome channel for the server.

        :param context: The hybrid command context.
        :param channel: The channel to set as the welcome channel.
        """
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        if channel is None:
            # Lookup the welcome channel from the GuildWelcomeChannels table
            cursor = c.execute("SELECT channel_id FROM GuildWelcomeChannels WHERE guild_id = ?", (context.guild.id,))
            row = cursor.fetchone()
            if row:
                channel = context.guild.get_channel(row[0])
                embed = discord.Embed(
                    title="Welcome Channel",
                    description=f"The current welcome channel is {channel.mention}",
                    color=0xBEBEFE,
                )
                embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
                await context.send(embed=embed)
            else:
                embed = discord.Embed(
                    title="Error!",
                    description="No welcome channel has been set for this server.",
                    color=0xE02B2B,
                )
                embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
                await context.send(embed=embed)
        else:
            # Write to the table
            try:
                c.execute("INSERT INTO GuildWelcomeChannels (guild_id, channel_id) VALUES (?, ?)", (context.guild.id, channel.id))
            except sqlite3.IntegrityError:
                c.execute("UPDATE GuildWelcomeChannels SET channel_id = ? WHERE guild_id = ?", (channel.id, context.guild.id))
            conn.commit()
            embed = discord.Embed(
                title="Welcome Channel",
                description=f"Welcome channel set to {channel.mention}",
                color=0xBEBEFE,
            )
            embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
            await context.send(embed=embed)
        conn.close()
    
    @commands.hybrid_command(
        name="removewelcomechannel",
        description="Remove the welcome channel for the server.",
        aliases=["rwc", "rmwelcomechannel"],
        usage="removewelcomechannel"
    )
    async def remove_welcome_channel(self, context: Context) -> None:
        """
        Remove the welcome channel for the server.

        :param context: The hybrid command context.
        """
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        # Check if welcome channel is even set
        cursor = c.execute("SELECT channel_id FROM GuildWelcomeChannels WHERE guild_id = ?", (context.guild.id,))
        row = cursor.fetchone()
        if row:
            c.execute("DELETE FROM GuildWelcomeChannels WHERE guild_id = ?", (context.guild.id,))
            conn.commit()
            embed = discord.Embed(
                title="Welcome Channel",
                description=f"Welcome channel removed",
                color=0xBEBEFE,
            )
            embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
            await context.send(embed=embed)
        else:
            embed = discord.Embed(
                title="Error!",
                description="No welcome channel has been set for this server.",
                color=0xE02B2B,
            )
            embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
            await context.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        cursor = c.execute("SELECT channel_id FROM GuildWelcomeChannels WHERE guild_id = ?", (member.guild.id,))
        row = cursor.fetchone()
        if row:
            async with aiohttp.ClientSession() as session:
                async with session.get("https://purrbot.site/api/img/sfw/dance/gif") as request:
                    if request.status == 200:
                        data = await request.json()
                        gif = data["link"]
                    else:
                        gif = None
            channel = member.guild.get_channel(row[0])
            embed = discord.Embed(
                title=f"{member.guild.name}",
                description=f"Welcome to {member.guild.name}, {member.mention}!",
                color=0xBEBEFE,
            )
            embed.set_image(url=gif)
            embed.set_footer(text="ByteBot - THE Mediocre Discord Bot", icon_url=self.bot.user.avatar.url)
            await channel.send(f"{member.mention} has joined!", embed=embed)
            
        conn.close()

async def setup(bot) -> None:
    await bot.add_cog(Utilities(bot))
