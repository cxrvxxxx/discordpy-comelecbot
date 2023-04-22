from .help_commands import HelpCommands

async def setup(client):
    await client.add_cog(HelpCommands(client))
