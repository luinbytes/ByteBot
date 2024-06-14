import json
import os
import sqlite3

import aiosqlite
import discord
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import Context

DATABASE_DIR = "database"
ABS_PATH = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(DATABASE_DIR, "database.db")

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()


class Owner(commands.Cog, name="owner"):
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

    async def guild_autoroles(db, guild_id, role_id=None):
        async with aiosqlite.connect(DB_PATH) as db_conn:
            db = await db_conn.cursor()
            if role_id is not None:
                # Write to the table
                await db.execute("UPDATE GuildSettings SET autorole_id = ? WHERE guild_id = ?", (role_id, guild_id))
                await db_conn.commit()
            else:
                # Read from the table
                await db.execute("SELECT autorole_id FROM GuildSettings WHERE guild_id = ?", (guild_id,))
                row = await db.fetchone()
                return row[0] if row else None

    def guild_starboard_channels(db, guild_id, channel_id=None, starboard_min_reactions=None):
        db_conn = sqlite3.connect(DB_PATH)
        db = db_conn.cursor()
        if channel_id is not None and starboard_min_reactions is not None:
            # Write to the table
            db.execute(
                "UPDATE GuildSettings SET starboard_channel_id = ?, starboard_min_stars = ? WHERE guild_id = ?",
                (guild_id, channel_id, starboard_min_reactions))
            db.commit()
        else:
            # Read from the table
            cursor = db.execute(
                "SELECT starboard_channel_id, starboard_min_stars FROM GuildSettings WHERE guild_id = ?",
                (guild_id,))
            row = cursor.fetchone()
            return row if row else None
        db.close()

    @commands.command(
        name="sync",
        description="Synchonizes the slash commands.",
    )
    @app_commands.describe(scope="The scope of the sync. Can be `global` or `guild`")
    @commands.is_owner()
    async def sync(self, context: Context, scope: str) -> None:
        """
        Synchronizes the slash commands.

        :param context: The command context.
        :param scope: The scope of the sync. Can be `global` or `guild`.
        """

        if scope == "global":
            await context.bot.tree.sync()
            embed = discord.Embed(
                description="Slash commands have been globally synchronized.",
                color=0xBEBEFE,
            )
            await context.send(embed=embed)
            return
        elif scope == "guild":
            context.bot.tree.copy_global_to(guild=context.guild)
            await context.bot.tree.sync(guild=context.guild)
            embed = discord.Embed(
                description="Slash commands have been synchronized in this guild.",
                color=0xBEBEFE,
            )
            await context.send(embed=embed)
            return
        embed = discord.Embed(
            description="The scope must be `global` or `guild`.", color=0xE02B2B
        )
        await context.send(embed=embed)

    @commands.command(
        name="unsync",
        description="Unsynchonizes the slash commands.",
    )
    @app_commands.describe(
        scope="The scope of the sync. Can be `global`, `current_guild` or `guild`"
    )
    @commands.is_owner()
    async def unsync(self, context: Context, scope: str) -> None:
        """
        Un-Synchronizes the slash commands.

        :param context: The command context.
        :param scope: The scope of the sync. Can be `global`, `current_guild` or `guild`.
        """

        if scope == "global":
            context.bot.tree.clear_commands(guild=None)
            await context.bot.tree.sync()
            embed = discord.Embed(
                description="Slash commands have been globally unsynchronized.",
                color=0xBEBEFE,
            )
            await context.send(embed=embed)
            return
        elif scope == "guild":
            context.bot.tree.clear_commands(guild=context.guild)
            await context.bot.tree.sync(guild=context.guild)
            embed = discord.Embed(
                description="Slash commands have been unsynchronized in this guild.",
                color=0xBEBEFE,
            )
            await context.send(embed=embed)
            return
        embed = discord.Embed(
            description="The scope must be `global` or `guild`.", color=0xE02B2B
        )
        await context.send(embed=embed)

    @commands.hybrid_command(
        name="load",
        description="Load a cog",
    )
    @app_commands.describe(cog="The name of the cog to load")
    @commands.is_owner()
    async def load(self, context: Context, cog: str) -> None:
        """
        The bot will load the given cog.

        :param context: The hybrid command context.
        :param cog: The name of the cog to load.
        """
        try:
            await self.bot.load_extension(f"cogs.{cog}")
        except Exception:
            embed = discord.Embed(
                description=f"Could not load the `{cog}` cog.", color=0xE02B2B
            )
            await context.send(embed=embed)
            return
        embed = discord.Embed(
            description=f"Successfully loaded the `{cog}` cog.", color=0xBEBEFE
        )
        await context.send(embed=embed)

    @commands.hybrid_command(
        name="unload",
        description="Unloads a cog.",
    )
    @app_commands.describe(cog="The name of the cog to unload")
    @commands.is_owner()
    async def unload(self, context: Context, cog: str) -> None:
        """
        The bot will unload the given cog.

        :param context: The hybrid command context.
        :param cog: The name of the cog to unload.
        """
        try:
            await self.bot.unload_extension(f"cogs.{cog}")
        except Exception:
            embed = discord.Embed(
                description=f"Could not unload the `{cog}` cog.", color=0xE02B2B
            )
            await context.send(embed=embed)
            return
        embed = discord.Embed(
            description=f"Successfully unloaded the `{cog}` cog.", color=0xBEBEFE
        )
        await context.send(embed=embed)

    @commands.hybrid_command(
        name="reload",
        description="Reloads a cog.",
    )
    @app_commands.describe(cog="The name of the cog to reload")
    @commands.is_owner()
    async def reload(self, context: Context, cog: str) -> None:
        """
        The bot will reload the given cog.

        :param context: The hybrid command context.
        :param cog: The name of the cog to reload.
        """
        try:
            await self.bot.reload_extension(f"cogs.{cog}")
        except Exception:
            embed = discord.Embed(
                description=f"Could not reload the `{cog}` cog.", color=0xE02B2B
            )
            await context.send(embed=embed)
            return
        embed = discord.Embed(
            description=f"Successfully reloaded the `{cog}` cog.", color=0xBEBEFE
        )
        await context.send(embed=embed)

    @commands.hybrid_command(
        name="shutdown",
        description="Make the bot shutdown.",
    )
    @commands.is_owner()
    async def shutdown(self, context: Context) -> None:
        """
        Shuts down the bot.

        :param context: The hybrid command context.
        """
        embed = discord.Embed(description="Shutting down. Bye! :wave:", color=0xBEBEFE)
        await context.send(embed=embed)
        await self.bot.close()

    @commands.hybrid_command(
        name="say",
        description="The bot will say anything you want.",
    )
    @app_commands.describe(message="The message that should be repeated by the bot")
    @commands.is_owner()
    async def say(self, context: Context, *, message: str) -> None:
        """
        The bot will say anything you want.

        :param context: The hybrid command context.
        :param message: The message that should be repeated by the bot.
        """
        await context.send(message)

    @commands.hybrid_command(
        name="embed",
        description="The bot will say anything you want, but within embeds.",
    )
    @app_commands.describe(message="The message that should be repeated by the bot")
    @commands.is_owner()
    async def embed(self, context: Context, *, message: str) -> None:
        """
        The bot will say anything you want, but using embeds.

        :param context: The hybrid command context.
        :param message: The message that should be repeated by the bot.
        """
        embed = discord.Embed(description=message, color=0xBEBEFE)
        await context.send(embed=embed)

    @commands.hybrid_command(
        name="addcurr",
        description="Add a currency to a user's balance.",
        usage="<@user> <amount>"
    )
    @commands.is_owner()
    async def addcurr(self, context: Context, user: discord.User, amount: int) -> None:
        """
        This command allows administrators to add currency to a user's balance.

        :param context: The application command context.
        :param user: The user to add currency to.
        :param amount: The amount of currency to add.
        """
        user_id = user.id

        c.execute("SELECT user_id FROM UserEconomy WHERE user_id = ?", (user_id,))
        user_data = c.fetchone()
        if not user_data:
            embed = discord.Embed(
                title="User Not Registered",
                description="The specified user is not registered.",
                color=discord.Color.red()
            )
            embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
            await context.send(embed=embed)
            return

        c.execute("UPDATE UserEconomy SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
        conn.commit()

        embed = discord.Embed(
            title="🪙 Currency Added",
            description=f"{amount} coins have been added to {user.display_name}'s balance.",
            color=discord.Color.green()
        )
        embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
        await context.send(embed=embed)

    @commands.hybrid_command(
        name="rmbalance",
        description="Remove a user's balance.",
        usage="<@user> <@amount>",
        aliases=["rmbal", "removebal", "removebalance"]
    )
    @commands.is_owner()
    async def rmcurr(self, ctx, user: discord.User, amount: int):
        """
        Remove currency from a user's balance.
        
        :param user: The user to remove currency from.
        :param amount: The amount of currency to remove.
        """
        user_id = user.id

        c.execute("SELECT user_id FROM UserEconomy WHERE user_id = ?", (user_id,))
        user_data = c.fetchone()
        if not user_data:
            embed = discord.Embed(
                title="User Not Registered",
                description="The specified user is not registered.",
                color=discord.Color.red()
            )
            embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.avatar)
            await ctx.send(embed=embed)
            return

        c.execute("UPDATE UserEconomy SET balance = balance - ? WHERE user_id = ?", (amount, user_id))
        conn.commit()

        embed = discord.Embed(
            title="🪙 Currency Removed",
            description=f"{amount} coins have been removed from {user.display_name}'s balance.",
            color=discord.Color.green()
        )
        embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.avatar)
        await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="resetbalance",
        description="Resets a user's balance.",
        usage="<@user>",
        aliases=["rsbalance", "resetbal", "rsbal"]
    )
    @commands.is_owner()
    async def resetcurr(self, ctx, user: discord.User):
        """
        Reset a user's balance to 0.
        
        :param user: The user whose balance to reset.
        """
        user_id = user.id

        # Check if user is registered
        c.execute("SELECT user_id FROM UserEconomy WHERE user_id = ?", (user_id,))
        user_data = c.fetchone()
        if not user_data:
            embed = discord.Embed(
                title="User Not Registered",
                description="The specified user is not registered.",
                color=discord.Color.red()
            )
            embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.avatar)
            await ctx.send(embed=embed)
            return

        # Reset user's balance to 0
        c.execute("UPDATE UserEconomy SET balance = 0 WHERE user_id = ?", (user_id,))
        conn.commit()

        embed = discord.Embed(
            title="🪙 Balance Reset",
            description=f"{user.display_name}'s balance has been reset to 0 coins.",
            color=discord.Color.green()
        )
        embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.avatar)
        await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="setbalance",
        description="Set a user's balance.",
        usage="<@user> <@amount>",
        aliases=["setbal"]
    )
    @commands.has_permissions(administrator=True)
    async def setcurr(self, ctx, user: discord.User, amount: int):
        """
        Set a user's balance to a specific amount.
        
        :param user: The user whose balance to set.
        :param amount: The amount of currency to set.
        """
        user_id = user.id

        # Check if user is registered
        c.execute("SELECT user_id FROM UserEconomy WHERE user_id = ?", (user_id,))
        user_data = c.fetchone()
        if not user_data:
            embed = discord.Embed(
                title="User Not Registered",
                description="The specified user is not registered.",
                color=discord.Color.red()
            )
            embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.avatar)
            await ctx.send(embed=embed)
            return

        # Update user's balance to the specified amount
        c.execute("UPDATE UserEconomy SET balance = ? WHERE user_id = ?", (amount, user_id))
        conn.commit()

        embed = discord.Embed(
            title="🪙 Balance Set",
            description=f"{user.display_name}'s balance has been set to {amount} coins.",
            color=discord.Color.green()
        )
        embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.avatar)
        await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="setcolourroleprice",
        description="Set the price of a colour role.",
        usage="<price>",
        aliases=["colourroleprice", "setcolourrole"]
    )
    @app_commands.describe(price="The price of the colour role.")
    @commands.is_owner()
    async def setcolourroleprice(self, context: Context, price: int = None) -> None:
        """
        Set the price of a colour role.
        
        :param price: The price of the colour role.
        """
        config = await self.load_config()

        if not price:
            embed = discord.Embed(
                title="Colour Role Price",
                description=f"The price of a colour role is currently set to {config['market_colour_pricing']}.",
                color=discord.Color.blue()
            )
            embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
            await context.send(embed=embed)
            return
        else:
            config["market_colour_pricing"] = price
            await self.save_config(config)

            embed = discord.Embed(
                title="Colour Role Price",
                description=f"The price of a colour role has been set to {price}.",
                color=discord.Color.green()
            )
            embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
            await context.send(embed=embed)

    @commands.hybrid_command(
        name="massmessage",
        description="Send a message to all servers.",
        usage="<message>",
        aliases=["massmsg"]
    )
    @app_commands.describe(message="The message to send.")
    @commands.is_owner()
    async def massmessage(self, context: Context, *, message: str):
        """
        Send a message to all servers.

        :param message: The message to send.
        """
        for guild in self.bot.guilds:
            # try and find a general channel, if not then use the first channel
            channel = discord.utils.get(guild.text_channels, name="general")
            if not channel:
                channel = guild.text_channels[0]
            embed = discord.Embed(title="ByteBot Mass Message", description=message, color=discord.Color.pink())
            embed.set_footer(text=f"Message from the developer")
            try:
                await channel.send(embed=embed)
            except discord.Forbidden:
                continue  # Skip this server and continue with the next one
        embed = discord.Embed(
            title="Message Sent",
            description="The message has been sent successfully.",
            color=discord.Color.green()
        )
        embed.add_field(name="Message", value=message)
        embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
        await context.send(embed=embed)

    @commands.hybrid_command(
        name="massmessage",
        description="Send a message to all servers.",
        usage="<message>",
        aliases=["massmsg"]
    )
    @app_commands.describe(message="The message to send.")
    @commands.is_owner()
    async def massmessage(self, context: Context, *, message: str):
        """
        Send a message to all servers.

        :param message: The message to send.
        """
        for guild in self.bot.guilds:
            # try and find a general channel, if not then use the first channel
            channel = discord.utils.get(guild.text_channels, name="general")
            if not channel:
                channel = guild.text_channels[0]
            embed = discord.Embed(title="ByteBot Mass Message", description=message, color=discord.Color.pink())
            embed.set_footer(text=f"Message from the developer")
            try:
                await channel.send(embed=embed)
            except discord.Forbidden:
                continue  # Skip this server and continue with the next one
        embed = discord.Embed(
            title="Message Sent",
            description="The message has been sent successfully.",
            color=discord.Color.green()
        )
        embed.add_field(name="Message", value=message)
        embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
        await context.send(embed=embed)


@commands.Cog.listener()
async def on_disconnect(self):
    conn.close()


async def setup(bot) -> None:
    await bot.add_cog(Owner(bot))
