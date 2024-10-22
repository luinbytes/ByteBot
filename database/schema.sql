CREATE TABLE IF NOT EXISTS GuildSettings
(
    guild_id             INTEGER PRIMARY KEY,
    prefix               TEXT,
    rj_webhook           TEXT,
);

CREATE TABLE IF NOT EXISTS Steam
(
    steam_id             TEXT PRIMARY KEY,
    discord_id           INTEGER
)