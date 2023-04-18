from .canvasser import Canvasser
from .election_stats import ElectionStats
from core.bot import ComelecBot

async def setup(client: ComelecBot) -> None:
    await client.add_cog(Canvasser(client))
    await client.add_cog(ElectionStats(client))
