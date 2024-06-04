import json
import os
import re
from datetime import datetime
from datetime import timedelta

import aiosqlite
import discord
from discord import app_commands
from discord.ext import commands, tasks
from discord.ext.commands import Context

DATABASE_DIR = "database"
ABS_PATH = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(DATABASE_DIR, "database.db")


async def guild_prefix(db, guild_id, prefix=None):
    async with aiosqlite.connect(DB_PATH) as conn:
        c = await conn.cursor()
        if prefix is not None:
            # Write to the table
            try:
                await c.execute("INSERT INTO GuildPrefix (guild_id, prefix) VALUES (?, ?)", (guild_id, prefix))
            except aiosqlite.IntegrityError:
                await c.execute("UPDATE GuildPrefix SET prefix = ? WHERE guild_id = ?", (prefix, guild_id))
            await conn.commit()
        else:
            # Read from the table
            await c.execute("SELECT prefix FROM GuildPrefix WHERE guild_id = ?", (guild_id,))
            row = await c.fetchone()
            return row[0] if row else None


async def update_guild_prefix(db, guild_id, prefix):
    async with aiosqlite.connect(DB_PATH) as conn:
        c = await conn.cursor()
        await c.execute("INSERT OR REPLACE INTO GuildPrefix (guild_id, prefix) VALUES (?, ?)", (guild_id, prefix))
        await conn.commit()


async def guild_autoroles(db, guild_id, role_id=None):
    async with aiosqlite.connect(DB_PATH) as conn:
        c = await conn.cursor()
        if role_id is not None:
            # Write to the table
            await c.execute("INSERT OR REPLACE INTO GuildAutoroles (guild_id, role_id) VALUES (?, ?)",
                            (guild_id, role_id))
            await conn.commit()
        else:
            # Read from the table
            await c.execute("SELECT role_id FROM GuildAutoroles WHERE guild_id = ?", (guild_id,))
            row = await c.fetchone()
            return row[0] if row else None


async def guild_starboard_channels(self, guild_id, starboard_min_reactions=None, channel_id=None):
    # Connect to the database
    async with aiosqlite.connect(DB_PATH) as conn:
        c = await conn.cursor()

        # If both starboard_min_reactions and channel_id are None, read from the database
        if starboard_min_reactions is None and channel_id is None:
            await c.execute("SELECT * FROM GuildStarboardChannels WHERE guild_id = ?", (guild_id,))
            rows = await c.fetchall()
            return rows

        # If starboard_min_reactions is not None, update the starboard_min_reactions column
        if starboard_min_reactions is not None:
            await c.execute("UPDATE GuildStarboardChannels SET starboard_min_reactions = ? WHERE guild_id = ?",
                            (starboard_min_reactions, guild_id))

        # If channel_id is not None, update the channel_id column
        if channel_id is not None:
            await c.execute("UPDATE GuildStarboardChannels SET channel_id = ? WHERE guild_id = ?",
                            (channel_id, guild_id))

        # Commit the changes
        await conn.commit()


