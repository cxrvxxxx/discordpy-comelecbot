"""
Project name: CIT-U ComelecBot - Official CIT-U Discord Bot
Author: cxrvxxx
Description: A feature-packed Discord bot using discord.py
"""
# Standard imports
import os
import sqlite3
from typing import Dict

# Third-party libraries
import discord
from discord.ext import commands
from dotenv import load_dotenv

# Version information
PROJECT_NAME:   str = "CIT-U ComelecBot - Official CIT-U Discord Bot"
VERSION:        str = "1.0.0"
AUTHOR:         str = "cxrvxxxx"
PREFIX:         str = "$"

# Subclassing commands.Bot
class ComelecBot(commands.Bot):
    def __init__(self) -> None:
        super().__init__(
            command_prefix=PREFIX,
            help_command=None,
            intents=discord.Intents().all()
        )

    async def setup_hook(self) -> None:
        """Performs setup tasks on before the bot starts"""
        # Setting up directories
        folders = (
            "cogs", "data"
        )
        for folder in folders:
            if not os.path.exists(f"./{folder}/"):
                os.mkdir(folder)

        # Loading cogs.
        for filename in os.listdir("./cogs"):
            if filename.endswith(".py"):
                # cut off the .py from the file name
                await self.load_extension(f"cogs.{filename[:-3]}")

    async def on_ready(self) -> None:
        """Called when the bot has finished loading"""
        # Setting bot activity status
        # await self.change_presence(
        #     activity = discord.Activity(
        #         type = discord.ActivityType.watching,
        #         name = "$"
        #     )
        # )

    async def close(self) -> None:
        """Bot shutdown"""
        await super().close()
        await self.session.close()

# Running the bot.
if __name__ == "__main__":
    load_dotenv()
    TOKEN = os.getenv('TOKEN')

    client = ComelecBot()
    client.run(TOKEN)
