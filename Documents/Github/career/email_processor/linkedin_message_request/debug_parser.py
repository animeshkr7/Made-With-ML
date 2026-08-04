import re, sys
from bs4 import BeautifulSoup

html = open('debug_people_search.html', 'r', encoding='utf-8').read()
soup = BeautifulSoup(html, 'html.parser')

cards = soup.select('div[componentkey]')
print(f"Found {len(cards)} cards")

for i, card in enumerate(cards[:3]):
    print(f"\nCard {i}:")
    links = card.find_all('a')
    for link in links:
        print(f"  Link text: '{link.text.strip()}' | href: {link.get('href', '')}")
    
    name_div = card.select_one('div.e31d23d7')
    if name_div:
        print(f"  Name: {name_div.text.strip()}")
