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


class MusicSearchModal(discord.ui.Modal):
    def __init__(self, view, bot):
        super().__init__(title="Search for a song")
        self.view = view
        self.bot = bot

    response = discord.ui.TextInput(label="Search for a song", placeholder="Enter a song name or URL")

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            query = self.response.value
            await self.view.play_music(interaction, query)  # Pass the interaction object
        except Exception as e:
            await interaction.followup.send(  # Use followup.send instead of response.send_message
                f"An error occurred - Please send this to @0x6c75: {traceback.format_exc()}", ephemeral=True)


class Music(commands.Cog, name="music"):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.channel = None

    class MusicButtons(discord.ui.View):
        def __init__(self, user, bot):
            super().__init__()
            self.user = user
            self.player = None
            self.volume = 10
            self.bot = bot
            self.wavelink = self.bot.wavelink

        async def play_music(self, interaction, query):
            logging.log(logging.INFO, f"Playing {query}")
            query = query.strip('<>')
            context = await self.bot.get_context(interaction.message)

            if not context.author.voice or not context.author.voice.channel:
                await interaction.followup.send("You are not connected to a voice channel.", ephemeral=True)
                return

            destination = context.author.voice.channel

            if not context.author.voice.channel.permissions_for(
                    context.guild.me).connect or not context.author.voice.channel.permissions_for(
                context.guild.me).speak:
                await interaction.followup.send(
                    "I don't have permission to connect and speak in your voice channel.", ephemeral=True)
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

            if player.playing and player.queue:
                async with aiosqlite.connect(DB_PATH) as conn:
                    c = await conn.cursor()
                    guild_id = player.guild.id
                    channel_id = await c.execute("SELECT music_channel_id FROM GuildSettings WHERE guild_id = ?",
                                                 (guild_id,))
                    channel_id = await channel_id.fetchone()
                    if channel_id:
                        channel = await self.bot.fetch_channel(channel_id[0])
                        message_id = await c.execute(
                            "SELECT music_message_id FROM GuildSettings WHERE guild_id = ?",
                            (guild_id,))
                        message_id = await message_id.fetchone()
                        if message_id:
                            message = await channel.fetch_message(message_id[0])
                            embed = message.embeds[0]
                            queue = []
                            for i, track in enumerate(player.queue):
                                queue.append(f"{i + 1}. {track.title} - {track.author}")
                            queue = "\n".join(queue)
                            embed.set_field_at(1, name="Queue:", value=queue, inline=False)
                            await message.edit(embed=embed)

            volume_global = self.volume

        async def pause_music(self, guild_id):
            context = await self.bot.get_context(self.user)
            player: wavelink.Player = cast(
                wavelink.Player,
                context.guild.voice_client
            )
            await player.pause(not player.paused)

        async def skip_music(self, guild_id):
            context = await self.bot.get_context(self.user)
            player: wavelink.Player = cast(
                wavelink.Player,
                context.guild.voice_client
            )
            self.player = player
            await player.stop()

        async def connect_to_channel(self, channel):
            context = await self.bot.get_context(self.user)
            player: wavelink.Player = cast(
                wavelink.Player,
                context.guild.voice_client
            )
            self.player = player
            await player.connect(channel.id)

        async def disconnect_from_channel(self, guild_id):
            context = await self.bot.get_context(self.user)
            player: wavelink.Player = cast(
                wavelink.Player,
                context.guild.voice_client
            )
            await player.disconnect()

        @discord.ui.button(label="⏯️", style=discord.ButtonStyle.green, row=1)
        async def pause(self, interaction: discord.Interaction, button: discord.ui.Button):
            await interaction.response.defer()
            try:
                context = await self.bot.get_context(self.user)
                player: wavelink.Player = cast(
                    wavelink.Player,
                    context.guild.voice_client
                )
                await player.pause(not player.paused)
            except Exception as e:
                logging.log(logging.ERROR, f"An error occurred: {str(e)}")

        @discord.ui.button(label="⏭️", style=discord.ButtonStyle.primary, row=1)
        async def skip(self, interaction: discord.Interaction, button: discord.ui.Button):
            await interaction.response.defer()
            try:
                context = await self.bot.get_context(self.user)
                player: wavelink.Player = cast(
                    wavelink.Player,
                    context.guild.voice_client
                )
                await player.stop()
            except Exception as e:
                logging.log(logging.ERROR, f"An error occurred: {str(e)}")

        @discord.ui.button(label="🔊-", style=discord.ButtonStyle.red, row=2)
        async def volume_down(self, interaction: discord.Interaction, button: discord.ui.Button):
            await interaction.response.defer()
            try:
                context = await self.bot.get_context(self.user)
                channel_id = context.channel.id
                player: wavelink.Player = cast(
                    wavelink.Player,
                    context.guild.voice_client
                )
                await player.set_volume(player.volume - 5)
                volume_global = player.volume
                async with aiosqlite.connect(DB_PATH) as conn:
                    c = await conn.cursor()
                    guild_id = player.guild.id
                    message_id = await c.execute("SELECT music_message_id FROM GuildSettings WHERE guild_id = ?",
                                                 (guild_id,))
                    message_id = await message_id.fetchone()
                    if message_id:
                        channel = await self.bot.fetch_channel(channel_id)
                        message = await channel.fetch_message(message_id[0])
                        embed = message.embeds[0]
                        embed.set_field_at(2, name="Volume:", value=f"{volume_global} (Default: 10)", inline=False)
                        await message.edit(embed=embed)
            except Exception as e:
                logging.log(logging.ERROR, f"An error occurred: {str(e)}")

        @discord.ui.button(label="🔊+", style=discord.ButtonStyle.green, row=2)
        async def volume_up(self, interaction: discord.Interaction, button: discord.ui.Button):
            await interaction.response.defer()
            try:
                context = await self.bot.get_context(self.user)
                player: wavelink.Player = cast(
                    wavelink.Player,
                    context.guild.voice_client
                )
                channel_id = context.channel.id
                await player.set_volume(player.volume + 5)
                volume_global = player.volume
                async with aiosqlite.connect(DB_PATH) as conn:
                    c = await conn.cursor()
                    guild_id = player.guild.id
                    message_id = await c.execute("SELECT music_message_id FROM GuildSettings WHERE guild_id = ?",
                                                 (guild_id,))
                    message_id = await message_id.fetchone()
                    if message_id:
                        channel = await self.bot.fetch_channel(channel_id)
                        message = await channel.fetch_message(message_id[0])
                        embed = message.embeds[0]
                        embed.set_field_at(2, name="Volume:", value=f"{player.volume} (Default: 10)", inline=False)
                        await message.edit(embed=embed)
            except Exception as e:
                logging.log(logging.ERROR, f"An error occurred: {str(e)}")

        @discord.ui.button(label="🔍", style=discord.ButtonStyle.secondary, row=1)
        async def search(self, interaction: discord.Interaction, button: discord.ui.Button):
            await interaction.response.send_modal(MusicSearchModal(view=self, bot=self.bot))

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
            channel_id_tuple = await c.execute("SELECT music_channel_id FROM GuildSettings WHERE guild_id = ?",
                                               (guild_id,))
            channel_id_tuple = await channel_id_tuple.fetchone()
            channel_id = channel_id_tuple[0]  # Extract the channel_id from the tuple
            message_id = await c.execute("SELECT music_message_id FROM GuildSettings WHERE guild_id = ?", (guild_id,))
            message_id = await message_id.fetchone()
            if message_id:
                channel = await self.bot.fetch_channel(channel_id)
                message = await channel.fetch_message(message_id[0])
                buttons = self.MusicButtons(self.current_context.author, self.bot)
                embed = message.embeds[0]
                embed.set_field_at(0, name="Now Playing:", value=f"{track.title} - {track.author} - {track_duration}",
                                   inline=False)
                # update the album art
                if track.artwork:
                    embed.set_thumbnail(url=payload.track.artwork)
                else:
                    embed.set_thumbnail(
                        url="https://community.mp3tag.de/uploads/default/original/2X/a/acf3edeb055e7b77114f9e393d1edeeda37e50c9.png")
                await message.edit(embed=embed, view=buttons)

        # Add embed elements to the main embed with the queue
        if player.queue:
            queue = []
            for i, track in enumerate(player.queue):
                queue.append(f"{i + 1}. {track.title} - {track.author}")
            queue = "\n".join(queue)
            embed.set_field_at(1, name="Queue:", value=queue, inline=False)
            await message.edit(embed=embed)
        else:
            embed.set_field_at(1, name="Queue:", value="Empty", inline=False)
            await message.edit(embed=embed, view=message.components)

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

            # update the main embed to show that nothing is playing
            async with aiosqlite.connect(DB_PATH) as conn:
                c = await conn.cursor()
                guild_id = payload.player.guild.id
                channel_id_tuple = await c.execute("SELECT music_channel_id FROM GuildSettings WHERE guild_id = ?",
                                                   (guild_id,))
                channel_id_tuple = await channel_id_tuple.fetchone()
                channel_id = channel_id_tuple[0]  # Extract the channel_id from the tuple
                message_id = await c.execute("SELECT music_message_id FROM GuildSettings WHERE guild_id = ?",
                                             (guild_id,))
                message_id = await message_id.fetchone()
                channel = self.bot.get_channel(channel_id)
                if channel and message_id:
                    try:
                        message = await channel.fetch_message(message_id[0])
                        buttons = self.MusicButtons(self.current_context.author, self.bot)
                        embed = message.embeds[0]
                        embed.set_field_at(0, name="Now Playing:", value="Nothing", inline=False)
                        embed.set_field_at(1, name="Queue:", value="Empty", inline=False)
                        embed.set_thumbnail(
                            url="https://community.mp3tag.de/uploads/default/original/2X/a/acf3edeb055e7b77114f9e393d1edeeda37e50c9.png")
                        await message.edit(embed=embed, view=buttons)
                    except discord.NotFound:
                        print(f"Message with ID {message_id[0]} not found.")

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
            channel_id = await c.execute("SELECT music_channel_id FROM GuildSettings WHERE guild_id = ?",
                                         (guild_id,))
            channel_id = await channel_id.fetchone()
            if channel_id and channel_id[0] is not None:
                embed = discord.Embed(
                    title="Error",
                    description=f"Music bot is already setup in this server. Channel ID: {channel_id[0]}",
                    color=discord.Colour.red()
                )
                await context.send(embed=embed)
                return

        # create a text channel
        channel = await context.guild.create_text_channel("bytebot-🎵")
        permissions = discord.PermissionOverwrite(
            read_messages=True,
            send_messages=False,
            manage_messages=False,
            embed_links=False,
            add_reactions=False,
            read_message_history=True,
            attach_files=False,
            mention_everyone=False,
            use_external_emojis=False,
            manage_threads=False,
        )
        await channel.set_permissions(context.guild.default_role, overwrite=permissions)
        channel_id = channel.id

        # send music control embed to the channel
        main_embed = discord.Embed(
            title="🎶 ByteBot DJ",
            description="Welcome to ByteBot DJ! Use the buttons below to control the music bot.",
            color=discord.Colour.pink()
        )
        main_embed.set_thumbnail(
            url="https://community.mp3tag.de/uploads/default/original/2X/a/acf3edeb055e7b77114f9e393d1edeeda37e50c9.png")
        main_embed.add_field(name="Now Playing:", value="Nothing", inline=False)
        main_embed.add_field(name="Queue:", value="Empty", inline=False)
        main_embed.add_field(name="Volume:", value=f"{volume_global} (Default: 10)", inline=False)
        main_embed.set_footer(text="ByteBot DJ")
        buttons = self.MusicButtons(context.author, self.bot)

        await channel.send(embed=main_embed, view=buttons)
        message_id = channel.last_message_id

        # store these values in the database in the GuildMusicChannels table with aiosqlite
        try:
            async with aiosqlite.connect(DB_PATH) as conn:
                c = await conn.cursor()
                await c.execute(
                    "UPDATE GuildSettings SET music_channel_id = ?, music_message_id = ? WHERE guild_id = ?",
                    (channel_id, message_id, guild_id))
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
                channel_id = await c.execute("SELECT music_channel_id FROM GuildSettings WHERE guild_id = ?",
                                             (guild_id,))
                channel_id = await channel_id.fetchone()
                if channel_id:
                    channel = context.guild.get_channel(channel_id[0])
                    if channel:  # Check if the channel exists on Discord
                        await channel.delete()
                await c.execute("UPDATE GuildSettings SET music_channel_id = NULL WHERE guild_id = ?", (guild_id,))
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
