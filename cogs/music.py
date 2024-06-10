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


async def connect_to_channel(self, channel):
    player = self.bot.wavelink.get_player(channel.guild.id)
    await player.connect(channel.id)


async def disconnect_from_channel(self, guild_id):
    player = self.bot.wavelink.get_player(guild_id)
    await player.disconnect()


async def play_music(self, guild_id, query):
    player = self.bot.wavelink.get_player(guild_id)
    results = await player.node.get_tracks(query)

    if not results or not results['tracks']:
        return None

    track = results['tracks'][0]
    await player.play(track)
    return track


async def pause_music(self, guild_id):
    player = self.bot.wavelink.get_player(guild_id)
    await player.set_pause(True)


async def resume_music(self, guild_id):
    player = self.bot.wavelink.get_player(guild_id)
    await player.set_pause(False)


async def skip_music(self, guild_id):
    player = self.bot.wavelink.get_player(guild_id)
    await player.stop()


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

        # send music control embed to the channel
        class MusicButtons(discord.ui.View):
            def __init__(self, user, bot):
                super().__init__()
                self.user = user
                self.bot = bot
                self.value = None
                self.player = None

            @discord.ui.button(label="⏮️", style=discord.ButtonStyle.primary)
            async def previous(self, button: discord.ui.Button, interaction: discord.Interaction):
                player: wavelink.Player = context.guild.voice_client
                if self.player.get_player(interaction.guild_id).queue:
                    await self.player

            @discord.ui.button(label="⏯️", style=discord.ButtonStyle.green)
            async def pause(self, button: discord.ui.Button, interaction: discord.Interaction):
                player: wavelink.Player = context.guild.voice_client
                if player.set_pause(True):
                    await resume_music(interaction.guild_id)
                else:
                    await pause_music(interaction.guild_id)

            @discord.ui.button(label="⏭️", style=discord.ButtonStyle.primary)
            async def skip(self, button: discord.ui.Button, interaction: discord.Interaction):
                player: wavelink.Player = context.guild.voice_client
                await skip_music(interaction.guild_id)

            @discord.ui.button(label="⠀", style=discord.ButtonStyle.primary, disabled=True)
            async def spacer(self, button: discord.ui.Button, interaction: discord.Interaction):
                pass

            @discord.ui.button(label="🔊+", style=discord.ButtonStyle.green)
            async def volume_up(self, button: discord.ui.Button, interaction: discord.Interaction):
                player: wavelink.Player = context.guild.voice_client
                await player.set_volume(player.volume + 10)

            @discord.ui.button(label="🔊-", style=discord.ButtonStyle.red)
            async def volume_down(self, button: discord.ui.Button, interaction: discord.Interaction):
                player: wavelink.Player = context.guild.voice_client
                await player.set_volume(player.volume - 10)

            @discord.ui.button(label="🔍", style=discord.ButtonStyle.blurple)
            async def search(self, interaction: discord.Interaction, item: discord.ui.Item):
                await interaction.response.send_modal(MusicSearchModal(self, self.bot))

        class MusicSearchModal(discord.ui.Modal):
            def __init__(self, view, bot):
                super().__init__(title="Search for a song")
                self.view = view
                self.bot = bot
                self.placeholder = discord.ui.TextInput(label="Enter the song you would like to search for.")

            async def interaction_check(self, interaction: discord.Interaction) -> bool:
                return interaction.user == self.view.user

            async def on_submit(self, interaction: discord.Interaction):
                await interaction.response.send_message("Searching for the song...", ephemeral=True)
                query = interaction.message.content
                music_cog = self.bot.get_cog("music")
                track = await music_cog.play_music(interaction.guild_id, query)
                if track:
                    await interaction.response.send_message(f"Playing {track.title} by {track.author}.", ephemeral=True)
                else:
                    await interaction.response.send_message("No results found.", ephemeral=True)

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
