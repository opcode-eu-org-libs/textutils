#!/usr/bin/python3

# create miror of links to mediawiki pages using api.php
# add links from page to database for recursive mirroring


# Copyright (c) 2015-2017 Robert Ryszard Paciorek <rrp@opcode.eu.org>
# 
# MIT License
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


import sys, os, re, time

from http.client    import HTTPSConnection
from urllib.parse   import quote, unquote
from urllib.request import urlretrieve
import json
import sqlite3

dbConn = None
httpHeaders = {'User-Agent':'MediawikiMirrorBot'}

def doQuery(propFull, propShort, pageID, title, conn,  extraInfo = None, baseSubProp = None, subProps = None):
	queryStr = '/w/api.php?action=query&continue&format=json&titles=' + quote(title)
	if subProps != None:
		queryStr += '&' + propShort + 'prop=' + subProps
	queryStr += '&prop=' + propFull + '&' + propShort + 'limit=100'
	
	contTxt = ''
	contFlag = True
	retInfoBase = []
	retInfoExtra = None
	while contFlag:
		conn.request('GET', queryStr + contTxt, headers=httpHeaders)
		res = conn.getresponse()
		if res.status != 200:
			raise IOError('GET HTTP code: ' + res.status + res.reason + ' for ' + propFull + ' request: ' + queryStr)
		data = json.loads(res.read().decode())
		
		if pageID == None:
			tmp = list(data['query']['pages'].keys())
			if len(tmp) != 1:
				raise ValueError('Multiple pages in reply for: ' + queryStr)
			else:
				pageID = tmp[0]
		
		if data['query']['pages'][pageID]['title'] != title:
			raise ValueError('Invalid title in reply for: ' + queryStr)
		if 'continue' in data:
			contTxt = '&' + propShort + 'continue=' + quote(data['continue'][propShort + 'continue'])
		else:
			contFlag = False
		
		if propFull in data['query']['pages'][pageID]:
			if baseSubProp == None:
				retInfoBase += data['query']['pages'][pageID][propFull]
			else:
				for tmp in data['query']['pages'][pageID][propFull]:
					retInfoBase += [ tmp[baseSubProp] ]
		if (not contFlag) and extraInfo != None and extraInfo in data['query']['pages'][pageID]:
			retInfoExtra  = data['query']['pages'][pageID][extraInfo]
	
	return {'base': retInfoBase, 'extra': retInfoExtra}


def getDstDir(title, create=False):
	dstDir = ''
	for d in title.split('/'):
		dstDir += d + '/'
		if not os.path.isdir(dstDir):
			if create:
				os.mkdir(dstDir)
			else:
				return None
	return dstDir


