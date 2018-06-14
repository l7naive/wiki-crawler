import bs4
import re
import requests
import sqlite3

def start():
	init_db()
	urls = generate_urls()
	for url in urls:
		fetch_data(url)


def fetch_data(url):
	print(url)
	# fuck GFW
	proxies = {'http': 'http://127.0.0.1:911', 'https':'http://127.0.0.1:911'}
	resp = requests.get(url, proxies=proxies)

	resp.raise_for_status()
	
	match = re.match(r'https://zh.wikipedia.org/wiki/(\d+)月(\d+)日', url)
	month = match.group(1)
	day = match.group(2)
	
	conn = sqlite3.connect('wiki.db')
	curor = conn.cursor()
	
	html = bs4.BeautifulSoup(resp.text, 'lxml')
	content_div = html.find('div', class_='mw-parser-output')

	sections = content_div.find_all('h2', recursive=False) 
	
	items = []

	for i in range(4):
		type = get_type(i)

		start = sections[i]
		next_element = start.next_sibling

		while True:
			if next_element.name == 'ul':
				if i == 3:
					lis = next_element.find_all('li')
					for li in lis:
						items.append((None, None, month, day, li.get_text(), type))
				else:
					lis = next_element.find_all('li')
					for li in lis:
						text = li.get_text()
						arr = text.split("：")
						if len(arr) == 2:
							items.append((None, get_year(arr[0]), month, day, arr[1], type))

			next_element = next_element.next_sibling

			if next_element.name == 'h2':
				break	

	curor.executemany('INSERT INTO items(id, year, month, day, content, type) VALUES (?, ?, ?, ?, ?, ?)', items)
			
	conn.commit()
	curor.close()
	conn.close()

def get_type(index):
	if index == 0:
		return 'event'
	elif index == 1:
		return 'birth'
	elif index == 2:
		return 'death'
	elif index == 3:
		return 'holiday'
	else:
		return ''

def get_year(str):
	year = int(re.sub('\D', '', str))
	if '前' in str:
		return -year
	else:
		return year


def generate_urls():
	urls = []
	url_template = 'https://zh.wikipedia.org/wiki/%d月%d日'
	for i in range(12):
		for j in range(31):
			month = i + 1
			day = j + 1
			if month == 2 and day > 29:
				break
			if month in [4, 6, 9, 11] and day > 30:
				break
			urls.append(url_template % (month, day))
	return urls


def init_db():
	conn = sqlite3.connect('wiki.db')
	curor = conn.cursor()
	curor.execute('''CREATE TABLE items(
		id INTEGER PRIMARY KEY,
		year INTEGER,
		month INTEGER,
		day INTEGER,
		content TEXT,
		type CHAR(10)
		)''')
	conn.commit()
	curor.close()
	conn.close()

if __name__ == '__main__':
	start()
