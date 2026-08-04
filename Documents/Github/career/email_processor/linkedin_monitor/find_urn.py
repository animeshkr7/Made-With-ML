import re
with open('debug_html.html', 'r', encoding='utf-8') as f:
    html = f.read()
urns = re.findall(r'urn:li:activity:\d+', html)
print("URNs:", set(urns))

urn_attrs = re.findall(r'data-urn="([^"]+)"', html)
print("data-urn attributes:", set(urn_attrs))
