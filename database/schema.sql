CREATE TABLE IF NOT EXISTS `warns` (
  `id` int(11) NOT NULL,
  `user_id` varchar(20) NOT NULL,
  `server_id` varchar(20) NOT NULL,
  `moderator_id` varchar(20) NOT NULL,
  `reason` varchar(255) NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS GuildStarboardChannels (
            guild_id INTEGER PRIMARY KEY,
            channel_id INTEGER NOT NULL,
            starboard_min_reactions INTEGER NOT NULL DEFAULT 3
);

        CREATE TABLE IF NOT EXISTS GuildAutoroles (
            guild_id INTEGER PRIMARY KEY,
            role_id INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS GuildPrefix (
            guild_id INTEGER PRIMARY KEY,
            prefix TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS GuildLoggingChannels (
            guild_id INTEGER PRIMARY KEY,
            channel_id INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS GuildMuteRole (
            guild_id INTEGER PRIMARY KEY,
            role_id INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS GuildWelcomeChannels (
            guild_id INTEGER PRIMARY KEY,
            channel_id INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS GuildLeaveChannels (
            guild_id INTEGER PRIMARY KEY,
            channel_id INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS ChatSync (
  channel_id_1 INTEGER NOT NULL,
  guild_id_1 INTEGER NOT NULL,
  channel_id_2 INTEGER NOT NULL,
  guild_id_2 INTEGER NOT NULL,
  PRIMARY KEY (channel_id_1, guild_id_1, channel_id_2, guild_id_2)
);

CREATE TABLE IF NOT EXISTS UserEconomy (
            user_id INTEGER PRIMARY KEY,
            user_name TEXT NOT NULL,
            balance INTEGER NOT NULL,
            last_roll INTEGER NOT NULL
);