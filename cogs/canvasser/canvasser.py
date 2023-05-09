import os
import pandas as pd
import logging
from time import time
from typing import List, Union, Callable, Coroutine, Dict, Any
import functools
import asyncio
from datetime import datetime

import discord
from discord import app_commands
from discord.ext import commands

from fpdf import FPDF

from core.bot import ComelecBot

from .models.candidate_model import CandidateModel
from .classes.candidate import Candidate

def to_thread(func: Callable) -> Coroutine:
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        return await asyncio.to_thread(func, *args, **kwargs)
    return wrapper


class Canvasser(commands.Cog):
    def __init__(self, client: ComelecBot) -> None:
        self.client = client
        self.WORKDIR = os.path.join(os.path.dirname(__file__), 'data', 'workfile')
        self.LOGGER = logging.getLogger('canvasser')

    def is_validated(self, vote_id: int) -> bool:
        with self.client.DB_POOL as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM tblVote WHERE id=%(id)s", { "id": vote_id, })

            return False if c.fetchone() else True

    def is_unique(self, student_id: str, email: str) -> bool:
        # Clean arguments
        student_id = student_id.strip()
        email = email.strip()

        with self.client.DB_POOL as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM tblVote WHERE studentId=%(studentId)s OR email=%(email)s", { "studentId": student_id, "email": email, })

            return False if c.fetchone() else True  

    def is_enrolled(self, student_id: str) -> bool:
        student_id = student_id.strip()

        with self.client.DB_POOL as conn:
            c = conn.cursor()
            c.execute("SELECT studentNo FROM tblStudent WHERE studentNo=%(studentNo)s", { "studentNo": student_id, })
            
            return True if c.fetchone() else False
        
    def get_department(self, student_id: str) -> Union[str, None]:
        student_id = student_id.strip()

        with self.client.DB_POOL as conn:
            c = conn.cursor()
            c.execute("SELECT department FROM tblStudent WHERE studentNo=%(studentNo)s", { "studentNo": student_id, })
            
            result = c.fetchone()

        if result:
            return result[0]
        
        self.LOGGER.info(f"No 'department' found for {student_id}")
            
    def process_nameset(self, nameset: str) -> List[Candidate]:
        candidates = []
        nameset = nameset.split(';')

        for i in range(len(nameset)):
            if nameset[i] != '':
                candidate_id = self.extract_id(nameset[i].strip())

                candidate = CandidateModel.get_candidate_by_id(self.client.DB_POOL, candidate_id)
                
                if not candidate:
                    self.LOGGER.info(f"No 'candidate' found for: {candidate_id}-{nameset[i]}")
                    continue

                self.LOGGER.info(f"Found candidate: '{candidate.candidate_id}-{candidate.lastname}'.")
                candidates.append(candidate)

        return candidates
    
    def extract_id(self, name: str) -> Union[str, None]:
        name = name.split('-')
        return name[0]
    
    @to_thread
    def dump_to_pdf(self, sql_query, output_file):
        # Connect to SQLite database

        LAST_UPDATE_DATETIME = datetime.fromtimestamp(os.path.getmtime(fr"{self.WORKDIR}/{os.listdir(self.WORKDIR)[0]}")).strftime('%m/%d/%Y %H:%M')

        with self.client.DB_POOL as conn:
            c = conn.cursor()
            c.execute(sql_query)
            results = c.fetchall()

        # Create PDF document and set properties
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font('Arial', 'B', 12)

        # Add text header above table
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, 'CIT-U SSG General Election Results', ln=1)

        pdf.set_font('Arial', 'B', 9)
        pdf.cell(0, 10, f'As of {LAST_UPDATE_DATETIME}', ln=1)

        # Set table header row
        header = ['Position', 'ID', 'Name', 'Party', 'Valid Votes', 'Invalid Votes']

        # Calculate column widths based on header and data values
        col_widths = [pdf.get_string_width(str(header[i]).strip()) + 2 for i in range(len(header))]
        for row in results:
            col_widths[0] = max(col_widths[0], pdf.get_string_width(str(row[0]).strip()) + 2)
            col_widths[1] = max(col_widths[1], pdf.get_string_width(str(row[1]).strip()) + 2)
            col_widths[2] = max(col_widths[2], pdf.get_string_width(str(row[2]).strip()) + 2)
            col_widths[3] = max(col_widths[3], pdf.get_string_width(str(row[3]).strip()) + 2)
            col_widths[4] = max(col_widths[4], pdf.get_string_width(str(row[4]).strip()) + 2)
            col_widths[5] = max(col_widths[5], pdf.get_string_width(str(row[5]).strip()) + 2)

        # Add header row to PDF document
        pdf.ln()
        pdf.set_font('Arial', 'B', 9)
        for i in range(len(header)):
            pdf.cell(col_widths[i], 6, str(header[i]).strip(), border=1)
        pdf.ln()

        # Loop through results and add to PDF document
        pdf.set_font('Arial', '', 9)
        for row in results:
            pdf.cell(col_widths[0], 6, str(row[0]).strip(), border=1)
            pdf.cell(col_widths[1], 6, str(row[1]).strip(), border=1)
            pdf.cell(col_widths[2], 6, str(row[2]).strip(), border=1)
            pdf.cell(col_widths[3], 6, str(row[3]).strip(), border=1)
            pdf.cell(col_widths[4], 6, str(row[4]).strip(), border=1)
            pdf.cell(col_widths[5], 6, str(row[5]).strip(), border=1)
            pdf.ln()

        # Save PDF document to file
        pdf.output(output_file, 'F')

    @to_thread
    def process_votes(self) -> None:
        # Load file
        df = pd.read_excel(fr"{self.WORKDIR}/{os.listdir(self.WORKDIR)[0]}", header=0)
        df = df.fillna('None')
        df = df.astype("object")

        # Loop through all votes
        loop_start = time()
        for index, row in df.iterrows():
            iter_start = time()

            vote_id = row["ID"]
            student_no = row["ID Number"].strip()
            email = row["Email"].strip()
            is_valid = 1
            reason = ""

            try:
                # Check if validated
                if not self.is_validated(vote_id):
                    self.LOGGER.info(f"(ID: {vote_id}) flagged as VALIDATED. Skipping...")
                    continue

                # Check if duplicate
                if not self.is_unique(student_no, email):
                    is_valid = 0
                    reason += "Duplicate vote. "
                    self.LOGGER.info(f"(ID: {vote_id}) flagged as 'Duplicate'.")

                # Check if agreed
                if is_valid and not row["Agreement"] == "AGREE":
                    is_valid = 0
                    reason += "Did not agree. "
                    self.LOGGER.info(f"(ID: {vote_id}) flagged as 'DNA'.")

                # Check if enrolled
                if is_valid and not self.is_enrolled(student_no):
                    is_valid = 0
                    reason += "Not enrolled. "
                    self.LOGGER.info(f"(ID: {vote_id}) flagged as 'NE'.")

                college = row["College"]
                department = self.get_department(student_no)

                # Check if voted for correct department
                if college == "COLLEGE OF ARTS, SCIENCES, AND EDUCATION":
                    departments = [
                        "BSBIO", "BEED", "AB COMM", "AB-E", "AQAD", "BMMA", "BPA", "BSED-E",
                        "BSED-F", "BSED-M", "BSED-S", "BSMATH", "BSPSYCH"
                    ]

                    if is_valid and not department in departments:
                        is_valid = 0
                        reason += "Incorrect deapartment. "
                        self.LOGGER.info(f"(ID: {vote_id}) flagged as 'ID'.")
                elif college == "COLLEGE OF NURSING ANG ALLIED HEALTH SCIENCES":
                    departments = [
                        "BSN", "BSPHARMA"
                    ]

                    if is_valid and not department in departments:
                        is_valid = 0
                        reason += "Incorrect department. "
                        self.LOGGER.info(f"(ID: {vote_id}) flagged as 'ID'.")
                elif college == "COLLEGE OF MANAGEMENT, BUSINESS, AND ACCOUNTANCY":
                    departments = [
                        "BSA", "BSAIS", "BSBA-BA", "BSBA-BFM", "BSBA-GBM", "BSBA-HR", "BSBA-MKM",
                        "BSBA-OM", "BSBA-QM", "BSHM", "BSHRM", "BSMA", "BSOAD", "BSTM"
                    ]

                    if is_valid and not department in departments:
                        is_valid = 0
                        reason += "Incorrect department. "
                        self.LOGGER.info(f"(ID: {vote_id}) flagged as 'ID'.")
                elif college == "COLLEGE OF ENGINEERING AND ARCHITECTURE":
                    if is_valid and not row["CEA Department"] in department:
                        is_valid = 0
                        reason += "Incorrect department. "
                        self.LOGGER.info(f"(ID: {vote_id}) flagged as 'ID'.")
                elif college == "COLLEGE OF COMPUTER STUDIES":
                    if is_valid and not row["CCS Department"] in department:
                        is_valid = 0
                        reason += "Incorrect Department. "
                        self.LOGGER.info(f"(ID: {vote_id}) flagged as 'ID'.")
                elif college == "COLLEGE OF CRIMINAL JUSTICE":
                    if is_valid and not "BSCRIM" in department:
                        is_valid = 0
                        reason += "Incorrect Department. "
                        self.LOGGER.info(f"(ID: {vote_id}) flagged as 'ID'.")

                with self.client.DB_POOL as conn:
                    c = conn.cursor()
                    # Save vote to DB
                    self.LOGGER.info(f"(ID: {vote_id}) Recording vote entry for: '{student_no}'.")
                    c.execute(
                        "INSERT INTO tblVote VALUES (%(id)s, %(studentId)s, %(email)s, %(isValid)s, %(reason)s)",
                        {
                            "id": vote_id,
                            "studentId": student_no,
                            "email": email,
                            "isValid": is_valid,
                            "reason": reason
                        }
                    )
                # Process candidates
                selected_row = df.loc[
                    index,
                    [
                        "President", "Vice President", "Secretary General", "Treasurer General", "Auditor General",
                        "CASE Rep", "CNAHS Rep", "CMBA Rep", "ARCH Rep", "CE Rep", "CHE Rep", "CPE Rep",
                        "ECE Rep", "EE Rep", "EM Rep", "IE Rep", "ME Rep", "CS Rep", "IT Rep"
                    ]
                ]

                # Loop through voted candidates
                for name, value in selected_row.items():
                    if value == 'None':
                        continue

                    self.LOGGER.info(f"(ID: {vote_id}) Prcessing votes for position: '{name}'.")

                    nameset = value
                    candidates = self.process_nameset(nameset)

                    with self.client.DB_POOL as conn:
                        c = conn.cursor()
                        # Record candidate votes
                        for candidate in candidates:
                            c.execute("SELECT * FROM tblStudentVote WHERE voteId=%(voteId)s AND candidateId=%(candidateId)s", {
                                "voteId": vote_id,
                                "candidateId": candidate.candidate_id,
                            })

                            if c.fetchone():
                                self.LOGGER.info(f"(ID: {vote_id}) has already voted for candidate: '{candidate.candidate_id}-{candidate.lastname}'. Ignoring...")
                                continue

                            self.LOGGER.info(f"(ID: {vote_id}) Recording vote for candidate: '{candidate.candidate_id}-{candidate.lastname}'.")
                            c.execute("INSERT INTO tblStudentVote (voteId, candidateId) VALUES (%(voteId)s, %(candidateId)s)", {
                                "voteId": vote_id,
                                "candidateId": candidate.candidate_id,
                            })

                            # Check if saved
                            c.execute("SELECT * FROM tblStudentVote WHERE voteId=%(voteId)s AND candidateId=%(candidateId)s", {
                                "voteId": vote_id,
                                "candidateId": candidate.candidate_id,
                            })

                            if not c.fetchone():
                                self.LOGGER.info(f"(ID: {vote_id}) WARNING!: VOTE NOT SAVED FOR: '{candidate.candidate_id}-{candidate.lastname}'.")
                    
                self.LOGGER.info(f"Processed ({'{:.2f}'.format(time() - iter_start)})s | voteId: {vote_id}, studentNo: {student_no}, is_valid: {is_valid}, reason: {reason}")
            except Exception as e:
                self.LOGGER.info(e)
                continue

        self.LOGGER.info("Done {:.2f}s".format(time() - loop_start))

    @to_thread
    def get_vote_data(self, vote_id: int) -> Dict[str, Any]:
        # Load file
        df = pd.read_excel(fr"{self.WORKDIR}/{os.listdir(self.WORKDIR)[0]}", header=0)
        df = df.fillna('None')
        df = df.astype("object")

        selected_row = df[df['ID'] == vote_id].iloc[0]

        return {
            "consent": selected_row['Agreement'],
            "name": selected_row['Full Name'],
            "year": selected_row['Year level'],
            "college": selected_row['College'],
        }

    @app_commands.command(name="clearwd", description="Removes the current working file")
    async def clearwd(self, interaction: discord.Interaction) -> None:
        required_role = interaction.guild.get_role(1096073463313219687)
        if not required_role in interaction.user.roles:
            await interaction.response.send_message("You are not authorized to use this command")
            return
        
        for file in os.listdir(self.WORKDIR):
            os.remove(fr"{self.WORKDIR}/{file}")

        await interaction.response.send_message(embed=discord.Embed(
            color=discord.Color.gold(),
            description="Working directory cleared. Commands dependent on the working file will no longer function."
        ).set_footer(
            text="Use 'loadfile' to load a working file."
        ))

    @commands.command()
    async def loadfile(self, ctx: commands.Context) -> None:
        required_role = ctx.guild.get_role(1096073463313219687)
        if not required_role in ctx.author.roles:
            await ctx.send("You are not authorized to use this command")
            return
        
        if not ctx.message.attachments:
            await ctx.send("Error: No attached file.")
            return
        
        if len(ctx.message.attachments) > 1:
            await ctx.send("Error: Too many files.")
            return
        
        file = ctx.message.attachments[0]
        if not file.filename.endswith('.xlsx'):
            await ctx.send("Error: Not an Excel file.")
            return
        
        if len(os.listdir(self.WORKDIR)) > 0:
            await ctx.send("Error: Workfile already exists.")
            return
        
        await file.save(fr"{self.WORKDIR}/{file.filename}")   
        await ctx.send("File saved!")

    @commands.command()
    async def autovalidate(self, ctx: commands.Context) -> None:
        required_role = ctx.guild.get_role(1096073463313219687)
        if not required_role in ctx.author.roles:
            await ctx.send("You are not authorized to use this command")
            return

        if not len(os.listdir(self.WORKDIR)) > 0:
            await ctx.send("Error: No workfile.")
            return

        # Send message
        msg = await ctx.send(embed=discord.Embed(
            color=discord.Color.gold(),
            description="Processing votes, please wait..."
        ))

        await self.process_votes()

        # Update counter
        with self.client.DB_POOL as conn:
            c = conn.cursor()
            c.execute("SELECT COUNT(id) FROM tblVote")
            count = c.fetchone()[0]

            c.execute("SELECT COUNT(id) FROM tblVote WHERE isValid=0")
            voided = c.fetchone()[0]
        
        await msg.edit(content=None, embed=discord.Embed(
            color=discord.Color.gold(),
            title="Validation Complete!",
            description=f"Total: {count}\nVoid: {voided}"
        ).set_image(url="https://scontent.fceb3-1.fna.fbcdn.net/v/t39.30808-6/330836006_736551421144884_8269249174951218445_n.png?_nc_cat=102&ccb=1-7&_nc_sid=e3f864&_nc_eui2=AeHZBZ99StbsdLOml4D-razBJyqCl2kuENUnKoKXaS4Q1Xv44TTvciLS860w8x76OVfXnypEjHchNPiS5tEyZQFp&_nc_ohc=cEQMN75HmNwAX8B4Nse&_nc_ht=scontent.fceb3-1.fna&oh=00_AfBXE8cdx8GgAPS78ke79PsdAHXeGTae5KYChwd-Nox_Kw&oe=645C3D7A"))

    @commands.command()
    async def votereview(self, ctx: commands.Context, vote_id: int) -> None:
        required_role = ctx.guild.get_role(1096073463313219687)
        if not required_role in ctx.author.roles:
            await ctx.send("You are not authorized to use this command")
            return
        
        if not len(os.listdir(self.WORKDIR)) > 0:
            await ctx.send("Error: No workfile.")
            return
                
        with self.client.DB_POOL as conn:
            c = conn.cursor()

            c.execute("SELECT * FROM tblVote WHERE id=%(id)s", { "id": vote_id, })
            data = c.fetchone()

            if not data:
                await ctx.send(f"Error, no validated vote with ID {vote_id} found")
                return
            
            ID, STUDENT_ID, EMAIL, IS_VALID, REASON = data
            
            c.execute("SELECT candidateId FROM tblStudentVote WHERE voteId=%(voteId)s", { "voteId": ID, })
            candidate_ids = c.fetchall()

        VOTE_DATA = await self.get_vote_data(vote_id)
        CONSENT = VOTE_DATA.get('consent')

        candidates = ""
        for candidate_id in candidate_ids:
            candidate = CandidateModel.get_candidate_by_id(self.client.DB_POOL, candidate_id[0])

            if candidate:
                candidates += f"({candidate.candidate_id}) {candidate.lastname}, {candidate.firstname} {candidate.middle_initial + '.' if candidate.middle_initial else ''}\n"

        embed = discord.Embed(
            color=discord.Color.green() if IS_VALID else discord.Color.red(),
            title=f"ID: {ID} | {VOTE_DATA.get('name')}",
            description=f"{STUDENT_ID} : {EMAIL}\n{VOTE_DATA.get('college')}"
        )

        embed.add_field(
            name="General Information",
            value=f"""{'🔴' if CONSENT != 'AGREE' else '🟢'} Consent: {CONSENT}
            {'🔴' if not IS_VALID else '🟢'} Valid: {True if IS_VALID else False}
            {'🔴' if not REASON == '' else '🟢'} Reason: {REASON if REASON else 'N/A'}"""
        )

        embed.add_field(
            name="Affected Candidates",
            value=candidates,
            inline=False
        )

        await ctx.send(embed=embed)

    @app_commands.command(name="validate", description="Mark a vote as validated")
    @app_commands.describe(vote_id="The ID of the vote to validate")
    async def validate(self, interaction: discord.Interaction, vote_id: int) -> None:
        required_role = interaction.guild.get_role(1096073463313219687)
        if not required_role in interaction.user.roles:
            await interaction.response.send_message("You are not authorized to use this command")
            return
        
        with self.client.DB_POOL as conn:
            c = conn.cursor()

            c.execute("SELECT * FROM tblVote WHERE id=%(id)s", { "id": vote_id, })
            data = c.fetchone()

            if not data:
                await interaction.response.send_message(f"Error, no validated vote with ID {vote_id} found")
                return
            
            c.execute("UPDATE tblVote SET isValid=1, reason='' WHERE id=%(id)s", { "id": vote_id, })

        await interaction.response.send_message(embed=discord.Embed(
            color=discord.Color.gold(),
            description=f"Vote ID {vote_id} is now marked as **VALID**."
        ))

    @app_commands.command(name="void", description="Mark a vote as voided")
    @app_commands.describe(vote_id="The ID of the vote to void")
    @app_commands.describe(reason="The reason for voiding the vote")
    async def void(self, interaction: discord.Interaction, vote_id: int, *, reason: str) -> None:
        required_role = interaction.guild.get_role(1096073463313219687)
        if not required_role in interaction.user.roles:
            await interaction.response.send_message("You are not authorized to use this command")
            return
        
        with self.client.DB_POOL as conn:
            c = conn.cursor()

            c.execute("SELECT * FROM tblVote WHERE id=%(id)s", { "id": vote_id, })
            data = c.fetchone()

            if not data:
                await interaction.response.send_message(f"Error, no validated vote with ID {vote_id} found")
                return
            
            c.execute("UPDATE tblVote SET isValid=0, reason=%(reason)s WHERE id=%(id)s", { "id": vote_id, "reason": reason, })

        await interaction.response.send_message(embed=discord.Embed(
            color=discord.Color.gold(),
            description=f"Vote ID {vote_id} is now marked as **VOID**. Reason: '{reason}'."
        ))

    @app_commands.command(name="getvoided", description="List all voided votes")
    @app_commands.describe(offset="Offset the list by specified amount")
    async def getvoided(self, interaction: discord.Interaction, offset: int=0) -> None:
        with self.client.DB_POOL as conn:
            c = conn.cursor()

            c.execute("SELECT id, reason FROM tblVote WHERE isValid=0 LIMIT 20 OFFSET %(offset)s", { "offset": offset, })
            dataset = c.fetchall()

            c.execute("SELECT COUNT(id) FROM tblVote WHERE isValid=0")
            COUNT = c.fetchone()[0]

            if not dataset:
                await interaction.response.send_message("No voided votes found")
                return
            
        embed = discord.Embed(
            color=discord.Color.gold(),
            title="Elections 2023 Statistics",
            description="List of voided votes. Subject to review by the Commission on Elections"
        )

        voided_votes = ""
        for data in dataset:
            voided_votes += f"**`{data[0]}`** - {data[1]}\n"

        embed.add_field(
            name="ID - Void reason",
            value=voided_votes,
            inline=False
        )

        embed.set_image(url="https://scontent.fceb3-1.fna.fbcdn.net/v/t39.30808-6/330836006_736551421144884_8269249174951218445_n.png?_nc_cat=102&ccb=1-7&_nc_sid=e3f864&_nc_eui2=AeHZBZ99StbsdLOml4D-razBJyqCl2kuENUnKoKXaS4Q1Xv44TTvciLS860w8x76OVfXnypEjHchNPiS5tEyZQFp&_nc_ohc=cEQMN75HmNwAX8B4Nse&_nc_ht=scontent.fceb3-1.fna&oh=00_AfBXE8cdx8GgAPS78ke79PsdAHXeGTae5KYChwd-Nox_Kw&oe=645C3D7A")

        if COUNT > 20:
            embed.add_footer(text="Specify an offset to see the voided votes 21st and above")

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="electionresults", description="Retrieve election results")
    async def electionresults(self, interaction: discord.Interaction) -> None:
        query = """
            SELECT 
                pos.name AS 'Position',
                c.id AS 'ID', 
                CONCAT_WS(' ', CONCAT(c.lastname, ','), c.firstname, NULLIF(CONCAT(NULLIF(c.middleInitial, ''), '.'), '')) AS 'Name', 
                p.name AS 'Party', 
                COUNT(CASE WHEN t.isValid THEN 1 END) AS 'Valid Votes', 
                COUNT(CASE WHEN NOT t.isValid THEN 1 END) AS 'Invalid Votes'
            FROM tblCandidate AS c 
            JOIN tblSSGPosition as pos ON c.position = pos.id
            JOIN tblParty AS p ON c.affiliation = p.id 
            LEFT JOIN tblStudentVote AS v ON c.id = v.candidateId 
            LEFT JOIN tblVote AS t ON v.voteId = t.id AND t.isValid IS NOT NULL
            GROUP BY 
                c.id, 
                c.lastname
            ORDER BY
                c.position,
                `Valid Votes`
            DESC
        """

        await self.dump_to_pdf(query,"CITUGeneralElections2023Results.pdf")

        with open("CITUGeneralElections2023Results.pdf", 'rb') as f:
            file = discord.File(f)

            await interaction.response.send_message(embed=discord.Embed(
                color=discord.Color.gold(),
                title="Election results 2023",
                description="See attached file."
            ), file=file)
