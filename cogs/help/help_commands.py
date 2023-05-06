import discord
from discord import app_commands
from discord.ext import commands

from core.bot import ComelecBot

class HelpCommands(commands.Cog):
    def __init__(self, client: ComelecBot) -> None:
        self.client = client
        self.client.logger.info("HelpCommands loaded")

    @app_commands.command(name='help', description='Show a guide on how to use app commands')
    async def help(self, interaction: discord.Interaction) -> None:
        embed = discord.Embed(
            color=discord.Color.gold(),
            title="Command Usage Guide",
        )

        for command in self.client.tree.walk_commands():
            embed.add_field(
                name='/' + command.name,
                value=command.description
            )

        await interaction.response.send_message(embed=embed)
