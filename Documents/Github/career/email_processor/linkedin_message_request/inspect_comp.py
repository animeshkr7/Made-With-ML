from bs4 import BeautifulSoup
html = open('test_company_results.html', encoding='utf-8').read()
soup = BeautifulSoup(html, 'html.parser')
link = soup.select_one('a[href*="/company/"]')
if link:
    print(link.prettify()[:500])
else:
    print("Not found")
