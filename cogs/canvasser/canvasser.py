import os
import pandas as pd
import logging
from time import time
from typing import List, Union

import discord
from discord import app_commands
from discord.ext import commands

from core.bot import ComelecBot

from .models.candidate_model import CandidateModel

class Canvasser(commands.Cog):
    def __init__(self, client: ComelecBot) -> None:
        self.client = client
        self.WORKDIR = os.path.join(os.path.dirname(__file__), 'data', 'workfile')
        self.LOGGER = logging.getLogger('canvasser')

    def is_enrolled(self, student_id: str) -> bool:
        with self.client.DB_POOL as conn:
            c = conn.cursor()
            c.execute("SELECT studentNo FROM tblStudent WHERE studentNo LIKE %(studentNo)s", {"studentNo": '%' + student_id + '%',})
            
            return True if c.fetchone() else False
        
    def get_department(self, student_id: str) -> str:
        with self.client.DB_POOL as conn:
            c = conn.cursor()
            c.execute("SELECT department FROM tblStudent WHERE studentNo LIKE %(studentNo)s", {"studentNo": '%' + student_id + '%',})
            
            try:
                return c.fetchone()[0].strip()
            except Exception:
                return "NULL"
            
    def process_nameset(self, nameset: str) -> List[str]:
        names = nameset.split(';')

        for x in range(len(names)):
            names[x] = names[x].strip()

        return names
    
    def process_name(self, name: str) -> List[Union[str, None]]:
        lastname = None
        firstname = None
        mid_init = None

        name = name.split(',')

        for i in range(len(name)):
            name[i] = name[i].strip()

        lastname = name[0]
        name[1] = name[1].split(' ')
        for x in range(len(name[1])):
            if name[1][x].endswith('.'):
                mid_init = name[1].pop(x)
        
                if mid_init.endswith('.'):
                    mid_init = mid_init[:-1]

        firstname = ""
        for y in range(len(name[1])):
            firstname += name[1][y] + ' '

        if firstname.endswith(' '):
            firstname = firstname[:-1]

        return lastname, firstname, mid_init

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
    async def autovalidate(self, ctx: commands.Context) -> None:
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
        await ctx.message.delete()
        
        df = pd.read_excel(fr"{self.WORKDIR}/{os.listdir(self.WORKDIR)[0]}", header=0)
        df = df.fillna('None')
        df = df.astype("object")

        sql_insert_vote = "INSERT INTO tblVote VALUES "
        sql_insert_vote_params = {}

        count = 0
        voided = 0

        embed=discord.Embed(
            color=discord.Color.gold(),
            title="Validating...",
            description=f"Total: {count}\n\t Void: {voided}"
        )

        msg = await ctx.send(embed=embed)

        # Loop through all votes
        loop_start = time()
        for index, row in df.iterrows():
            iter_start = time()

            vote_id = row["ID"]
            student_no = row["ID Number"].strip()
            is_valid = 1
            reason = ""

            try:
                # Check if agreed
                if not row["Agreement"] == "AGREE":
                    is_valid = 0
                    reason = "Did not agree. "

                # Check if enrolled
                if is_valid and not self.is_enrolled(student_no):
                    is_valid = 0
                    reason += "Not enrolled. "

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
                elif college == "COLLEGE OF NURSING ANG ALLIED HEALTH SCIENCES":
                    departments = [
                        "BSN", "BSPHARMA"
                    ]

                    if is_valid and not department in departments:
                        is_valid = 0
                        reason += "Incorrect department. "
                elif college == "COLLEGE OF MANAGEMENT, BUSINESS, AND ACCOUNTANCY":
                    departments = [
                        "BSA", "BSAIS", "BSBA-BA", "BSBA-BFM", "BSBA-GBM", "BSBA-HR", "BSBA-MKM",
                        "BSBA-OM", "BSBA-QM", "BSHM", "BSHRM", "BSMA", "BSOAD", "BSTM"
                    ]

                    if is_valid and not department in departments:
                        is_valid = 0
                        reason += "Incorrect department. "
                elif college == "COLLEGE OF ENGINEERING AND ARCHITECTURE":
                    if is_valid and not row["CEA Department"] in department:
                        is_valid = 0
                        reason += "Incorrect department. "
                elif college == "COLLEGE OF COMPUTER STUDIES":
                    if is_valid and not row["CCS Department"] in department:
                        is_valid = 0
                        reason += "Incorrect Department. "
                elif college == "COLLEGE OF CRIMINAL JUSTICE":
                    if is_valid and not "BSCRIM" in department:
                        is_valid = 0
                        reason += "Incorrect Department. "

                # Append to query
                sql_insert_vote += f"(%(id{index})s, %(isValid{index})s, %(reason{index})s), "
                sql_insert_vote_params[f"id{index}"] = vote_id
                sql_insert_vote_params[f"isValid{index}"] = is_valid
                sql_insert_vote_params[f"reason{index}"] = reason
            except Exception as e:
                self.LOGGER.info(e)
                continue
            finally:
                # Update counter
                count += 1
                if is_valid == 0:
                    voided += 1

                log_msg = f"Processed ({'{:.2f}'.format(time() - iter_start)})s | voteId: {vote_id}, studentNo: {student_no}, is_valid: {is_valid}, reason: {reason}"
                
                embed = discord.Embed(
                    color=discord.Color.gold(),
                    title="Validating...",
                    description=f"Total: {count}\n\t Void: {voided}"
                )

                embed.set_footer(text=log_msg)

                msg = await msg.edit(embed=embed)
                self.LOGGER.info(log_msg)

        embed=discord.Embed(
            color=discord.Color.gold(),
            title="Validation Complete",
            description=f"Total: {count}\n\t Void: {voided}"
        )

        try:
            # Save to database
            with self.client.DB_POOL as conn:
                c = conn.cursor()

                # Insert votes
                sql_insert_vote = sql_insert_vote[:-2]
                c.execute(sql_insert_vote, sql_insert_vote_params)
        except Exception as e:
            embed.set_footer(text=f"WARNING!: {e}")
        finally:
            for file in os.listdir(self.WORKDIR):
                os.remove(fr"{self.WORKDIR}/{file}")

            self.LOGGER.info("Done {:.2f}s".format(time() - loop_start))
            await msg.edit(embed=embed)

