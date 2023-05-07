import os
import pandas as pd
import logging
from time import time
from typing import List, Union, Callable, Coroutine
import functools
import asyncio

import discord
from discord import app_commands
from discord.ext import commands

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

    def is_unique(self, vote_id: int, student_id: str, email: str) -> bool:
        # Clean arguments
        student_id = student_id.strip()
        email = email.strip()

        with self.client.DB_POOL as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM tblVote WHERE id=%(id)s OR studentId=%(studentId)s OR email=%(email)s", { "id": vote_id, "studentId": student_id, "email": email, })

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
                # Check if unique
                if not self.is_unique(vote_id, student_no, email):
                    is_valid = 0
                    reason = "Duplicate vote. "
                    self.LOGGER.info(f"(ID: {vote_id}) flagged as DUPLICATE. Skipping...")
                    continue

                # Check if agreed
                if is_valid and not row["Agreement"] == "AGREE":
                    is_valid = 0
                    reason = "Did not agree. "
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

    @commands.command()
    async def student(self, ctx: commands.Context, *, student_id: str) -> None:
        is_enrolled = self.is_enrolled(student_id)
        await ctx.send(f"Student with ID Number {student_id} is {'enrolled' if is_enrolled else 'not enrolled'}")

    @commands.command()
    async def clearwd(self, ctx: commands.Context) -> None:
        for file in os.listdir(self.WORKDIR):
            os.remove(fr"{self.WORKDIR}/{file}")

        await ctx.send("Working Directory cleared!")

    @commands.command()
    async def loadfile(self, ctx: commands.Context) -> None:
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
            title="Validation Complete",
            description=f"Total: {count}\nVoid: {voided}"
        ))

