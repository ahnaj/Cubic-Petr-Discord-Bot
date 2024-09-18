import aiohttp
from bs4 import BeautifulSoup

async def request(url: str) -> str:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.text() if response.status == 200 else None

async def scrape_text(tag_name: str, class_name: str, href_name: str, response: str) -> str:
    scraper = BeautifulSoup(response, 'html.parser')
    tag = scraper.find(tag_name, attrs = {'class': class_name, 'href': href_name})
    return None if tag is None else tag.get_text(strip = True)

async def get_competitor_id_from_query(query: str) -> str: 
    wca_response = await request(f'https://www.worldcubeassociation.org/search?q={query}#people')
    return await scrape_text('span', 'wca-id', '', wca_response)

async def get_competition_id_from_query(query: str) -> str: 
    wca_response = await request(f'https://www.worldcubeassociation.org/search?q={query}#competition')
    scraper = BeautifulSoup(wca_response, 'html.parser') 
    table = scraper.find('table', attrs = {'class': 'table table-nonfluid'})
    anchor = table.find('a', href = lambda href: href and href.startswith('/competitions/'))
    id = anchor['href'].removeprefix('/competitions/')
    return id if anchor else None