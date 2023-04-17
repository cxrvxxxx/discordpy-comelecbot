"""
Project name: CIT-U ComelecBot - Official CIT-U Discord Bot
Author: cxrvxxx
Description: A feature-packed Discord bot using discord.py
"""
# Standard imports
import os
import sys

# Third-party libraries
from dotenv import load_dotenv

# Package imports
from core.bot import ComelecBot

# Running the bot.
if __name__ == "__main__":
    load_dotenv()
    TOKEN = os.getenv('TOKEN')

    client = ComelecBot(sys_params=sys.argv)
    client.run(TOKEN, root_logger=True)
