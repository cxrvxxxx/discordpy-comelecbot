import discord
from discord import app_commands
from discord.ext import commands

from core.bot import ComelecBot

class Announcer(commands.Cog):
    def __init__(self, client: ComelecBot) -> None:
        self.client = client

    @app_commands.command(name="echo", description="Make an announcement")
    @app_commands.describe(channel="The channel to send the announcement to")
    @app_commands.describe(message_id="Message ID to copy")
    async def echo(self, interaction: discord.Interaction, channel: discord.TextChannel, message_id: str) -> None:
        if not interaction.user in channel.members and not channel.permissions_for(interaction.user).manage_channels:
            await interaction.response.send_message("You do not have permission to use this command.")
            await interaction.message.delete()
            return
        
        try:
            message_id = int(message_id)
        except ValueError:
            await interaction.response.send_message("Invalid message", ephemeral=True)
            return

        message = await interaction.channel.fetch_message(message_id)
        if not message:
            await interaction.response.send_message("Cannot find message.")
            return
        
        await channel.send(message.content)
        await interaction.response.send_message(f"Sent a message in {channel.name}")

    @app_commands.command(name="announce", description="Make an announcement")
    @app_commands.describe(channel="Where to announce")
    @app_commands.describe(message="Say something")
    async def announce(self, interaction: discord.Interaction, channel: discord.TextChannel, *, message: str) -> None:
        if not interaction.user in channel.members and not channel.permissions_for(interaction.user).manage_channels:
            await interaction.response.send_message("You do not have permission to use this command.")
            await interaction.message.delete()
            return
            
        await channel.send(message)
        await interaction.response.send_message(f"Sent a message in {channel.name}")
