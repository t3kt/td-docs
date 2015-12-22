#!/usr/bin/python

import sys
from bs4 import BeautifulSoup
import re
import os.path
from optparse import OptionParser

def removeTags(tags):
  for tag in tags:
    tag.extract()

def removeByTags(soup, *names):
  for name in names:
    removeTags(soup.find_all(name))

def removeBySelectors(soup, *selectors):
  for selector in selectors:
    removeTags(soup.select(selector))

def removeByIds(soup, *ids):
  for i in ids:
    removeTags(soup.find_all(id=i))


def cleanPageUrl(url):
  if not url:
    return None
  if '?' in url:
    return url.split('?')[0]
  return url

class TScriptPageParser:
  def __init__(self, subType):
    self.pageType = 'tscript' + subType
    self.subType = subType

  def parsePage(self, page):
    title = page.title
    info = {
      'name': title.replace('TScript:', '')
    }
    return info

class CategoryChunkPageParser:
  def __init__(self):
    self.pageType = 'category'

  def parsePage(self, page):
    title = page.title
    prevTag = page.soup.find('a', string=re.compile('previous [0-9]+'))
    nextTag = page.soup.find('a', string=re.compile('next [0-9]+'))
    info = {
      'name': title.replace('Category:', '')
    }
    if prevTag:
      info['prev'] = cleanPageUrl(prevTag['href'])
    if nextTag:
      info['next'] = cleanPageUrl(nextTag['href'])
    return info

class PyClassPageParser:
  def __init__(self):
    self.pageType = 'pyclass'

  def parsePage(self, page):
    return {}

class PyModulePageParser:
  def __init__(self):
    self.pageType = 'pymodule'

  def parsePage(self, page):
    return {}

class OPPageParser:
  def __init__(self, subType):
    self.pageType = subType
    self.subType = subType

  def parsePage(self, page):
    title = page.title
    info = {
      'name': title
    }
    return info

def _buildParserSet():
  parsers = {
    'category': CategoryChunkPageParser(),
    'tscriptcmd': TScriptPageParser('cmd'),
    'tscriptexpr': TScriptPageParser('expr'),
  }
  for subType in ['chop', 'sop', 'comp', 'mat', 'top', 'dat']:
    parsers[subType] = OPPageParser(subType)
  return parsers

parsersByType = _buildParserSet()

def _parsePageInfo(page):
  pageType = page.pageType
  parser = parsersByType.get(pageType)
  if parser is None:
    return {}
  return parser.parsePage(page)

def _extractPageType(title):
  if title.startswith('Category:'):
    return 'category'
  if re.match('[a-zA-Z0-9]+ Class', title):
    return 'pyclass'
  if re.match('[a-zA-Z0-9] Module', title):
    return 'pymodule'
  if title.startswith('TScript:'):
    if title.endswith(' Command'):
      return 'tscriptcmd'
    else:
      return 'tscriptexpr'
  if title.endswith(' Command'):
    return 'tscriptcmd'
  if title.endswith(' CHOP'):
    return 'chop'
  if title.endswith(' SOP'):
    return 'sop'
  if title.endswith(' COMP'):
    return 'comp'
  if title.endswith(' MAT'):
    return 'mat'
  if title.endswith(' TOP'):
    return 'top'
  if title.endswith(' DAT'):
    return 'dat'
  if title.endswith(' Vid'):
    return 'video'
  return 'other'

class WikiPage:
  def __init__(self, fpath, soup):
    self.fpath = fpath
    self.soup = soup
    self._title = None
    self._pageType = None
    self._pageInfo = None

  _cleanTitleRx = re.compile('\s+-\s+TouchDesigner\s+088\s*Wiki')
  @property
  def title(self):
    if self._title is None:
      self._title = WikiPage._cleanTitleRx.sub('', self.soup.title.text.strip())
    return self._title

  @property
  def fname(self):
    return os.path.split(self.fpath)[1]

  @property
  def pageType(self):
    if self._pageType is None:
      self._pageType = _extractPageType(self.title)
    return self._pageType

  @property
  def pageInfo(self):
    if self._pageInfo is None:
      self._pageInfo = _parsePageInfo(self)
    return self._pageInfo

  def clean(self):
    removeByTags(self.soup,
                 'meta', 'link', 'style')
    removeBySelectors(self.soup,
                      '#globalWrapper div:nth-of-type(1)',
                      '.visualClear')
    removeByIds(self.soup,
                'top',
                'column-one',
                'siteSub',
                'contentSub',
                'jump-to-nav',
                'p-TouchDesigner_088',
                "'catlinks'")
    self.soup.h1.span.unwrap()
    self.soup.find(id='globalWrapper').unwrap()
    self.soup.find(id='column-content').unwrap()

  def write(self, f):
    f.write(self.soup.prettify('utf-8', formatter='xml'))

  def __str__(self):
    return 'WikiPage(fname: %s, pageType: %s, title: %s, info: %s)' % (
      self.fname, self.pageType, self.title, self .pageInfo)

  @staticmethod
  def loadPage(fpath):
    with open(fpath) as f:
      soup = BeautifulSoup(f, 'html.parser')
      return WikiPage(fpath, soup)


def _addToMultiDict(d, key, val):
  if key in d:
    d[key].append(val)
  else:
    d[key] = [val]

def _sortPagesByFilename(pages):
  return sorted(pages, key=lambda p: p.fname)

class WikiPageSet:
  def __init__(self):
    self.pagesByFilename = {}
    self.pagesByType = {}
    self.categoryPageGroups = {}

  def _getOrAddCategoryGroup(self, name):
    if name in self.categoryPageGroups:
      return self.categoryPageGroups[name]
    group = CategoryPageGroup(name)
    self.categoryPageGroups[name] = group
    return group

  def addPage(self, page):
    self.pagesByFilename[page.fname] = page
    _addToMultiDict(self.pagesByType, page.pageType, page)
    if page.pageType == 'category':
      group = self._getOrAddCategoryGroup(page.pageInfo['name'])
      group.addPage(page)

  def loadPages(self, fpaths):
    for fpath in fpaths:
      page = WikiPage.loadPage(fpath)
      self.addPage(page)

  def dumpInfo(self):
    print('WikiPageSet:')
    for pageType in self.pagesByType:
      print('  [%s]' % (pageType,))
      pages = self.pagesByType[pageType]
      for page in _sortPagesByFilename(pages):
        print('    %s' % (page,))
    print(' category groups:')
    for group in self.categoryPageGroups.values():
      group.dumpInfo()

class CategoryPageGroup:
  def __init__(self, name):
    self.name = name
    self.pagesByFilename = {}
    self.pages = []

  def addPage(self, page):
    self.pages.append(page)
    self.pagesByFilename[page.fname] = page

  def dumpInfo(self):
    print('  [category group: %s]' % (self.name,))
    for page in self.pages:
      print('    %s' % (page,))


def main():
  optParser = OptionParser()
  action = sys.argv[1]

  options, fpaths = optParser.parse_args(sys.argv[2:])

  if action == 'clean':
    if len(fpaths) > 1:
      raise Exception('Cleaning multiple files not currently supported')
    fpath = fpaths[0]

    page = WikiPage.loadPage(fpath)

    page.clean()

    page.write(sys.stdout)
  elif action == 'getinfo':
    pageSet = WikiPageSet()
    pageSet.loadPages(fpaths)
    pageSet.dumpInfo()
  else:
    raise Exception('unsupported action: ' + action)

if __name__ == '__main__':
  main()