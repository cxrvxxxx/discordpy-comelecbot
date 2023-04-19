from .canvasser import Canvasser
from .candidate_stats import CandidateStats
from .election_stats import ElectionStats
from .student_stats import StudentStats
from core.bot import ComelecBot

async def setup(client: ComelecBot) -> None:
    await client.add_cog(Canvasser(client))
    await client.add_cog(ElectionStats(client))
    await client.add_cog(StudentStats(client))
    await client.add_cog(CandidateStats(client))
