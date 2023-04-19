from datetime import datetime

import discord
from discord import app_commands
from discord.ext import commands

from core.bot import ComelecBot

class ElectionStats(commands.Cog):
    def __init__(self, client: ComelecBot) -> None:
        self.client = client

    @app_commands.command(name='stats', description='Show an overview of the current elections')
    async def stats(self, interaction: discord.Interaction) -> None:
        with self.client.DB_POOL as conn:
            c = conn.cursor()

            c.execute("SELECT COUNT(id) FROM tblCandidate WHERE id<6")
            EXECOM_COUNT = c.fetchone()[0]

            c.execute("SELECT COUNT(id) FROM tblCandidate WHERE id>5")
            REP_COUNT = c.fetchone()[0]

            TOTAL = EXECOM_COUNT + REP_COUNT

            c.execute("SELECT COUNT(id) FROM tblCandidate WHERE affiliation=1")
            UNITED_COUNT = c.fetchone()[0]

            c.execute("SELECT COUNT(id) FROM tblCandidate WHERE affiliation=2")
            SAVE_COUNT = c.fetchone()[0]

            c.execute("SELECT COUNT(id) FROM tblCandidate WHERE affiliation=3")
            INDEP_COUNT = c.fetchone()[0]

        embed = discord.Embed(
            title="Election 2023 Statistics",
            description=f"As of {datetime.now().strftime('%m/%d/%Y %H:%M')}",
            color=discord.Color.gold()
        )
        embed.add_field(
            name="Candidate statistics",
            value=f"""Total: {TOTAL}
            EXECOM Canidates: {EXECOM_COUNT}
            Representatives: {REP_COUNT}
            
            UNITED: {UNITED_COUNT}
            SAVE: {SAVE_COUNT}
            INDEPENDENT: {INDEP_COUNT}""",
            inline=False
        )

        await interaction.response.send_message(embed=embed)