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
            title=f"({rs_id}) {rs_name}",
            description=f"Running for {rs_pos} under {rs_party}"
        )

        embed.add_field(
            name="Voting statistics",
            value=f"Total votes: {rs_valid_count + rs_void_count}\nValid votes: {rs_valid_count}\nVoided votes: {rs_void_count}",
            inline=False
        )
        
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
            title=f"{position.name}",
            description=content
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)
