import os
import sqlite3
from sys import platform

import aiohttp
import aiosqlite
import discord
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import Context

DATABASE_DIR = "database"
ABS_PATH = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(DATABASE_DIR, "database.db")


class Utilities(commands.Cog, name="utilities"):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.context_menu_user = app_commands.ContextMenu(
            name="Grab ID", callback=self.grab_id
        )
        self.bot.tree.add_command(self.context_menu_user)
        self.context_menu_message = app_commands.ContextMenu(
            name="Remove spoilers", callback=self.remove_spoilers
        )
        self.bot.tree.add_command(self.context_menu_message)

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
        # This will prevent your bot from stopping everything when doing a web request - see:
        # https://discordpy.readthedocs.io/en/stable/faq.html#how-do-i-make-a-web-request
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
        prefix = self.guild_prefix(context.guild.id)
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
        async with aiosqlite.connect(DB_PATH) as conn:
            c = await conn.cursor()
            if channel is None:
                # Lookup the welcome channel from the GuildWelcomeChannels table
                await c.execute("SELECT welcome_channel_id FROM GuildSettings WHERE guild_id = ?", (context.guild.id,))
                row = await c.fetchone()
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
                await c.execute("UPDATE GuildSettings SET welcome_channel_id = ? WHERE guild_id = ?",
                                (channel.id, context.guild.id))
                await conn.commit()
                embed = discord.Embed(
                    title="Welcome Channel",
                    description=f"Welcome channel set to {channel.mention}",
                    color=0xBEBEFE,
                )
                embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
                await context.send(embed=embed)

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
        async with aiosqlite.connect(DB_PATH) as conn:
            c = await conn.cursor()
            # Check if welcome channel is even set
            await c.execute("SELECT channel_id FROM GuildWelcomeChannels WHERE guild_id = ?", (context.guild.id,))
            row = await c.fetchone()
            if row:
                await c.execute("DELETE FROM GuildWelcomeChannels WHERE guild_id = ?", (context.guild.id,))
                await conn.commit()
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

    @commands.hybrid_command(
        name="setleavechannel",
        description="Set the leave channel for the server.",
        usage="setleavechannel <#channel>",
        aliases=["slc"]
    )
    @app_commands.describe(
        channel="The channel to set as the leave channel."
    )
    async def set_leave_channel(self, context: Context, channel: discord.TextChannel = None) -> None:
        """
        Set the leave channel for the server.
        :param context:
        :param channel:
        """
        async with aiosqlite.connect(DB_PATH) as conn:
            c = conn.cursor()
            if channel is None:
                # Lookup the leave channel from the GuildLeaveChannels table
                await c.execute("SELECT leave_channel_id FROM GuildSettings WHERE guild_id = ?", (context.guild.id,))
                row = await c.fetchone()
                if row:
                    channel = context.guild.get_channel(row[0])
                    embed = discord.Embed(
                        title="Leave Channel",
                        description=f"The current leave channel is {channel.mention}",
                        color=0xBEBEFE,
                    )
                    embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
                    await context.send(embed=embed)
                else:
                    embed = discord.Embed(
                        title="Error!",
                        description="No leave channel has been set for this server.",
                        color=0xE02B2B,
                    )
                    embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
                    await context.send(embed=embed)
            else:
                # Write to the table
                await c.execute("UPDATE GuildSettings SET leave_channel_id = ? WHERE guild_id = ?",
                                (channel.id, context.guild.id))
                await conn.commit()
                embed = discord.Embed(
                    title="Leave Channel",
                    description=f"Leave channel set to {channel.mention}",
                    color=0xBEBEFE,
                )
                embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
                await context.send(embed=embed)

    @commands.hybrid_command(
        name="removeleavechannel",
        description="Remove the leave channel for the server.",
        aliases=["rlc", "rmleavechannel"],
        usage="removeleavechannel"
    )
    async def remove_leave_channel(self, context: Context) -> None:
        async with aiosqlite.connect(DB_PATH) as conn:
            c = conn.cursor()
            # Check if leave channel is even set
            await c.execute("SELECT leave_channel_id FROM GuildSettings WHERE guild_id = ?", (context.guild.id,))
            row = await c.fetchone()
            if row:
                await c.execute("DELETE FROM GuildSettings WHERE guild_id = ?", (context.guild.id,))
                await conn.commit()
                embed = discord.Embed(
                    title="Leave Channel",
                    description=f"Leave channel removed",
                    color=0xBEBEFE,
                )
                embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
                await context.send(embed=embed)
            else:
                embed = discord.Embed(
                    title="Error!",
                    description="No leave channel has been set for this server.",
                    color=0xE02B2B,
                )
                embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
                await context.send(embed=embed)

    async def remove_spoilers(
            self, interaction: discord.Interaction, message: discord.Message
    ) -> None:
        """
        Removes the spoilers from the message. This command requires the MESSAGE_CONTENT intent to work properly.

        :param interaction: The application command interaction.
        :param message: The message that is being interacted with.
        """
        spoiler_attachment = None
        for attachment in message.attachments:
            if attachment.is_spoiler():
                spoiler_attachment = attachment
                break
        embed = discord.Embed(
            title="Message without spoilers",
            description=message.content.replace("||", ""),
            color=0xBEBEFE,
        )
        if spoiler_attachment is not None:
            embed.set_image(url=attachment.url)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # User context menu command
    async def grab_id(
            self, interaction: discord.Interaction, user: discord.User) -> None:
        """
        Grabs the ID of the user.

        :param interaction: The application command interaction.
        :param user: The user that is being interacted with.
        """
        embed = discord.Embed(
            description=f"The ID of {user.mention} is `{user.id}`.",
            color=0xBEBEFE,
        )
        embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)  # type: ignore
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @commands.hybrid_command(
        name="help",
        description="List all commands the bot has loaded or show commands in a specific category.",
    )
    async def help(self, context: Context, category: str = None) -> None:
        db_conn = sqlite3.connect(DB_PATH)
        db = db_conn.cursor()
        prefix = self.guild_prefix(context.guild.id)
        embed = discord.Embed(
            title="Help", description="List of available categories:", color=0xBEBEFE
        )
        embed.add_field(name=f"Use {prefix}help <category> to see commands", value="", inline=False)
        for cog_name in self.bot.cogs:
            if cog_name == "owner" and not (await self.bot.is_owner(context.author)):
                continue
            embed.add_field(name="", value=cog_name.capitalize(), inline=False)
        embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)

        if category:
            category_lower = category.lower()
            cog = self.bot.get_cog(category_lower)
            if cog:
                commands = cog.get_commands()
                data = []
                for command in commands:
                    description = command.description.partition("\n")[0]
                    data.append(f"{prefix}{command.name} - {description}")
                help_text = "\n".join(data)
                category_embed = discord.Embed(
                    title=f"{category.capitalize()} Commands",
                    description=f"```{help_text}```",
                    color=0xBEBEFE
                )
                category_embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
                await context.send(embed=category_embed)
            else:
                await context.send("Invalid category. Please use !help to see available categories.")
        else:
            await context.send(embed=embed)

    @commands.hybrid_command(
        name="botinfo",
        description="Get some useful (or not) information about the bot.",
    )
    async def botinfo(self, context: Context) -> None:
        """
        Get some useful (or not) information about the bot.

        :param context: The hybrid command context.
        """
        embed = discord.Embed(
            description="Made by @0x6c75",
            color=0xBEBEFE,
        )
        embed.set_author(name="Bot Information")
        embed.add_field(name="Owner:", value="@0x6c75", inline=True)
        embed.add_field(
            name="Python Version:", value=f"{platform.python_version()}", inline=True
        )
        embed.add_field(
            name="Discord.py Version:",
            value=f"{discord.__version__}",
            inline=True,
        )
        embed.add_field(
            name="Prefix:",
            value=f"/ (Slash Commands) or {self.guild_prefix(self, context.guild.id)} for normal commands",
            inline=False,
        )
        embed.add_field(
            name="Enjoying ByteBot?",
            value="Consider [voting](https://top.gg/bot/1240320839719719025#vote) for ByteBot on top.gg!"
        )
        embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
        await context.send(embed=embed)

    @commands.hybrid_command(
        name="serverinfo",
        description="Get some useful (or not) information about the server.",
    )
    async def serverinfo(self, context: Context) -> None:
        """
        Get some useful (or not) information about the server.

        :param context: The hybrid command context.
        """
        roles = [role.name for role in context.guild.roles]
        num_roles = len(roles)
        if num_roles > 50:
            roles = roles[:50]
            roles.append(f">>>> Displaying [50/{num_roles}] Roles")
        roles = ", ".join(roles)

        embed = discord.Embed(
            title="**Server Name:**", description=f"{context.guild}", color=0xBEBEFE
        )
        if context.guild.icon is not None:
            embed.set_thumbnail(url=context.guild.icon.url)
        embed.add_field(name="Server ID", value=context.guild.id)
        embed.add_field(name="Member Count", value=context.guild.member_count)
        embed.add_field(
            name="Text/Voice Channels", value=f"{len(context.guild.channels)}"
        )
        embed.add_field(name=f"Roles ({len(context.guild.roles)})", value=roles)
        embed.add_field(name="Created At", value=f"{context.guild.created_at}")
        embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
        await context.send(embed=embed)

    @commands.hybrid_command(
        name="ping",
        description="Check if the bot is alive.",
    )
    async def ping(self, context: Context) -> None:
        """
        Check if the bot is alive.

        :param context: The hybrid command context.
        """
        embed = discord.Embed(
            title="🏓 Pong!",
            description=f"The bot latency is {round(self.bot.latency * 1000)}ms.",
            color=0xBEBEFE,
        )
        embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
        await context.send(embed=embed)

    @commands.hybrid_command(
        name="invite",
        description="Get the invite link of the bot to be able to invite it.",
    )
    async def invite(self, context: Context) -> None:
        """
        Get the invite link of the bot to be able to invite it.

        :param context: The hybrid command context.
        """
        embed = discord.Embed(
            title=f"Invite {self.bot.config['bot_name']}",
            description=f"Invite me by clicking [here]({self.bot.config['invite_link']}).",
            color=0xD75BF4,
        )
        embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
        try:
            await context.author.send(embed=embed)
            await context.send("I sent you a private message!")
        except discord.Forbidden:
            await context.send(embed=embed)

    @commands.hybrid_command(
        name="server",
        description="Get the invite link of the discord server of the bot for some support.",
    )
    async def server(self, context: Context) -> None:
        """
        Get the invite link of the discord server of the bot for some support.

        :param context: The hybrid command context.
        """
        embed = discord.Embed(
            title=f"Support Server for {self.bot.config['bot_name']}",
            description=f"Join the support server for the bot by clicking [here](https://discord.gg/ADzuh7EEQB).",
            color=0xD75BF4,
        )
        embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
        try:
            await context.author.send(embed=embed)
            await context.send("I sent you a private message!")
        except discord.Forbidden:
            await context.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        async with aiosqlite.connect(DB_PATH) as conn:
            c = await conn.cursor()
            await c.execute("SELECT welcome_channel_id FROM GuildSettings WHERE guild_id = ?", (member.guild.id,))
            row = await c.fetchone()
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

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        async with aiosqlite.connect(DB_PATH) as conn:
            c = await conn.cursor()
            await c.execute("SELECT leave_channel_id FROM GuildSettings WHERE guild_id = ?", (member.guild.id,))
            row = await c.fetchone()
            if row:
                channel = member.guild.get_channel(row[0])
                embed = discord.Embed(
                    title=f"{member.guild.name}",
                    description=f"{member.mention} has left {member.guild.name}.",
                    color=0xBEBEFE,
                )
                embed.set_footer(text="ByteBot - THE Mediocre Discord Bot", icon_url=self.bot.user.avatar.url)
                await channel.send(embed=embed)

    async def guild_prefix(db, guild_id, prefix=None):
        async with aiosqlite.connect(DB_PATH) as conn:
            c = await conn.cursor()
            if prefix is not None:
                # Write to the table
                await c.execute("UPDATE GuildSettings SET prefix = ? WHERE guild_id = ?", (prefix, guild_id))
                await conn.commit()
            else:
                # Read from the table
                await c.execute("SELECT prefix FROM GuildSettings WHERE guild_id = ?", (guild_id,))
                row = await c.fetchone()
                return row[0] if row else None


async def setup(bot) -> None:
    await bot.add_cog(Utilities(bot))
