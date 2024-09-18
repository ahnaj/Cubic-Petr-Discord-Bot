from PIL import ImageFont

# Colors
UCI_LIGHT_BLUE = (37, 87, 153)
UCI_GOLD = (254, 204, 7)
UCI_DARK_BLUE = (27, 61, 109)
UCI_DARKEST_BLUE = (0 ,34, 68)

# Events
EVENT_MAP = {
    '222': '2x2',
    '333': '3x3',
    '333bf': '3BLD',
    '333fm': 'FMC',
    '333mbf': 'MBLD',
    '333oh': 'OH',
    '444': '4x4',
    '444bf': '4BLD',
    '555': '5x5',
    '555bf': '5BLD',
    '666': '6x6',
    '777': '7x7',
    'clock': 'Clock',
    'minx': 'Megaminx',
    'pyram': 'Pyraminx',
    'skewb': 'Skewb',
    'sq1': 'Square-1'
}

REMOVED_EVENTS = ['333ft','magic','mmagic']

# Fonts
FONT = ImageFont.truetype('resources/DejaVuSansMono.ttf', 50)

# URLs
WCA_DEFAULT_AVATAR = 'https://www.worldcubeassociation.org/assets/missing_avatar_thumb-d77f478a307a91a9d4a083ad197012a391d5410f6dd26cb0b0e3118a5de71438.png'
WCA_LOGO = 'https://upload.wikimedia.org/wikipedia/en/e/ec/World_Cube_Association_Logo.png'