def getArticle(title, site, getLinks=True, save=True, forceRefresh=False):
	saveDir = getDstDir(site + '/' + title)
	if saveDir != None and not forceRefresh:
		return { 'meta': {'site': site, 'title': title}, 'dir': saveDir, 'status': ['done'] }
	
	conn     = HTTPSConnection(site)
	
	# get page ID and page text
	queryStr = '/w/api.php?action=query&continue&format=json&titles=' + quote(title) \
		     + '&prop=revisions&rvprop=content&rvlimit=1&redirects=1'
	conn.request('GET', queryStr, headers=httpHeaders)
	res = conn.getresponse()
	if res.status != 200:
		raise IOError('GET HTTP code: ' + res.status + res.reason + ' for revisions request: ' + queryStr)
	data = json.loads(res.read().decode())
	
	if '-1' in data['query']['pages'] and 'missing' in data['query']['pages']['-1']:
		raise ValueError('Page Missing')
	
	txt    = ''
	pageID = 0
	status  = []
	for pID in data['query']['pages']:
		if data['query']['pages'][pID]['revisions'][0]['contentformat'] != 'text/x-wiki' and \
		   data['query']['pages'][pID]['revisions'][0]['contentformat'] != 'text/plain':
				raise ValueError('Invalid contentformat in reply for: ' + queryStr)
		if data['query']['pages'][pID]['revisions'][0]['contentmodel'] != 'wikitext' and \
		   data['query']['pages'][pID]['revisions'][0]['contentmodel'] != 'Scribunto':
				raise ValueError('Invalid contentmodel in reply for: ' + queryStr)
		if txt != '':
			raise ValueError('More one page in reply for: ' + queryStr)
		if data['query']['pages'][pID]['title'] != title:
			oldTitle = title
			if 'normalized' in data['query'] and \
			    data['query']['normalized'][0]['to'] == data['query']['pages'][pID]['title']:
					title = data['query']['normalized'][0]['to']
					status += ['normalized']
			if 'redirects' in data['query'] and \
			    data['query']['redirects'][0]['to'] == data['query']['pages'][pID]['title']:
					title = data['query']['redirects'][0]['to']
					status += ['redirect']
			
			if 'normalized' in data['query'] and data['query']['normalized'][0]['from'] != oldTitle and \
			   'redirects' in data['query'] and data['query']['redirects'][0]['from'] != oldTitle:
					status = []
			
			if status != []:
				saveDir = getDstDir(site + '/' + title)
				if saveDir != None and not forceRefresh:
					return { 'meta': {'site': site, 'title': title}, 'dir': saveDir, 'status': status + ['done'] }
			else:
				raise ValueError('Invalid title in reply for: ' + queryStr)
		
		txt = data['query']['pages'][pID]['revisions'][0]['*']
		pageID = pID
	
	# get page authors
	res = doQuery('contributors', 'pc', pageID, title, conn,  extraInfo='anoncontributors')
	contributors = {'users': res['base'], 'anonymous': res['extra']}
	
	# get redirect to this article
	res = doQuery('redirects', 'rd', pageID, title, conn,  baseSubProp='title')
	redirects = res['base']
	
	if getLinks:
		# get page level links (images, templates)
		res = doQuery('images', 'im', pageID, title, conn,  baseSubProp='title')
		images = res['base']
		
		res = doQuery('templates', 'tl', pageID, title, conn,  baseSubProp='title')
		templates = res['base']
		
		# get page sub level links (links, interwiki, ...)
		res = doQuery('links', 'pl', pageID, title, conn,  baseSubProp='title')
		links = res['base']
		
		res = doQuery('iwlinks', 'iw', pageID, title, conn)
		for tmp in res['base']:
			links += [ tmp['prefix'] + ':' + tmp['*'] ]
		
		res = doQuery('langlinks', 'll', pageID, title, conn)
		for tmp in res['base']:
			if tmp['lang'] == 'en' or tmp['lang'] == 'pl':
				links += [ tmp['lang'] + ':' + tmp['*'] ]
	else:
		images = None
		templates = None
		links = None
	
	# save meta, links and data(text)
	if save:
		saveDir = getDstDir(site + '/' + title, create=True)
		
		infoFile = open(saveDir + '/info.txt', 'w')
		infoFile.write(json.dumps(
			{'site': site, 'title': title, 'pageID': pageID, 'contributors': contributors, \
			 'images': images, 'templates': templates, 'links': links},
			indent=1,
			ensure_ascii=False)
		)
		infoFile.close()
		
		infoFile = open(saveDir + '/data.txt', 'w')
		infoFile.write(txt)
		infoFile.close()
	else:
		saveDir = None
	
	conn.close()
	return { 'meta': {'site': site, 'title': title, 'pageID': pageID, 'contributors': contributors}, \
	         'txt': txt, 'dir': saveDir, 'redirects': redirects, 'status': status, \
	         'images': images, 'templates': templates, 'links': links }


def getImage(title, site, save=True):
	conn     = HTTPSConnection(site)
	
	res = doQuery('imageinfo', 'ii', None, title, conn,  subProps='user|userid|url|comment')
	
	# save meta and data (download image file)
	if save:
		dstDir = getDstDir(site + '/' + title, create=True)
		infoFile = open(dstDir + '/info.txt', 'w')
		infoFile.write(json.dumps(res['base'], indent=1, ensure_ascii=False))
		infoFile.close()
		
		urlretrieve( res['base'][0]['descriptionurl'], dstDir + '/info.html' )
		urlretrieve( res['base'][0]['url'], dstDir + '/data.' + res['base'][0]['url'].rsplit('.', 1)[1] )
	                                           # '/' + re.sub(' ', '_', unquote(res['base'][0]['url'].rsplit('/', 1)[1]))
	conn.close()
	return {'dir': dstDir, 'title': title, 'site': site, 'info': res['base']}


