import discord
from discord import app_commands
from discord.ext import commands

from .models.student_model import StudentModel
from core.bot import ComelecBot

class StudentStats(commands.Cog):
    def __init__(self, client: ComelecBot) -> None:
        self.client = client
        self.client.logger.info("StudentStats loaded")

    @app_commands.command(name='studentinfo', description='Show information about a student')
    @app_commands.describe(student_id='The ID of the student to check')
    async def studentinfo(self, interaction: discord.Interaction, *, student_id: str) -> None:
        required_role = interaction.guild.get_role(1096073463313219687)
        if not required_role in interaction.user.roles:
            await interaction.response.send_message("You are not authorized to use this command")
            return
        
        student = StudentModel.get_student(self.client.DB_POOL, student_id)

        if not student:
            await interaction.response.send_message("Student is not enrolled", ephemeral=True)
            return
        
        await interaction.response.send_message(
            embed=discord.Embed(
                color=discord.Color.gold(),
                description=f"{student.student_num}, {student.program}, {student.year}"
            ), ephemeral=True
        )
