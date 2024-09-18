import aiohttp
import aiosqlite
import asyncio
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
import logging
import os

from resources.constants import *

load_dotenv()
TOKEN = os.getenv('TOKEN')
OWNER_ID = int(os.getenv('OWNER_ID'))

logging.basicConfig(filename = 'logs/app.log', level = logging.INFO, format = '%(asctime)s - %(levelname)s - %(message)s')

command_prefix = 'p!'
bot = commands.Bot(command_prefix , intents = discord.Intents.all())

@bot.command()
async def sync(ctx):
    if ctx.author.id == OWNER_ID:
        tree = await bot.tree.sync(guild = ctx.guild)
        await ctx.send(f'Synced {len(tree)} commands to the {ctx.guild.name}!')
    else:
        await ctx.send("You don't have permission to use this command.", ephemeral = True)

@bot.event
async def on_ready():
    print ("Bot is online!")

async def load():
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            await bot.load_extension(f'cogs.{filename[:-3]}')
        
@bot.tree.error
async def on_app_command_error(error: app_commands.AppCommandError, interaction: discord.Interaction):
    if isinstance(error, app_commands.CommandOnCooldown):
        print('hello')
    else: 
        logging.error(f'An error occurred: {error}')

async def main():
    async with bot:
        await load()
        await bot.start(TOKEN)

asyncio.run(main())