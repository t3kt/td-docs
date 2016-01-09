import re
import os
import os.path
import utils
import cleaning

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
      info['prev'] = utils.cleanPageUrl(prevTag['href'])
    if nextTag:
      info['next'] = utils.cleanPageUrl(nextTag['href'])
    if page.soup.find_all('em', string='This category currently contains no pages or media'):
      info['empty'] = True
    else:
      table = page.soup.find(id='mw-content-text').find(**{"class":"mw-content-ltr"})
      if table:
        contents = [utils.cleanString(link.text) for link in table.find_all('a')]
        info['contents'] = contents
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

parsersByType = {
  'category': CategoryChunkPageParser(),
  'tscriptcmd': TScriptPageParser('cmd'),
  'tscriptexpr': TScriptPageParser('expr'),
}
parsersByType.update({
  subType: OPPageParser(subType) for subType in ['chop', 'sop', 'comp', 'mat', 'top', 'dat']
})

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

_cleanTitleRx = re.compile('\s+-\s+TouchDesigner\s+088\s*Wiki')

class WikiPage:
  def __init__(self, fpath, soup):
    self.fpath = fpath
    self.soup = soup
    self._title = None
    self._pageType = None
    self._pageInfo = None

  @property
  def title(self):
    if self._title is None:
      self._title = _cleanTitleRx.sub('', self.soup.title.text.strip())
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
    cleaning.cleanPageSoup(self.soup)

  def writeContents(self, f):
    f.write(self.soup.prettify('utf-8', formatter='xml'))

  def __str__(self):
    return 'WikiPage(fname: %s, pageType: %s, title: %s, info: %s)' % (
      self.fname, self.pageType, self.title, self .pageInfo)

  def toDict(self):
    return {
      'fpath': self.fpath,
      'fname': self.fname,
      'title': self.title,
      'pageType': self.pageType,
      'pageInfo': self.pageInfo,
    }


def _sortPagesByFilename(pages):
  return sorted(pages, key=lambda p: p.fname)

class WikiPageSet:
  def __init__(self):
    self.pagesByFilename = {}
    self.pagesByType = {}
    self.categoryPageGroups = {}

  def toDict(self):
    return {
      'pages': [page.toDict() for page in self.pagesByFilename.values()],
      'pageTypes': {
        pageType: [page.fname for page in typePages]
        for (pageType, typePages) in self.pagesByType.items()
      },
      'categoryGroups': {
        groupName: group.toDict()
        for (groupName, group) in self.categoryPageGroups.items()
      }
    }

  def _getOrAddCategoryGroup(self, name):
    if name in self.categoryPageGroups:
      return self.categoryPageGroups[name]
    group = CategoryPageGroup(name)
    self.categoryPageGroups[name] = group
    return group

  def addPage(self, page):
    self.pagesByFilename[page.fname] = page
    utils.addToMultiDict(self.pagesByType, page.pageType, page)
    if page.pageType == 'category':
      group = self._getOrAddCategoryGroup(page.pageInfo['name'])
      group.addPage(page)

  def dumpInfo(self, out):
    out.write('WikiPageSet:\n')
    for pageType in self.pagesByType:
      out.write('  [%s]\n' % (pageType,))
      pages = self.pagesByType[pageType]
      for page in _sortPagesByFilename(pages):
        out.write('    %s\n' % (page,))
    out.write(' category groups:\n')
    for group in self.categoryPageGroups.values():
      group.dumpInfo(out)

class CategoryPageGroup:
  def __init__(self, name):
    self.name = name
    self.pagesByFilename = {}
    self.pages = []
    self.subjectsToPages = {}
    self.redundantPages = []

  def toDict(self):
    return {
      'name': self.name,
      'pages': self.pagesByFilename.keys(),
      'subjects': {
        subject: [page.fname for page in subjPages]
        for (subject, subjPages) in self.subjectsToPages.items()
      }
    }

  def addPage(self, page):
    self.pages.append(page)
    self.pagesByFilename[page.fname] = page

  def linkPages(self):
    for page in self.pages:
      prevName = page.pageInfo.get('prev')
      nextName = page.pageInfo.get('next')
      page.prevPage = self.pagesByFilename.get(prevName) if prevName else None
      page.nextPage = self.pagesByFilename.get(nextName) if nextName else None

  def indexSubjects(self):
    for page in self.pages:
      contents = page.pageInfo.get('contents')
      if contents:
        for subject in contents:
          utils.addToMultiDict(self.subjectsToPages, subject, page)

  def separateRealAndRedundantPages(self):
    firsts = self.findFirsts()
    if len(firsts) <= 1:
      redundantPages = []
      realPages = list(self.pages)
    else:
      realPages = []
      redundantPages = []
      firsts = self.findFirsts()
      densestFirst = min(firsts, key=lambda p: len(CategoryPageGroup._getChain(p)))
      for first in firsts:
        chain = CategoryPageGroup._getChain(first)
        if first is densestFirst:
          realPages = chain
        else:
          redundantPages += chain
      print('found %i/%i real pages and %i/%i redundant pages' % (len(realPages), len(self.pages), len(redundantPages), len(self.pages)))
    return realPages, redundantPages
    #raise NotImplementedError()

  # def findRedundantFirstPages(self):
  #   firsts = self.findFirsts()
  #   if len(firsts) <= 1:
  #     return []
  #   return max(firsts, key=lambda p: len(p.pageInfo['contents']))

  def findFirsts(self):
    return [page for page in self.pages if page.prevPage is None]

  @staticmethod
  def _getChain(firstPage):
    chain = []
    page = firstPage
    while page:
      chain.append(page)
      page = page.nextPage
    return chain

  def dumpInfo(self, out):
    out.write('  [category group: %s]\n' % (self.name,))
    for page in self.pages:
      out.write('    %s\n' % (page,))
    out.write('    first pages:\n')
    for page in self.findFirsts():
      out.write('      %s\n' % (page,))
      out.write('         %s\n' % ([page.fname for page in CategoryPageGroup._getChain(page)]))
    out.write('    pages by subject:\n')
    for subject in self.subjectsToPages:
      out.write('      %s: ' % (subject,))
      for page in self.subjectsToPages[subject]:
        out.write(' %s' % (page.fname,))
      out.write('\n')
    realPages, redundantPages = self.separateRealAndRedundantPages()
    out.write('    real pages:\n')
    for page in realPages:
      out.write('         %s\n' % page.fname)
    out.write('    redundant pages:\n')
    for page in redundantPages:
      out.write('         %s\n' % page.fname)
