import discord
from discord import app_commands
from discord.ext import commands

from core.bot import ComelecBot

from .models.candidate_model import CandidateModel

class CandidateStats(commands.Cog):
    def __init__(self, client: ComelecBot) -> None:
        self.client = client
        self.client.logger.info("CandidateStats loaded")

    @app_commands.command(name='candidateinfo', description="Show candidate information")
    @app_commands.describe(candidate_id='ID of the candidate')
    @app_commands.describe(lastname='Lastname of the candidate')
    @app_commands.describe(firstname='Firstname of the candidate')
    @app_commands.describe(middle_initial='Middle initial of the candidate')
    async def candidateinfo(self, interaction: discord.Interaction, candidate_id: int=None, lastname: str=None, firstname: str=None, middle_initial: str=None) -> None:
        required_role = interaction.guild.get_role(1096073463313219687)
        if not required_role in interaction.user.roles:
            await interaction.response.send_message("You are not authorized to use this command")
            return
        
        candidate = CandidateModel.get_candidate(
            self.client.DB_POOL,
            candidate_id=candidate_id,
            lastname=lastname,
            firstname=firstname,
            middle_initial=middle_initial
        )

        if not candidate:
            await interaction.response.send_message("No candidate found", ephemeral=True)
            return
        
        await interaction.response.send_message(
            embed=discord.Embed(
                color=discord.Color.gold(),
                title=f"{candidate.lastname}, {candidate.firstname} {f'{candidate.middle_initial}.' if candidate.middle_initial else ''}",
                description=f"Running for {candidate.position.name}. Party: {candidate.affiliation.name}"
            ), ephemeral=True
        )
