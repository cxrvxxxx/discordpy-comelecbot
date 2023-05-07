from datetime import datetime
import os

import discord
from discord import app_commands
from discord.ext import commands

from core.bot import ComelecBot

from .models.candidate_model import CandidateModel

class CandidateStats(commands.Cog):
    def __init__(self, client: ComelecBot) -> None:
        self.client = client
        self.client.logger.info("CandidateStats loaded")
        self.WORKDIR = os.path.join(os.path.dirname(__file__), 'data', 'workfile')

    @app_commands.command(name='candidateinfo', description="Show candidate information")
    @app_commands.describe(candidate_id='ID of the candidate')
    @app_commands.describe(lastname='Lastname of the candidate')
    @app_commands.describe(firstname='Firstname of the candidate')
    @app_commands.describe(middle_initial='Middle initial of the candidate')
    async def candidateinfo(self, interaction: discord.Interaction, candidate_id: int=None, lastname: str=None, firstname: str=None, middle_initial: str=None) -> None:       
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
        
        query = """
        SELECT 
            c.id AS 'ID', 
            CONCAT_WS(' ', c.firstname, NULLIF(c.middleInitial, ''), c.lastname) AS 'Name', 
            p.name AS 'Party', 
            COUNT(CASE WHEN t.isValid THEN 1 END) AS 'Valid Votes', 
            COUNT(CASE WHEN NOT t.isValid THEN 1 END) AS 'Invalid Votes', 
            pos.name AS 'Position' 
        FROM 
            tblCandidate AS c 
            JOIN tblParty AS p ON c.affiliation = p.id 
            JOIN tblSSGPosition AS pos ON c.position = pos.id 
            JOIN tblStudentVote AS v ON c.id = v.candidateId 
            JOIN tblVote AS t ON v.voteId = t.id 
        WHERE
            c.id = %(candidateId)s
        GROUP BY 
            c.id, 
            c.lastname, 
            pos.name, 
            p.name 
        """

        with self.client.DB_POOL as conn:
            c = conn.cursor()
            c.execute(query, { "candidateId": candidates[0].candidate_id, })
            rs_id, rs_name, rs_party, rs_valid_count, rs_void_count, rs_pos = c.fetchone()

        embed = discord.Embed(
            color=discord.Color.gold(),
            title="Elections 2023 Statistics",
            description="Candidate name search"
        )

        embed.add_field(
            name=f"({rs_id}) {rs_name}",
            value=f"Running for {rs_pos} under {rs_party}",
            inline=False
        )

        embed.add_field(
            name="Polling statistics",
            value=f"Total votes: {rs_valid_count + rs_void_count}\nValid votes: {rs_valid_count}\nVoided votes: {rs_void_count}",
            inline=False
        )

        embed.set_image(url="https://scontent.fceb3-1.fna.fbcdn.net/v/t39.30808-6/330836006_736551421144884_8269249174951218445_n.png?_nc_cat=102&ccb=1-7&_nc_sid=e3f864&_nc_eui2=AeHZBZ99StbsdLOml4D-razBJyqCl2kuENUnKoKXaS4Q1Xv44TTvciLS860w8x76OVfXnypEjHchNPiS5tEyZQFp&_nc_ohc=cEQMN75HmNwAX8B4Nse&_nc_ht=scontent.fceb3-1.fna&oh=00_AfBXE8cdx8GgAPS78ke79PsdAHXeGTae5KYChwd-Nox_Kw&oe=645C3D7A")
        
        LAST_UPDATE_DATETIME = datetime.fromtimestamp(os.path.getmtime(fr"{self.WORKDIR}/{os.listdir(self.WORKDIR)[0]}")).strftime('%m/%d/%Y %H:%M')
        embed.set_footer(text=f"As of {LAST_UPDATE_DATETIME}")

        await interaction.response.send_message(embed=embed, ephemeral=True)

    # TODO: Fix issue: No response for party data exceeding (1024 characters in size)
    # @app_commands.command(name='partyinfo', description='Show candidates running under a specific party')
    # @app_commands.describe(party_name="The party to search for")
    # async def partyinfo(self, interaction: discord.Interaction, party_name: str) -> None:
    #     required_role = interaction.guild.get_role(1096073463313219687)
    #     if not required_role in interaction.user.roles:
    #         await interaction.response.send_message("You are not authorized to use this command")
    #         return
        
    #     candidates = CandidateModel.get_party(self.client.DB_POOL, party_name)

    #     if not candidates:
    #         await interaction.response.send_message("No candidate found", ephemeral=True)
    #         return
        
    #     embed = discord.Embed(
    #         color=discord.Color.gold(),
    #         title="Search results",
    #         description=f"{len(candidates)} possible matches found"
    #     )

    #     positions = []
    #     for candidate in candidates:
    #         if not candidate.position.name in positions:
    #             positions.append(candidate.position.name)

    #     for position in positions:
    #         position_candidates = []
    #         for candidate in candidates:
    #             if position == candidate.position.name:
    #                 position_candidates.append(candidate)

    #         embed.add_field(
    #             name=position,
    #             value="".join([f"{candidate.lastname}, {candidate.firstname}{f' {candidate.middle_initial}.' if candidate.middle_initial else ''}\n" for candidate in position_candidates]),
    #             inline=False
    #         )

    #     await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name='positioninfo', description="Show candidates running for a specific position")
    @app_commands.describe(position_name="The position to search for")
    async def positioninfo(self, interaction: discord.Interaction, position_name: str) -> None:       
        position = CandidateModel.get_position(self.client.DB_POOL, position_name)
        if not position:
            await interaction.response.send_message(f"No position found matching '{position_name}'", ephemeral=True)
            return
        
        query = """
        SELECT 
            c.id AS 'ID', 
            CONCAT_WS(' ', c.firstname, NULLIF(c.middleInitial, ''), c.lastname) AS 'Name', 
            p.name AS 'Party', 
            COUNT(CASE WHEN t.isValid THEN 1 END) AS 'Valid Votes', 
            COUNT(CASE WHEN NOT t.isValid THEN 1 END) AS 'Invalid Votes'
        FROM 
            tblCandidate AS c 
            JOIN tblParty AS p ON c.affiliation = p.id 
            JOIN tblStudentVote AS v ON c.id = v.candidateId 
            JOIN tblVote AS t ON v.voteId = t.id 
        WHERE
            c.position = %(positionId)s
        GROUP BY 
            c.id, 
            c.lastname
        ORDER BY
            `Valid Votes` DESC
        """

        with self.client.DB_POOL as conn:
            c = conn.cursor()
            c.execute(query, { "positionId": position.position_id, })

            dataset = c.fetchall()

        content = ""
        count = 1
        for i in range(len(dataset)):
            rs_id, rs_name, rs_party, rs_valid_count, rs_void_count = dataset[i]

            if i != 0:
                if dataset[i - 1][3] > rs_valid_count:
                    count += 1

            stats = f'Votes: {rs_valid_count} valid, {rs_void_count} void'
            content += f"**#{count}** | {stats:24} | ({rs_id}) {rs_name} [{rs_party}] \n"

        embed = discord.Embed(
            color=discord.Color.gold(),
            title="Elections 2023 Statistics",
            description="Candidates who did not garner at least one (1) vote may not appear in the list."
        )

        embed.add_field(
            name=f"{position.name}",
            value=content,
            inline=False
        )

        embed.set_image(url="https://scontent.fceb3-1.fna.fbcdn.net/v/t39.30808-6/330836006_736551421144884_8269249174951218445_n.png?_nc_cat=102&ccb=1-7&_nc_sid=e3f864&_nc_eui2=AeHZBZ99StbsdLOml4D-razBJyqCl2kuENUnKoKXaS4Q1Xv44TTvciLS860w8x76OVfXnypEjHchNPiS5tEyZQFp&_nc_ohc=cEQMN75HmNwAX8B4Nse&_nc_ht=scontent.fceb3-1.fna&oh=00_AfBXE8cdx8GgAPS78ke79PsdAHXeGTae5KYChwd-Nox_Kw&oe=645C3D7A")
        
        LAST_UPDATE_DATETIME = datetime.fromtimestamp(os.path.getmtime(fr"{self.WORKDIR}/{os.listdir(self.WORKDIR)[0]}")).strftime('%m/%d/%Y %H:%M')
        embed.set_footer(text=f"As of {LAST_UPDATE_DATETIME}")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