class Moderation(commands.Cog, name="moderation"):
    def __init__(self, bot) -> None:
        self.bot = bot

    async def load_config(self):
        try:
            with open('config.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    async def save_config(self, config):
        with open('config.json', 'w') as f:
            json.dump(config, f, indent=4)

    @commands.hybrid_command(
        name="kick",
        description="Kick a user out of the server.",
    )
    @commands.has_permissions(kick_members=True)
    @commands.bot_has_permissions(kick_members=True)
    @app_commands.describe(
        user="The user that should be kicked.",
        reason="The reason why the user should be kicked.",
    )
    async def kick(
            self, context: Context, user: discord.User, *, reason: str = "Not specified"
    ) -> None:
        """
        Kick a user out of the server.

        :param context: The hybrid command context.
        :param user: The user that should be kicked from the server.
        :param reason: The reason for the kick. Default is "Not specified".
        """
        member = context.guild.get_member(user.id) or await context.guild.fetch_member(
            user.id
        )
        if member.guild_permissions.administrator:
            embed = discord.Embed(
                description="User has administrator permissions.", color=0xE02B2B
            )
            await context.send(embed=embed)
        else:
            try:
                embed = discord.Embed(
                    description=f"**{member}** was kicked by **{context.author}**!",
                    color=0xBEBEFE,
                )
                embed.add_field(name="Reason:", value=reason)
                await context.send(embed=embed)
                try:
                    await member.send(
                        f"You were kicked by **{context.author}** from **{context.guild.name}**!\nReason: {reason}"
                    )
                except:
                    # Couldn't send a message in the private messages of the user
                    pass
                await member.kick(reason=reason)
            except:
                embed = discord.Embed(
                    description="An error occurred while trying to kick the user. Make sure my role is above the role of the user you want to kick.",
                    color=0xE02B2B,
                )
                await context.send(embed=embed)

    @commands.hybrid_command(
        name="nick",
        description="Change the nickname of a user on a server.",
    )
    @commands.has_permissions(manage_nicknames=True)
    @commands.bot_has_permissions(manage_nicknames=True)
    @app_commands.describe(
        user="The user that should have a new nickname.",
        nickname="The new nickname that should be set.",
    )
    async def nick(
            self, context: Context, user: discord.User, *, nickname: str = None
    ) -> None:
        """
        Change the nickname of a user on a server.

        :param context: The hybrid command context.
        :param user: The user that should have its nickname changed.
        :param nickname: The new nickname of the user. Default is None, which will reset the nickname.
        """
        member = context.guild.get_member(user.id) or await context.guild.fetch_member(
            user.id
        )
        try:
            await member.edit(nick=nickname)
            embed = discord.Embed(
                description=f"**{member}'s** new nickname is **{nickname}**!",
                color=0xBEBEFE,
            )
            await context.send(embed=embed)
        except:
            embed = discord.Embed(
                description="An error occurred while trying to change the nickname of the user. Make sure my role is above the role of the user you want to change the nickname.",
                color=0xE02B2B,
            )
            await context.send(embed=embed)

    @commands.hybrid_command(
        name="ban",
        description="Bans a user from the server.",
    )
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    @app_commands.describe(
        user="The user that should be banned.",
        reason="The reason why the user should be banned.",
    )
    async def ban(
            self, context: Context, user: discord.User, *, reason: str = "Not specified"
    ) -> None:
        """
        Bans a user from the server.

        :param context: The hybrid command context.
        :param user: The user that should be banned from the server.
        :param reason: The reason for the ban. Default is "Not specified".
        """
        member = context.guild.get_member(user.id) or await context.guild.fetch_member(
            user.id
        )
        try:
            if member.guild_permissions.administrator:
                embed = discord.Embed(
                    description="User has administrator permissions.", color=0xE02B2B
                )
                await context.send(embed=embed)
            else:
                embed = discord.Embed(
                    description=f"**{member}** was banned by **{context.author}**!",
                    color=0xBEBEFE,
                )
                embed.add_field(name="Reason:", value=reason)
                await context.send(embed=embed)
                try:
                    await member.send(
                        f"You were banned by **{context.author}** from **{context.guild.name}**!\nReason: {reason}"
                    )
                except:
                    # Couldn't send a message in the private messages of the user
                    pass
                await member.ban(reason=reason)
        except:
            embed = discord.Embed(
                title="Error!",
                description="An error occurred while trying to ban the user. Make sure my role is above the role of the user you want to ban.",
                color=0xE02B2B,
            )
            await context.send(embed=embed)

    @commands.hybrid_group(
        name="warning",
        description="Manage warnings of a user on a server.",
    )
    @commands.has_permissions(manage_messages=True)
    async def warning(self, context: Context) -> None:
        """
        Manage warnings of a user on a server.

        :param context: The hybrid command context.
        """
        if context.invoked_subcommand is None:
            embed = discord.Embed(
                description="Please specify a subcommand.\n\n**Subcommands:**\n`add` - Add a warning to a user.\n`remove` - Remove a warning from a user.\n`list` - List all warnings of a user.",
                color=0xE02B2B,
            )
            await context.send(embed=embed)

    @warning.command(
        name="add",
        description="Adds a warning to a user in the server.",
    )
    @commands.has_permissions(manage_messages=True)
    @app_commands.describe(
        user="The user that should be warned.",
        reason="The reason why the user should be warned.",
    )
    async def warning_add(
            self, context: Context, user: discord.User, *, reason: str = "Not specified"
    ) -> None:
        """
        Warns a user in his private messages.

        :param context: The hybrid command context.
        :param user: The user that should be warned.
        :param reason: The reason for the warn. Default is "Not specified".
        """
        member = context.guild.get_member(user.id) or await context.guild.fetch_member(
            user.id
        )
        total = await self.bot.database.add_warn(
            user.id, context.guild.id, context.author.id, reason
        )
        embed = discord.Embed(
            description=f"**{member}** was warned by **{context.author}**!\nTotal warns for this user: {total}",
            color=0xBEBEFE,
        )
        embed.add_field(name="Reason:", value=reason)
        await context.send(embed=embed)
        try:
            await member.send(
                f"You were warned by **{context.author}** in **{context.guild.name}**!\nReason: {reason}"
            )
        except:
            # Couldn't send a message in the private messages of the user
            await context.send(
                f"{member.mention}, you were warned by **{context.author}**!\nReason: {reason}"
            )

    @warning.command(
        name="remove",
        description="Removes a warning from a user in the server.",
    )
    @commands.has_permissions(manage_messages=True)
    @app_commands.describe(
        user="The user that should get their warning removed.",
        warn_id="The ID of the warning that should be removed.",
    )
    async def warning_remove(
            self, context: Context, user: discord.User, warn_id: int
    ) -> None:
        """
        Warns a user in his private messages.

        :param context: The hybrid command context.
        :param user: The user that should get their warning removed.
        :param warn_id: The ID of the warning that should be removed.
        """
        member = context.guild.get_member(user.id) or await context.guild.fetch_member(
            user.id
        )
        total = await self.bot.database.remove_warn(warn_id, user.id, context.guild.id)
        embed = discord.Embed(
            description=f"I've removed the warning **#{warn_id}** from **{member}**!\nTotal warns for this user: {total}",
            color=0xBEBEFE,
        )
        await context.send(embed=embed)

    @warning.command(
        name="list",
        description="Shows the warnings of a user in the server.",
    )
    @commands.has_guild_permissions(manage_messages=True)
    @app_commands.describe(user="The user you want to get the warnings of.")
    async def warning_list(self, context: Context, user: discord.User) -> None:
        """
        Shows the warnings of a user in the server.

        :param context: The hybrid command context.
        :param user: The user you want to get the warnings of.
        """
        warnings_list = await self.bot.database.get_warnings(user.id, context.guild.id)
        embed = discord.Embed(title=f"Warnings of {user}", color=0xBEBEFE)
        description = ""
        if len(warnings_list) == 0:
            description = "This user has no warnings."
        else:
            for warning in warnings_list:
                description += f"• Warned by <@{warning[2]}>: **{warning[3]}** (<t:{warning[4]}>) - Warn ID #{warning[5]}\n"
        embed.description = description
        await context.send(embed=embed)

    @commands.hybrid_command(
        name="purge",
        description="Delete a number of messages.",
    )
    @commands.has_guild_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    @app_commands.describe(amount="The amount of messages that should be deleted.")
    async def purge(self, context: Context, amount: int) -> None:
        """
        Delete a number of messages.

        :param context: The hybrid command context.
        :param amount: The number of messages that should be deleted.
        """
        await context.defer()
        purged_messages = await context.channel.purge(limit=amount + 1)
        embed = discord.Embed(
            description=f"**{context.author.mention}** cleared **{len(purged_messages) - 1}** messages!",
            color=0xBEBEFE,
        )
        await context.channel.send(embed=embed)

    @commands.hybrid_command(
        name="hackban",
        description="Bans a user without the user having to be in the server.",
    )
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    @app_commands.describe(
        user_id="The user ID that should be banned.",
        reason="The reason why the user should be banned.",
    )
    async def hackban(
            self, context: Context, user_id: str, *, reason: str = "Not specified"
    ) -> None:
        """
        Bans a user without the user having to be in the server.

        :param context: The hybrid command context.
        :param user_id: The ID of the user that should be banned.
        :param reason: The reason for the ban. Default is "Not specified".
        """
        try:
            await self.bot.http.ban(user_id, context.guild.id, reason=reason)
            user = self.bot.get_user(int(user_id)) or await self.bot.fetch_user(
                int(user_id)
            )
            embed = discord.Embed(
                description=f"**{user}** (ID: {user_id}) was banned by **{context.author}**!",
                color=0xBEBEFE,
            )
            embed.add_field(name="Reason:", value=reason)
            await context.send(embed=embed)
        except Exception:
            embed = discord.Embed(
                description="An error occurred while trying to ban the user. Make sure ID is an existing ID that "
                            "belongs to a user.",
                color=0xE02B2B,
            )
            await context.send(embed=embed)

    @commands.hybrid_command(
        name="archive",
        description="Archives in a text file the last messages with a chosen limit of messages.",
    )
    @commands.has_permissions(manage_messages=True)
    @app_commands.describe(
        limit="The limit of messages that should be archived.",
    )
    async def archive(self, context: Context, limit: int = 10) -> None:
        """
        Archives in a text file the last messages with a chosen limit of messages. This command requires the MESSAGE_CONTENT intent to work properly.

        :param limit: The limit of messages that should be archived. Default is 10.
        """
        log_file = f"{context.channel.id}.log"
        with open(log_file, "w", encoding="UTF-8") as f:
            f.write(
                f'Archived messages from: #{context.channel} ({context.channel.id}) in the guild "{context.guild}" ({context.guild.id}) at {datetime.now().strftime("%d.%m.%Y %H:%M:%S")}\n'
            )
            async for message in context.channel.history(
                    limit=limit, before=context.message
            ):
                attachments = []
                for attachment in message.attachments:
                    attachments.append(attachment.url)
                attachments_text = (
                    f"[Attached File{'s' if len(attachments) >= 2 else ''}: {', '.join(attachments)}]"
                    if len(attachments) >= 1
                    else ""
                )
                f.write(
                    f"{message.created_at.strftime('%d.%m.%Y %H:%M:%S')} {message.author} {message.id}: {message.clean_content} {attachments_text}\n"
                )
        f = discord.File(log_file)
        await context.send(file=f)
        os.remove(log_file)

    @commands.hybrid_command(
        name="purge",
        description="Deletes a user selected amount of messages from the current channel.",
    )
    @commands.has_permissions(manage_messages=True)
    @app_commands.describe(
        amount="The amount of messages that should be deleted. The maximum amount of messages that can be deleted is 100."
    )
    async def purge(self, context: Context, amount: int) -> None:
        """
        Purges a number of messages.
        """
        if 0 < amount <= 100:
            await context.channel.purge(limit=amount + 1)
            embed = discord.Embed(
                description=f"**{context.author}** cleared **{amount}** messages!",
                color=0xBEBEFE,
            )
            embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
            await context.send(embed=embed)

    @commands.hybrid_command(
        name="autorole",
        description="Sets the role to grant users on server join."
    )
    @commands.has_permissions(administrator=True)
    async def autorole(self, context: Context, role: discord.Role):
        await guild_autoroles(self, context.guild.id, role.id)

        for member in context.guild.members:
            if not member.bot:
                await member.add_roles(role)

        embed = discord.Embed(
            title="Autorole Set",
            description=f"The autorole has been set to {role.mention}."
        )
        await context.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        autorole_id = await guild_autoroles(self, member.guild.id)
        if autorole_id:
            role = member.guild.get_role(autorole_id)
            if role:
                await member.add_roles(role)

    @commands.hybrid_command(
        name="starboard",
        description="Sets the starboard channel for the server.",
        usage="starboard <#channel>",
        aliases=["starboardchannel", "sbchannel"]
    )
    @commands.has_permissions(administrator=True)
    async def starboard(self, context: Context, channel: discord.TextChannel):
        if channel.id == guild_starboard_channels(self, context.guild.id):
            embed = discord.Embed(
                title="Starboard already set",
                description=f"The starboard channel is already set to {channel.mention}.",
                color=0xE02B2B
            )
            await context.send(embed=embed)
        else:
            await guild_starboard_channels(self, context.guild.id, channel.id)
            embed = discord.Embed(
                title="Starboard Channel Set",
                description=f"The starboard channel has been set to {channel.mention}.",
                color=0xBEBEFE
            )
            await context.send(embed=embed)

    @commands.hybrid_command(
        name="sbreactionamount",
        description="Sets the minimum amount of reactions needed to pin a message to the starboard.",
        usage="sbreactionamount <amount>",
        aliases=["starboardreactionamount", "sbreaction", "reactionamount", "sbreacts", "sbreact"]
    )
    @commands.has_permissions(administrator=True)
    @app_commands.describe(
        amount="The minimum amount of reactions needed to pin a message to the starboard."
    )
    async def sbreactionamount(self, context: Context, amount: int = None):
        async with aiosqlite.connect(DB_PATH) as conn:
            c = await conn.cursor()
            if amount is None:
                min_reactions = await guild_starboard_channels(self, context.guild.id)
                embed = discord.Embed(
                    title="Current Starboard Reaction Amount",
                    description=f"The current minimum amount of reactions needed to pin a message to the starboard is `{min_reactions}`.",
                    color=0xBEBEFE
                )
                await context.send(embed=embed)
            else:
                await guild_starboard_channels(self, context.guild.id, amount)
                embed = discord.Embed(
                    title="Starboard Reaction Amount Set",
                    description=f"The minimum amount of reactions needed to pin a message to the starboard has been "
                                f"set to `{amount}`.",
                    color=0xBEBEFE
                )
                await context.send(embed=embed)

    async def award(self, user_id: int, coins: int) -> None:
        """
        This command allows users to be awarded coins. If the user is not registered, they are registered first.

        :param user_id: The ID of the user to award coins to.
        :param coins: The number of coins to award.

        """
        async with aiosqlite.connect("database/database.db") as conn:
            c = await conn.cursor()
            await c.execute("SELECT balance FROM UserEconomy WHERE user_id = ?", (user_id,))
            result = await c.fetchone()
            if result:
                # User is registered, award coins
                await c.execute("UPDATE UserEconomy SET balance = balance + ? WHERE user_id = ?", (coins, user_id))
                await conn.commit()
            else:
                # User is not registered, register them and award coins
                user = self.bot.get_user(user_id)
                username = user.name if user else "Unknown User"
                await c.execute("INSERT INTO UserEconomy (user_id, user_name, balance) VALUES (?, ?, ?)",
                                (user_id, username, coins))
                await conn.commit()

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        # print("Reaction added")

        # Get starboard channels and minimum reactions from the database
        result = guild_starboard_channels(self, payload.guild_id)
        if result:
            # print(result)
            starboard_guild_id, starboard_channel_id, min_reactions = result[0]
            # print(f"Starboard channel ID: {starboard_channel_id}, Minimum reactions: {min_reactions}")

            if payload.emoji.name == "⭐":
                # print("Star reaction detected")

                channel = self.bot.get_channel(payload.channel_id)
                message = await channel.fetch_message(payload.message_id)
                reaction = [react for react in message.reactions if str(react.emoji) == "⭐"][0]

                if reaction and reaction.count >= min_reactions:
                    # print("Reaction count is greater than or equal to minimum reactions")

                    if starboard_channel_id:
                        # print("Starboard channel ID exists")

                        starboard_channel = reaction.message.guild.get_channel(int(starboard_channel_id))

                        if starboard_channel:
                            # print("Starboard channel exists")

                            # Check if the message is already in the starboard
                            starboard_messages = []
                            async for message in starboard_channel.history():
                                starboard_messages.append(message)

                            if any(f"[Click here]({reaction.message.jump_url})" in embed.fields[0].value for message in
                                   starboard_messages for embed in message.embeds if embed.fields):
                                # print("Message is already in the starboard")
                                return

                            # print("Creating embed")

                            embed = discord.Embed(
                                title="⭐ Pinned!",
                                description=reaction.message.content,
                                color=0xFFFF00,
                            )
                            embed.set_author(name=reaction.message.author.name,
                                             icon_url=reaction.message.author.avatar.url)
                            embed.set_footer(text=f"Original message in #{reaction.message.channel.name}")
                            embed.add_field(name="Jump to message", value=f"[Click here]({reaction.message.jump_url})",
                                            inline=False)
                            embed.add_field(name="Award", value="1000 🪙", inline=True)

                            # Check if the message content is a URL to an image
                            url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
                            urls = re.findall(url_pattern, reaction.message.content)
                            if urls:
                                # print("URLs found in message content")

                                for url in urls:
                                    if url.endswith(('.png', '.jpg', '.gif')):
                                        # print("Image URL found")
                                        embed.set_image(url=url)
                                        break

                            if reaction.message.attachments:
                                # print("Message has attachments")
                                embed.set_image(url=reaction.message.attachments[0].url)

                            # print("Sending embed to starboard channel")
                            await starboard_channel.send(embed=embed)

                            message_id = payload.message_id
                            channel_id = payload.channel_id
                            guild_id = payload.guild_id

                            # Fetch the message that was reacted to
                            channel = self.bot.get_channel(channel_id)
                            message = await channel.fetch_message(message_id)

                            # Award coins to the user who sent the message
                            user_id = message.author.id
                            # print("Awarding coins to user")
                            await self.award(user_id, coins=1000)
        else:
            return

    @commands.hybrid_command(
        name="verifystarboard",
        description="Verifies the starboard channel for the server.",
        usage="verifystarboard",
        aliases=["verifyboard"]
    )
    @app_commands.describe(

    )
    @commands.has_permissions(administrator=True)
    async def verifystarboard(self, context: Context):
        starboard_channel_info = guild_starboard_channels(self, context.guild.id)
        if starboard_channel_info:
            starboard_channel_id, min_reactions = starboard_channel_info
            starboard_channel = context.guild.get_channel(int(starboard_channel_id))
            if starboard_channel:
                embed = discord.Embed(
                    title="Starboard Channel Verified",
                    description=f"The starboard channel is set to {starboard_channel.mention}.",
                    color=0xBEBEFE
                )
                await context.send(embed=embed)
            else:
                embed = discord.Embed(
                    title="Starboard Channel Verification",
                    description="The starboard channel is not set.",
                    color=0xE02B2B
                )
                await context.send(embed=embed)
        else:
            embed = discord.Embed(
                title="Starboard Channel Verification",
                description="The starboard channel is not set.",
                color=0xE02B2B
            )
            await context.send(embed=embed)

    @commands.hybrid_command(
        name="setprefix",
        description="Sets the prefix for the server.",
        usage="setprefix <prefix>",
    )
    @app_commands.describe(
        prefix="The new prefix for the server."
    )
    @commands.has_permissions(administrator=True)
    async def setprefix(self, context: Context, prefix: str):
        await update_guild_prefix(self, context.guild.id, prefix)
        embed = discord.Embed(
            title="Prefix Set",
            description=f"The prefix for this server has been set to `{prefix}`.",
            color=0xBEBEFE
        )
        await context.send(embed=embed)

    @commands.hybrid_command(
        name="createmuterole",
        description="Creates a mute role for the server.",
        usage="createmuterole <custom_name(optional)>",
        aliases=["addmuterole", "makemuterole"]
    )
    @app_commands.describe(
        custom_name="The custom name for the mute role. Default is 'Muted'."
    )
    @commands.has_permissions(administrator=True)
    async def createmuterole(self, context: Context, custom_name: str = None) -> None:
        async with aiosqlite.connect(DB_PATH) as conn:
            c = await conn.cursor()
            await c.execute("SELECT role_id FROM GuildMuteRole WHERE guild_id = ?", (context.guild.id,))
            result = await c.fetchone()
            if result:
                embed = discord.Embed(
                    title="Mute Role Already Exists",
                    description="A mute role already exists for this server.",
                    color=0xE02B2B
                )
                await context.send(embed=embed)
            else:
                if custom_name is None:
                    custom_name = "Muted"
                role = await context.guild.create_role(name=custom_name)
                for channel in context.guild.channels:
                    await channel.set_permissions(role, send_messages=False)
                await c.execute("INSERT INTO GuildMuteRole (guild_id, role_id) VALUES (?, ?)",
                                (context.guild.id, role.id))
                await conn.commit()
                embed = discord.Embed(
                    title="Mute Role Created",
                    description=f"The mute role has been created with the name `{custom_name}`.",
                    color=0xBEBEFE
                )
                await context.send(embed=embed)

    @commands.hybrid_command(
        name="rmmuterole",
        description="Removes the mute role from the server.",
        usage="rmmuterole",
        aliases=["deletemuterole", "removemuterole"]
    )
    @commands.has_permissions(administrator=True)
    async def rmmuterole(self, context: Context) -> None:
        async with aiosqlite.connect(DB_PATH) as conn:
            c = await conn.cursor()
            await c.execute("SELECT role_id FROM GuildMuteRole WHERE guild_id = ?", (context.guild.id,))
            result = await c.fetchone()
            if result:
                role_id = result[0]
                role = context.guild.get_role(role_id)
                if role:
                    await role.delete()
                await c.execute("DELETE FROM GuildMuteRole WHERE guild_id = ?", (context.guild.id,))
                await conn.commit()
                embed = discord.Embed(
                    title="Mute Role Removed",
                    description="The mute role has been removed from this server.",
                    color=0xBEBEFE
                )
                await context.send(embed=embed)
            else:
                embed = discord.Embed(
                    title="Mute Role Not Found",
                    description="No mute role was found for this server.",
                    color=0xE02B2B
                )
                await context.send(embed=embed)

    @commands.hybrid_command(
        name="mute",
        description="Mutes a user in the server.",
        usage="mute <user> <reason(optional)>",
        aliases=["silence"]
    )
    @app_commands.describe(
        user="The user that should be muted.",
        reason="The reason why the user should be muted.",
        length="The length of the mute in minutes."
    )
    @commands.has_permissions(manage_roles=True)
    async def mute(self, context: Context, user: discord.Member, reason: str = None, length: int = None) -> None:
        async with aiosqlite.connect(DB_PATH) as conn:
            c = await conn.cursor()
            await c.execute("SELECT role_id FROM GuildMuteRole WHERE guild_id = ?", (context.guild.id,))
            result = await c.fetchone()
            if result:
                role_id = result[0]
                role = context.guild.get_role(role_id)
                if role:
                    await user.add_roles(role)
                    if length:
                        end_time = datetime.now() + timedelta(minutes=length)
                        await c.execute("INSERT INTO GuildMutedUsers (guild_id, user_id, end_time) VALUES (?, ?, ?)",
                                        (context.guild.id, user.id, end_time.timestamp()))
                    else:
                        await c.execute("INSERT INTO GuildMutedUsers (guild_id, user_id) VALUES (?, ?)",
                                        (context.guild.id, user.id))
                    await conn.commit()
                    embed = discord.Embed(
                        title="User Muted",
                        description=f"{user.mention} has been muted.",
                        color=0xBEBEFE
                    )
                    embed.add_field(name="Reason", value=reason if reason else "No reason provided.")
                    embed.add_field(name="Length", value=f"{length} minutes" if length else "Indefinite")
                    await context.send(f"{user.mention} has been muted!")
                    await context.send(embed=embed)
                else:
                    embed = discord.Embed(
                        title="Mute Role Not Found",
                        description="No mute role was found for this server.",
                        color=0xE02B2B
                    )
                    await context.send(embed=embed)
            else:
                embed = discord.Embed(
                    title="Mute Role Not Found",
                    description="No mute role was found for this server.",
                    color=0xE02B2B
                )
                await context.send(embed=embed)

    @commands.hybrid_command(
        name="chatsync",
        description="Syncs the chat of two channels on 2 different servers.",
        usage="chatsync <channelID-1> <channelID-2>",
        aliases=["syncchat", "chatlink"]
    )
    @app_commands.describe(
        channel2="The ID of the second channel."
    )
    @commands.has_permissions(administrator=True)
    async def chatsync(self, context: Context, channel2: int) -> None:
        # Fetch the channels from their IDs
        channel1 = context.channel
        channel2 = await self.bot.fetch_channel(channel2)

        # Get the guilds from the channels
        guild1 = channel1.guild
        guild2 = channel2.guild

        async with aiosqlite.connect(DB_PATH) as conn:
            c = await conn.cursor()
            await c.execute(
                "SELECT * FROM ChatSync WHERE (channel_id_1 = ? AND channel_id_2 = ?) OR (channel_id_1 = ? AND channel_id_2 = ?)",
                (channel1.id, channel2.id, channel2.id, channel1.id))
            result = await c.fetchone()
            if result:
                embed = discord.Embed(
                    title="❌ Chat Sync Already Exists",
                    description="A chat sync already exists between these two channels.",
                    color=0xE02B2B
                )
                await context.send(embed=embed)
            else:
                await c.execute(
                    "INSERT INTO ChatSync (channel_id_1, guild_id_1, channel_id_2, guild_id_2) VALUES (?, ?, ?, ?)",
                    (channel1.id, guild1.id, channel2.id, guild2.id))
                await conn.commit()
                embed = discord.Embed(
                    title="✅ Chat Sync Created",
                    description=f"The chat between {channel1.mention} and {channel2.mention} has been synced.",
                    color=0xBEBEFE
                )
                await context.send(embed=embed)

    @commands.hybrid_command(
        name="unsyncchat",
        description="Unsyncs the chat of two channels on 2 different servers.",
        usage="unsyncchat <channelID-1> <channelID-2>",
        aliases=["unlinkchat"]
    )
    @app_commands.describe(
        channel2="The ID of the second channel."
    )
    @commands.has_permissions(administrator=True)
    async def unsyncchat(self, context: Context, channel2: int) -> None:
        # Fetch the channels from their IDs
        channel1 = context.channel
        channel2 = await self.bot.fetch_channel(channel2)

        # Get the guilds from the channels
        guild1 = channel1.guild
        guild2 = channel2.guild

        async with aiosqlite.connect(DB_PATH) as conn:
            c = await conn.cursor()
            await c.execute(
                "SELECT * FROM ChatSync WHERE (channel_id_1 = ? AND channel_id_2 = ?) OR (channel_id_1 = ? AND channel_id_2 = ?)",
                (channel1.id, channel2.id, channel2.id, channel1.id))
            result = await c.fetchone()
            if result:
                await c.execute(
                    "DELETE FROM ChatSync WHERE (guild_id_1 = ? AND channel_id_1 = ? AND guild_id_2 = ? AND channel_id_2 = ?) OR (guild_id_1 = ? AND channel_id_1 = ? AND guild_id_2 = ? AND channel_id_2 = ?)",
                    (channel1.id, guild1.id, channel2.id, guild2.id, channel2.id, guild2.id, channel1.id, guild1.id))
                await conn.commit()
                embed = discord.Embed(
                    title="✅ Chat Sync Removed",
                    description=f"The chat between {channel1.mention} and {channel2.mention} has been unsynced.",
                    color=0xBEBEFE
                )
                await context.send(embed=embed)
            else:
                embed = discord.Embed(
                    title="❌ Chat Sync Not Found",
                    description="No chat sync was found between these two channels.",
                    color=0xE02B2B
                )
                await context.send(embed=embed)

    @commands.hybrid_command(
        name="syncedchats",
        description="Shows the synced chats in the current channel.",
        usage="syncedchats",
        aliases=["syncedchannels", "syncedchat", "syncedchannel"]
    )
    async def syncedchats(self, context: Context) -> None:
        async with aiosqlite.connect(DB_PATH) as conn:
            c = await conn.cursor()
            await c.execute(
                "SELECT * FROM ChatSync WHERE guild_id_1 = ? OR guild_id_2 = ?",
                (context.guild.id, context.guild.id))
            result = await c.fetchall()
            if result:
                embed = discord.Embed(
                    title="Synced Chats",
                    description="The following channels are synced with this channel:",
                    color=0xBEBEFE
                )
                for row in result:
                    channel_id_1, guild_id_1, channel_id_2, guild_id_2 = row
                    if guild_id_1 == context.guild.id:
                        guild = self.bot.get_guild(guild_id_2)
                        channel = guild.get_channel(channel_id_2) if guild else None
                        if channel:
                            embed.add_field(name=f"{channel.guild.name} - #{channel.name}", value=f"ID: {channel.id}",
                                            inline=False)
                    elif guild_id_2 == context.guild.id:
                        guild = self.bot.get_guild(guild_id_1)
                        channel = guild.get_channel(channel_id_1) if guild else None
                        if channel:
                            embed.add_field(name=f"{channel.guild.name} - #{channel.name}", value=f"ID: {channel.id}",
                                            inline=False)
                await context.send(embed=embed)
            else:
                embed = discord.Embed(
                    title="No Synced Chats",
                    description="No channels are synced with this channel.",
                    color=0xE02B2B
                )
                await context.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        prefix = await guild_prefix(self, message.guild.id)
        if message.content.startswith(prefix):
            return

        async with aiosqlite.connect(DB_PATH) as conn:
            c = await conn.cursor()
            await c.execute(
                "SELECT * FROM ChatSync WHERE (guild_id_1 = ? AND channel_id_1 = ?) OR (guild_id_2 = ? AND channel_id_2 = ?)",
                (message.guild.id, message.channel.id, message.guild.id, message.channel.id))
            result = await c.fetchall()
            if result:
                for row in result:
                    channel_id_1, guild_id_1, channel_id_2, guild_id_2 = row
                    if guild_id_1 == message.guild.id and channel_id_1 == message.channel.id:
                        guild = self.bot.get_guild(guild_id_2)
                        channel = guild.get_channel(channel_id_2) if guild else None
                        if channel and not message.author == self.bot.user:
                            await channel.send(f"{message.author.mention}: {message.content}",
                                               allowed_mentions=discord.AllowedMentions.none())
                    elif guild_id_2 == message.guild.id and channel_id_2 == message.channel.id:
                        guild = self.bot.get_guild(guild_id_1)
                        channel = guild.get_channel(channel_id_1) if guild else None
                        if channel and not message.author == self.bot.user:
                            await channel.send(f"{message.author.mention}: {message.content}",
                                               allowed_mentions=discord.AllowedMentions.none())


@tasks.loop(minutes=1)
async def check_mutes(self):
    async with aiosqlite.connect(DB_PATH) as conn:
        c = await conn.cursor()
        await c.execute("SELECT * FROM GuildMutedUsers")
        result = await c.fetchall()
        for row in result:
            guild_id, user_id, end_time = row
            if datetime.now().timestamp() >= end_time:
                guild = self.bot.get_guild(guild_id)
                user = guild.get_member(user_id)
                if user:
                    await c.execute("SELECT role_id FROM GuildMuteRole WHERE guild_id = ?", (guild_id,))
                    role_id = await c.fetchone()
                    role = guild.get_role(role_id)
                    if role:
                        await user.remove_roles(role)
                await c.execute("DELETE FROM GuildMutedUsers WHERE guild_id = ? AND user_id = ?", (guild_id, user_id))
                await conn.commit()


async def setup(bot) -> None:
    await bot.add_cog(Moderation(bot))