def parseLink(link, base = None, level = 0, site = None):
	if site != None:
		ss = site.split('.', 3)
		lang=ss[0]
		project=ss[1]
	else:
		lang='pl'
		project='wikipedia'
	
	langs={'pl', 'en', 'de', 'es', 'fr', 'it'}
	projects={ 'w':'wikipedia', 'b':'wikibooks', 'c':'commons.wikimedia', 'wikt':'wiktionary', 's':'wikisource', \
	           'q':'wikiquote', 'species':'wikispecies', 'voy':'wikivoyage', 'v':'wikiversity', \
	           'wikipedia':'wikipedia', 'wikibooks':'wikibooks', 'commons':'commons.wikimedia', \
	           'wiktionary':'wiktionary', 'wikisource':'wikisource', 'wikiquote':'wikiquote', \
	           'wikispecies':'wikispecies', 'wikivoyage':'wikivoyage', 'wikiversity':'wikiversity' }
	title=''
	
	ls = link.split('#', 2)[0].split(':', 3)
	titleStartAt = 2
	
	for i in range(0, len(ls)-1):
		tmp = ls[i]
		if tmp in langs:
			lang = tmp
		elif tmp in projects:
			project=projects[tmp]
		else:
			titleStartAt = i
			break
	
	for i in range(titleStartAt, len(ls)-1):
		title += ls[i] + ':'
	title += ls[len(ls)-1]
	
	newLevel = level + 10
	if base != None and title.startswith(base):
		subtitle = title.replace(base, '', 1)
		if subtitle.startswith("#"):
			return None
		elif subtitle.startswith("/") or subtitle.startswith(":"):
			newLevel = level + 1
	
	return { 'site': lang + '.' + project + '.org', 'title': title, 'level': newLevel }




def saveFullArticle(site, title, level, verify, cnt):
	aInfo = getArticle(title, site)
	
	if not os.path.isfile(aInfo['dir'] + '/info.txt'):
		aInfo = getArticle(title, site, forceRefresh=True)
	
	if not 'done' in aInfo['status']:
		# mirror all images from article
		for tmp in aInfo['images']:
			res = chechInDatabase(aInfo['meta']['site'], tmp, level, 0)
			if res['status'] != 'done':
				tmpInfo = getImage(tmp, aInfo['meta']['site'])
				addToDatabase(tmpInfo['site'], tmpInfo['title'], tmpInfo['dir'], res['level'], res['verify'], res['cnt'] + 1)
		
		# mirror all templates from article
		for tmp in aInfo['templates']:
			res = chechInDatabase(aInfo['meta']['site'], tmp, level, 0)
			if res['status'] != 'done':
				try:
					tmpInfo = getArticle(tmp, aInfo['meta']['site'], getLinks=False)
					addToDatabase(tmpInfo['meta']['site'], tmpInfo['meta']['title'], tmpInfo['dir'], res['level'], res['verify'], res['cnt'] + 1)
				except ValueError as e:
					print("\n[" + tmp + "] ERROR:", e)
	else:
		infoFile = open(aInfo['dir'] + '/info.txt', 'r')
		data = json.load(infoFile)
		aInfo['links'] = data['links']
	
	# add all links from article to mirroring queue
	for tmp in aInfo['links']:
		tmpInfo = parseLink(tmp, title, level, site)
		if tmpInfo == None:
			continue
		
		res = chechInDatabase(tmpInfo['site'], tmpInfo['title'], tmpInfo['level'], 0)
		if res['status'] != 'done':
			addToDatabase(tmpInfo['site'], tmpInfo['title'], None, res['level'], res['verify'], res['cnt'] + 1)
		else:
			if tmpInfo['level'] < res['level']:
				addToDatabase(tmpInfo['site'], tmpInfo['title'], None, tmpInfo['level'], res['verify'], res['cnt'] + 1)
	
	# update database:
	dbCursor = dbConn.cursor()
	#  - when change title delete old entry
	if title != aInfo['meta']['title']:
		dbCursor.execute("INSERT INTO normalized VALUES (?, ?, ?)", (title, aInfo['meta']['title'], aInfo['meta']['site']))
		dbCursor.execute("DELETE FROM pages WHERE site=? AND title=?", (site, title))
	#  - add article and all redirects to him to database
	dbCursor.execute("INSERT INTO pages VALUES (?, ?, ?, ?, ?, ?)", (aInfo['meta']['site'], aInfo['meta']['title'], aInfo['dir'], level, verify, cnt))
	if 'redirects' in aInfo:
		for rt in aInfo['redirects']:
			dbCursor.execute("INSERT INTO pages VALUES (?, ?, ?, ?, ?, ?)", (aInfo['meta']['site'], rt, aInfo['dir'], level, 2, cnt))
	dbConn.commit()




