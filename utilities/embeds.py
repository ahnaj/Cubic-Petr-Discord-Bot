from datetime import datetime
import discord

from resources.constants import *

async def get_competitor_embed(info: dict) -> discord.Embed:
    embed_message = discord.Embed(title = info['name'], description = f"[{info['id']}]({info['url']})", color = discord.Color.from_rgb(*UCI_LIGHT_BLUE))
    embed_message.set_thumbnail(url = info['avatar'])
    embed_message.add_field(name = 'Region', value = info['region'], inline = False)
    embed_message.add_field(name = 'Medals', value = info['medals'], inline = True)
    embed_message.add_field(name = 'Records', value = info['records'], inline = True)
    embed_message.add_field(name = '', value = '', inline = False)
    embed_message.add_field(name = 'Competitions', value = info['number_of_competitions'], inline = True)
    embed_message.add_field(name = 'Championships', value = info['number_of_championships'], inline = True)
    embed_message.add_field(name = 'Completed Solves', value = info['solves'], inline = False)
    embed_message.set_footer(text = f"World Cube Association - {datetime.now().strftime('%B %#d, %Y')}", icon_url = WCA_LOGO)
    return embed_message

async def get_competition_embed(info: dict) -> discord.Embed:
    embed_message = discord.Embed(title = f"{info['status']} {info['name']}", description = f"[{info['id']}]({info['url']})", color = discord.Color.from_rgb(*UCI_LIGHT_BLUE))
    embed_message.set_thumbnail(url = info['sponsor'])
    embed_message.add_field(name = 'City', value = info['city'], inline = True)
    embed_message.add_field(name = 'Country', value = info['country'], inline = True)
    embed_message.add_field(name = 'Events', value = info['events'], inline = True)
    embed_message.add_field(name = '', value = '', inline = False)
    embed_message.add_field(name = 'Delegates', value = info['delegates'], inline = True)
    embed_message.add_field(name = 'Organizers', value = info['organizers'], inline = True)
    embed_message.add_field(name = '', value = '', inline = False)
    embed_message.add_field(name = 'Dates', value = info['dates'], inline = True)
    embed_message.add_field(name = 'Address', value = f"[{info['address']}]({info['location_url']})", inline = True)
    embed_message.add_field(name = 'Venue', value = info['venue'], inline = True)
    embed_message.add_field(name = '', value = '', inline = False)
    embed_message.add_field(name = 'Base Fee', value = info['registration_fee'], inline = True)
    embed_message.add_field(name = 'Competitor Limit', value = info['competitor_limit'], inline = True)
    embed_message.add_field(name = 'Registration Period', value = info['registration'], inline = False)
    embed_message.set_footer(text = f"World Cube Association - {datetime.now().strftime('%B %#d, %Y')}", icon_url = WCA_LOGO)
    return embed_message

async def get_competitions_notifications_embed(results: list) -> discord.Embed:
    embed_message = discord.Embed(title = 'Nearby WCA Competitions', description = '', color = discord.Color.from_rgb(*UCI_LIGHT_BLUE))
    embed_message.set_thumbnail(url = WCA_LOGO)
    body_text = '\n'.join([competition['name'] for competition in results])
    embed_message.add_field(name = '', value = body_text, inline = False)
    return embed_message

async def get_hq_embed(interaction: discord.Interaction, info: tuple) -> discord.Embed: 
    hq, latitude, longitude, radius, competitions_channel_id, deals_channel_id = info
    embed_message = discord.Embed(title = f"{interaction.guild.name}'s HQ", description = '', color = discord.Color.from_rgb(*UCI_GOLD))
    embed_message.set_thumbnail(url = interaction.guild.icon)
    embed_message.add_field(name = 'Address', value = hq, inline = False) 
    embed_message.add_field(name = 'Coordinates', value = f'{latitude}, {longitude}', inline = True) 
    embed_message.add_field(name = 'Scanning Radius', value = 'None' if radius is None else f'{radius} km', inline = True)
    embed_message.add_field(name = 'Notification Channels', value = f"**WCA Competitions:** <#{competitions_channel_id}>", inline = False) 
    # embed_message.add_field(name = 'Notification Channels', value = f"**Online Deals/Sales:** <#{deals_channel_id}>")
    return embed_message
    
async def get_results_embed(info: dict) -> discord.Embed: 
    embed_message = discord.Embed(title = '', description = '', color = discord.Color.from_rgb(*UCI_GOLD))
    return embed_message