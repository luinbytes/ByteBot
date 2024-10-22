CREATE TABLE IF NOT EXISTS GuildSettings
(
    guild_id             INTEGER PRIMARY KEY,
    prefix               TEXT,
    autorole_id          INTEGER,
    steam_ban_channel_id INTEGER,
    leave_channel_id     INTEGER,
    welcome_channel_id   INTEGER,
    music_channel_id     INTEGER,
    music_message_id     INTEGER,
    mute_role_id         INTEGER,
    starboard_channel_id INTEGER,
    starboard_min_stars  INTEGER,
    coin_drop_channel_id INTEGER
);

CREATE TABLE IF NOT EXISTS GuildSteamBans
(
    guild_id         INTEGER NOT NULL,
    channel_id       INTEGER NOT NULL,
    tracked_by       TEXT    NOT NULL,
    steamid_64       TEXT    NOT NULL,
    CommunityBanned  BOOLEAN,
    VACBanned        BOOLEAN,
    NumberOfVACBans  INTEGER,
    DaysSinceLastBan INTEGER,
    NumberOfGameBans INTEGER,
    EconomyBan       TEXT,
    PRIMARY KEY (guild_id, channel_id, steamid_64)
);