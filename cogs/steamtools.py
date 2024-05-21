import aiohttp
import discord
import sqlite3
from discord.ext import commands, tasks
from discord.ext.commands import Context
from discord import app_commands

class SteamTracker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = sqlite3.connect('database/tracked_steamids.db')
        self.cursor = self.db.cursor()
        # self.check_bans.start()

    def populate_db(self):
        self.cursor.execute("CREATE TABLE IF NOT EXISTS tracked_steamids (steamid TEXT PRIMARY KEY, vac_bans INTEGER DEFAULT 0, game_bans INTEGER DEFAULT 0)")
        self.cursor.execute("CREATE TABLE IF NOT EXISTS config (guild_id INTEGER PRIMARY KEY, bans_channel INTEGER)")
        self.db.commit()

        self.cursor.execute("SELECT * FROM config")
        guilds = self.cursor.fetchall()
        if not guilds:
            for guild in self.bot.guilds:
                self.cursor.execute("INSERT INTO config VALUES (?, NULL)", (guild.id,))
            self.db.commit()

        self.cursor.execute("SELECT * FROM tracked_steamids")
        steamids = self.cursor.fetchall()
        if not steamids:
            # Populate the database with initial steamids
            initial_steamids = ["64n"]  # Replace with your desired initial steamids
            for steamid in initial_steamids:
                self.cursor.execute("INSERT INTO tracked_steamids VALUES (?, 0, 0)", (steamid,))
            self.db.commit()

    @commands.hybrid_command(
            name="track",
            description="Track a Steam ID",
            usage="track <steamid>",
    )
    @app_commands.describe(
        steamid="The Steam ID to track."
    )
    async def track(self, context, steamid: str):
        # Get current bans
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://api.snaz.in/v2/steam/user-profile/{steamid}") as response:
                data = await response.json()
                if data['vacBans'] > 0 or data['gameBans'] > 0:
                    self.cursor.execute("UPDATE tracked_steamids SET vac_bans = ?, game_bans = ? WHERE steamid = ?", (data['vacBans'], data['gameBans'], steamid))
                    self.db.commit()

        self.cursor.execute("INSERT INTO tracked_steamids VALUES (?)", (steamid,))
        self.db.commit()
        await context.send(f"Started tracking Steam ID {steamid}")

    @commands.hybrid_command(
            name="untrack",
            description="Untrack a Steam ID",
            usage="untrack <steamid>",
    )
    @app_commands.describe(
        steamid="The Steam ID to untrack."
    )
    async def untrack(self, context, steamid: str):
        self.cursor.execute("DELETE FROM tracked_steamids WHERE steamid = ?", (steamid,))
        self.db.commit()
        await context.send(f"Stopped tracking Steam ID {steamid}")

    @commands.hybrid_command(
            name="tracked",
            description="List all tracked Steam IDs",
            usage="tracked",
    )
    async def tracked(self, context):
        self.cursor.execute("SELECT * FROM tracked_steamids")
        steamids = self.cursor.fetchall()
        if not steamids:
            embed = discord.Embed(
                title="Error",
                description="No Steam IDs are being tracked.",
                color=discord.Color.red()
            )
            embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
            await context.send(embed=embed)
        else:
            embed = discord.Embed(
                title="Tracked Steam IDs",
                description="\n".join([f"Steam ID: {steamid[0]}" for steamid in steamids]),
                color=discord.Color.green()
            )
            embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
            await context.send(embed=embed)

    @commands.hybrid_command(
            name="setbanschannel",
            description="Set the channel to send ban notifications to.",
            usage="setbanschannel <channel>",
            aliases=["banschannel"]
    )
    @commands.has_permissions(administrator=True)
    @app_commands.describe(
        channel="The channel to send ban notifications to."
    )
    async def set_bans_channel(self, context: Context, channel: discord.TextChannel) -> None:
        self.cursor.execute("UPDATE config SET bans_channel = ? WHERE guild_id = ?", (channel.id, context.guild.id))
        self.db.commit()
        await context.send(f"Set the bans channel to {channel.mention}")

    # @tasks.loop(minutes=15)
    # async def check_bans(self):
    #     self.cursor.execute("SELECT * FROM tracked_steamids")
    #     steamids = self.cursor.fetchall()
    #     for steamid in steamids:
    #         async with aiohttp.ClientSession() as session:
    #             async with session.get(f"https://api.snaz.in/v2/steam/user-profile/{steamid[0]}") as response:
    #                 data = await response.json()
    #                 if data['vacBans'] > 0 or data['gameBans'] > 0:
    #                     self.cursor.execute("SELECT bans_channel FROM config WHERE guild_id = ?", (self.bot.guild.id,))
    #                     channel_id = self.cursor.fetchone()[0]
    #                     channel = self.bot.get_channel(channel_id)
    #                     embed = discord.Embed(
    #                         title="Ban Notification",
    #                         description=f"Steam ID {steamid[0]} has been banned.",
    #                         color=discord.Color.red()
    #                     )
    #                     embed.add_field(name="VAC Bans", value=data['vacBans'])

    # @check_bans.before_loop
    # async def before_check_bans(self):
    #     await self.bot.wait_until_ready()

async def setup(bot) -> None:
    await bot.add_cog(SteamTracker(bot))