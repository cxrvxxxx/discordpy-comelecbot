from .announcer import Announcer
from core.bot import ComelecBot

async def setup(client: ComelecBot) -> None:
    await client.add_cog(Announcer(client))
