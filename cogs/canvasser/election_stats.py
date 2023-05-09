from datetime import datetime
import os

import discord
from discord import app_commands
from discord.ext import commands

import pandas as pd

from core.bot import ComelecBot

from .models.candidate_model import CandidateModel

class ElectionStats(commands.Cog):
    def __init__(self, client: ComelecBot) -> None:
        self.client = client
        self.client.logger.info("ElectionStats loaded")
        self.WORKDIR = os.path.join(os.path.dirname(__file__), 'data', 'workfile')

    @app_commands.command(name='stats', description='Show an overview of the current elections')
    async def stats(self, interaction: discord.Interaction) -> None:
        try:
            LAST_UPDATE_DATETIME = datetime.fromtimestamp(os.path.getmtime(fr"{self.WORKDIR}/{os.listdir(self.WORKDIR)[0]}")).strftime('%m/%d/%Y %H:%M')
        except Exception:
            LAST_UPDATE_DATETIME = "No file uploaded."

        with self.client.DB_POOL as conn:
            c = conn.cursor()

            c.execute("SELECT COUNT(id) FROM tblVote")
            TOTAL_VOTES = c.fetchone()[0]

            c.execute("SELECT COUNT(id) FROM tblCandidate WHERE id<6")
            EXECOM_COUNT = c.fetchone()[0]

            c.execute("SELECT COUNT(id) FROM tblCandidate WHERE id>5")
            REP_COUNT = c.fetchone()[0]

            TOTAL = EXECOM_COUNT + REP_COUNT

            c.execute("SELECT COUNT(id) FROM tblCandidate WHERE affiliation=1")
            UNITED_COUNT = c.fetchone()[0]

            c.execute("SELECT COUNT(tblStudentVote.id) FROM tblStudentVote LEFT JOIN tblCandidate ON tblStudentVote.candidateId=tblCandidate.id LEFT JOIN tblVote ON tblStudentVote.voteId=tblVote.id WHERE tblCandidate.affiliation=1 AND tblVote.isValid=1")
            UNITED_VALID_COUNT = c.fetchone()[0]

            c.execute("SELECT COUNT(tblStudentVote.id) FROM tblStudentVote LEFT JOIN tblCandidate ON tblStudentVote.candidateId=tblCandidate.id LEFT JOIN tblVote ON tblStudentVote.voteId=tblVote.id WHERE tblCandidate.affiliation=1 AND tblVote.isValid=0")
            UNITED_VOID_COUNT = c.fetchone()[0]

            UNITED_TOTAL_VOTE = UNITED_VALID_COUNT + UNITED_VOID_COUNT

            c.execute("SELECT COUNT(tblStudentVote.id) FROM tblStudentVote LEFT JOIN tblCandidate ON tblStudentVote.candidateId=tblCandidate.id LEFT JOIN tblVote ON tblStudentVote.voteId=tblVote.id WHERE tblCandidate.affiliation=2 AND tblVote.isValid=1")
            SAVE_VALID_COUNT = c.fetchone()[0]

            c.execute("SELECT COUNT(tblStudentVote.id) FROM tblStudentVote LEFT JOIN tblCandidate ON tblStudentVote.candidateId=tblCandidate.id LEFT JOIN tblVote ON tblStudentVote.voteId=tblVote.id WHERE tblCandidate.affiliation=2 AND tblVote.isValid=0")
            SAVE_VOID_COUNT = c.fetchone()[0]

            SAVE_TOTAL_VOTE = SAVE_VALID_COUNT + SAVE_VOID_COUNT

            c.execute("SELECT COUNT(tblStudentVote.id) FROM tblStudentVote LEFT JOIN tblCandidate ON tblStudentVote.candidateId=tblCandidate.id LEFT JOIN tblVote ON tblStudentVote.voteId=tblVote.id WHERE tblCandidate.affiliation=3 AND tblVote.isValid=1")
            INDEP_VALID_COUNT = c.fetchone()[0]

            c.execute("SELECT COUNT(tblStudentVote.id) FROM tblStudentVote LEFT JOIN tblCandidate ON tblStudentVote.candidateId=tblCandidate.id LEFT JOIN tblVote ON tblStudentVote.voteId=tblVote.id WHERE tblCandidate.affiliation=3 AND tblVote.isValid=0")
            INDEP_VOID_COUNT = c.fetchone()[0]

            INDEP_TOTAL_VOTE = INDEP_VALID_COUNT + INDEP_VOID_COUNT
            
            c.execute("SELECT COUNT(id) FROM tblCandidate WHERE affiliation=2")
            SAVE_COUNT = c.fetchone()[0]

            c.execute("SELECT COUNT(id) FROM tblCandidate WHERE affiliation=3")
            INDEP_COUNT = c.fetchone()[0]

            c.execute("SELECT COUNT(id) FROM tblVote")
            VALIDATED_VOTE_COUNT = c.fetchone()[0]

            c.execute("SELECT COUNT(id) FROM tblVote WHERE isValid=0")
            VOIDED_VOTE_COUNT = c.fetchone()[0]

            c.execute("SELECT COUNT(id) FROM tblStudentVote")
            TOTAL_CANDIDATE_VOTES = c.fetchone()[0]

            c.execute("SELECT reason, COUNT(reason) FROM tblVote WHERE reason NOT LIKE '' GROUP BY reason")
            TOP_VOID_REASONS = c.fetchall()

        embed = discord.Embed(
            title="CIT-U SSG General Elections 2023",
            color=discord.Color.gold()
        )
        embed.add_field(
            name="Candidate statistics",
            value=f"Out of **`{TOTAL}`** candidates,\n**`{EXECOM_COUNT}`** of which are **EXECOM**.\n**`{REP_COUNT}`** of which are from **REPRESENTATIVES**.",
            inline=False
        )
        
        embed.add_field(
            name="Party statistics",
            value=f"Out of **`{TOTAL}`** candidates,\n**`{UNITED_COUNT}`** of which are from **UNITED**.\n**`{SAVE_COUNT}`** of which are from **SAVE**.\n**`{INDEP_COUNT}`** of which are **INDEPENDENT**.",
            inline=False
        )

        embed.add_field(
            name="Polling statistics (overall)",
            value=f"Out of **`{TOTAL_VOTES}`** votes,\n**`{VALIDATED_VOTE_COUNT}`** valid.\n**`{VOIDED_VOTE_COUNT}`** void.",
            inline=False
        )

        embed.add_field(
            name="Polling statistics (per-candidate)",
            value=f"Out of **`{TOTAL_CANDIDATE_VOTES}`** candidate votes,\n**`{UNITED_VALID_COUNT+SAVE_VALID_COUNT+INDEP_VALID_COUNT}`** valid.\n**`{UNITED_VOID_COUNT+SAVE_VOID_COUNT+INDEP_VOID_COUNT}`** void.\n",
            inline=False
        )

        embed.add_field(
            name="Polling statistics (per-party)",
            value=f"Out of **`{TOTAL_CANDIDATE_VOTES}`** candidate votes,\n**`{UNITED_TOTAL_VOTE}`** for **UNITED**.\n**`{UNITED_VALID_COUNT}`** valid. **`{UNITED_VOID_COUNT}`** void.\n**`{SAVE_TOTAL_VOTE}`** for **SAVE**.\n**`{SAVE_VALID_COUNT}`** valid, **`{SAVE_VOID_COUNT}`** void.\n**`{INDEP_TOTAL_VOTE}`** for **INDEPENDENT**.\n**`{INDEP_VALID_COUNT}`** valid, **`{INDEP_VOID_COUNT}`** void."
        )

        void_reasons = ""
        for reason in TOP_VOID_REASONS:
            void_reasons += f"`{reason[1]}` voided vote(s) for reason: `{reason[0].strip()}'\n"

        embed.add_field(
            name="Top reason(s) for voided votes",
            value=void_reasons,
            inline=False
        )

        embed.set_image(url="https://scontent.fceb3-1.fna.fbcdn.net/v/t39.30808-6/330836006_736551421144884_8269249174951218445_n.png?_nc_cat=102&ccb=1-7&_nc_sid=e3f864&_nc_eui2=AeHZBZ99StbsdLOml4D-razBJyqCl2kuENUnKoKXaS4Q1Xv44TTvciLS860w8x76OVfXnypEjHchNPiS5tEyZQFp&_nc_ohc=cEQMN75HmNwAX8B4Nse&_nc_ht=scontent.fceb3-1.fna&oh=00_AfBXE8cdx8GgAPS78ke79PsdAHXeGTae5KYChwd-Nox_Kw&oe=645C3D7A")

        embed.set_footer(text=f"As of {LAST_UPDATE_DATETIME}")

        await interaction.response.send_message(embed=embed)
