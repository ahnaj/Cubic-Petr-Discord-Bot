import aiosqlite
from datetime import datetime
import discord
from discord import app_commands
from discord.ext import commands
import json
import logging
import random
import string

from resources.constants import *
from utilities.query import *

class DiscordToWCA(commands.Cog): 
    def __init__(self, bot): 
        self.bot = bot
        
    @commands.Cog.listener()
    async def on_ready(self: commands.Bot) -> None:
        print('The cog DiscordToWCA.py is online!')
        
    @app_commands.command(name = 'link', description = 'Link a WCA ID to your Discord account.')
    async def link(self, interaction: discord.Interaction, id: str) -> None:
        try: 
            await interaction.response.defer(ephemeral = True)
            
            wca_id = await get_competitor_id_from_query(id)
            if wca_id is None: 
                await interaction.followup.send(f'**{id}** is not a valid WCA ID.')
                return
            
            with open('storage/verification.json', 'r') as file: 
                data = json.load(file) 
                
            discord_id = interaction.user.id
            user = await self.bot.fetch_user(discord_id)
            
            verification_code = await generate_code(10)
            while verification_code in data: 
                verification_code = await generate_code(10)
                    
            await reset_verification_code(data, discord_id)
            data.update({verification_code: {"discord_id": discord_id, "wca_id": wca_id}})
                
            with open('storage/verification.json', 'w') as file:
                json.dump(data, file, indent = 4)
            file.close()
                
            await user.send(f"Here is your new verification code to associate the WCA ID **[{wca_id}](https://www.worldcubeassociation.org/persons/{wca_id})** with your Discord account: ```{verification_code}``` ")
            
            await interaction.followup.send(f'Check your DMs! Then, enter the code in the command /verify to associate your WCA ID with your Discord account.', ephemeral = True)
        except Exception as error: 
            logging.error(f'An error occurred: {error}')
            
    @app_commands.command(name = 'verify', description = 'Link a WCA ID to your Discord account.')
    async def verify(self, interaction: discord.Interaction, code: str) -> None:   
        try: 
            await interaction.response.defer(ephemeral = True)
            with open('storage/verification.json', 'r') as file: 
                data = json.load(file) 
            if not code in data: 
                await interaction.response.send_message(f'**{code}** is not a valid verification code.', ephemeral = True)
                return 
            
            info = data[code]
            db = await aiosqlite.connect('storage/linked_ids.db')
            cursor = await db.cursor()

            sql = '''
                INSERT INTO linked_ids (discord_id, wca_id)
                VALUES (?, ?)
                ON CONFLICT(discord_id) DO UPDATE SET
                discord_id = excluded.discord_id,
                wca_id = excluded.wca_id
            '''
            parameters = (info['discord_id'], info['wca_id'])
            
            await cursor.execute(sql, parameters)
            await db.commit()
            await cursor.close()
            await db.close()
            del data[code]
            with open('storage/verification.json', 'w') as file:
                json.dump(data, file, indent = 4)
            file.close()
            
            await interaction.followup.send(f'**{info["wca_id"]}** has been linked to your Discord account!', ephemeral = True)
        except Exception as error:
            logging.error(f'An error occurred: {error}')
            await interaction.followup.send(f'**{code}** is not a valid verification code.', ephemeral = True)
            
    @app_commands.command(name = 'unlink', description = 'Unlink a WCA ID from your Discord account.')
    async def unlink(self, interaction: discord.Interaction) -> None: 
        try: 
            await interaction.response.defer(ephemeral = True)
            db = await aiosqlite.connect('storage/linked_ids.db')
            cursor = await db.cursor()
            await cursor.execute(f'DELETE FROM linked_ids WHERE discord_id = ?', (interaction.user.id,))
            await db.commit()
            await cursor.close()
            await db.close()
            await interaction.followup.send(f'Your WCA ID has been unlinked from your Discord account!', ephemeral = True)
        except Exception as error: 
            logging.error(f'An error occurred: {error}')
            
    @app_commands.command(name = 'id', description = 'Get your WCA ID.') 
    async def id(self, interaction: discord.Interaction) -> None:
        try:
            await interaction.response.defer(ephemeral = True)
            db = await aiosqlite.connect('storage/linked_ids.db')
            cursor = await db.cursor()
            await cursor.execute(f'SELECT wca_id FROM linked_ids WHERE discord_id = ?', (interaction.user.id,))
            wca_id = await cursor.fetchone()
            
            if wca_id is None:
                await interaction.followup.send("You haven't linked your WCA ID yet!")
                return
            
            await cursor.close()
            await db.close()
            await interaction.followup.send(f'Your WCA ID is **{wca_id[0]}**.', ephemeral = True)
        except Exception as error: 
            logging.error(f'An error occurred: {error}')

async def generate_code(length: int) -> str: 
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for character in range(length))

async def reset_verification_code(data: dict, discord_id: int) -> None:
    for code in data: 
        if data[code]['discord_id'] == discord_id: 
            del data[code]
            break
            
async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(DiscordToWCA(bot), guilds = [discord.Object(id=1259875466936975460)])