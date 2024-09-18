import aiosqlite
import asyncio
from datetime import datetime
from dateutil import parser
import discord
from discord import app_commands
from discord.ext import commands, tasks
from geopy.distance import geodesic
import json

from utilities.query import * 
from utilities.embeds import *

class CompetitionNotifer(commands.Cog): 
    def __init__(self, bot): 
        self.bot = bot
        
    @commands.Cog.listener()
    async def on_ready(self) -> None:
        self.fetch_new_competitions.start()
        print('The cog CompetitionNotifier.py is online!')
        
    @tasks.loop(minutes = 15)
    async def fetch_new_competitions(self):
        competitions = await get_current_competitions()
        await dump_competitions(competitions)
        await self.deliver_competitions(competitions)
        
    @tasks.loop(hours = 1)
    async def check_registration(self): 
        today = datetime.now()
        if not today.hour == 12: 
            return 
        with open('storage/new_competitions.json', 'r') as file: 
            new_competitions = json.load(file)
        for competition in new_competitions:
            id = competition['id']
            api_response = await request('https://www.worldcubeassociation.org/api/v0/competitions/{id}')
            registration_open = parser.isoparse(api_response['registration_open'])
            registration_close = parser.isoparse(api_response['registration_close'])
            if registration_open == today: 
                print(competition['name'] + ' ')
            elif today == registration_close: 
                print(competition['name'] + ' ')
    
    async def deliver_competitions(self, competitions: list):
        try: 
            old_competitions, current_competitions = await asyncio.gather(
                get_old_competitions(),
                get_current_competitions()
            )
            results = await compare_competitions(old_competitions, current_competitions)
            print(results)
            if results == []: 
                return 
            await update_new_competitions(results)
            await update_old_competitions(current_competitions)
            async with aiosqlite.connect('storage/main.db') as db:
                async with db.execute('SELECT latitude, longitude, radius, competitions_channel_id FROM server_info') as cursor:
                    async for row in cursor:
                        current_results = []
                        
                        hq_coordinates = (row[0], row[1])
                        radius = row[2]
                        competitions_channel_id = row[3] 
                        
                        if radius is None: 
                            current_results = results
                        else: 
                            for competition in results: 
                                current_coordinates = (competition['latitude'], competition['longitude'])
                                distance = geodesic(hq_coordinates, current_coordinates).kilometers
                                if distance <= radius: 
                                    current_results.append(competition)
                                    
                        if current_results == []: 
                            return
                        
                        results_embed = await get_competitions_notifications_embed(current_results)
                        competitions_channel = self.bot.get_channel(competitions_channel_id)
                        await competitions_channel.send(embed = results_embed)
        except Exception as error:
            print(error)
                    
async def get_current_competitions() -> list: 
    try: 
        year = datetime.now().year
        
        api_url_next_year = f'https://raw.githubusercontent.com/robiningelbrecht/wca-rest-api/master/api/competitions/{year+1}.json'
        api_url_this_year = f'https://raw.githubusercontent.com/robiningelbrecht/wca-rest-api/master/api/competitions/{year}.json'
        
        api_response_next_year, api_response_this_year = await asyncio.gather(
            request(api_url_next_year),
            request(api_url_this_year)
        )
        
        data_next_year = json.loads(api_response_next_year)
        data_this_year = json.loads(api_response_this_year)
        
        competitions = [
            {'id': competition['id'], 'name': competition['name'], 'country': competition['country'], 'latitude': competition['venue']['coordinates']['latitude'], 'longitude': competition['venue']['coordinates']['longitude']}
            for data in [data_next_year, data_this_year]
            for competition in data['items']
            if not competition['isCanceled']
        ]
        return competitions
    except Exception as error: 
        raise(error)
    
async def get_old_competitions() -> list:
    with open('storage/old_competitions.json', 'r') as file:  
        return json.load(file)
    
async def update_old_competitions(competitions: list) -> None: 
    with open('storage/old_competitions.json', 'w') as file:
        json.dump(competitions, file)
    file.close()
        
async def compare_competitions(old: list, new: list) -> list: 
    result = [] 
    if old == new: 
        return result
    
    for competition in new: 
        if competition['id'] not in [old_competition['id'] for old_competition in old]: 
            result.append(competition)
    return result

async def dump_competitions(competitions: list) -> None: 
    with open('storage/competitions.json', 'w') as file:        
        json.dump(competitions, file)    
    file.close()
    
async def update_new_competitions(competitions: list) -> None: 
    with open('storage/new_competitions.json', 'r') as file:
        current_competitions = json.load(file)
    updated_competitions = competitions + current_competitions
    with open('storage/new_competitions.json', 'w') as file:
        json.dump(updated_competitions, file, indent = 4)
    file.close()
    
async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(CompetitionNotifer(bot))