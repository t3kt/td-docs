from bs4 import BeautifulSoup
import logging
import re
import os.path

from td_docs import WikiPage, WikiPageSet
import utils
import model

class TScriptPageParser:
  def __init__(self, subType):
    self.pageType = 'tscript' + subType
    self.subType = subType

  def parsePage(self, title, soup):
    info = {
      'name': title.replace('TScript:', ''),
      'subType': self.subType
    }
    return info

class CategoryChunkPageParser:
  def __init__(self):
    self.pageType = 'category'

  def parsePage(self, title, soup):
    prevTag = soup.find('a', string=re.compile('previous [0-9]+'))
    nextTag = soup.find('a', string=re.compile('next [0-9]+'))
    info = {
      'name': title.replace('Category:', '')
    }
    if prevTag:
      info['prev'] = utils.cleanPageUrl(prevTag['href'])
    if nextTag:
      info['next'] = utils.cleanPageUrl(nextTag['href'])
    if soup.find_all('em', string='This category currently contains no pages or media'):
      info['empty'] = True
    else:
      table = soup.find(id='mw-content-text').find(**{"class":"mw-content-ltr"})
      if table:
        contents = [utils.cleanString(link.text) for link in table.find_all('a')]
        info['contents'] = contents
    return info

class PyClassPageParser:
  def __init__(self):
    self.pageType = 'pyclass'

  def parsePage(self, title, soup):
    return {}

class PyModulePageParser:
  def __init__(self):
    self.pageType = 'pymodule'

  def parsePage(self, title, soup):
    return {}

class OPPageParser:
  def __init__(self, subType):
    self.pageType = subType
    self.subType = subType

  def parsePage(self, title, soup):
    info = {
      'name': title,
      'subType': self.subType
    }
    return info

_parsersByType = {
  'category': CategoryChunkPageParser(),
  'tscriptcmd': TScriptPageParser('cmd'),
  'tscriptexpr': TScriptPageParser('expr'),
  'chop': OPPageParser('chop'),
  'sop': OPPageParser('sop'),
  'comp': OPPageParser('comp'),
  'mat': OPPageParser('mat'),
  'top': OPPageParser('top'),
  'dat': OPPageParser('dat'),
}

def _parsePageInfo(pageType, title, soup):
  parser = _parsersByType.get(pageType)
  if parser is None:
    return {}
  return parser.parsePage(title, soup)

_cleanTitleRx = re.compile('\s+-\s+TouchDesigner\s+088\s*Wiki')

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

def loadWikiPage(fpath):
  soup = _loadFileSoup(fpath)
  fname = os.path.split(fpath)[1]
  title = _cleanTitleRx.sub('', soup.title.text.strip())
  pageType = _extractPageType(title)
  pageInfo = _parsePageInfo(pageType, title, soup)
  return model.WikiPage(fname, title, pageType, pageInfo)

def _loadFileSoup(fpath):
  with open(fpath) as f:
    return BeautifulSoup(f, 'html.parser')

def loadWikiPageSet(fpaths):
  pageSet = WikiPageSet()
  for fpath in fpaths:
    logging.info('loading page %s...\n' % (fpath,))
    page = loadWikiPage(fpath)
    pageSet.addPage(page)
  for group in pageSet.categoryPageGroups.values():
    group.linkPages()
    group.indexSubjects()
  return pageSet
