import logging
import os
from datetime import timedelta

import aiosqlite
import discord
import wavelink
from discord.ext import commands
from discord.ext.commands import Context

# Ensure database directory exists
DATABASE_DIR = "database"
if not os.path.exists(DATABASE_DIR):
    os.makedirs(DATABASE_DIR)
DB_PATH = os.path.join(DATABASE_DIR, "database.db")


class Music(commands.Cog, name="music"):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.channel = None
        self.volume = 5

    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, node: wavelink.Node) -> None:
        logging.info(logging.INFO, f"Wavelink node '{node.node.uri}' is ready.")

    @commands.Cog.listener()
    async def on_wavelink_track_start(self, payload: wavelink.TrackStartEventPayload) -> None:
        player: wavelink.Player | None = payload.player
        if not player:
            return

        track: wavelink.Playable = payload.track
        track_duration = str(timedelta(milliseconds=track.length))
        if '.' in track_duration:
            track_duration = track_duration.split('.')[0]
        description = track.title

        embed = discord.Embed(
            title="Now Playing",
            description=f"**{payload.track.title}**",
            color=discord.Colour.green()
        )
        if track.artwork:
            embed.set_thumbnail(url=payload.track.artwork)
        embed.add_field(name="Duration:", value=track_duration, inline=True)
        embed.add_field(name="Queue", value=f"{len(player.queue)} songs", inline=True)
        embed.set_footer(text=f"Source: {track.source.capitalize()}")
        await self.channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_wavelink_track_end(self, payload: wavelink.TrackStartEventPayload) -> None:
        player: wavelink.Player | None = payload.player

        if not player:
            return

        if player.queue:
            pass
        else:
            self.channel = None
            await player.disconnect()

    @commands.hybrid_command(
        name="setupmusic",
        description="Setup the music bot. Creates a text channel for music bot controls.",

    )
    @commands.has_permissions(manage_channels=True)
    async def setup_music(self, context: Context) -> None:
        await context.defer()
        # grab the guild id
        guild_id = context.guild.id
        # check if music channel already exists
        async with aiosqlite.connect(DB_PATH) as conn:
            c = await conn.cursor()
            channel_id = await c.execute("SELECT channel_id FROM GuildMusicChannels WHERE guild_id = ?",
                                         (guild_id,))
            channel_id = await channel_id.fetchone()
            if channel_id:
                embed = discord.Embed(
                    title="Error",
                    description="Music bot is already setup in this server.",
                    color=discord.Colour.red()
                )
                await context.send(embed=embed)
                return

        # create a text channel
        channel = await context.guild.create_text_channel("music-control")
        channel_id = channel.id

        # send music control embed to the channel
        class MusicButtons(discord.ui.View):
            def __init__(self, user):
                super().__init__()
                self.user = user
                self.value = None

            @discord.ui.button(label="⏮️", style=discord.ButtonStyle.primary)
            async def previous(self, button: discord.ui.Button, interaction: discord.Interaction):
                self.value = "previous"
                self.stop()

            @discord.ui.button(label="⏯️", style=discord.ButtonStyle.green)
            async def pause(self, button: discord.ui.Button, interaction: discord.Interaction):
                self.value = "pause"
                self.stop()

            @discord.ui.button(label="⏭️", style=discord.ButtonStyle.primary)
            async def skip(self, button: discord.ui.Button, interaction: discord.Interaction):
                self.value = "skip"
                self.stop()

            @discord.ui.button(label="🔊+", style=discord.ButtonStyle.green)
            async def volume_up(self, button: discord.ui.Button, interaction: discord.Interaction):
                self.value = "volume_up"
                self.stop()

            @discord.ui.button(label="🔊-", style=discord.ButtonStyle.red)
            async def volume_down(self, button: discord.ui.Button, interaction: discord.Interaction):
                self.value = "volume_down"
                self.stop()

        embed = discord.Embed(
            title="🎶 ByteBot DJ",
            description="Welcome to ByteBot DJ! Use the buttons below to control the music bot.",
            color=discord.Colour.pink()
        )
        embed.set_thumbnail(
            url="https://community.mp3tag.de/uploads/default/original/2X/a/acf3edeb055e7b77114f9e393d1edeeda37e50c9.png")
        embed.add_field(name="Now Playing:", value="Nothing", inline=False)
        embed.set_footer(text="ByteBot DJ")
        buttons = MusicButtons(context.author)
        await channel.send(embed=embed, view=buttons)

        # grab the message id of the music control embed so its easily editable in the future
        message_id = channel.last_message_id

        # store these values in the database in the GuildMusicChannels table with aiosqlite
        try:
            async with aiosqlite.connect(DB_PATH) as conn:
                c = await conn.cursor()
                await c.execute("INSERT INTO GuildMusicChannels (guild_id, channel_id, message_id) VALUES (?, ?, ?)",
                                (guild_id, channel_id, message_id))
                await conn.commit()
                embed = discord.Embed(
                    title="Success",
                    description="Music bot setup successfully.",
                    color=discord.Colour.green()
                )
                embed.set_footer(text=f"Requested by {context.author.display_name}", icon_url=context.author.avatar.url)
                await context.send(embed=embed)
        except aiosqlite.IntegrityError:
            embed = discord.Embed(
                title="Error",
                description="Music bot is already setup in this server.",
                color=discord.Colour.red()
            )
            await context.send(embed=embed)
            return

    @commands.hybrid_command(
        name="removemusic",
        description="Remove the music bot setup from the server.",
        aliases=["deletemusic", "rmmusic", "delmusic"]
    )
    @commands.has_permissions(manage_channels=True)
    async def remove_music(self, context: Context) -> None:
        await context.defer()
        # grab the guild id
        guild_id = context.guild.id

        # remove the music channel
        try:
            async with aiosqlite.connect(DB_PATH) as conn:
                c = await conn.cursor()
                channel_id = await c.execute("SELECT channel_id FROM GuildMusicChannels WHERE guild_id = ?",
                                             (guild_id,))
                channel_id = await channel_id.fetchone()
                if channel_id:
                    channel = context.guild.get_channel(channel_id[0])
                    if channel is None:
                        embed = discord.Embed(
                            title="Error",
                            description="The music channel does not exist.",
                            color=discord.Colour.red()
                        )
                        await context.send(embed=embed)
                        return
                    try:
                        await channel.delete()
                    except discord.Forbidden:
                        embed = discord.Embed(
                            title="Error",
                            description="I do not have permission to delete the music channel.",
                            color=discord.Colour.red()
                        )
                        await context.send(embed=embed)
                        return

                else:
                    embed = discord.Embed(
                        title="Error",
                        description="Music bot is not setup in this server.",
                        color=discord.Colour.red()
                    )
                    await context.send(embed=embed)
                    return

                embed = discord.Embed(
                    title="Success",
                    description="Music bot removed successfully.",
                    color=discord.Colour.green()
                )
                embed.set_footer(text=f"Requested by {context.author.display_name}", icon_url=context.author.avatar.url)
                await context.send(embed=embed)
        except aiosqlite.IntegrityError:
            embed = discord.Embed(
                title="Error",
                description="Music bot is not setup in this server.",
                color=discord.Colour.red()
            )
            await context.send(embed=embed)
            pass

        try:
            async with aiosqlite.connect(DB_PATH) as conn:
                c = await conn.cursor()
                await c.execute("DELETE FROM GuildMusicChannels WHERE guild_id = ?", (guild_id,))
                await conn.commit()
        except aiosqlite.IntegrityError:
            embed = discord.Embed(
                title="Error",
                description="Music bot is not setup in this server.",
                color=discord.Colour.red()
            )
            await context.send(embed=embed)
            return


async def setup(bot) -> None:
    await bot.add_cog(Music(bot))
