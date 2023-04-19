import os

import discord
from discord import app_commands
from discord.ext import commands

from core.bot import ComelecBot

class Canvasser(commands.Cog):
    def __init__(self, client: ComelecBot) -> None:
        self.client = client
        self.working_directory = os.path.join(os.path.dirname(__file__), 'data')

    @commands.command()
    async def isenrolled(self, ctx: commands.Context, *, student_id: str) -> None:
        with self.client.DB_POOL as conn:
            c = conn.cursor()
            c.execute("SELECT studentNo FROM tblStudent WHERE studentNo=%(studentNo)s", {"studentNo": student_id,})
            
            await ctx.send(f"Student with ID Number {student_id} is {'enrolled' if c.fetchone() else 'not enrolled'}")
