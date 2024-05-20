import discord
import wavelink
import logging
from datetime import timedelta
from discord.ext import commands
from wavelink.exceptions import LavalinkLoadException

class Music(commands.Cog, name="music"):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.channel = None
        self.volume = 100

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


async def setup(bot) -> None:
    await bot.add_cog(Music(bot))