CREATE TABLE IF NOT EXISTS `warns`
(
    `id`           int(11)      NOT NULL,
    `user_id`      varchar(20)  NOT NULL,
    `server_id`    varchar(20)  NOT NULL,
    `moderator_id` varchar(20)  NOT NULL,
    `reason`       varchar(255) NOT NULL,
    `created_at`   timestamp    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE GuildSettings
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

CREATE TABLE IF NOT EXISTS GuildLoggingChannels
(
    guild_id   INTEGER PRIMARY KEY,
    channel_id INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS GuildMutedUsers
(
    guild_id INTEGER NOT NULL,
    user_id  INTEGER NOT NULL,
    end_time INTEGER NOT NULL,
    PRIMARY KEY (guild_id, user_id)
);

CREATE TABLE IF NOT EXISTS ChatSync
(
    channel_id_1 INTEGER NOT NULL,
    guild_id_1   INTEGER NOT NULL,
    channel_id_2 INTEGER NOT NULL,
    guild_id_2   INTEGER NOT NULL,
    PRIMARY KEY (channel_id_1, guild_id_1, channel_id_2, guild_id_2)
);

CREATE TABLE IF NOT EXISTS UserEconomy
(
    user_id   INTEGER PRIMARY KEY,
    user_name TEXT    NOT NULL,
    balance   INTEGER NOT NULL,
    last_roll INTEGER NOT NULL
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