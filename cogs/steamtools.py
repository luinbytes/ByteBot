import aiohttp
import discord
import sqlite3
import urllib.parse
import json
import time
import os
from discord.ext import commands, tasks
from discord.ext.commands import Context
from discord import app_commands

DATABASE_DIR = "database"
ABS_PATH = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(DATABASE_DIR, "database.db")

steam_api_key = "3D74A7C8126D2470FB47E835F149F45D"
access_token = "eyAidHlwIjogIkpXVCIsICJhbGciOiAiRWREU0EiIH0.eyAiaXNzIjogInI6MEVDOV8yNDExNENFMV9DMkIyNCIsICJzdWIiOiAiNzY1NjExOTkyMjA5MDc5MDYiLCAiYXVkIjogWyAid2ViOnN0b3JlIiBdLCAiZXhwIjogMTcxNjgxNjUwMSwgIm5iZiI6IDE3MDgwOTAwMDMsICJpYXQiOiAxNzE2NzMwMDAzLCAianRpIjogIjBFRTlfMjQ3QUI4MERfMDZBNUMiLCAib2F0IjogMTcwOTgxMzI2NywgInJ0X2V4cCI6IDE3MjgwMDc5ODUsICJwZXIiOiAwLCAiaXBfc3ViamVjdCI6ICIxOTMuMzIuMjQ4LjE1OSIsICJpcF9jb25maXJtZXIiOiAiMTkzLjMyLjI0OC4xNTkiIH0.ppi6qsVFsbFaF8AoU_smHIajTOVNV5iQgggt4Zdn6xUkLewn3_3wPRBazESLvFaCteWx3PYY3QBFMtJ5o5aKBw"
steam_id_test = "76561197964559112"

