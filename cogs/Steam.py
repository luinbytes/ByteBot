import json
import os
import urllib.parse
from datetime import datetime

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

# Steam API Setup
steam_api_key = ""
access_token = ""
steam_id_test = ""

get_player_summaries = "https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/?"
get_player_bans = "https://api.steampowered.com/ISteamUser/GetPlayerBans/v1/?"
get_friends_list = "https://api.steampowered.com/ISteamUser/GetFriendList/v1/?"
convert_to_steamid64 = "https://api.steampowered.com/ISteamUser/ResolveVanityURL/v1/?"

# FACEIT API Setup
player_search_url = "https://open.faceit.com/data/v4/players"

headers = {
    'accept': 'application/json',
    'Authorization': 'Bearer ...'
}

# SteamHistory.net API Setup

# Example Data: 

# {
#  "response": [
#   {
#    "SteamID": "7656XXXXXXXXXXXXX",
#    "Name": "Username",
#    "CurrentState": "Permanent",
#    "BanReason": "Hacker",
#    "UnbanReason": null,
#    "BanTimestamp": 1685513965,
#    "UnbanTimestamp": 0,
#    "Server": "Skial"
#   }
#  ]
# }

steamhistory_api_key = ""
get_sourcebans = "https://steamhistory.net/api/sourcebans?key=key&shouldkey=0&steamids={steamids}"


async def get_steam_profile_name(steamid64):
    url = f"http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key={steam_api_key}&steamids={steamid64}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            data = await response.json()
            if 'response' in data and 'players' in data['response']:
                players = data['response']['players']
                if players:
                    return players[0]['personaname']
            return "Unknown Player"  # Or handle this case as you see fit
        
async def scrape_status_command(status):
    steamids = []
    flaggedids = []
    map_name = ""
    valve_official = False
    players = 0
    max_players = 0
    hostname = ""

    for line in status.split("\n"):
        print(f"Processing line: {line}")
        if line.startswith("#") and "[U:1:" not in line:
            print("Skipping comment line.")
            continue
        if "[U:1:" in line:
            steamid = line.split("[U:1:")[1].split("]")[0]
            steamids.append(f"[U:1:{steamid}]")
            print(f"Found SteamID: [U:1:{steamid}]")
        elif line.startswith("map"):
            map_name = line.split(":")[1].strip().split(" ")[0]
            print(f"Found map name: {map_name}")
        elif line.startswith("tags"):
            valve_official = "valve" in line
            print(f"Valve official server: {valve_official}")
        elif line.startswith("players"):
            players_info = line.split(":")[1].strip().split(",")[0]
            players = int(players_info.split(" ")[0])
            max_players = int(line.split("(")[1].split(" ")[0])
            print(f"Found players info: {players}/{max_players}")
        elif line.startswith("hostname"):
            hostname = line.split(":", 1)[1].strip()
            print(f"Found hostname: {hostname}")

    print("Finished scraping status command output.")

    for steamid in steamids:
        print(f"Processing SteamID: {steamid}")
        steamid64 = SteamID(steamid).as_64
        steam_profile_name = await get_steam_profile_name(steamid64)

        async with aiohttp.ClientSession() as session:
            # Get sourcebans info
            async with session.get(get_sourcebans.format(steamids=steamid64)) as response:
                data = await response.json()
                if data['response']:
                    sourcebans = data['response']
                    bans_info = []
                    for ban in sourcebans:
                        ban_info = {
                            "name_at_ban": ban['Name'],
                            "ban_reason": ban['BanReason'],
                            "ban_timestamp": datetime.utcfromtimestamp(ban['BanTimestamp']).strftime('%d-%m-%Y @ %H:%M:%S'),
                            "unban_timestamp": datetime.utcfromtimestamp(ban['UnbanTimestamp']).strftime('%d-%m-%Y @ %H:%M:%S') if ban['UnbanTimestamp'] != 0 else "N/A",
                            "unban_reason": ban['UnbanReason'],
                            "server": ban['Server'],
                            "current_state": ban['CurrentState']
                        }
                        flaggedids.append(steamid)
                        bans_info.append(ban_info)
                else:
                    bans_info = [{
                        "name_at_ban": "N/A",
                        "ban_reason": "No bans found.",
                        "ban_timestamp": "N/A",
                        "unban_timestamp": "N/A",
                        "server": "N/A",
                        "current_state": "N/A"
                    }]

        

    return flaggedids, map_name, valve_official, players, max_players, hostname

