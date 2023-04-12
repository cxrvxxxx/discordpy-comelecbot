# Standard imports
from logging.config import dictConfig
from typing import List
import json
import logging
import os

# Third-party imports
import discord
from discord.ext import commands

# Package imports
from .mysql_pool import MySQLPool

# Subclassing commands.Bot
class ComelecBot(commands.Bot):
    def __init__(self, sys_params: List[str]=None) -> None:
        # Setting up bot settings
        with open(os.path.join(os.path.dirname(__file__), "..", "settings.json"), "r") as f:
            self.SETTINGS = json.load(f)

        # Setting up logger
        with open(os.path.join(os.path.dirname(__file__), "..", "logging_config.json"), "r") as f:
            path = os.path.join(os.path.dirname(__file__), "..", "logs")

            if not os.path.exists(path):
                os.mkdir("logs")

            dictConfig(json.load(f))            

        # Initialize superclass
        super().__init__(
            command_prefix=self.SETTINGS.get("default_prefix"),
            help_command=None,
            intents=discord.Intents().all()
        )

        self.logger = logging.getLogger("bot")
        self.DB_POOL = MySQLPool()
        self.SYS_PARAMS = sys_params

    async def setup_hook(self) -> None:
        """Performs setup tasks on before the bot starts"""
        # Loading cogs
        for module in self.SETTINGS.get("installed_modules"):
            await self.load_extension(module)

    async def on_ready(self) -> None:
        """Called when the bot has finished loading"""
        await self.wait_until_ready()
        self.logger.debug(f"Connected to discord as {self.user}")
        # Setting bot activity status
        # await self.change_presence(
        #     activity = discord.Activity(
        #         type = discord.ActivityType.watching,
        #         name = "prefix 'c!'"
        #     )
        # )
        if "sync" in self.SYS_PARAMS:
            await self.sync_app_commands()

    async def sync_app_commands(self) -> List[str]:
        """Sync application commands"""
        self.logger.debug("Syncronizing application commands to Discord")
        synced = await self.tree.sync()
        self.logger.debug(f"Sync finished ({len(synced)} commands)")
        return synced

    async def close(self) -> None:
        """Bot shutdown"""
        await super().close()
        await self.session.close()
