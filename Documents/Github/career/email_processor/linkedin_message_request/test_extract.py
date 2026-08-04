from bs4 import BeautifulSoup

html=open('test_search_results.html', encoding='utf-8').read()
soup=BeautifulSoup(html, 'html.parser')
cards=soup.select('[role="listitem"]')

for card in cards:
    img = card.select_one('img[alt]')
    a = card.select_one('a[href*="/in/"]')
    name = img['alt'] if img else 'Unknown'
    href = a['href'] if a else 'Unknown'
    if href and "?" in href:
        href = href.split("?")[0]
    print(f"Name: {name.split()[0] if name != 'Unknown' else 'Unknown'}, URL: {href}")
