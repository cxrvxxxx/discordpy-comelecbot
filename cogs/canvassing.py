import discord
from discord.ext import commands

from core.canvassing.checker import Checker
from core.canvassing.workfile import Workfile, workfile_path
from core.canvassing.vote import Vote

class Canvassing(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.command()
    async def loadfile(self, ctx: commands.Context):
        if len(ctx.message.attachments) == 0:
            await ctx.send("Error, there is no attached file!")
            return

        if len(ctx.message.attachments) > 1:
            await ctx.send("Error, too many files attached!")
            return

        fn = ctx.message.attachments[0].filename

        if not fn.endswith(".xlsx"):
            await ctx.send("Error, invalid file format.")
            return

        if Workfile.check_exists(fn):
            await ctx.send("Error, file already exists.")
            return

        await ctx.message.attachments[0].save(fr"{workfile_path}/{ctx.message.attachments[0].filename}")
        await ctx.send(f"File saved.")

    @commands.command()
    async def unloadfile(self, ctx, *, fn):
        wf = Workfile(fn)
        wf.delete()

        await ctx.send("File removed.")

    @commands.command()
    async def status(self, ctx: commands.Context): 
        embed = discord.Embed(
            color = discord.Color.gold(),
            title = "Vote Checking System"
        )

        fn = Workfile.get_workfile()
        embed.add_field(
            name = f"{'🟢' if fn is not None else '🔴'} Working File",
            value = f"{fn}",
            inline= False
        )

        if fn:
            fields = Vote.fetch_valid_votes()
            validated = len(fields)
            if fields:
                embed.add_field(
                    name = "Validated Votes",
                    value = validated,
                )

            fields = Vote.fetch_invalid_votes()
            voided = len(fields)
            if fields:
                embed.add_field(
                    name = "Voided Votes",
                    value = voided,
                )

            wf = Workfile(Workfile.get_workfile())
            total = 0
            while True:
                if not wf.cell(1, total + 1).value: break
                total += 1

            embed.add_field(
                name = "Canvassed votes",
                value = f"{validated + voided}/{total - 1}"
            )

        await ctx.send(embed=embed)

    @commands.command()
    async def validated(self, ctx):
        fields = Vote.fetch_valid_votes()

        embed = discord.Embed(
            colour = discord.Color.gold(),
            title = "Validated votes",
            description = "".join([f"{field[0]}; " for field in fields])
        )

        await ctx.send(embed=embed)

    @commands.command()
    async def voided(self, ctx):
        fields = Vote.fetch_invalid_votes()

        embed = discord.Embed(
            colour = discord.Color.gold(),
            title = "Voided votes",
            description = "".join([f"{field[0]}; " for field in fields])
        )

        await ctx.send(embed=embed)

    @commands.command()
    async def register(self, ctx, *, details: str = None):
        if not details:
            embed = discord.Embed(
                colour = discord.Color.gold(),
                title = "How to use the 'register' command?",
                description = "$register firstname_lastname_citu-email"
            )
            embed.add_field(
                name = "Sample",
                value = "$register John Van_Doe_johnvan.doe@cit.edu"
            )
            await ctx.send(embed=embed)
            return

        fields = details.split("_")

        if len(fields) != 3:
            await ctx.send("Invalid details, try again.")
            return
        
        checker = Checker.create(ctx.author.id, *fields)

        if not checker:
            await ctx.send("Error, you are already registered.")
            return

        await ctx.send("You are now registered!")

    @commands.command()
    async def checker(self, ctx, *, member: discord.Member):
        checker = Checker.get_by_id(member.id)

        if not checker:
            await ctx.send("Error, user is not a registered checker.")

        embed = discord.Embed(
            colour = discord.Color.gold(),
            title = "Checker Information",
            description = None
        )

        embed.add_field(
            name = "ID",
            value = checker.get_id(),
            inline = False
        )

        embed.add_field(
            name = "Lastname, Firstname",
            value = f"{checker.get_lastname()}, {checker.get_firstname()}",
            inline = False
        )

        embed.add_field(
            name = "Email",
            value = checker.get_email(),
            inline = False
        )

        embed.add_field(
            name = "Discord User",
            value = ctx.guild.get_member(checker.get_discord_id()).mention,
            inline = False
        )

        await ctx.send(embed=embed)

    @commands.command()
    async def checkers(self, ctx):
        checkers = Checker.get_all()

        embed = discord.Embed(
            colour = discord.Color.gold(),
            title = "List of Registered Checkers",
            description = None
        )

        embed.add_field(
            name = "ID, Lastname, Firstname, Email",
            value = "".join([f"`{checker.get_id()}` {checker.get_lastname()}, {checker.get_firstname()}; {checker.get_email()}\n" for checker in checkers]) if checkers else None
        )

        await ctx.send(embed=embed)

    @commands.command()
    async def pullvote(self, ctx, custom_id = None):
        if not Checker.is_checker(ctx.author.id):
            await ctx.send("Error, you must be a checker to do this.")
            return
        
        wf = Workfile(Workfile.get_workfile())
        if not wf:
            await ctx.send("Error, no working file.")
            return

        row_id = int(custom_id) + 1 if custom_id else 2
        if not custom_id:
            while True and wf.cell(1, row_id):
                if not Vote.check_exists(wf.cell(1, row_id).value): break
                row_id += 1

            if wf.cell(1, row_id).value is None:
                await ctx.send("Error, no available vote.")
                return

        embed = discord.Embed(
            colour = discord.Color.green(),
            title = f"ID: {wf.cell(1, row_id).value} | {wf.cell(7, row_id).value}",
            description = f"Consent: {wf.cell(6, row_id).value}"
        )

        embed.add_field(
            name = f"Study Load & Proof",
            value = f"Study Load: {wf.cell(8, row_id).value}\nProof: {wf.cell(9, row_id).value}",
            inline = False
        )

        for i in range(10, 35):
            if wf.cell(i, row_id).value:
                names = wf.cell(i, row_id).value.split(';')
            else:
                continue

            embed.add_field(
                name = f"{wf.cell(i, 1).value}",
                value = "".join([f'{name}\n' for name in names] if names else 'None'),
                inline = False
            )

        if Vote.check_exists(wf.cell(1, row_id).value):
            fields = Vote.fetch_vote(wf.cell(1, row_id).value)
            embed.add_field(
                name = "Checker",
                value = fields[0]
            )

            embed.add_field(
                name = "Validity",
                value = f"{'Valid' if fields[1] == 1 else 'Voided'}"
            )

            if fields[1] == 0:
                embed.add_field(
                    name = "Reason",
                    value = fields[2]
                )

        await ctx.send(embed=embed)

    @commands.command()
    async def validate(self, ctx, vote_id: int):
        if not Checker.is_checker(ctx.author.id):
            await ctx.send("Error, you must be a checker to do this.")
            return

        wf = Workfile(Workfile.get_workfile())
        fields = wf.fetch_row(vote_id, 35)
        vote = Vote(
            fields[0],
            Checker.get_checker_by_id(ctx.author.id).id,
            1,
            None
        )

        if Vote.check_exists(fields[0]):
            await ctx.send("Error, vote already checked.")
            return

        vote.save()
        await ctx.send("Vote processed!")

    @commands.command()
    async def void(self, ctx, vote_id: int, reason: int):
        if not Checker.is_checker(ctx.author.id):
            await ctx.send("Error, you must be a checker to do this.")
            return

        wf = Workfile(Workfile.get_workfile())
        fields = wf.fetch_row(vote_id, 35)
        vote = Vote(
            fields[0],
            Checker.get_checker_by_id(ctx.author.id).id,
            0,
            reason
        )

        if Vote.check_exists(fields[0]):
            await ctx.send("Error, vote already validated.")
            return

        vote.save()
        await ctx.send("Vote processed!")

    @commands.command()
    async def updatechecker(self, ctx, field, *, value):
        checker = Checker.get_by_id(ctx.author.id)
        if not checker:
            await ctx.send("Error, you must be a checker to do this.")
            return

        fields = ['firstname', 'lastname', 'email']
        if not field in fields:
            await ctx.send("Error, invalid field.")
            return

        if field == 'firstname':
            checker = checker.set_firstname(value)
        elif field == 'lastname':
            checker = checker.set_lastname(value)
        elif field == 'email':
            checker = checker.set_email(value)

        await ctx.send(f"Updated {field} to {value}.")

async def setup(client):
    await client.add_cog(Canvassing(client))
