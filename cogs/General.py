import os

import aiosqlite
import aiohttp
import discord
from discord.ext import commands
from discord.ext.commands import Context

DATABASE_DIR = "database"
ABS_PATH = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(DATABASE_DIR, "database.db")


class General(commands.Cog, name="general"):
    def __init__(self, bot) -> None:
        self.bot = bot

    async def guild_prefix(db, guild_id, prefix=None):
        async with aiosqlite.connect(DB_PATH) as conn:
            c = await conn.cursor()
            if prefix is not None:
                # Write to the table
                await c.execute("UPDATE GuildSettings SET prefix = ? WHERE guild_id = ?", (prefix, guild_id))
                await conn.commit()
            else:
                # Read from the table
                await c.execute("SELECT prefix FROM GuildSettings WHERE guild_id = ?", (guild_id,))
                row = await c.fetchone()
                return row[0] if row else None
    
    @commands.hybrid_command(
        name="help",
        description="List all commands the bot has loaded or show commands in a specific category.",
    )
    async def help(self, context: Context, category: str = None) -> None:
        db_conn = aiosqlite.connect(DB_PATH)
        db = db_conn.cursor()
        prefix = await self.guild_prefix(context.guild.id)
        embed = discord.Embed(
            title="Help", description="List of available categories:", color=0xBEBEFE
        )
        embed.add_field(name=f"Use {prefix}help <category> to see commands", value="", inline=False)
        for cog_name in self.bot.cogs:
            if cog_name == "owner" and not (await self.bot.is_owner(context.author)):
                continue
            embed.add_field(name="", value=cog_name.capitalize(), inline=False)
        embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)

        if category:
            category_lower = category.lower()
            cog = self.bot.get_cog(category_lower)
            if cog:
                commands = cog.get_commands()
                data = []
                for command in commands:
                    description = command.description.partition("\n")[0]
                    data.append(f"{prefix}{command.name} - {description}")
                help_text = "\n".join(data)
                category_embed = discord.Embed(
                    title=f"{category.capitalize()} Commands",
                    description=f"```{help_text}```",
                    color=0xBEBEFE
                )
                category_embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
                await context.send(embed=category_embed)
            else:
                await context.send("Invalid category. Please use !help to see available categories.")
        else:
            await context.send(embed=embed)

    @commands.hybrid_command(
        name="cat",
        description="Spawns a random cat! Big thanks to The Cat API!",
        usage="cat",
        aliases=["kitty", "car"]
    )
    async def cat(self, context: Context) -> None:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://api.thecatapi.com/v1/images/search"
            ) as request:
                # print(request.status)
                if request.status == 200:
                    data = await request.json()
                    url = data[0]["url"]
                    id = data[0]["id"]
                    embed = discord.Embed(title="Random Cat!", color=0xD75BF4)
                    embed.set_image(url=url)
                    embed.add_field(name="Cat ID", value="```" + str(id) + "```", inline=False)
                    embed.add_field(name="Thanks to The Cat API!", value=f"[Open in browser]({url})", inline=False)
                    embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)

                else:
                    embed = discord.Embed(
                        title="Error!",
                        description="There is something wrong with the API, please try again later",
                        color=0xE02B2B,
                    )
                await context.send(embed=embed)

async def setup(bot) -> None:
    await bot.add_cog(General(bot))
