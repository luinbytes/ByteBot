import logging
import os
import traceback
from datetime import timedelta
from typing import cast

import aiosqlite
import discord
import wavelink
from discord.ext import commands
from discord.ext.commands import Context
from wavelink.exceptions import LavalinkLoadException

# Ensure database directory exists
DATABASE_DIR = "database"
if not os.path.exists(DATABASE_DIR):
    os.makedirs(DATABASE_DIR)
DB_PATH = os.path.join(DATABASE_DIR, "database.db")


class Music(commands.Cog, name="music"):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.channel = None

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
        await channel.set_permissions(context.guild.default_role, send_messages=True, read_messages=True,
                                      add_reactions=False)
        channel_id = channel.id

        class MusicSearchModal(discord.ui.Modal):
            def __init__(self, view, bot):
                super().__init__(title="Search for a song")
                self.view = view
                self.bot = bot

            response = discord.ui.TextInput(label="Search for a song", placeholder="Enter a song name or URL")

            async def on_submit(self, interaction: discord.Interaction):
                try:
                    query = self.response.value
                    await self.view.play_music(interaction.guild_id, query)
                    await interaction.response.send_message(f"Searching for {query}...")
                except Exception as e:
                    await interaction.response.send_message(f"An error occurred: {traceback.format_exc()}")

        # send music control embed to the channel
        class MusicButtons(discord.ui.View):
            def __init__(self, user, bot):
                super().__init__()
                self.user = user
                self.player = None
                self.volume = 10
                self.bot = bot
                self.wavelink = self.bot.wavelink

            async def play_music(self, guild_id, query):
                logging.log(logging.INFO, f"Playing {query}")
                player = wavelink.Player(context.guild.voice_client)
                self.player = player
                query = query.strip('<>')
                destination = self.user.voice.channel
                try:
                    tracks: wavelink.Search = await wavelink.Playable.search(query)
                    if not tracks:
                        return None
                except LavalinkLoadException:
                    return None

                # Connect the player to the voice channel if it's not already connected
                if not context.guild.voice_client:
                    await destination.connect(cls=wavelink.Player, self_deaf=True)

                track: wavelink.Playable = tracks[0]
                await self.player.queue.put_wait(track)

                if not self.player.playing:
                    await self.player.play(player.queue.get(), volume=self.volume)

            async def pause_music(self, guild_id):
                player = wavelink.Player(context.guild.voice_client)
                self.player = player
                await player.pause(not player.paused)

            async def skip_music(self, guild_id):
                player = wavelink.Player(context.guild.voice_client)
                self.player = player
                await player.stop()

            async def connect_to_channel(self, channel):
                player = wavelink.Player(context.guild.voice_client)
                self.player = player
                await player.connect(channel.id)

            async def disconnect_from_channel(self, guild_id):
                player: wavelink.Player = cast(
                    wavelink.Player,
                    context.guild.voice_client
                )
                await player.disconnect()

            @discord.ui.button(label="⏮️", style=discord.ButtonStyle.primary)
            async def previous(self, button: discord.ui.Button, interaction: discord.Interaction):
                player = wavelink.Player(context.guild.voice_client)
                self.player = player
                if self.player.get_player(interaction.guild_id).queue:
                    await self.skip_music(interaction.guild_id)
                    await interaction.response.send_message("Skipped to the previous song.")
                else:
                    await interaction.response.send_message("No previous song in the queue.")

            @discord.ui.button(label="⏯️", style=discord.ButtonStyle.green)
            async def pause(self, button: discord.ui.Button, interaction: discord.Interaction):
                player = wavelink.Player(context.guild.voice_client)
                self.player = player
                await self.pause_music(interaction.guild_id)
                await interaction.response.send_message("Toggled pause on the current song.")

            @discord.ui.button(label="⏭️", style=discord.ButtonStyle.primary)
            async def skip(self, button: discord.ui.Button, interaction: discord.Interaction):
                player = wavelink.Player(context.guild.voice_client)
                self.player = player
                await self.skip_music(interaction.guild_id)
                await interaction.response.send_message("Skipped the current song.")

            @discord.ui.button(label="🔊+", style=discord.ButtonStyle.green)
            async def volume_up(self, button: discord.ui.Button, interaction: discord.Interaction):
                player = wavelink.Player(context.guild.voice_client)
                self.player = player
                await player.set_volume(player.volume + 10)
                await interaction.response.send_message(f"Volume set to {player.volume}%")

            @discord.ui.button(label="🔊-", style=discord.ButtonStyle.red)
            async def volume_down(self, button: discord.ui.Button, interaction: discord.Interaction):
                player = wavelink.Player(context.guild.voice_client)
                self.player = player
                await player.set_volume(player.volume - 10)
                await interaction.response.send_message(f"Volume set to {player.volume}%")

            @discord.ui.button(label="🔍", style=discord.ButtonStyle.blurple)
            async def search(self, interaction: discord.Interaction, button: discord.ui.Button):
                await interaction.response.send_modal(MusicSearchModal(view=self, bot=self.bot))

        embed = discord.Embed(
            title="🎶 ByteBot DJ",
            description="Welcome to ByteBot DJ! Use the buttons below to control the music bot.",
            color=discord.Colour.pink()
        )
        embed.set_thumbnail(
            url="https://community.mp3tag.de/uploads/default/original/2X/a/acf3edeb055e7b77114f9e393d1edeeda37e50c9.png")
        embed.add_field(name="Now Playing:", value="Nothing", inline=False)
        embed.set_footer(text="ByteBot DJ")
        buttons = MusicButtons(context.author, self.bot)
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
                    description=f"Music bot setup successfully - {channel.mention}",
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
                            description="The music channel does not exist. Records have still been removed from the "
                                        "database.",
                            color=discord.Colour.red()
                        )
                        await context.send(embed=embed)
                        c = await conn.cursor()
                        await c.execute("DELETE FROM GuildMusicChannels WHERE guild_id = ?", (guild_id,))
                        await conn.commit()
                        return
                    try:
                        await channel.delete()
                    except discord.Forbidden:
                        embed = discord.Embed(
                            title="Error",
                            description="I do not have permission to delete the music channel. Records have still "
                                        "been removed from the database.",
                            color=discord.Colour.red()
                        )
                        await context.send(embed=embed)
                        c = await conn.cursor()
                        await c.execute("DELETE FROM GuildMusicChannels WHERE guild_id = ?", (guild_id,))
                        await conn.commit()
                        return

                else:
                    embed = discord.Embed(
                        title="Error",
                        description="Music bot is not setup in this server. Records have still been removed from the "
                                    "database.",
                        color=discord.Colour.red()
                    )
                    await context.send(embed=embed)
                    c = await conn.cursor()
                    await c.execute("DELETE FROM GuildMusicChannels WHERE guild_id = ?", (guild_id,))
                    await conn.commit()
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