class status_form(discord.ui.Modal, title="TF2 Status Scraper"):
    feedback = discord.ui.TextInput(
        label="Please input the entire status output.",
        style=discord.TextStyle.long,
        placeholder="Paste the output here.",
        required=True,
        max_length=4000,
    )
    async def on_submit(self, interaction: discord.Interaction):
        self.interaction = interaction
        self.status_output = str(self.feedback)
        self.stop()
    
class SteamTools(commands.Cog, name="steamtools"):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="info",
        description="Scrapes as much info on a steam user as possible.",
    )
    @app_commands.describe(
        steamid="Scrapes as much info on a steam user as possible."
    )
    async def info(self, context: Context, steamid: str) -> None:
        await context.defer()
        try:
            if len(steamid) == 17:
                steamid64 = steamid
            else:
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
        
        has_bans = False

        async with aiohttp.ClientSession() as session:
            # Get sourcebans info
            async with session.get(get_sourcebans.format(steamids=steamid64)) as response:
                data = await response.json()
                if data['response']:
                    sourcebans = data['response']
                    bans_info = []
                    for ban in sourcebans:
                        ban_info = {
                            "name_at_ban": ban['Name'],
                            "ban_reason": ban['BanReason'],
                            "ban_timestamp": datetime.utcfromtimestamp(ban['BanTimestamp']).strftime('%d-%m-%Y @ %H:%M:%S'),
                            "unban_timestamp": datetime.utcfromtimestamp(ban['UnbanTimestamp']).strftime('%d-%m-%Y @ %H:%M:%S') if ban['UnbanTimestamp'] != 0 else "N/A",
                            "unban_reason": ban['UnbanReason'],
                            "server": ban['Server'],
                            "current_state": ban['CurrentState']
                        }
                        bans_info.append(ban_info)
                    has_bans = True
                else:
                    bans_info = [{
                        "name_at_ban": "N/A",
                        "ban_reason": "No bans found.",
                        "ban_timestamp": "N/A",
                        "unban_timestamp": "N/A",
                        "server": "N/A",
                        "current_state": "N/A"
                    }]

            # Get player summaries
            async with session.get(get_player_summaries + f"key={steam_api_key}&steamids={steamid64}") as response:
                data = await response.json()
                if data is not None:
                        community_visibility_state_map = {
                            1: "Private",
                            2: "Friends Only",
                            3: "Public"
                        }

                        profile_state_map = {
                            0: "Not setup",
                            1: "Setup"
                        }

                        persona_state_map = {
                            0: "Offline",
                            1: "Online",
                            2: "Busy",
                            3: "Away",
                            4: "Snooze",
                            5: "Looking to trade",
                            6: "Looking to play"
                        }

                        profile = data['response']['players'][0]
                        profile_name = profile['personaname']
                        profile_url = profile['profileurl']
                        avatar_url = profile['avatarfull']
                        time_created = datetime.utcfromtimestamp(profile['timecreated']).strftime('%d-%m-%Y @ %H:%M:%S')
                        community_visibility_state = community_visibility_state_map[profile['communityvisibilitystate']]
                        profile_state = profile_state_map[profile['profilestate']]
                        persona_state = persona_state_map[profile['personastate']]

            # Create embed
            if has_bans:
                embed = discord.Embed(
                    title=f"[FLAGGED] {profile_name}",
                    url=profile_url,
                    description=f"[SteamHistory](https://steamhistory.net/id/{steamid64}) bans detected.",
                    color=discord.Color.red()
                )
            else:
                embed = discord.Embed(
                    title=f"{profile_name}",
                    url=profile_url,
                    description=f"[SteamHistory](https://steamhistory.net/id/{steamid64}) no bans detected.",
                    color=discord.Color.blue()
                )
            embed.set_thumbnail(url=avatar_url)
            embed.add_field(name="Account Created", value=time_created, inline=True)
            embed.add_field(name="Community Visibility State", value=community_visibility_state, inline=True)
            embed.add_field(name="Profile State", value=profile_state, inline=True)
            embed.add_field(name="Persona State", value=persona_state, inline=True)
            embed.add_field(name="\u200b", value="\u200b", inline=False)

            if has_bans:
                for ban in bans_info:
                    if len(bans_info) == 1:
                        embed.add_field(name="Name at Ban", value=ban['name_at_ban'], inline=True)
                        embed.add_field(name="Ban Reason", value=ban['ban_reason'], inline=True)
                        embed.add_field(name="Ban Timestamp", value=ban['ban_timestamp'], inline=True)
                        if ban['current_state'] != "Permanent":
                            embed.add_field(name="Unban Timestamp", value=ban["unban_timestamp"], inline=True)
                        embed.add_field(name="Server", value=ban['server'], inline=True)
                        embed.add_field(name="Current State", value=ban['current_state'], inline=True)
                        if ban["current_state"] == "Unbanned":
                            embed.add_field(name="Unban Reason", value=ban['unban_reason'], inline=True)
                        embed.add_field(name="\u200b", value="\u200b", inline=False)
                    else:
                        embed.add_field(name="Ban #"+str(bans_info.index(ban)+1), value="", inline=False)
                        embed.add_field(name="Name at Ban", value=ban['name_at_ban'], inline=True)
                        embed.add_field(name="Ban Reason", value=ban['ban_reason'], inline=True)
                        embed.add_field(name="Ban Timestamp", value=ban['ban_timestamp'], inline=True)
                        if ban['current_state'] != "Permanent":
                            embed.add_field(name="Unban Timestamp", value=ban["unban_timestamp"], inline=True)
                        embed.add_field(name="Server", value=ban['server'], inline=True)
                        embed.add_field(name="Current State", value=ban['current_state'], inline=True)
                        if ban["current_state"] == "Unbanned":
                            embed.add_field(name="Unban Reason", value=ban['unban_reason'], inline=True)
                        embed.add_field(name="\u200b", value="\u200b", inline=False)

            embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)

            await context.send(embed=embed)

    @app_commands.command(
    name="status",
    description="Scrapes TF2 status.",
    )
    async def status(self, interaction: discord.Interaction):
        # Create and send the modal for user input
        status = status_form()
        await interaction.response.send_modal(status)

        # Wait for the user to submit the modal
        await status.wait()

        # Interaction is still valid after the modal is submitted
        flagged, map_name, valve_official, players, max_players, hostname = await scrape_status_command(status.status_output)

        # Create the embed for the status information
        embed = discord.Embed(
            title="TF2 Status",
            description=f"Hostname: {hostname}\nMap: {map_name}\nValve Official: {valve_official}\nPlayers: {players}/{max_players}",
            color=discord.Color.blue()
        )
        for steamid in flagged:
            steamid64 = SteamID(steamid).as_64
            steam_profile_name = await get_steam_profile_name(steamid64)
            embed.add_field(name=steam_profile_name, value=f"[SteamHistory](https://steamhistory.net/id/{steamid64})", inline=False)
        embed.set_footer(text=f"Requested by {interaction.user.name}", icon_url=interaction.user.avatar)

        # Send the response as a followup, no need to check if response is done
        await interaction.followup.send(embed=embed)

async def setup(bot) -> None:
    await bot.add_cog(SteamTools(bot))
