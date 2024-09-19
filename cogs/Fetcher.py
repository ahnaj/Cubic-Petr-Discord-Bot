import asyncio
from bs4 import BeautifulSoup
from datetime import datetime
import discord
from discord import app_commands
from discord.ext import commands
import io
import json
import logging
from PIL import Image, ImageDraw
import re
from table2ascii import table2ascii, PresetStyle

from resources.constants import *
from utilities.embeds import * 
from utilities.query import *

class Fetcher(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        print('The cog Fetcher.py is online!')
        
    @app_commands.command(name = 'competition', description = 'I fetch information about a WCA competition.')
    async def competition(self, interaction: discord.Interaction, query: str) -> None:
        try: 
            await interaction.response.defer()
            embed_message = await get_competition_embed(
                await fetch_competition_by_query(query)
            )
            await interaction.followup.send(embed = embed_message)
        except Exception as error: 
            logging.error(f'An error occurred: {error}')
            await interaction.followup.send(f'**{query}** is not a valid WCA competition.', ephemeral = True)
            
    @app_commands.command(name = 'info', description = 'I fetch information about a WCA competitor.')
    async def info(self, interaction: discord.Interaction, query: str) -> None:
        try: 
            await interaction.response.defer()
            embed_message = await get_competitor_embed(
                await fetch_competitor_by_query(query)
            )
            await interaction.followup.send(embed = embed_message)
        except Exception as error: 
            logging.error(f'An error occurred: {error}')
            await interaction.followup.send(f'**{query}** is not a valid WCA competitor.', ephemeral = True)

    @app_commands.command(name = 'pr', description = 'I fetch the current personal records of a WCA competitor.')
    async def pr(self, interaction: discord.Interaction, query: str) -> None: 
        try: 
            await interaction.response.defer()
        
            info = await fetch_competitor_by_query(query)
            
            id, name = info['id'], info['name']
            titles = ['Event', 'NR', 'CR', 'WR', 'Single', 'Average', 'WR', 'CR', 'NR']
            rows = []
            singles = info['singles']
            averages = {avg['eventId']: avg for avg in info['averages']}
            for event in singles:
                event_id = event['eventId']
                if event_id in REMOVED_EVENTS: continue
                match event_id: 
                    case '333mbf': single_best = info['mbld']
                    case _: single_best = event['best'] if event_id == '333fm' else await format_solve_time(event['best'])
                        
                single_ranks = event['rank']
                current_avg = averages.get(event_id, {})
                avg_best = '-' if current_avg.get('best', None) is None else await format_solve_time(current_avg['best'])
                avg_ranks = current_avg.get('rank', {})

                rows.append([
                    EVENT_MAP[event_id],               
                    single_ranks.get('country', '-'),   
                    single_ranks.get('continent', '-'),
                    single_ranks.get('world', '-'),     
                    single_best,                       
                    avg_best,       
                    avg_ranks.get('world', '-'),                      
                    avg_ranks.get('continent', '-'),           
                    avg_ranks.get('country', '-')
                ])
            output = f'{table2ascii(header = titles, body = rows, style = PresetStyle.thin_compact_rounded)}'
            buffer = await string_to_img(output)
            hyperlink = f'[{name}](https://www.worldcubeassociation.org/persons/{id})'
            await interaction.followup.send(f"**Current Personal Records for {hyperlink}**", file = discord.File(fp = buffer, filename = f"pr-{name}.png"))
        except Exception as error: 
            logging.error(f'An error occurred: {error}')
            await interaction.followup.send(f'**{query}** is not a valid WCA competitor.', ephemeral = True)

async def fetch_competitor_by_id(id: str) -> dict: 
    wca_url = f'https://www.worldcubeassociation.org/persons/{id}'
    api_url = f'https://raw.githubusercontent.com/robiningelbrecht/wca-rest-api/master/api/persons/{id}.json'
  
    wca_response, api_response = await asyncio.gather(
        request(wca_url), 
        request(api_url)
    )
    data = json.loads(api_response)
    medals, records = await asyncio.gather(
        fetch_medals(data['medals']),
        fetch_records(data['records'])
    )
    championships = data['numberOfChampionships']
    scraper = BeautifulSoup(wca_response, 'html.parser')
    table = scraper.find('table')
    completed_solves = table.find_all('td')[-1].get_text(strip = True) 
    avatar = scraper.find('img', class_ = 'avatar')
    return {
        'avatar': avatar['src'] if avatar else WCA_DEFAULT_AVATAR,
        'averages': data['rank']['averages'],
        'id': id,
        'medals': medals,
        'mbld': await scrape_text('a', 'plain', '/results/rankings/333mbf/single', wca_response), 
        'name': data['name'],
        'number_of_championships': 'None' if championships == 0 else championships,
        'number_of_competitions': data['numberOfCompetitions'],
        'records': records,
        'region': data['country'],
        'response': wca_response,
        'singles': data['rank']['singles'],
        'solves': completed_solves,
        'url': wca_url
    } 
    
async def get_competition_status(cancelled: bool, registration_open: datetime.date, registration_close: datetime.date, start_date: datetime.date, end_date: datetime.date, limit_reached: str) -> str:
    today = datetime.now() 
    if cancelled:
        return '**CANCELLED**'
    if today > end_date:
        return ':red_circle:'
    if start_date <= today <= end_date:
        return '**ONGOING**'
    if today < registration_open:
        return '**UPCOMING**'
    if limit_reached or registration_close < today < start_date:
        return ':yellow_circle:'
    return ':green_circle:'
    
async def fetch_competition_by_id(id: str) -> dict: 
    wca_api_v0_url= f'https://www.worldcubeassociation.org/api/v0/competitions/{id}'
    wca_register_url = f'https://www.worldcubeassociation.org/competitions/{id}/register'
    
    wca_api_v0_response, wca_register_response = await asyncio.gather(
        request(wca_api_v0_url),
        request(wca_register_url)
    )
    
    if wca_api_v0_response is None or wca_register_response is None: 
        return
    
    data = json.loads(wca_api_v0_response)
    
    scraper = BeautifulSoup(wca_register_response, 'html.parser')
    registration_fee = scraper.find(text = lambda words : 'The base registration fee for this competition' in words)
    competitor_limit = scraper.find(text = lambda words : 'There is a competitor limit of' in words)
    limit_reached = scraper.find(text = lambda words: 'it has already been reached.' in words)
    
    start_date = datetime.strptime(data['start_date'], '%Y-%m-%d')
    end_date = datetime.strptime(data['end_date'], '%Y-%m-%d')
    
    latitude = data.get('latitude_degrees', 0)
    longitude = data.get('longitude_degrees', 0)
    
    sponsor_logo = re.findall(r'(?<!#!)\[.*?\]\((https://.*?\.png)\)', data.get('information', 'NO INFORMATION'))
    
    registration_open = None if data['registration_open'] is None else datetime.strptime(data['registration_open'], '%Y-%m-%dT%H:%M:%S.%fZ')
    registration_close = None if data['registration_open'] is None else datetime.strptime(data['registration_close'], '%Y-%m-%dT%H:%M:%S.%fZ')
    registration_period = 'N/A' if registration_open is None or registration_close is None else f"From {registration_open.strftime('%B %#d, %Y')} to {registration_close.strftime('%B %#d, %Y')}."
    
    return { 
        'address': data.get('venue_address', 'N/A'),
        'competitor_limit': competitor_limit,
        'status': await get_competition_status(data['cancelled_at'] is not None, registration_open, registration_close, start_date, end_date, limit_reached),
        'city': data.get('city', 'N/A'),
        'country': data.get('country_iso2', 'N/A'),
        'dates': start_date.strftime('%B %#d, %Y') if start_date == end_date else f"{start_date.strftime('%B %#d, %Y')} to {end_date.strftime('%B %#d, %Y')}",
        'delegates': ', '.join(delegate['name'] for delegate in data['delegates']),
        'events': ', '.join(EVENT_MAP[event] for event in data['event_ids'] if not event in REMOVED_EVENTS),
        'registration_fee': registration_fee, 
        'location_url': f'https://www.google.com/maps/place/{latitude},{longitude}',
        'id': id,
        'name': data.get('name', 'N/A'), 
        'organizers': ', '.join(organizer['name'] for organizer in data['organizers']),
        'registration': registration_period,
        'sponsor': WCA_LOGO if len(sponsor_logo) == 0 else sponsor_logo[0],
        'url': f'https://www.worldcubeassociation.org/competitions/{id}',
        'venue': data.get('venue', 'N/A')
    }

async def fetch_results(ctx: discord.ext.commands.Context, competition_name: str, competitor_name: str) -> dict: 
    competition_id = await get_competition_id_from_query(competition_name)
    competitor_id = await get_competitor_id_from_query(competitor_name)
    if competition_id is None or competitor_id is None: return await ctx.send(f'Either {competition_name} or {competitor_name} is invalid.')
    api_response = await request(f'https://raw.githubusercontent.com/robiningelbrecht/wca-rest-api/master/api/results/{competition_id}.json')
    data = json.loads(api_response)
    
async def fetch_competitor_by_query(query: str) -> dict:
    id = await get_competitor_id_from_query(query)
    return await fetch_competitor_by_id(id) 

async def fetch_competition_by_query(query: str) -> dict: 
    id = await get_competition_id_from_query(query)
    return await fetch_competition_by_id(id) 

async def fetch_medals(info: dict) -> str:
    num_gold = info['gold']
    num_silver = info['silver']
    num_bronze = info['bronze'] 
    return 'None' if num_gold + num_silver + num_bronze == 0 else f':first_place: Gold: {num_gold} \n :second_place: Silver: {num_silver} \n :third_place: Bronze: {num_bronze}'

async def fetch_records(info: dict) -> str:
    singles = info['single']
    averages = info['average']
    singles = {} if isinstance(singles, list) else singles
    averages = {} if isinstance(averages, list) else averages
    num_wr = singles.get('WR', 0) + averages.get('WR', 0)
    num_cr = singles.get('CR', 0) + averages.get('CR', 0)
    num_nr = singles.get('NR', 0) + averages.get('NR', 0)
    return 'None' if num_wr + num_cr + num_nr == 0 else f'WR: {num_wr} \nCR: {num_cr} \nNR: {num_nr}'

async def format_solve_time(centiseconds: int) -> str:
    if centiseconds == -1: return 'DNF'
    minutes = centiseconds // 6000
    seconds = (centiseconds % 6000) / 100
    return f'{minutes}:{seconds:05.2f}' if minutes > 0 else f'{seconds:.2f}'

async def string_to_img(input: str) -> io.BytesIO: 
    text_width, text_height = ImageDraw.Draw(Image.new('RGB', (1, 1))).textsize(input, font = FONT)
    bg_color = UCI_DARKEST_BLUE
    padding = 10
    image = Image.new('RGB', (text_width + 2 * padding, text_height + 2 * padding), bg_color)
    draw = ImageDraw.Draw(image)
    draw.text((padding, padding), input, fill = UCI_GOLD, font = FONT)
    buffer = io.BytesIO()
    image.save(buffer, format = 'PNG')
    buffer.seek(0)
    return buffer

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Fetcher(bot), guilds = [discord.Object(id=1259875466936975460)])
