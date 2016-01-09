import re
from bs4 import BeautifulSoup

def cleanString(s):
  s = re.sub(' {2,}', '', s)
  return re.sub('\n*', '', s)

def cleanPageUrl(url):
  if not url:
    return None
  if '?' in url:
    return url.split('?')[0]
  return url

def addToMultiDict(d, key, val):
  if key in d:
    d[key].append(val)
  else:
    d[key] = [val]

def loadFileSoup(fpath):
  with open(fpath) as f:
    return BeautifulSoup(f, 'html.parser')