def connecteDatabase():
	global dbConn
	dbConn=sqlite3.connect('wikiPages.db')


def chechInDatabase(site, title, level = 999, verify = 0):
	dbCursor = dbConn.cursor()
	dbCursor.execute("SELECT path, level, verify, cnt FROM pages WHERE site = ? AND title = ?", (site, title))
	res = dbCursor.fetchone();
	if res is None:
		# not in mirroring queue
		return { 'status': 'new', 'level': level, 'verify': verify, 'cnt': 0 }
	elif res[0] is None:
		# in mirroring queue or mirrored
		if level > res[1]:
			level = res[1]
		return { 'status': 'waiting', 'level': level, 'verify': res[2], 'cnt': res[3] }
	else:
		# mirroring is done
		return { 'status': 'done', 'level': res[1], 'verify': res[2], 'cnt': res[3] }


def addToDatabase(site, title, directory, level, verify, cnt):
	dbCursor = dbConn.cursor()
	dbCursor.execute("INSERT INTO pages VALUES (?, ?, ?, ?, ?, ?)", (site, title, directory, level, verify, cnt))
	dbConn.commit()


def createDatabase():
	global dbConn
	
	if os.path.isfile("wikiPages.db"):
		if not dbConn is None:
			dbConn.close()
		os.rename("wikiPages.db", "wikiPages.db.old")
	
	dbConn=sqlite3.connect('wikiPages.db')
	dbCursor = dbConn.cursor()
	dbCursor.execute("CREATE TABLE pages (site TEXT, title TEXT, path TEXT, level INT, verify INT DEFAULT 0, cnt INT DEFAULT 0, PRIMARY KEY (site, title) ON CONFLICT REPLACE)")
	dbCursor.execute("CREATE TABLE normalized (oldTitle TEXT, newTitle TEXT, site TEXT)")
	dbConn.commit()


def loadLinksToDatabase():
	dbCursor = dbConn.cursor()
	
	f = open('entry_points-ignore.txt', 'r')
	for line in f:
		line = line.strip()
		if line != '':
			tmpInfo = parseLink(line)
			dbCursor.execute("SELECT * FROM pages WHERE site = ? AND title = ?", (tmpInfo['site'], tmpInfo['title']))
			if dbCursor.fetchone() is None:
				dbCursor.execute("INSERT INTO pages VALUES (?, ?, '__IGNORE__', -1, 1, 0)", (tmpInfo['site'], tmpInfo['title']))
	dbConn.commit()
	f.close()
	
	f = open('entry_points-auto.txt', 'r')
	for line in f:
		line = line.strip()
		if line != '':
			tmpInfo = parseLink(line)
			dbCursor.execute("SELECT * FROM pages WHERE site = ? AND title = ?", (tmpInfo['site'], tmpInfo['title']))
			if dbCursor.fetchone() is None:
				dbCursor.execute("INSERT INTO pages VALUES (?, ?, NULL, 1, 1, 1)", (tmpInfo['site'], tmpInfo['title']))
	dbConn.commit()
	f.close()
	
	f = open('entry_points-manual.txt', 'r')
	for line in f:
		line = line.strip()
		if line != '':
			tmpInfo = parseLink(line)
			dbCursor.execute("SELECT * FROM pages WHERE site = ? AND title = ?", (tmpInfo['site'], tmpInfo['title']))
			if dbCursor.fetchone() is None:
				dbCursor.execute("INSERT INTO pages VALUES (?, ?, NULL, 123, 1, 0)", (tmpInfo['site'], tmpInfo['title']))
	dbConn.commit()
	f.close()


