import discord
import wavelink
import logging
from datetime import timedelta
from discord.ext import commands
from discord import app_commands
from discord.ext.commands import Context
from wavelink.exceptions import LavalinkLoadException
from typing import cast

class Music(commands.Cog, name="music"):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.channel = None
        self.volume = 50

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
        embed.set_footer(name="Source:", value=f"{track.source.capitalize()}", inline=True)
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
        name="play",
        description="Play a song.",
        usage="play <song>",
        aliases=["search"]
    )
    @app_commands.describe(
        song="The song to search for and play."
    )
    async def play(self, context, *, song: str) -> None:
        if not context.author.voice:
            embed = discord.Embed(
                title="Error",
                description="You are not connected to a voice channel.",
                color=discord.Colour.red()
            )
            embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
            return await context.send(embed=embed)

        if not context.author.voice.channel:
            embed = discord.Embed(
                title="Error",
                description="You are not connected to a voice channel.",
                color=discord.Colour.red()
            )
            embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
            return await context.send(embed=embed)

        if not context.author.voice.channel.permissions_for(context.guild.me).connect:
            embed = discord.Embed(
                title="Error",
                description="I do not have permission to connect to your voice channel.",
                color=discord.Colour.red()
            )
            embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
            return await context.send(embed=embed)

        if not context.author.voice.channel.permissions_for(context.guild.me).speak:
            embed = discord.Embed(
                title="Error",
                description="I do not have permission to speak in your voice channel.",
                color=discord.Colour.red()
            )
            embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
            return await context.send(embed=embed)
        
        self.channel = context.channel
        destination = context.author.voice.channel

        try:
            tracks: wavelink.Search = await wavelink.Playable.search(song)
            if not tracks:
                embed = discord.Embed(
                    title="Error",
                    description="No tracks found.",
                    color=discord.Colour.red()
                )
                embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
                return await context.send(embed=embed)
        except LavalinkLoadException:
            embed = discord.Embed(
                title="Error",
                description="An error occurred while loading the track.",
                color=discord.Colour.red()
            )
            embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
            return await context.send(embed=embed)
        
        if not context.guild.voice_client:
            await destination.connect(cls=wavelink.Player, self_deaf=True)

        player: wavelink.Player = cast(
            wavelink.Player,
            context.guild.voice_client
        )

        player.autoplay = wavelink.AutoPlayMode.partial
        track: wavelink.Playable = tracks[0]
        artist_name = track.artist

        await player.queue.put_wait(track)

        embed = discord.Embed(
            title="Queued",
            description=f"**{track.title} - {track.author}**",
            color=discord.Colour.green()
        )
        if track.artwork:
            embed.set_thumbnail(url=track.artwork)
        embed.add_field(name="Duration:", value=str(timedelta(milliseconds=track.length)), inline=True)
        embed.add_field(name="Queue", value=f"{len(player.queue)} songs", inline=True)
        embed.set_footer(text=f"Source: {track.source.capitalize()}", icon_url=track.artwork)
        await context.send(embed=embed)

        if not player.playing:
            await player.play(player.queue.get(), volume=self.volume)

    @commands.hybrid_command(
        name="stop",
        description="Stop the music.",
        usage="stop",
        aliases=["leave"]
    )
    async def stop(self, context: commands.Context) -> None:
        player: wavelink.Player = context.guild.voice_client
        if not context.author.voice:
            embed = discord.Embed(
                title="Error",
                description="You are not connected to a voice channel.",
                color=discord.Colour.red()
            )
            embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
            return await context.send(embed=embed)

        if not context.author.voice.channel:
            embed = discord.Embed(
                title="Error",
                description="You are not connected to a voice channel.",
                color=discord.Colour.red()
            )
            embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
            return await context.send(embed=embed)

        if not context.author.voice.channel.permissions_for(context.guild.me).connect:
            embed = discord.Embed(
                title="Error",
                description="I do not have permission to connect to your voice channel.",
                color=discord.Colour.red()
            )
            embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
            return await context.send(embed=embed)

        if not context.author.voice.channel.permissions_for(context.guild.me).speak:
            embed = discord.Embed(
                title="Error",
                description="I do not have permission to speak in your voice channel.",
                color=discord.Colour.red()
            )
            embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
            return await context.send(embed=embed)

        if not context.guild.voice_client:
            embed = discord.Embed(
                title="Error",
                description="I am not connected to a voice channel.",
                color=discord.Colour.red()
            )
            embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
            return await context.send(embed=embed)

        self.channel = None
        await player.disconnect()

        embed = discord.Embed(
            title="Stopped",
            description="The music has been stopped.",
            color=discord.Colour.green()
        )
        embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
        await context.send(embed=embed)

    @commands.hybrid_command(
        name="pause",
        description="Pause the music.",
        usage="pause"
    )
    async def pause(self, context: commands.Context) -> None:
        player: wavelink.Player = context.guild.voice_client
        if not context.author.voice:
            embed = discord.Embed(
                title="Error",
                description="You are not connected to a voice channel.",
                color=discord.Colour.red()
            )
            embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
            return await context.send(embed=embed)

        if not context.author.voice.channel:
            embed = discord.Embed(
                title="Error",
                description="You are not connected to a voice channel.",
                color=discord.Colour.red()
            )
            embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
            return await context.send(embed=embed)

        if not context.author.voice.channel.permissions_for(context.guild.me).connect:
            embed = discord.Embed(
                title="Error",
                description="I do not have permission to connect to your voice channel.",
                color=discord.Colour.red()
            )
            embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
            return await context.send(embed=embed)

        if not context.author.voice.channel.permissions_for(context.guild.me).speak:
            embed = discord.Embed(
                title="Error",
                description="I do not have permission to speak in your voice channel.",
                color=discord.Colour.red()
            )
            embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
            return await context.send(embed=embed)

        if not context.guild.voice_client:
            embed = discord.Embed(
                title="Error",
                description="I am not connected to a voice channel.",
                color=discord.Colour.red()
            )
            embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
            return await context.send(embed=embed)

        await player.pause(not player.paused)

        if player.pause:
            embed = discord.Embed(
                title="Paused",
                description="The music has been paused.",
                color=discord.Colour.green()
            )
            embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
        else:
            embed = discord.Embed(
                title="Resumed",
                description="The music has been resumed.",
                color=discord.Colour.green()
            )
            embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)    
            
        await context.send(embed=embed)

    @commands.hybrid_command(
        name = "skip",
        description = "Skip the current song.",
        usage = "skip",
        aliases = ["next"]
    )
    async def skip(self, context: commands.Context) -> None:
        player: wavelink.Player = context.guild.voice_client
        if not context.author.voice:
            embed = discord.Embed(
                title="Error",
                description="You are not connected to a voice channel.",
                color=discord.Colour.red()
            )
            embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
            return await context.send(embed=embed)

        if not context.author.voice.channel:
            embed = discord.Embed(
                title="Error",
                description="You are not connected to a voice channel.",
                color=discord.Colour.red()
            )
            embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
            return await context.send(embed=embed)

        if not context.author.voice.channel.permissions_for(context.guild.me).connect:
            embed = discord.Embed(
                title="Error",
                description="I do not have permission to connect to your voice channel.",
                color=discord.Colour.red()
            )
            embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
            return await context.send(embed=embed)

        if not context.author.voice.channel.permissions_for(context.guild.me).speak:
            embed = discord.Embed(
                title="Error",
                description="I do not have permission to speak in your voice channel.",
                color=discord.Colour.red()
            )
            embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
            return await context.send(embed=embed)

        if not context.guild.voice_client:
            embed = discord.Embed(
                title="Error",
                description="I am not connected to a voice channel.",
                color=discord.Colour.red()
            )
            embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
            return await context.send(embed=embed)

        if player.playing:
            if player.queue:
                await player.skip()
                embed = discord.Embed(
                    title="Skipped",
                    description="The current song has been skipped.",
                    color=discord.Colour.green()
                )
                embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
                await context.send(embed=embed)
            else:
                await player.stop(force=False)
                await player.disconnect()
                embed = discord.Embed(
                    title="Skipped",
                    description="The song has been skipped but theres no other songs in the queue.",
                    color=discord.Colour.green()
                )
                embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
                await context.send(embed=embed)
        else:
            embed = discord.Embed(
                title="Error",
                description="There is no music playing.",
                color=discord.Colour.red()
            )
            embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
            await context.send(embed=embed)

    @commands.hybrid_command(
        name="volume",
        description="Change the volume.",
        usage="volume <volume>",
        aliases=["vol"]
    )
    @app_commands.describe(
        volume="The volume to set."
    )
    async def volume(self, context: commands.Context, volume: int) -> None:
        player: wavelink.Player = context.guild.voice_client
        if not context.author.voice:
            embed = discord.Embed(
                title="Error",
                description="You are not connected to a voice channel.",
                color=discord.Colour.red()
            )
            embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
            return await context.send(embed=embed)

        if not context.author.voice.channel:
            embed = discord.Embed(
                title="Error",
                description="You are not connected to a voice channel.",
                color=discord.Colour.red()
            )
            embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
            return await context.send(embed=embed)

        if not context.author.voice.channel.permissions_for(context.guild.me).connect:
            embed = discord.Embed(
                title="Error",
                description="I do not have permission to connect to your voice channel.",
                color=discord.Colour.red()
            )
            embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
            return await context.send(embed=embed)

        if not context.author.voice.channel.permissions_for(context.guild.me).speak:
            embed = discord.Embed(
                title="Error",
                description="I do not have permission to speak in your voice channel.",
                color=discord.Colour.red()
            )
            embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
            return await context.send(embed=embed)

        if not context.guild.voice_client:
            embed = discord.Embed(
                title="Error",
                description="I am not connected to a voice channel.",
                color=discord.Colour.red()
            )
            embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
            return await context.send(embed=embed)

        if volume < 0 or volume > 100:
            embed = discord.Embed(
                title="Error",
                description="The volume must be between 0 and 100.",
                color=discord.Colour.red()
            )
            embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
            return await context.send(embed=embed)

        self.volume = volume
        await player.set_volume(volume)
        embed = discord.Embed(
            title="Volume",
            description=f"The volume has been set to {volume}.",
            color=discord.Colour.green()
        )
        embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
        await context.send(embed=embed)

    @commands.hybrid_command(
        name="nowplaying",
        description="View the current song.",
        usage="nowplaying",
        aliases=["np"]
    )
    async def nowplaying(self, context: Context) -> None:
        player: wavelink.Player = context.guild.voice_client
        if player.playing:
            track = player.current
            track_duration = str(timedelta(milliseconds=track.length))
            
            embed = discord.Embed(
                title="Now Playing",
                description=f"**{track.title} - {track.author}**",
                color=discord.Colour.green()
            )
            if track.artwork:
                embed.set_thumbnail(url=track.artwork)
            embed.add_field(name="Duration:", value=track_duration, inline=True)
            embed.add_field(name="Queue", value=f"{len(player.queue)} songs", inline=True)
            embed.set_footer(text=f"Source: {track.source.capitalize()}", icon_url=track.artwork)
            await context.send(embed=embed)
        else:
            embed = discord.Embed(
                title="Error",
                description="There is no music playing.",
                color=discord.Colour.red()
            )
            embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
            await context.send(embed=embed)

    @commands.hybrid_command(
        name="queue",
        description="View the queue.",
        usage="queue",
        aliases=["q"]
    )
    async def queue(self, context: Context) -> None:
        player: wavelink.Player = context.guild.voice_client
        if player.queue:
            embed = discord.Embed(
                title="Queue",
                description="",
                color=discord.Colour.green()
            )
            for index, track in enumerate(player.queue):
                track_duration = str(timedelta(milliseconds=track.length))
                if '.' in track_duration:
                    track_duration = track_duration.split('.')[0]
                embed.add_field(name=f"#{index + 1} >> {track.title} - {track.author}", value=f"Duration: {track_duration}", inline=False)
            embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
            await context.send(embed=embed)
        else:
            embed = discord.Embed(
                title="Error",
                description="There are no songs in the queue.",
                color=discord.Colour.red()
            )
            embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
            await context.send(embed=embed)

async def setup(bot) -> None:
    await bot.add_cog(Music(bot))