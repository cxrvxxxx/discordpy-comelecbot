from .greeter import Greeter

async def setup(client):
    await client.add_cog(Greeter(client))
