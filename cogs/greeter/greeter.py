from datetime import datetime

import discord
from discord import app_commands
from discord.ext import commands

from core.bot import ComelecBot

class Greeter(commands.Cog):
    def __init__(self, client: ComelecBot) -> None:
        self.client = client

    @app_commands.command(name='setgreeting', description="Set a custom greet message when someone joins.")
    @app_commands.describe(message="The message to send.")
    async def setgreeting(self, interaction: discord.Interaction, *, message: str) -> None:
        if not interaction.user.guild_permissions.manage_channels:
            await interaction.response.send_message("You do not have permission to use this command.")
            return

        with self.client.DB_POOL as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM tblGreeting WHERE isActive=1 AND guildId=%(guildId)s", {"guildId": interaction.guild_id,})
            entry = c.fetchone()
            if entry:
                c.execute("UPDATE tblGreeting SET isActive=0 WHERE id=%s", (entry[0], ))
            message = {
                "guildId": interaction.guild_id,
                "message": message,
                "createdBy": interaction.user.id,
                "createdOn": datetime.now().strftime("%y-%m-%d")
            }
            c.execute(f"""INSERT INTO tblGreeting (guildId, message, isActive, createdBy, createdOn)
            VALUES (%(guildId)s, %(message)s, 1, %(createdBy)s, %(createdOn)s)""", message)

        await interaction.response.send_message("Custom greet message set!")

