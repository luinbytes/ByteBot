import os

import aiosqlite
from discord.ext import commands

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
                try:
                    await c.execute("INSERT INTO GuildPrefix (guild_id, prefix) VALUES (?, ?)", (guild_id, prefix))
                except aiosqlite.IntegrityError:
                    await c.execute("UPDATE GuildPrefix SET prefix = ? WHERE guild_id = ?", (prefix, guild_id))
                await conn.commit()
            else:
                # Read from the table
                await c.execute("SELECT prefix FROM GuildPrefix WHERE guild_id = ?", (guild_id,))
                row = await c.fetchone()
                return row[0] if row else None


async def setup(bot) -> None:
    await bot.add_cog(General(bot))
