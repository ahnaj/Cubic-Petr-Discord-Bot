from datetime import datetime
import discord
from discord import app_commands
from discord.ext import commands


from resources.constants import *

class Fun(commands.Cog): 
    def __init__(self, bot): 
        self.bot = bot
        
    @commands.Cog.listener()
    async def on_ready(self: commands.Bot) -> None:
        print('The cog Fun.py is online!')
        
    @app_commands.command(name = 'ping', description = 'Get my latency in ms.')
    async def ping(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer()
        await interaction.followup.send(f'Pong! {round(self.bot.latency * 1000)} ms')
        
    @app_commands.command(name = 'say', description = 'I repeat what you say.')
    async def say(self, interaction: discord.Interaction, message: str) -> None:
        await interaction.response.defer()
        await interaction.channel.send(message)
        await interaction.followup.send('I know what you are but what am I.', ephemeral = True)
    
    @app_commands.command(name = 'stats', description = "Lists all the Discord servers I'm in.")
    async def servers(self, interaction: discord.Interaction) -> None: 
        await interaction.response.defer()
        servers = [server.name for server in self.bot.guilds]
        await interaction.followup.send(f'**Servers I\'m in:**\n{", ".join(servers)}')
            
async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Fun(bot))