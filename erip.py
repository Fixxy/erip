import os, re, sys, urllib2, socket
from bs4 import BeautifulSoup

#get html from url
def returnHTML(url):
	hdr = {'Accept': 'text/html', 'User-Agent' : 'Fiddler'}
	req = urllib2.Request(url, headers=hdr)
	html = urllib2.urlopen(req).read()
	return html

#get html from url via proxy
def returnHTMLProxy(url, address):
	hdr = {'Accept': 'text/html', 'User-Agent' : 'Fiddler'}
	req = urllib2.Request(url, headers=hdr)
	proxy = urllib2.ProxyHandler({'https': address})
	opener = urllib2.build_opener(proxy)
	urllib2.install_opener(opener)
	html = urllib2.urlopen(req).read()
	return html

#get inner html from tag
def getTagData(html, tag, mode, classid):
	list = ''
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
	html = returnHTML('https://www.us-proxy.org/')
	table = getTagData(html, 'table', 0, 'proxylisttable')[0].tbody
	rows = table.find_all('tr')
	for row in rows:
		r = row.find_all('td')
		print('Checking: %s:%s' % (r[0].get_text(),r[1].get_text()))
		try:
			address = r[0].get_text() + ':' +  r[1].get_text()
			testHTML = returnHTMLProxy('https://example.org', address)
			print('found one!')
			file = open('proxy.txt','w')
			file.write('%s:%s' % (r[0].get_text(), r[1].get_text()))
			file.close()
			break
		except (urllib2.HTTPError, urllib2.URLError, socket.timeout) as e:
			print('this one doesn\'t work (%s)' % e)
	return address
	
#check if old one works, if not findProxy()
def proxySetup():
	file = open('proxy.txt','r')
	proxy = file.read()
	file.close()
	print('old proxy: %s' % proxy)
	
	try:
		testHTML = returnHTMLProxy('https://example.org', proxy)
		print('old proxy works')
	except:
		print('old proxy doesn\'t work, let\'s find a new one')
		proxy = findProxy()
	return proxy

proxy = proxySetup()
url = str(sys.argv[1])

# get title
html = returnHTMLProxy(url, proxy)
title = getTagData(html, 'h1', 0, 'gn')[0].get_text()
print('Title: %s' % title)

# find the first link to begin scrapping
divStart = getTagData(html, 'div', 1, 'gdtm')
linkStart = divStart[0].div.a['href']
print ('Beginning: %s' % linkStart)

# retrieve the total number of pages
html = returnHTMLProxy(linkStart, proxy)
countRaw = getTagData(html, 'div', 0, 'i2')[0].div.div.get_text()
countRegex = re.search('^\d+ \/(.*?)$', countRaw)
count = countRegex.group(1).strip()
print('Number of pages: %s' % count)

# save the first pic
imgRaw = getTagData(html, 'div', 0, 'i3')
imgUrl = imgRaw[0].a.img['src']

# create folder and save img
os.mkdir(title)
r = urllib2.urlopen(imgUrl)
downloadPic(r, '%s//%s.png' % (str(title),('%03d' % (1,))))

# go through all the pages
for i in range(2,int(count)+1):

	# next page url
	nextUrl = getTagData(html, 'a', 0, 'next')[0]
	html = returnHTMLProxy(nextUrl['href'], proxy)
	
	# current img
	imgRaw = getTagData(html, 'div', 0, 'i3')
	imgUrl = imgRaw[0].a.img['src']
	
	# save to folder
	r = urllib2.urlopen(imgUrl)
	downloadPic(r, '%s//%s.png' % (str(title),('%03d' % (i,))))
	
	print('%s/%s' % (i, count))
