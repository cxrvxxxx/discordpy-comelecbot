from datetime import datetime
import os

import discord
from discord import app_commands
from discord.ext import commands

import pandas as pd

from core.bot import ComelecBot

class ElectionStats(commands.Cog):
    def __init__(self, client: ComelecBot) -> None:
        self.client = client
        self.client.logger.info("ElectionStats loaded")
        self.WORKDIR = os.path.join(os.path.dirname(__file__), 'data', 'workfile')

    @app_commands.command(name='stats', description='Show an overview of the current elections')
    async def stats(self, interaction: discord.Interaction) -> None:
        df = pd.read_excel(fr"{self.WORKDIR}/{os.listdir(self.WORKDIR)[0]}", header=0)
        df = df.fillna('None')
        df = df.astype("object")

        LAST_UPDATE_DATETIME = datetime.fromtimestamp(os.path.getmtime(fr"{self.WORKDIR}/{os.listdir(self.WORKDIR)[0]}")).strftime('%m/%d/%Y %H:%M')

        TOTAL_VOTES = df.shape[0]

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

            c.execute("SELECT COUNT(id) FROM tblVote")
            VALIDATED_VOTE_COUNT = c.fetchone()[0]

            c.execute("SELECT COUNT(id) FROM tblVote WHERE isValid=0")
            VOIDED_VOTE_COUNT = c.fetchone()[0]

        embed = discord.Embed(
            title="Election 2023 Statistics",
            color=discord.Color.gold()
        )
        embed.add_field(
            name="Candidate statistics",
            value=f"""Total: {TOTAL}
            EXECOM Canidates: {EXECOM_COUNT}
            Representatives: {REP_COUNT}""",
            inline=False
        )
        
        embed.add_field(
            name="Party Statistics",
            value=f"""UNITED: {UNITED_COUNT}
            SAVE: {SAVE_COUNT}
            INDEPENDENT: {INDEP_COUNT}""",
            inline=False
        )

        embed.add_field(
            name="Polling statistics",
            value=f"""Total votes: {TOTAL_VOTES}
            Validated votes: {VALIDATED_VOTE_COUNT}
            Voided votes: {VOIDED_VOTE_COUNT}""",
            inline=False
        )

        embed.set_image(url="https://scontent.fceb3-1.fna.fbcdn.net/v/t39.30808-6/330836006_736551421144884_8269249174951218445_n.png?_nc_cat=102&ccb=1-7&_nc_sid=e3f864&_nc_eui2=AeHZBZ99StbsdLOml4D-razBJyqCl2kuENUnKoKXaS4Q1Xv44TTvciLS860w8x76OVfXnypEjHchNPiS5tEyZQFp&_nc_ohc=cEQMN75HmNwAX8B4Nse&_nc_ht=scontent.fceb3-1.fna&oh=00_AfBXE8cdx8GgAPS78ke79PsdAHXeGTae5KYChwd-Nox_Kw&oe=645C3D7A")

        embed.set_footer(text=f"As of {LAST_UPDATE_DATETIME}")

        await interaction.response.send_message(embed=embed)