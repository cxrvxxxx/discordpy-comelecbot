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
        
        if not candidate_id and not lastname and not firstname and not middle_initial:
            await interaction.response.send_message("You must specify at least one search filter")
            return
        
        candidates = CandidateModel.get_candidate(
            self.client.DB_POOL,
            candidate_id=candidate_id,
            lastname=lastname,
            firstname=firstname,
            middle_initial=middle_initial
        )

        if not candidates:
            await interaction.response.send_message("No candidate found", ephemeral=True)
            return
        
        embed = discord.Embed(
            color=discord.Color.gold(),
            title="Search results",
            description=f"{len(candidates)} possible matches found"
        )

        for candidate in candidates:
            embed.add_field(
                name=f"{candidate.lastname}, {candidate.firstname} {f'{candidate.middle_initial}.' if candidate.middle_initial else ''}",
                value=f"Running for {candidate.position.name}. Party: {candidate.affiliation.name}",
                inline=False
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name='partyinfo', description='Show candidates running under a specific party')
    @app_commands.describe(party_name="The party to search for")
    async def partyinfo(self, interaction: discord.Interaction, party_name: str) -> None:
        required_role = interaction.guild.get_role(1096073463313219687)
        if not required_role in interaction.user.roles:
            await interaction.response.send_message("You are not authorized to use this command")
            return
        
        candidates = CandidateModel.get_party(self.client.DB_POOL, party_name)

        if not candidates:
            await interaction.response.send_message("No candidate found", ephemeral=True)
            return
        
        embed = discord.Embed(
            color=discord.Color.gold(),
            title="Search results",
            description=f"{len(candidates)} possible matches found"
        )

        positions = []
        for candidate in candidates:
            if not candidate.position.name in positions:
                positions.append(candidate.position.name)

        for position in positions:
            position_candidates = []
            for candidate in candidates:
                if position == candidate.position.name:
                    position_candidates.append(candidate)

            embed.add_field(
                name=position,
                value="".join([f"{candidate.lastname}, {candidate.firstname}{f' {candidate.middle_initial}.' if candidate.middle_initial else ''}\n" for candidate in position_candidates]),
                inline=False
            )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name='positioninfo', description="Show candidates running for a specific position")
    @app_commands.describe(position_name="The position to search for")
    async def positioninfo(self, interaction: discord.Interaction, position_name: str) -> None:
        required_role = interaction.guild.get_role(1096073463313219687)
        if not required_role in interaction.user.roles:
            await interaction.response.send_message("You are not authorized to use this command")
            return
        
        candidates = CandidateModel.get_position(self.client.DB_POOL, position_name)
        if not candidates:
            await interaction.response.send_message("No candidates found", ephemeral=True)
            return

        embed = discord.Embed(
            color=discord.Color.gold(),
            title="Search results",
            description=f"{len(candidates)} possible matches found"
        )

        parties = []
        for candidate in candidates:
            if not candidate.affiliation.name in parties:
                parties.append(candidate.affiliation.name)
                
        for party in parties:
            party_candidates = []
            for candidate in candidates:
                if candidate.affiliation.name == party:
                    party_candidates.append(candidate)

            embed.add_field(
                name=party,
                value="".join([f"{candidate.lastname}, {candidate.firstname}{f' {candidate.middle_initial}.' if candidate.middle_initial else ''}\n" for candidate in party_candidates]) if party_candidates else 'None',
                inline=False
            )

        await interaction.response.send_message(embed=embed, ephemeral=True)
