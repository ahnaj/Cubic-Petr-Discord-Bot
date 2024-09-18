import aiosqlite
import discord
from discord import app_commands
from discord.ext import commands
import json
import logging
import urllib.parse

from resources.constants import *
from utilities.embeds import *
from utilities.query import *

def is_admin(interaction: discord.Interaction) -> bool:
    return interaction.user.guild_permissions.administrator

class ServerSettings(commands.Cog): 
    def __init__(self, bot): 
        self.bot = bot
        
    @commands.Cog.listener()
    async def on_ready(self): 
        print('The cog ServerSettings.py is online!')
        
    @app_commands.command(name = 'sethq', description = 'Set a location to base your WCA notifications on. Use a public address, not a private one!')
    @app_commands.check(is_admin)
    async def sethq(self, interaction: discord.Interaction, address: str, radius: int = None) -> None: 
        try: 
            await interaction.response.defer()
            url = 'https://nominatim.openstreetmap.org/search?q=' + urllib.parse.quote(address) + '&format=json' + '&accept-language=en'
            map_response = await request(url)
            
            map_data = json.loads(map_response)
            display_name = map_data[0]['display_name']
            region = display_name.split(',')[-1].strip()
            latitude, longitude = float(map_data[0]['lat']), float(map_data[0]['lon'])

            db = await aiosqlite.connect('storage/main.db')
            cursor = await db.cursor()
            
            sql = '''
                INSERT INTO server_info (guild_id, hq, region, latitude, longitude, radius)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(guild_id) DO UPDATE SET
                hq = excluded.hq,
                region = excluded.region,
                latitude = excluded.latitude,
                longitude = excluded.longitude,
                radius = excluded.radius
            '''
            parameters = (interaction.guild.id, display_name, region, latitude, longitude, radius)
            
            await cursor.execute(sql, parameters)
            await db.commit()
            await cursor.close()
            await db.close()
            await interaction.followup.send(f'Your HQ has been set to **{display_name}**!')
        except Exception as error: 
            logging.error(f'An error occurred: {error}')
                
    @app_commands.command(name = 'hq', description = 'I tell you the details of your HQ.')
    async def hq(self, interaction: discord.Interaction) -> None: 
        try: 
            await interaction.response.defer()
            db = await aiosqlite.connect('storage/main.db')
            cursor = await db.cursor()
            await cursor.execute(f'SELECT hq, latitude, longitude, radius, competitions_channel_id, deals_channel_id FROM server_info WHERE guild_id = ?', (interaction.guild.id,))
            hq_info = await cursor.fetchone()
            
            if hq_info is None: 
                await interaction.followup.send("You haven't set your HQ yet!")
                return 
            
            embed_message = await get_hq_embed(interaction, hq_info)
            await cursor.close()
            await db.close()
            await interaction.followup.send(embed = embed_message)
        except Exception as error: 
            logging.error(f'An error occurred: {error}')
            
    @app_commands.command(name = 'notifications', description = 'Set your notifications settings for WCA competitions and online deals/sales!')
    @commands.has_permissions(administrator = True)
    async def notifications(self, interaction: discord.Interaction, competitions_channel_id: str = None) -> None: 
        await interaction.response.defer()
        competitions_channel = discord.utils.get(interaction.guild.channels, name = competitions_channel_id)
    
        competitions_channel_id = interaction.channel_id if competitions_channel is None else competitions_channel.id
            
        db = await aiosqlite.connect('storage/main.db')
        cursor = await db.cursor()
        
        sql = '''
            INSERT INTO server_info (guild_id, competitions_channel_id)
            VALUES (?, ?)
            ON CONFLICT(guild_id) DO UPDATE SET
            competitions_channel_id = excluded.competitions_channel_id
        '''
        parameters = (interaction.guild.id, competitions_channel_id)
        
        await cursor.execute(sql, parameters)
        await db.commit()
        await cursor.close()
        await db.close()
        
        embed_message = discord.Embed(title = 'Notifications settings updated!', description = ' ', color = discord.Color.from_rgb(*UCI_GOLD))
        embed_message.add_field(name = '', value = f"**WCA Competitions:** <#{competitions_channel_id}>", inline = False)
        await interaction.followup.send(embed = embed_message)
    
async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ServerSettings(bot), guilds = [discord.Object(id=1259875466936975460)])