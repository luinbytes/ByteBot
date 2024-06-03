import json
import os
import urllib.parse

import aiohttp
import aiosqlite
import discord
from discord import app_commands
from discord.ext import commands, tasks
from discord.ext.commands import Context
from steam.steamid import SteamID

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

# FACEIT Stuff
player_search_url = "https://open.faceit.com/data/v4/players"

headers = {
    'accept': 'application/json',
    'Authorization': 'Bearer 65deedc2-1914-4efc-9308-a68cbe27db05'
}


async def get_steam_profile_name(steamid64):
    url = f"http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key={steam_api_key}&steamids={steamid64}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            data = await response.json()
            return data['response']['players'][0]['personaname']


class SteamTools(commands.Cog, name="steamtools"):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="steaminfo",
        description="Scrape info from a users steam account via their steamID.",
        usage="steaminfo <steamID>",
        aliases=["steam", "steamprofile", "steamuser"]
    )
    @app_commands.describe(
        steamid="The steamID of the user to scrape info from."
    )
    async def steamid(self, context: Context, steamid: str) -> None:
        try:
            steamid64 = SteamID.from_url(steamid).as_64
        except ValueError:
            embed = discord.Embed(
                title="Invalid Steam ID",
                description="Please enter a valid Steam ID, Steam ID3, Steam ID32, Steam ID64, or Steam profile URL.",
                color=discord.Color.red()
            )
            embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
            await context.send(embed=embed)
            return
        async with aiohttp.ClientSession() as session:
            async with session.get(f'https://api.snaz.in/v2/steam/user-profile/{steamid64}') as r:
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
                    embed.add_field(name="Bans",
                                    value=f"Community: {data['bans']['community']}\nGame: {data['bans']['game']}\nTrade: {data['bans']['trade']}\nVAC: {data['bans']['vac']}",
                                    inline=False)
                    embed.add_field(name="Level", value=data['level']['formatted'], inline=True)
                    embed.add_field(name="Member Since", value=data['badge']['meta'], inline=True)
                    friends = data['counts']['friends']['formatted'] if data['counts']['friends'] else 'None/Private'
                    embed.add_field(name="Friends", value=friends, inline=True)
                    embed.add_field(name="Games", value=data['counts']['games']['formatted'], inline=True)
                    embed.add_field(name="Badges", value=data['counts']['badges']['formatted'], inline=True)
                    embed.add_field(name="Artwork", value=data['counts']['artwork']['formatted'], inline=True)
                    embed.add_field(name="Screenshots", value=data['counts']['screenshots']['formatted'], inline=True)
                    workshop_files = data['counts']['workshop_files']['formatted'] if data['counts'][
                        'workshop_files'] else 'None/Private'
                    embed.add_field(name="Workshop Files", value=workshop_files, inline=True)
                    embed.add_field(name="Primary Group", value=data['primary_group']['name'], inline=True)
                    embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
                    await context.send(embed=embed)
                else:
                    embed = discord.embed(
                        title="Error",
                        description="An error occurred while fetching the data.",
                        color=discord.Color.red()
                    )
                    embed.add_field(name="Status Code", value=r.status, inline=False)
                    embed.add_field(name="Response", value=await r.text(), inline=False)
                    embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
                    await context.send(embed=embed)

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
            async with session.get(
                    f"{convert_to_steamid64}key={steam_api_key}&access_token={access_token}&vanityurl={vanity_name}") as resp:
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

        async with aiosqlite.connect(DB_PATH) as conn:
            async with conn.cursor() as cursor:
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
                    cursor.execute('UPDATE GuildBanChannels SET channel_id = ? WHERE guild_id = ?',
                                   (channel_id, guild_id))
                else:
                    cursor.execute('INSERT INTO GuildBanChannels (guild_id, channel_id) VALUES (?, ?)',
                                   (guild_id, channel_id))

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
        usage="tracksteam <steamID>",
        aliases=["track"]
    )
    @app_commands.describe(
        steamid="The steamID of the user to track."
    )
    async def track_steamid(self, context: Context, steamid: str) -> None:
        try:
            steamid64 = SteamID.from_url(steamid).as_64
        except ValueError:
            embed = discord.Embed(
                title="Invalid Steam ID",
                description="Please enter a valid Steam ID, Steam ID3, Steam ID32, Steam ID64, or Steam profile URL.",
                color=discord.Color.red()
            )
            embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
            await context.send(embed=embed)
            return

        guild_id = context.guild.id
        tracked_by = context.author.id
        profile_name = await get_steam_profile_name(steamid64)

        # check steamid against steam api
        async with aiohttp.ClientSession() as session:
            async with session.get(
                    f"{get_player_bans}key={steam_api_key}&access_token={access_token}&steamids={steamid64}") as resp:
                data = await resp.text()
                user_info = json.loads(data)
                player_info = user_info['players'][0]

        conn = aiosqlite.connect(DB_PATH)
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
                # Fetch the existing tracked_by field
                cursor.execute('SELECT tracked_by FROM GuildSteamBans WHERE guild_id = ? AND steamid_64 = ?',
                               (guild_id, steamid64))
                existing_tracked_by = cursor.fetchone()[0]

                # Check if the user's Discord ID is already in the tracked_by field
                if str(context.author.id) not in existing_tracked_by.split(','):
                    # Append the new Discord ID to the existing tracked_by field, with a comma if it's not empty
                    new_tracked_by = existing_tracked_by + (',' if existing_tracked_by else '') + str(context.author.id)

                    print(f'Before update: {new_tracked_by}')  # Debug print

                    # Update the tracked_by field in the database
                    cursor.execute('UPDATE GuildSteamBans SET tracked_by = ? WHERE guild_id = ? AND steamid_64 = ?',
                                   (new_tracked_by, guild_id, steamid64))

                    # Check if the UPDATE statement affected any rows
                    if cursor.rowcount > 0:
                        # Fetch the updated tracked_by field
                        cursor.execute('SELECT tracked_by FROM GuildSteamBans WHERE guild_id = ? AND steamid_64 = ?',
                                       (guild_id, steamid64))
                        conn.commit()
                        print(f'After update: {cursor.fetchone()[0]}')  # Debug print
                        # print everything in tracked_by
                        print(
                            f'All tracked_by fields: {cursor.execute("SELECT tracked_by FROM GuildSteamBans").fetchall()}',
                            end='\n\n')  # Debug print
                    else:
                        print('No rows updated')  # Debug print

                    # Rest of your code...
                    embed = discord.Embed(
                        title="Steam ID Already Tracked",
                        description=f"`{profile_name}` is already being tracked for bans. Your Discord ID has been added to the tracking list.",
                        color=discord.Color.red()
                    )
                    embed.add_field(name="Steam Profile",
                                    value=f"[Steam Profile](https://steamcommunity.com/profiles/{steamid64})",
                                    inline=False)
                    embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
                    await context.send(embed=embed)
                    return
                else:
                    embed = discord.Embed(
                        title="Already Tracking Steam ID",
                        description=f"You are already tracking {profile_name}.",
                        color=discord.Color.red()
                    )
                    embed.add_field(name="Steam Profile",
                                    value=f"[Steam Profile](https://steamcommunity.com/profiles/{steamid64})",
                                    inline=False)
                    embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
                    await context.send(embed=embed)
                    return

            cursor.execute(
                'UPDATE GuildSteamBans SET CommunityBanned = ?, VACBanned = ?, NumberOfVACBans = ?, DaysSinceLastBan = ?, NumberOfGameBans = ?, EconomyBan = ?, tracked_by = ?, channel_id = ? WHERE guild_id = ? AND steamid_64 = ?',
                (player_info['CommunityBanned'], player_info['VACBanned'], player_info['NumberOfVACBans'],
                 player_info['DaysSinceLastBan'], player_info['NumberOfGameBans'], player_info['EconomyBan'],
                 tracked_by, channel_id, guild_id, steamid64))
            conn.commit()
        else:
            cursor.execute(
                'INSERT INTO GuildSteamBans (guild_id, channel_id, tracked_by, steamid_64, CommunityBanned, VACBanned, NumberOfVACBans, DaysSinceLastBan, NumberOfGameBans, EconomyBan) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                (guild_id, channel_id, tracked_by, steamid64, player_info['CommunityBanned'], player_info['VACBanned'],
                 player_info['NumberOfVACBans'], player_info['DaysSinceLastBan'], player_info['NumberOfGameBans'],
                 player_info['EconomyBan']))
            conn.commit()

        conn.commit()
        conn.close()

        embed = discord.Embed(
            title="Tracking Steam ID",
            description=f"{profile_name} is now being tracked for bans.",
            color=discord.Color.green()
        )
        embed.add_field(name="Steam ID", value=f"`{steamid64}`", inline=False)
        embed.add_field(name="Steam Profile", value=f"[View Profile](https://steamcommunity.com/profiles/{steamid64})",
                        inline=False)
        embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
        await context.send(embed=embed)

    @commands.hybrid_command(
        name="untracksteam",
        description="Untrack a steam user for bans.",
        usage="untracksteam <steamID>",
        aliases=["untrack"]
    )
    @app_commands.describe(
        steamid="The steamID of the user to untrack."
    )
    async def untrack_steamid(self, context: Context, steamid: str) -> None:
        try:
            steamid64 = SteamID.from_url(steamid).as_64
        except ValueError:
            embed = discord.Embed(
                title="Invalid Steam ID",
                description="Please enter a valid Steam ID, Steam ID3, Steam ID32, Steam ID64, or Steam profile URL.",
                color=discord.Color.red()
            )
            embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
            await context.send(embed=embed)
            return

        guild_id = context.guild.id
        requested_by = context.author.id
        profile_name = await get_steam_profile_name(steamid64)

        async with aiosqlite.connect(DB_PATH) as conn:
            async with conn.cursor() as cursor:
                await cursor.execute('SELECT tracked_by FROM GuildSteamBans WHERE guild_id = ? AND steamid_64 = ?',
                                     (guild_id, steamid64))
                row = await cursor.fetchone()
        if row is None:
            embed = discord.Embed(
                title="Steam ID Not Tracked",
                description=f"`{profile_name}` is not being tracked for bans.",
                color=discord.Color.red()
            )
            embed.add_field(name="", value=f"[Steam Profile](https://steamcommunity.com/profiles/{steamid64})",
                            inline=False)
            embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
            await context.send(embed=embed)
        elif int(row[0]) != requested_by:
            embed = discord.Embed(
                title="Untrack Not Allowed",
                description=f"You are not allowed to untrack `{profile_name}` because you did not track them.",
                color=discord.Color.red()
            )
            embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
            embed.add_field(name="", value=f"[Steam Profile](https://steamcommunity.com/profiles/{steamid64})",
                            inline=False)
            await context.send(embed=embed)
        else:
            await cursor.execute('DELETE FROM GuildSteamBans WHERE guild_id = ? AND steamid_64 = ?',
                                 (guild_id, steamid64))
            embed = discord.Embed(
                title="Steam ID Untracked",
                description=f"`{profile_name}` is no longer being tracked for bans.",
                color=discord.Color.green()
            )
            embed.add_field(name="", value=f"[Steam Profile](https://steamcommunity.com/profiles/{steamid64})",
                            inline=False)
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

        async with aiosqlite.connect(DB_PATH) as conn:
            async with conn.cursor() as cursor:  # Create a Cursor object from the Result object
                await cursor.execute('SELECT steamid_64, tracked_by FROM GuildSteamBans WHERE guild_id = ?',
                                     (guild_id,))
                rows = await cursor.fetchall()
        if not rows:
            embed = discord.Embed(
                title="No Steam IDs Tracked",
                description="There are no steam IDs being tracked for bans.",
                color=discord.Color.red()
            )
            embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
            await context.send(embed=embed)
        else:
            tracked_ids_dict = {}
            for row in rows:
                steam_id = row[0]
                discord_ids = row[1].split(',')
                for discord_id in discord_ids:
                    discord_user = await self.bot.fetch_user(int(discord_id.strip()))
                    if steam_id not in tracked_ids_dict:
                        tracked_ids_dict[steam_id] = [discord_user.mention]
                    else:
                        tracked_ids_dict[steam_id].append(discord_user.mention)

            tracked_ids = []
            for steam_id, mentions in tracked_ids_dict.items():
                profile_name = await get_steam_profile_name(steam_id)
                tracked_ids.append(
                    f"[{profile_name}](https://steamcommunity.com/profiles/{steam_id}) tracked by {' '.join(mentions)}")

            embed = discord.Embed(
                title="Tracked Steam IDs",
                description="\n".join(tracked_ids),
                color=discord.Color.green()
            )
            embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar.url)
            await context.send(embed=embed)

    @tasks.loop(hours=1)
    async def check_bans(self):
        async with aiosqlite.connect(DB_PATH) as conn:
            async with conn.cursor() as cursor:
                await cursor.execute('SELECT * FROM GuildSteamBans')
                rows = await cursor.fetchall()

        for row in rows:
            guild_id, channel_id, tracked_by, steamid64, old_community_banned, old_vac_banned, old_number_of_vac_bans, old_days_since_last_ban, old_number_of_game_bans, old_economy_ban = row

            # Fetch the player_info from the Steam API
            async with aiohttp.ClientSession() as session:
                async with session.get(
                        f"{get_player_bans}key={steam_api_key}&access_token={access_token}&steamids={steamid64}") as resp:
                    data = await resp.text()
                    print(data)
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
                changes.append(
                    f"Community Banned: {'No' if old_community_banned == 0 else 'Yes'} ➡️ {'No' if new_community_banned == 0 else 'Yes'}")
            if old_vac_banned != new_vac_banned:
                changes.append(
                    f"VAC Banned: {'No' if old_vac_banned == 0 else 'Yes'} ➡️ {'No' if new_vac_banned == 0 else 'Yes'}")
            if old_number_of_vac_bans != new_number_of_vac_bans:
                changes.append(f"Number of VAC Bans: {old_number_of_vac_bans} ➡️ {new_number_of_vac_bans}")
            if old_number_of_game_bans != new_number_of_game_bans:
                changes.append(f"Number of Game Bans: {old_number_of_game_bans} ➡️ {new_number_of_game_bans}")
            if old_economy_ban != new_economy_ban:
                changes.append(
                    f"Economy Ban: {'No' if old_economy_ban == 'none' else 'Yes'} ➡️ {'No' if new_economy_ban == 'none' else 'Yes'}")

            if changes:
                async with aiohttp.ClientSession() as session:
                    params = {'game': 'cs2', 'game_player_id': f'{steamid64}'}
                    async with session.get(player_search_url, params=params, headers=headers) as response:
                        data = await response.json()

                    # Send an embed into the channel id for the tracked user
                    channel = self.bot.get_channel(channel_id)
                    tracked_by_ids = tracked_by.split(',')
                    tracked_by_users = []
                    for tracked_by_id in tracked_by_ids:
                        user = await self.bot.fetch_user(int(tracked_by_id.strip()))
                        tracked_by_users.append(user.name)
                    description = f"[`{steamid64}`](https://steamcommunity.com/profiles/{steamid64})'s ban status has changed.\n\n" + "\n".join(
                        changes)

                    # Extract nickname
                    nickname = data.get('nickname', 'Unknown')

                    # Initialize the embed
                    embed = discord.Embed(
                        title="Ban Update [VACLink]",
                        description=description,
                        color=discord.Color.red(),
                        url=f"https://vaclist.net/account/{steamid64}"
                    )

                    # Check if 'errors' in data
                    if 'errors' in data:
                        embed.add_field(name="❌ FACEIT:", value="No FACEIT information available.", inline=False)
                    else:
                        # Update description
                        description = f"[`{steamid64}`](https://steamcommunity.com/profiles/{steamid64})'s ban status has changed.\n\n" + "\n".join(
                            changes)

                        # Fetch the names and URLs of the first 5 friends
                        friend_links = []
                        for friend_id in data.get('friends_ids', [])[:5]:
                            async with session.get(f"{player_search_url}/{friend_id}",
                                                   headers=headers) as friend_response:
                                friend_data = await friend_response.json()
                                friend_links.append(
                                    f"[{friend_data.get('nickname', 'Unknown')}](https://www.faceit.com/{friend_data.get('settings', {}).get('language', '')}/players/{friend_data.get('nickname', 'Unknown')})")

                        # Add fields to the embed
                        embed.add_field(name="Changes:", value="\n".join(changes), inline=False)
                        embed.add_field(name="\u200b", value="\u200b", inline=False)
                        embed.add_field(name="✔️ FACEIT:", value="", inline=True)
                        embed.add_field(name="🔗 Steam Info",
                                        value=f"[Steam Profile](https://steamcommunity.com/profiles/{steamid64})\nSteam ID: `{data.get('platforms', {}).get('steam', '')}`\nNew Steam ID: `{data.get('new_steam_id', '')}`\nSteam ID 64: `{data.get('steam_id_64', '')}`",
                                        inline=False)
                        embed.add_field(name="🔫 CSGO Info",
                                        value=f"Region: `{data.get('games', {}).get('csgo', {}).get('region', '')}`\nSkill Level: `{data.get('games', {}).get('csgo', {}).get('skill_level', '')}`\nFaceit ELO: `{data.get('games', {}).get('csgo', {}).get('faceit_elo', '')}`",
                                        inline=False)
                        embed.add_field(name="🎮 CS2 Info",
                                        value=f"Region: `{data.get('games', {}).get('cs2', {}).get('region', '')}`\nSkill Level: `{data.get('games', {}).get('cs2', {}).get('skill_level', '')}`\nFaceit ELO: `{data.get('games', {}).get('cs2', {}).get('faceit_elo', '')}`",
                                        inline=False)
                        embed.add_field(name="👥 Friends", value=", ".join(friend_links) + " and more...",
                                        inline=False)  # Display only first 5 friends

                        # Add FACEIT profile link
                        embed.add_field(name="",
                                        value=f"[FACEIT Profile](https://www.faceit.com/en/players/{nickname})",
                                        inline=False)

                    # Set footer
                    embed.set_footer(text=f"Tracked by {' '.join(tracked_by_users)}")
                    tracked_by_mentions = []
                    for tracked_by_id in tracked_by_ids:
                        user = await self.bot.fetch_user(int(tracked_by_id.strip()))
                        tracked_by_mentions.append(user.mention)

                    # Only send the message if there are mentions
                    if tracked_by_mentions:
                        await channel.send(f"{' '.join(tracked_by_mentions)}", embed=embed)

                # Update the info in the database for the next check
                cursor.execute(
                    'UPDATE GuildSteamBans SET CommunityBanned = ?, VACBanned = ?, NumberOfVACBans = ?, DaysSinceLastBan = ?, NumberOfGameBans = ?, EconomyBan = ? WHERE guild_id = ? AND steamid_64 = ?',
                    (new_community_banned, new_vac_banned, new_number_of_vac_bans, new_days_since_last_ban,
                     new_number_of_game_bans, new_economy_ban, guild_id, steamid64))

    @commands.hybrid_command(
        name="faceit",
        description="Get a players FACEIT profile.",
        usage="faceit <steamID64>",
        aliases=["faceitprofile", "faceituser"]
    )
    @app_commands.describe(
        steamid64="The steamID64 of the user to scrape info from."
    )
    async def faceit(self, context: Context, steamid64: str) -> None:
        params = {'game': 'cs2', 'game_player_id': f'{steamid64}'}
        async with aiohttp.ClientSession() as session:
            async with session.get(player_search_url, params=params, headers=headers) as response:
                data = await response.json()

            if 'errors' in data:
                embed = discord.Embed(
                    title="Player Not Found",
                    description="The player was not found on FACEIT.",
                    color=discord.Color.red()
                )
                await context.send(embed=embed)
                return

            # Fetch the names and URLs of the first 5 friends
            friend_links = []
            for friend_id in data['friends_ids'][:5]:
                async with session.get(f"{player_search_url}/{friend_id}", headers=headers) as friend_response:
                    friend_data = await friend_response.json()
                    friend_links.append(
                        f"[{friend_data['nickname']}](https://www.faceit.com/{friend_data['settings']['language']}/players/{friend_data['nickname']})")

            # Create a Discord embed with the data
            embed = discord.Embed(
                title=f"🎮 Player Info for {data['nickname']}",
                description=f"🆔 Player ID: `{data['player_id']}`\n🌍 Country: `{data['country']}`\n🗣️ Language: `{data['settings']['language']}`",
                color=discord.Color.blue()
            )
            embed.set_thumbnail(url=data['avatar'])
            embed.add_field(name="🔗 Steam Info",
                            value=f"[Steam Profile](https://steamcommunity.com/profiles/{steamid64})\nSteam ID: `{data['platforms']['steam']}`\nNew Steam ID: `{data['new_steam_id']}`\nSteam ID 64: `{data['steam_id_64']}`",
                            inline=False)
            embed.add_field(name="🔫 CSGO Info",
                            value=f"Region: `{data['games']['csgo']['region']}`\nSkill Level: `{data['games']['csgo']['skill_level']}`\nFaceit ELO: `{data['games']['csgo']['faceit_elo']}`",
                            inline=False)
            embed.add_field(name="🎮 CS2 Info",
                            value=f"Region: `{data['games']['cs2']['region']}`\nSkill Level: `{data['games']['cs2']['skill_level']}`\nFaceit ELO: `{data['games']['cs2']['faceit_elo']}`",
                            inline=False)
            embed.add_field(name="👥 Friends", value=", ".join(friend_links) + " and more...",
                            inline=False)  # Display only first 5 friends
            embed.set_footer(text=f"🔗 Profile URL: https://www.faceit.com/en/players/{data['nickname']}")
            await context.send(embed=embed)

    @check_bans.before_loop
    async def before_check_bans(self):
        await self.bot.wait_until_ready()

    @commands.Cog.listener()
    async def on_ready(self):
        self.check_bans.start()


async def setup(bot) -> None:
    await bot.add_cog(SteamTools(bot))
