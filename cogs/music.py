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
volume_global = 10


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

        # Edit the main embed to show what is currently playing
        async with aiosqlite.connect(DB_PATH) as conn:
            c = await conn.cursor()
            guild_id = payload.player.guild.id
            channel_id_tuple = await c.execute("SELECT channel_id FROM GuildMusicChannels WHERE guild_id = ?",
                                               (guild_id,))
            channel_id_tuple = await channel_id_tuple.fetchone()
            channel_id = channel_id_tuple[0]  # Extract the channel_id from the tuple
            message_id = await c.execute("SELECT message_id FROM GuildMusicChannels WHERE guild_id = ?", (guild_id,))
            message_id = await message_id.fetchone()
            if message_id:
                channel = await self.bot.fetch_channel(channel_id)
                message = await channel.fetch_message(message_id[0])
                embed = message.embeds[0]
                embed.set_field_at(0, name="Now Playing:", value=f"{track.title} - {track.author} - {track_duration}",
                                   inline=False)
                # update the album art
                if track.artwork:
                    embed.set_thumbnail(url=payload.track.artwork)
                else:
                    embed.set_thumbnail(
                        url="https://community.mp3tag.de/uploads/default/original/2X/a/acf3edeb055e7b77114f9e393d1edeeda37e50c9.png")
                await message.edit(embed=embed)

        # Edit the queue embed to show the current queue
        if player.queue:
            async with aiosqlite.connect(DB_PATH) as conn:
                c = await conn.cursor()
                guild_id = payload.player.guild.id
                queue_id = await c.execute("SELECT queue_id FROM GuildMusicChannels WHERE guild_id = ?", (guild_id,))
                queue_id = await queue_id.fetchone()
                if queue_id:
                    channel = await self.bot.fetch_channel(channel_id)
                    queue_message = await channel.fetch_message(queue_id[0])
                    queue_embed = queue_message.embeds[0]
                    queue = player.queue
                    queue_list = []
                    for i, track in enumerate(queue):
                        queue_list.append(f"{i + 1}. {track.title} - {track.author}")
                    queue_embed.description = "Queue:\n" + "\n".join(queue_list)
                    await queue_message.edit(embed=queue_embed)
        else:
            async with aiosqlite.connect(DB_PATH) as conn:
                c = await conn.cursor()
                guild_id = payload.player.guild.id
                queue_id = await c.execute("SELECT queue_id FROM GuildMusicChannels WHERE guild_id = ?", (guild_id,))
                queue_id = await queue_id.fetchone()
                if queue_id:
                    channel = await self.bot.fetch_channel(channel_id)
                    queue_message = await channel.fetch_message(queue_id[0])
                    queue_embed = queue_message.embeds[0]
                    queue_embed.description = f"Queue:\n{track.title} - {track.author}"
                    await queue_message.edit(embed=queue_embed)

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
                    await interaction.response.send_message(f"Playing {query}", ephemeral=True)
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
                query = query.strip('<>')
                destination = context.author.voice.channel

                if not context.author.voice or not context.author.voice.channel:
                    # Handle the case when the user is not connected to a voice channel
                    return

                if not context.author.voice.channel.permissions_for(
                        context.guild.me).connect or not context.author.voice.channel.permissions_for(
                    context.guild.me).speak:
                    # Handle the case when the bot does not have permission to connect or speak in the voice channel
                    return

                if context.guild.voice_client is None:
                    await destination.connect(cls=wavelink.Player, self_deaf=True)

                player: wavelink.Player = cast(
                    wavelink.Player,
                    context.guild.voice_client
                )

                player.autoplay = wavelink.AutoPlayMode.partial

                try:
                    tracks: wavelink.Search = await wavelink.Playable.search(query)
                    if not tracks:
                        return None
                except LavalinkLoadException:
                    return None

                track: wavelink.Playable = tracks[0]
                await player.queue.put_wait(track)

                if not player.playing and player.queue:
                    await player.play(player.queue.get(), volume=self.volume)

                # edit the queue embed to show the current queue including the song just added
                async with aiosqlite.connect(DB_PATH) as conn:
                    c = await conn.cursor()
                    guild_id = player.guild.id
                    queue_id = await c.execute("SELECT queue_id FROM GuildMusicChannels WHERE guild_id = ?",
                                               (guild_id,))
                    queue_id = await queue_id.fetchone()
                    if queue_id:
                        channel = await self.bot.fetch_channel(channel_id)
                        queue_message = await channel.fetch_message(queue_id[0])
                        queue_embed = queue_message.embeds[0]
                        queue = player.queue
                        queue_list = []
                        for i, track in enumerate(queue):
                            queue_list.append(f"{i + 1}. {track.title}")
                        queue_embed.description = "Queue:\n" + "\n".join(queue_list)
                        await queue_message.edit(embed=queue_embed)

                volume_global = self.volume

            async def pause_music(self, guild_id):
                player: wavelink.Player = cast(
                    wavelink.Player,
                    context.guild.voice_client
                )
                await player.pause(not player.paused)

            async def skip_music(self, guild_id):
                player: wavelink.Player = cast(
                    wavelink.Player,
                    context.guild.voice_client
                )
                self.player = player
                await player.stop()

            async def connect_to_channel(self, channel):
                player: wavelink.Player = cast(
                    wavelink.Player,
                    context.guild.voice_client
                )
                self.player = player
                await player.connect(channel.id)

            async def disconnect_from_channel(self, guild_id):
                player: wavelink.Player = cast(
                    wavelink.Player,
                    context.guild.voice_client
                )
                await player.disconnect()

            @discord.ui.button(label="⏮️", style=discord.ButtonStyle.primary)
            async def previous(self, interaction: discord.Interaction, button: discord.ui.Button):
                await interaction.response.defer()
                try:
                    player: wavelink.Player = cast(
                        wavelink.Player,
                        context.guild.voice_client
                    )
                    if player and player.queue:
                        await self.skip_music(interaction.guild_id)
                        await interaction.response.send_message("Skipped to the previous song.", ephemeral=True)
                except Exception as e:
                    await interaction.response.send_message(f"An error occurred: {str(e)}")

            @discord.ui.button(label="⏯️", style=discord.ButtonStyle.green)
            async def pause(self, interaction: discord.Interaction, button: discord.ui.Button):
                await interaction.response.defer()
                try:
                    player: wavelink.Player = cast(
                        wavelink.Player,
                        context.guild.voice_client
                    )
                    await player.pause(not player.paused)
                    await interaction.response.send_message("Paused the music.", ephemeral=True)
                except Exception as e:
                    logging.log(logging.ERROR, f"An error occurred: {str(e)}")

            @discord.ui.button(label="⏭️", style=discord.ButtonStyle.primary)
            async def skip(self, interaction: discord.Interaction, button: discord.ui.Button):
                interaction.response.defer()
                try:
                    player: wavelink.Player = cast(
                        wavelink.Player,
                        context.guild.voice_client
                    )
                    await player.stop()
                    await interaction.response.send_message("Skipped the song.", ephemeral=True)
                except Exception as e:
                    logging.log(logging.ERROR, f"An error occurred: {str(e)}")

            @discord.ui.button(label="🔊+", style=discord.ButtonStyle.green)
            async def volume_up(self, interaction: discord.Interaction, button: discord.ui.Button):
                await interaction.response.defer()
                try:
                    player: wavelink.Player = cast(
                        wavelink.Player,
                        context.guild.voice_client
                    )
                    await player.set_volume(player.volume + 5)
                    await interaction.response.send_message("Volume increased.", ephemeral=True)
                    volume_global = player.volume
                    async with aiosqlite.connect(DB_PATH) as conn:
                        c = await conn.cursor()
                        guild_id = player.guild.id
                        message_id = await c.execute("SELECT message_id FROM GuildMusicChannels WHERE guild_id = ?",
                                                     (guild_id,))
                        message_id = await message_id.fetchone()
                        if message_id:
                            channel = await self.bot.fetch_channel(channel_id)
                            message = await channel.fetch_message(message_id[0])
                            embed = message.embeds[0]
                            embed.set_field_at(1, name="Volume:", value=f"{volume_global} (Default: 10)", inline=False)
                            await message.edit(embed=embed)
                except Exception as e:
                    logging.log(logging.ERROR, f"An error occurred: {str(e)}")

            @discord.ui.button(label="🔊-", style=discord.ButtonStyle.red)
            async def volume_down(self, interaction: discord.Interaction, button: discord.ui.Button):
                await interaction.response.defer()
                try:
                    player: wavelink.Player = cast(
                        wavelink.Player,
                        context.guild.voice_client
                    )
                    await player.set_volume(player.volume - 5)
                    volume_global = player.volume
                    async with aiosqlite.connect(DB_PATH) as conn:
                        c = await conn.cursor()
                        guild_id = player.guild.id
                        message_id = await c.execute("SELECT message_id FROM GuildMusicChannels WHERE guild_id = ?",
                                                     (guild_id,))
                        message_id = await message_id.fetchone()
                        if message_id:
                            channel = await self.bot.fetch_channel(channel_id)
                            message = await channel.fetch_message(message_id[0])
                            embed = message.embeds[0]
                            embed.set_field_at(1, name="Volume:", value=f"{volume_global} (Default: 10)", inline=False)
                            await message.edit(embed=embed)
                    await interaction.response.send_message("Volume decreased.", ephemeral=True)
                except Exception as e:
                    logging.log(logging.ERROR, f"An error occurred: {str(e)}")

            @discord.ui.button(label="🔍", style=discord.ButtonStyle.blurple)
            async def search(self, interaction: discord.Interaction, button: discord.ui.Button):
                await interaction.response.send_modal(MusicSearchModal(view=self, bot=self.bot))

        main_embed = discord.Embed(
            title="🎶 ByteBot DJ",
            description="Welcome to ByteBot DJ! Use the buttons below to control the music bot.",
            color=discord.Colour.pink()
        )
        main_embed.set_thumbnail(
            url="https://community.mp3tag.de/uploads/default/original/2X/a/acf3edeb055e7b77114f9e393d1edeeda37e50c9.png")
        main_embed.add_field(name="Now Playing:", value="Nothing", inline=False)
        main_embed.add_field(name="Volume:", value=f"{volume_global} (Default: 10)", inline=False)
        main_embed.set_footer(text="ByteBot DJ")
        buttons = MusicButtons(context.author, self.bot)

        queue_embed = discord.Embed(
            title="🎶 ByteBot DJ Current Queue:",
            description="Queue:",
            color=discord.Colour.pink()
        )
        queue_embed.set_footer(text="ByteBot DJ Queue")

        await channel.send(embed=main_embed, view=buttons)
        message_id = channel.last_message_id
        await channel.send(embed=queue_embed)
        queue_id = channel.last_message_id

        # store these values in the database in the GuildMusicChannels table with aiosqlite
        try:
            async with aiosqlite.connect(DB_PATH) as conn:
                c = await conn.cursor()
                await c.execute(
                    "INSERT INTO GuildMusicChannels (guild_id, channel_id, message_id, queue_id) VALUES (?, ?, ?, ?)",
                    (guild_id, channel_id, message_id, queue_id))
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
                    await channel.delete()
                await c.execute("DELETE FROM GuildMusicChannels WHERE guild_id = ?", (guild_id,))
                await conn.commit()
                embed = discord.Embed(
                    title="Success",
                    description="Music bot removed successfully.",
                    color=discord.Colour.green()
                )
                await context.send(embed=embed)
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
