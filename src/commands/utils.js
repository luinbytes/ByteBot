const { SlashCommandBuilder } = require('@discordjs/builders');
const Discord = require('discord.js')

module.exports = {
    register_command: new SlashCommandBuilder( )
        .setName( 'ping' )
        .setDescription( 'Replies with Pong(ms)!' ),
    async execute( client, interaction ) {
        return interaction.reply( `Pong! ${client.ws.ping}ms` )
    }
}