# Steam API Endpoints
# TODO - Add more endpoints for more data
get_player_bans = "https://api.steampowered.com/ISteamUser/GetPlayerBans/v1/?"
get_player_profile = "https://api.steampowered.com/ICSGOPlayers_730/GetPlayerProfile/v1/?"
get_player_profilecoin = "https://partner.steam-api.com/ICSGOPlayers_730/GetPlayerProfileCoin/v1/?"
convert_to_steamid64 = "http://api.steampowered.com/ISteamUser/ResolveVanityURL/v0001/?"

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
        steamuserid="The steamID of the user to scrape info from."
    )
    async def steamid(self, context: Context, steamuserid: str) -> None:
        async with aiohttp.ClientSession() as session:
            async with session.get(f'https://api.snaz.in/v2/steam/user-profile/{steamuserid}') as r:
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

    @commands.hybrid_command(
        name="steamid64",
        description="Convert a vanity URL into a SteamID64.",
        usage="steamid64 <vanityURL>",
        aliases=["sid64", "convertsteam"]
    )
    @app_commands.describe(
        vanityurl="The vanity URL to convert to a SteamID64."
    )
    async def steamid64(self, context: Context, vanityurl: str) -> None:
        parsed_url = urllib.parse.urlparse(vanityurl)
        if parsed_url.netloc:
            vanity_name = parsed_url.path.split('/')[-1]
        else:
            vanity_name = vanityurl

        async with aiohttp.ClientSession() as session:
            async with session.get(f"{convert_to_steamid64}key={steam_api_key}&access_token={access_token}&vanityurl={vanity_name}") as resp:
                data = await resp.text()
                user_info = json.loads(data)
                steamid64 = user_info['response']['steamid']
                embed = discord.Embed(
                    title="SteamID64 Converter",
                    description=f"SteamID64 for `{vanity_name}` -> `{steamid64}`",
                    color=discord.Color.green()
                )
                embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
                await context.send(embed=embed)
    
    @commands.hybrid_command(
        name="setbanchannel",
        description="Set the channel to post ban notifications.",
        usage="setbanchannel <channel>",
        aliases=["sbc"]
    )
    @app_commands.describe(
        channel="The channel to post ban notifications."
    )
    @commands.has_permissions(administrator=True)
    async def setbanchannel(self, context: Context, channel: discord.TextChannel) -> None:
        guild_id = context.guild.id
        channel_id = channel.id

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute('SELECT 1 FROM GuildBanChannels WHERE guild_id = ?', (guild_id,))
        if cursor.fetchone():
            cursor.execute('SELECT channel_id FROM GuildBanChannels WHERE guild_id = ?', (guild_id,))
            existing_channel_id = cursor.fetchone()
            if existing_channel_id and existing_channel_id[0] == channel_id:
                embed = discord.Embed(
                    title="Ban Channel Set",
                    description=f"Ban notifications are already being posted in {channel.mention}.",
                    color=discord.Color.red()
                )
                embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
                await context.send(embed=embed)
                return
            cursor.execute('UPDATE GuildBanChannels SET channel_id = ? WHERE guild_id = ?', (channel_id, guild_id))
        else:
            cursor.execute('INSERT INTO GuildBanChannels (guild_id, channel_id) VALUES (?, ?)', (guild_id, channel_id))

        conn.commit()
        conn.close()

        embed = discord.Embed(
            title="Ban Channel Set",
            description=f"Ban notifications will now be posted in {channel.mention}.",
            color=discord.Color.green()
        )
        embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
        await context.send(embed=embed)

    @commands.hybrid_command(
            name="tracksteam",
            description="Track a steam user for bans.",
            usage="tracksteam <steamID64>",
            aliases=["ts"]
    )
    @app_commands.describe(
        steamid64="The steamID of the user to track."
    )
    async def track_steamid(self, context: Context, steamid64: str) -> None:
        guild_id = context.guild.id
        tracked_by = context.author.id

        # check steamid against steam api
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{get_player_bans}key={steam_api_key}&access_token={access_token}&steamids={steam_id_test}") as resp:
                data = await resp.text()
                user_info = json.loads(data)
                player_info = user_info['players'][0]

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Fetch the channel_id from the GuildBanChannels table
        cursor.execute('SELECT channel_id FROM GuildBanChannels WHERE guild_id = ?', (guild_id,))
        row = cursor.fetchone()
        if row is None:
            embed = discord.Embed(
                title="Ban Channel Not Set",
                description="Please set the channel to post ban notifications using the `setbanchannel` command.",
                color=discord.Color.red()
            )
            embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
            await context.send(embed=embed)
            return
        channel_id = row[0]

        cursor.execute('SELECT 1 FROM GuildSteamBans WHERE steamid_64 = ?', (steamid64,))
        if cursor.fetchone():
            cursor.execute('SELECT 1 FROM GuildSteamBans WHERE guild_id = ? AND steamid_64 = ?', (guild_id, steamid64))
            if cursor.fetchone():
                embed = discord.Embed(
                    title="Steam ID Already Tracked",
                    description=f"{steamid64} is already being tracked for bans.",
                    color=discord.Color.red()
                )
                embed.add_field(name="", value=f"[Steam Profile](https://steamcommunity.com/profiles/{steamid64})", inline=False)
                embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
                await context.send(embed=embed)
                return
            cursor.execute('UPDATE GuildSteamBans SET CommunityBanned = ?, VACBanned = ?, NumberOfVACBans = ?, DaysSinceLastBan = ?, NumberOfGameBans = ?, EconomyBan = ?, tracked_by = ?, channel_id = ? WHERE guild_id = ? AND steamid_64 = ?',
                           (player_info['CommunityBanned'], player_info['VACBanned'], player_info['NumberOfVACBans'], player_info['DaysSinceLastBan'], player_info['NumberOfGameBans'], player_info['EconomyBan'], tracked_by, channel_id, guild_id, steamid64))
        else:
            cursor.execute('INSERT INTO GuildSteamBans (guild_id, channel_id, tracked_by, steamid_64, CommunityBanned, VACBanned, NumberOfVACBans, DaysSinceLastBan, NumberOfGameBans, EconomyBan) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                            (guild_id, channel_id, tracked_by, steamid64, player_info['CommunityBanned'], player_info['VACBanned'], player_info['NumberOfVACBans'], player_info['DaysSinceLastBan'], player_info['NumberOfGameBans'], player_info['EconomyBan']))

        conn.commit()
        conn.close()

        embed = discord.Embed(
            title="Steam ID Tracked",
            description=f"`{steamid64}` is now being tracked for bans.",
            color=discord.Color.green()
        )
        embed.add_field(name="", value=f"[Steam Profile](https://steamcommunity.com/profiles/{steamid64})", inline=False)
        embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
        await context.send(embed=embed)

    @commands.hybrid_command(
        name="untracksteam",
        description="Untrack a steam user for bans.",
        usage="untracksteam <steamID64>"
    )
    @app_commands.describe(
        steamid64="The steamID of the user to untrack."
    )
    async def untrack_steamid(self, context: Context, steamid64: str) -> None:
        guild_id = context.guild.id
        requested_by = context.author.id

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute('SELECT tracked_by FROM GuildSteamBans WHERE guild_id = ? AND steamid_64 = ?', (guild_id, steamid64))
        row = cursor.fetchone()
        if row is None:
            embed = discord.Embed(
                title="Steam ID Not Tracked",
                description=f"`{steamid64}` is not being tracked for bans.",
                color=discord.Color.red()
            )
            embed.add_field(name="", value=f"[Steam Profile](https://steamcommunity.com/profiles/{steamid64})", inline=False)
            embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
            await context.send(embed=embed)
        elif row[0] != requested_by:
            embed = discord.Embed(
                title="Untrack Not Allowed",
                description=f"You are not allowed to untrack `{steamid64}` because you did not track them.",
                color=discord.Color.red()
            )
            embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
            embed.add_field(name="", value=f"[Steam Profile](https://steamcommunity.com/profiles/{steamid64})", inline=False)
            await context.send(embed=embed)
        else:
            cursor.execute('DELETE FROM GuildSteamBans WHERE guild_id = ? AND steamid_64 = ?', (guild_id, steamid64))
            conn.commit()
            conn.close()
            embed = discord.Embed(
                title="Steam ID Untracked",
                description=f"`{steamid64}` is no longer being tracked for bans.",
                color=discord.Color.green()
            )
            embed.add_field(name="", value=f"[Steam Profile](https://steamcommunity.com/profiles/{steamid64})", inline=False)
            embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
            await context.send(embed=embed)

    @commands.hybrid_command(
            name="tracking",
            description="List all tracked steam users for bans.",
            usage="tracking",
            aliases=["listtracked", "listtrackedsteam", "listtracking", "trackedsteam", "tracked"]
    )
    async def list_tracked(self, context: Context) -> None:
        guild_id = context.guild.id

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute('SELECT steamid_64, tracked_by FROM GuildSteamBans WHERE guild_id = ?', (guild_id,))
        rows = cursor.fetchall()
        if not rows:
            embed = discord.Embed(
                title="No Steam IDs Tracked",
                description="There are no steam IDs being tracked for bans.",
                color=discord.Color.red()
            )
            embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
            await context.send(embed=embed)
        else:
            tracked_ids = []
            for row in rows:
                steam_id = row[0]
                discord_id = row[1]
                discord_user = await self.bot.fetch_user(discord_id)
                tracked_ids.append(f"[{steam_id}](https://steamcommunity.com/profiles/{steam_id}) tracked by {discord_user.name}")
            
            embed = discord.Embed(
                title="Tracked Steam IDs",
                description="\n".join(tracked_ids),
                color=discord.Color.green()
            )
            embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar.url)
            await context.send(embed=embed)
    
    @tasks.loop(hours=1)
    async def check_bans(self):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
    
        cursor.execute('SELECT * FROM GuildSteamBans')
        rows = cursor.fetchall()
    
        for row in rows:
            guild_id, channel_id, tracked_by, steamid64, old_community_banned, old_vac_banned, old_number_of_vac_bans, old_days_since_last_ban, old_number_of_game_bans, old_economy_ban = row
    
            # Fetch the player_info from the Steam API
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{get_player_bans}key={steam_api_key}&access_token={access_token}&steamids={steam_id_test}") as resp:
                    data = await resp.text()
                    user_info = json.loads(data)
                    player_info = user_info['players'][0]
    
            new_community_banned = player_info['CommunityBanned']
            new_vac_banned = player_info['VACBanned']
            new_number_of_vac_bans = player_info['NumberOfVACBans']
            new_days_since_last_ban = player_info['DaysSinceLastBan']
            new_number_of_game_bans = player_info['NumberOfGameBans']
            new_economy_ban = player_info['EconomyBan']
            # print(f"Old Community Banned: {old_community_banned}")
            # print(f"New Community Banned: {new_community_banned}")
            # print(f"Old VAC Banned: {old_vac_banned}")
            # print(f"New VAC Banned: {new_vac_banned}")
            # print(f"Old Number of VAC Bans: {old_number_of_vac_bans}")
            # print(f"New Number of VAC Bans: {new_number_of_vac_bans}")
            # print(f"Old Days Since Last Ban: {old_days_since_last_ban}")
            # print(f"New Days Since Last Ban: {new_days_since_last_ban}")
            # print(f"Old Number of Game Bans: {old_number_of_game_bans}")
            # print(f"New Number of Game Bans: {new_number_of_game_bans}")
            # print(f"Old Economy Ban: {old_economy_ban}")
            # print(f"New Economy Ban: {new_economy_ban}")

    
            changes = []
            if old_community_banned != new_community_banned:
                changes.append(f"Community Banned: {old_community_banned} -> {new_community_banned}")
            if old_vac_banned != new_vac_banned:
                changes.append(f"VAC Banned: {old_vac_banned} -> {new_vac_banned}")
            if old_number_of_vac_bans != new_number_of_vac_bans:
                changes.append(f"Number of VAC Bans: {old_number_of_vac_bans} -> {new_number_of_vac_bans}")
            if old_number_of_game_bans != new_number_of_game_bans:
                changes.append(f"Number of Game Bans: {old_number_of_game_bans} -> {new_number_of_game_bans}")
            if old_economy_ban != new_economy_ban:
                changes.append(f"Economy Ban: {old_economy_ban} -> {new_economy_ban}")

            if changes:
                # Send an embed into the channel id for the tracked user
                channel = self.bot.get_channel(channel_id)
                tracked_by_user = await self.bot.fetch_user(tracked_by)
                embed = discord.Embed(
                    title="Ban Status Changed",
                    description=f"`{steamid64}`'s ban status has changed.",
                    color=discord.Color.red()
                )
                embed.add_field(name="Changes", value="\n".join(changes), inline=False)
                embed.add_field(name="", value=f"[Steam Profile](https://steamcommunity.com/profiles/{steamid64})", inline=False)
                embed.set_footer(text=f"Tracked by {tracked_by_user.name}", icon_url=f"{tracked_by_user.avatar}")
                await channel.send(embed=embed)
    
                # Update the info in the database for the next check
                cursor.execute('UPDATE GuildSteamBans SET CommunityBanned = ?, VACBanned = ?, NumberOfVACBans = ?, DaysSinceLastBan = ?, NumberOfGameBans = ?, EconomyBan = ? WHERE guild_id = ? AND steamid_64 = ?',
                               (new_community_banned, new_vac_banned, new_number_of_vac_bans, new_days_since_last_ban, new_number_of_game_bans, new_economy_ban, guild_id, steamid64))
    
        conn.commit()
        conn.close()



    @check_bans.before_loop
    async def before_check_bans(self):
        await self.bot.wait_until_ready()

    @commands.Cog.listener()
    async def on_ready(self):
        self.check_bans.start()

async def setup(bot) -> None:
    await bot.add_cog(SteamTools(bot))