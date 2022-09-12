import os

import hikari
import lightbulb

bot = lightbulb.BotApp(
    os.environ["TOKEN"],
    default_enabled_guilds=int(os.environ["DEFAULT_GUILD_ID"]),
    help_slash_command = False,
    intents = hikari.Intents.ALL,
    prefix = os.environ["PREFIX"],
)

@bot.command()
@lightbulb.command("ping", "Replies with pong.")
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def ping(ctx: lightbulb.Context) -> None:
    await ctx.respond("Pong!")

@bot.command()
@lightbulb.option("text", "The thing to say.")
@lightbulb.command("say", "Make the bot say something.")
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def say(ctx: lightbulb.Context) -> None:
    await ctx.respond(ctx.options.text)

def run() -> None:
    if os.name != "nt":
        import uvloop
        uvloop.install()

    bot.run()