def downloadLevel(level):
	dbCursor = dbConn.cursor()
	
	for row in dbCursor.execute('SELECT * FROM pages WHERE level = ' + str(level) + ' AND path IS NULL AND verify=1'):
		info1 = 'Download [' + row[0] + "] " + row[1]
		sys.stdout.write(info1)
		sys.stdout.flush()
		t = time.time()
		msg=None
		
		try:
			saveFullArticle(row[0], row[1], row[3], row[4], row[5])
			t = time.time() - t
			info2 = 'done [' + str(round(t)) + 's]'
		except Exception as e:
			t = time.time() - t
			if e.args[0] == 'Page Missing':
				dbCursor2 = dbConn.cursor()
				dbCursor2.execute("INSERT INTO pages VALUES (?, ?, ?, ?, ?, ?)", (row[0], row[1], '__MISSING__', row[3], row[4], row[5]))
				dbConn.commit()
				info2 = 'NOT FOUND [' + str(round(t)) + 's]'
			else:
				print("\n       ERROR:", e)
				dbCursor2 = dbConn.cursor()
				dbCursor2.execute("INSERT INTO pages VALUES (?, ?, ?, ?, ?, ?)", (row[0], row[1], '__ERROR__', row[3], row[4], row[5]))
				dbConn.commit()
				info2 = 'ERROR [' + str(round(t)) + 's]'
		
		sys.stdout.write(' ' * (128 - len(info1) - len(info2)) + info2 + '\n')
		
		if t < 2:
			t = 2
		time.sleep(1.4 * t)

def printLinksToFix():
	if os.path.isfile('fixWikiLink.sh'):
		raise IOError('fixWikiLink.sh exist')
	f = open('fixWikiLink.sh', 'w')
	
	dbCursor = dbConn.cursor()
	sql1='SELECT DISTINCT n.site, n.oldTitle, n.newTitle FROM normalized AS n JOIN pages AS p'
	sql2='ON (n.site=p.site AND n.newTitle=p.title AND p.level=1)'
	for row in dbCursor.execute(sql1 + ' ' + sql2):
		if row[0] == "pl.wikipedia.org":
			print('fixWiki pl "' + row[1] + '" "' + row[2] + '"', file=f)
		elif row[0] == 'en.wikipedia.org':
			print('fixWiki en "' + row[1] + '" "' + row[2] + '"', file=f)
		elif row[0] == 'pl.wikibooks.org':
			print('fixWiki pl "b:' + row[1] + '" "b:' + row[2] + '"', file=f)
		elif row[0] == 'en.wikibooks.org':
			print('fixWiki en "b:' + row[1] + '" "b:' + row[2] + '"', file=f)
	
	f.close()

def getAllContributors(site = 'pl.wikibooks.org', contTxt = ''):
	conn     = HTTPSConnection(site)
	queryStr = '/w/api.php?action=query&continue&format=json&list=allusers&auprop=editcount&auwitheditsonly&aulimit=500'
	
	contFlag = True
	if contTxt != '':
		contTxt = contTxt = '&' + 'aufrom=' + quote(contTxt)
	infoFile = open(site + '_userList.txt', 'a')
	while contFlag:
		conn.request('GET', queryStr + contTxt, headers=httpHeaders)
		res = conn.getresponse()
		if res.status != 200:
			raise IOError('GET HTTP code: ' + res.status + res.reason + ' for ' + propFull + ' request: ' + queryStr)
		data = json.loads(res.read().decode())
		
		if 'continue' in data:
			contTxt = '&' + 'aufrom=' + quote(data['continue']['aufrom'])
		else:
			contFlag = False
		infoFile.write(json.dumps(data['query']['allusers'], indent=1, ensure_ascii=False))
		time.sleep(3.4)
	infoFile.close()
