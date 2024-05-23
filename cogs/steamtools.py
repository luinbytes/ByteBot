import aiohttp
import discord
import sqlite3
import json
import time
import os
from discord.ext import commands, tasks
from discord.ext.commands import Context
from discord import app_commands

DATABASE_DIR = "database"
ABS_PATH = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(DATABASE_DIR, "database.db")

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
        description="Track a user's ban status.",
        usage="tracksteam <steamID>",
        aliases=["trackban", "bantrack", "track"]
    )
    @app_commands.describe(
        steamid="The steamID of the user to track."
    )
    async def tracksteam(self, context: Context, steamid: str) -> None:
        guild_id = context.guild.id
        tracked_by = context.author.id

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        # Check if a logging channel has been set for this guild
        c.execute("SELECT channel_id FROM GuildBanChannels WHERE guild_id=?", (guild_id,))
        row = c.fetchone()
        if row is None:
            embed = discord.Embed(
                title="Track Steam",
                description="No logging channel has been set for this server.",
                color=discord.Colour.red()
            )
            embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
            await context.send(embed=embed)
            return
        
        c.execute("SELECT 1 FROM GuildSteamBans WHERE guild_id=? AND channel_id=? AND steamid_64=?", (guild_id, row[0], steamid))
        if c.fetchone() is not None:
            embed = discord.Embed(
                title="Track Steam",
                description="This user is already being tracked.",
                color=discord.Colour.red()
            )
            embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
            await context.send(embed=embed)
            return
        
        channel_id = row[0]

        # Make an API request to get the user's information
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://api.snaz.in/v2/steam/user-profile/{steamid}") as resp:
                data = await resp.text()
                user_info = json.loads(data)
            if 'status' in user_info and 'state' in user_info['status']:
                if user_info['status']['state'] == 'private':
                    embed = discord.Embed(
                        title="Track Steam",
                        description="This user has a private profile.",
                        color=discord.Colour.red()
                    )
                    embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
                    await context.send(embed=embed)
                    return

            
            days_since_last_ban = user_info['bans']['days_since_last']['value'] if 'bans' in user_info and 'days_since_last' in user_info['bans'] and user_info['bans']['days_since_last'] else None
            account_created = user_info['created'] if 'created' in user_info else None
            username = user_info['username'] if 'username' in user_info else None
            community_ban = user_info['bans']['community'] if 'bans' in user_info and 'community' in user_info['bans'] else None
            game_ban = user_info['bans']['game'] if 'bans' in user_info and 'game' in user_info['bans'] else None
            trade_ban = user_info['bans']['trade'] if 'bans' in user_info and 'trade' in user_info['bans'] else None
            vac_ban = user_info['bans']['vac'] if 'bans' in user_info and 'vac' in user_info['bans'] else None
            custom_url = user_info['custom_url'] if 'custom_url' in user_info else None
            level = user_info['level']['value'] if 'level' in user_info and 'value' in user_info['level'] else None
            private = user_info['private'] if 'private' in user_info else None
            real_name = user_info['real_name'] if 'real_name' in user_info else None
            status = user_info['status']['state'] if 'status' in user_info and 'state' in user_info['status'] else None
            
            c.execute("""
                INSERT INTO GuildSteamBans (
                    guild_id, channel_id, tracked_by, steamid_64, username, community_ban, game_ban, trade_ban, vac_ban, 
                    days_since_last_ban, account_created, custom_url, level, private, real_name, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                guild_id, channel_id, tracked_by, steamid, username, community_ban, 
                game_ban, trade_ban, vac_ban, 
                days_since_last_ban, account_created, custom_url, 
                level, private, real_name, status
            ))

        conn.commit()
        conn.close()

        embed = discord.Embed(
            title="Track Steam",
            description=f"{steamid} is now being tracked.",
            color=discord.Colour.green()
        )
        embed.set_thumbnail(url=user_info['avatar'])
        embed.set_footer(text=f"Requested by {context.author.name}", icon_url=user_info['avatar'])
        await context.send(embed=embed)

    @commands.hybrid_command(
        name="untracksteam",
        description="Untrack a user's ban status.",
        usage="untracksteam <steamID>",
        aliases=["untrackban", "banuntrack", "untrack"]
    )
    @app_commands.describe(
        steamusrid="The steamID of the user to untrack."
    )
    async def untracksteam(self, context: Context, steamusrid: str) -> None:
        guild_id = context.guild.id
        tracked_by = context.author.id

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        c.execute("SELECT 1 FROM GuildSteamBans WHERE guild_id=? AND steamid_64=?", (guild_id, steamusrid))
        if c.fetchone() is None:
            embed = discord.Embed(
                title="Untrack Steam",
                description="This user is not being tracked.",
                color=discord.Colour.red()
            )
            embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
            await context.send(embed=embed)
            return
        
        c.execute("SELECT 1 FROM GuildSteamBans WHERE guild_id=? AND steamid_64=? AND tracked_by=?", (guild_id, steamusrid, tracked_by))
        if c.fetchone() is None:
            embed = discord.Embed(
                title="Untrack Steam",
                description="You are not tracking this user.",
                color=discord.Colour.red()
            )
            embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
            await context.send(embed=embed)
            return
        
        c.execute("DELETE FROM GuildSteamBans WHERE guild_id=? AND steamid_64=?", (guild_id, steamusrid))

        c.execute("SELECT 1 FROM CachedSteamBans WHERE guild_id=? AND steamid_64=?", (guild_id, steamusrid))
        if c.fetchone() is not None:
            c.execute("DELETE FROM CachedSteamBans WHERE guild_id=? AND steamid_64=?", (guild_id, steamusrid))

        conn.commit()
        conn.close()

        embed = discord.Embed(
            title="Untrack Steam",
            description=f"{steamusrid} has been untracked.",
            color=discord.Colour.green()
        )
        embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
        await context.send(embed=embed)

    @commands.hybrid_command(
        name="tracking",
        description="List all users you are currently tracked.",
        usage="tracking",
        aliases=["tracklist", "listtrack"]
    )
    async def tracking(self, context: Context) -> None:
        guild_id = context.guild.id
        tracked_by = context.author.id

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        c.execute("SELECT steamid_64 FROM GuildSteamBans WHERE guild_id=? AND tracked_by=?", (guild_id, tracked_by))
        steam_ids = [row[0] for row in c.fetchall()]

        if not steam_ids:
            embed = discord.Embed(
                title="Tracking",
                description="You are not tracking any users.",
                color=discord.Colour.red()
            )
            embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
            await context.send(embed=embed)
            return

        embed = discord.Embed(
            title="Tracking",
            description="You are tracking the following users:",
            color=discord.Colour.green()
        )
        embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
        for steam_id in steam_ids:
            embed.add_field(name=steam_id, value=f"[Steam Profile](https://steamcommunity.com/profiles/{steam_id})", inline=False)
        await context.send(embed=embed)

    @tasks.loop(minutes=30)
    async def check_bans(self):
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        c.execute("SELECT steamid_64 FROM GuildSteamBans")
        steam_ids = [row[0] for row in c.fetchall()]

        for steam_id in steam_ids:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"https://api.snaz.in/v2/steam/user-profile/{steam_id}") as resp:
                    data = await resp.text()
                    user_info = json.loads(data)
                if 'status' in user_info and user_info['status']['state'] == 'private':
                    continue

            c.execute("SELECT * FROM GuildSteamBans WHERE steamid_64=?", (steam_id,))
            row = c.fetchone()
            cached_user_info = row[4:] if row is not None else [None] * 12
            guild_id, channel_id = row[:2] if row is not None else [None, None]
            is_private = user_info.get('private', False)

            if not is_private:
                current_user_info = [
                    user_info.get('username', None), 
                    int(user_info['bans']['community']) if 'bans' in user_info and 'community' in user_info['bans'] else None,
                    user_info['bans'].get('game', None) if 'bans' in user_info else None, 
                    int(user_info['bans'].get('trade', None)) if 'bans' in user_info and 'trade' in user_info['bans'] else None,
                    user_info['bans'].get('vac', None) if 'bans' in user_info else None, 
                    int(user_info['bans']['days_since_last']['formatted'].replace(',', '')) if 'bans' in user_info and user_info['bans'].get('days_since_last', {}).get('formatted', None) is not None else None,
                    user_info.get('created', None), 
                    user_info.get('custom_url', None), 
                    user_info['level'].get('value', None) if 'level' in user_info else None,
                    int(user_info.get('private', None)),
                    user_info.get('real_name', None), 
                    user_info['status'].get('state', None) if 'status' in user_info else None
                ]
    
                if any(str(current) != str(cached) for current, cached in zip(current_user_info, cached_user_info)):
                    field_names = ['username', 'community_ban', 'game_ban', 'trade_ban', 'vac_ban', 'days_since_last_ban', 'account_created', 'custom_url', 'level', 'private', 'real_name', 'status']
                    current_user_info_dict = dict(zip(field_names, current_user_info))
                    cached_user_info_dict = dict(zip(field_names, cached_user_info))
                    changes = []
        
                    for field, current_value in current_user_info_dict.items():
                        if field == 'days_since_last_ban':
                            continue
                        cached_value = cached_user_info_dict[field]
                        if str(current_value) != str(cached_value):
                            changes.append((field, f"{field}: {cached_value} -> {current_value}"))
        
                    if changes:
                        c.execute("SELECT 1 FROM GuildBanChannels WHERE guild_id=? AND channel_id=?", (guild_id, channel_id))
                        row = c.fetchone()
                        if row is not None:
                            guild = self.bot.get_guild(guild_id)
                            channel = guild.get_channel(channel_id)
        
                            title = "User Info Update"
                            footer = "User Info Update"
                            if any(change[0] == 'username' for change in changes):
                                title = "Username Change"
                                footer = f"Old Username: {cached_user_info_dict['username']}"
                            elif any(change[0].endswith('_ban') for change in changes):
                                title = "Ban Status Change"
                                footer = f"Old Ban Status: {cached_user_info_dict['username']}"
        
                            embed = discord.Embed(
                                title=title,
                                description=f"User {user_info['username']}'s info has been updated.",
                                color=discord.Colour.green()
                            )
                            embed.set_thumbnail(url=user_info['avatar'])
                            embed.set_footer(text=footer)
                            for _, change in changes:
                                embed.add_field(name="Change", value=change, inline=False)
                            await channel.send(embed=embed)
        
                c.execute("UPDATE CachedSteamBans SET username=?, community_ban=?, game_ban=?, trade_ban=?, vac_ban=?, days_since_last_ban=?, account_created=?, custom_url=?, level=?, private=?, real_name=?, status=?, last_checked=? WHERE steamid_64=?", (*current_user_info, int(time.time()), steam_id))
                conn.commit()

    @check_bans.before_loop
    async def before_check_bans(self):
        await self.bot.wait_until_ready()

    @commands.Cog.listener()
    async def on_ready(self):
        self.check_bans.start()

async def setup(bot) -> None:
    await bot.add_cog(SteamTools(bot))