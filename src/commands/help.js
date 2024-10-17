const { SlashCommandBuilder } = require('@discordjs/builders');
const Discord = require('discord.js')

module.exports = {
    register_command: new SlashCommandBuilder()
        .setName('help')
        .setDescription('Displays all commands available to you!'),
    async execute(client, interaction) {
        let commands = client.commands
        let embed = new Discord.Embed()
            
            .setColor('GREEN')
        commands.forEach(command => {
            embed.addField(command.register_command.name, command.register_command.description)
        })
        return interaction.reply({embeds:[embed],ephemeral :true})
    }
}