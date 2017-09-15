import argparse, os, re, sys, socket, urllib, urllib.request, urllib.error
from bs4 import BeautifulSoup

hdr = {'Accept': 'text/html', 'User-Agent' : 'Fiddler'}
website = 'http://example.com'
htmlTemp = begin = None

#get html / via proxy
def returnHTML(url, en_proxy, address):
	if (en_proxy == 0) :
		proxy = urllib.request.ProxyHandler({})
		timeout=120
	else:
		proxy = urllib.request.ProxyHandler({'https': address})
		timeout=20
	opener = urllib.request.build_opener(proxy)
	urllib.request.install_opener(opener)
	req = urllib.request.Request(url, headers=hdr)
	html = urllib.request.urlopen(req, timeout=timeout).read()
	return html

#get inner html from tag
def getTagData(html, tag, mode, classid):
	list = None
	if mode == 0: #id
		soup = BeautifulSoup(html, 'html.parser')
		list = soup.find_all(tag, id=classid)
	elif mode == 1: #class
		soup = BeautifulSoup(html, 'html.parser')
		list = soup.find_all(tag, class_=classid)
	else: #nothing
		soup = BeautifulSoup(html, 'html.parser')
		list = soup.find_all(tag)
	return list
	
def downloadPic(r, path):
	with open(path, 'wb') as f:
		while True:
			chunk = r.read(1024)
			if not chunk:
				break
			f.write(chunk)
	return
	
def findProxy():
	html = returnHTML('https://www.us-proxy.org/', 0, '')
	table = getTagData(html, 'table', 0, 'proxylisttable')[0].tbody
	rows = table.find_all('tr')
	for row in rows:
		r = row.find_all('td')
		print('Checking: %s:%s' % (r[0].get_text(),r[1].get_text()))
		try:
			address = r[0].get_text() + ':' +  r[1].get_text()
			testHTML = returnHTML(website, 1, address)
			print('found one!')
			file = open('proxy.txt','w')
			file.write('%s:%s' % (r[0].get_text(), r[1].get_text()))
			file.close()
			break
		except (urllib.error.URLError, socket.timeout, TimeoutError) as e:
			print('this one doesn\'t work (%s)' % e)
	return address
	
#check if old one works, if not findProxy()
def proxySetup():
	file = open('proxy.txt','r')
	proxy = file.read()
	file.close()
	print('old proxy: %s' % proxy)
	
	try:
		testHTML = returnHTML(website, 1, proxy)
		print('old proxy works')
	except:
		print('old proxy doesn\'t work, let\'s find a new one')
		proxy = findProxy()
	return proxy

url = str(sys.argv[1])
start = str(sys.argv[2])

# find a suitable proxy
proxy = proxySetup()

# get title
html = returnHTML(url, 1, proxy)
title = getTagData(html, 'h1', 0, 'gn')[0].get_text()
print('Title: %s' % title)

# find the first link to begin scrapping
divStart = getTagData(html, 'div', 1, 'gdtm')
linkStart = divStart[0].div.a['href']
print ('Beginning: %s' % linkStart)

# retrieve the total number of pages
html = returnHTML(linkStart, 1, proxy)
countRaw = getTagData(html, 'div', 0, 'i2')[0].div.div.get_text()
countRegex = re.search('^\d+ \/(.*?)$', countRaw)
count = countRegex.group(1).strip()
print('Number of pages: %s' % count)

# save the first pic
imgRaw = getTagData(html, 'div', 0, 'i3')
imgUrl = imgRaw[0].a.img['src']

# create folder and save the first img
try:
	os.mkdir(title)
except FileExistsError as err:
	print('Folder already exists')

r = urllib.request.urlopen(imgUrl)
downloadPic(r, '%s//%s.png' % (str(title),('%03d' % (1,))))

# skip if start var is > 0
htmlTemp = html
print('Skipping...')
for j in range(2, int(start)):
	nextUrlTemp = getTagData(htmlTemp, 'a', 0, 'next')[0]
	htmlTemp = returnHTML(nextUrlTemp['href'], 1, proxy)
	#print('Skipping... %s [%s]' % (j,nextUrlTemp['href'])) #debug
html = htmlTemp

if int(start) > 0:
	begin = int(start)
else:
	begin = 2

# go through all the pages 
for i in range(begin, int(count) + 1):
	
	# next page url
	nextUrl = getTagData(html, 'a', 0, 'next')[0]
	html = returnHTML(nextUrl['href'], 1, proxy)
	
	# current img
	imgRaw = getTagData(html, 'div', 0, 'i3')
	imgUrl = imgRaw[0].a.img['src']
	
	# save to folder
	r = urllib.request.urlopen(imgUrl)
	downloadPic(r, '%s//%s.png' % (str(title),('%03d' % (i,))))
	
	print('%s/%s' % (i, count))
