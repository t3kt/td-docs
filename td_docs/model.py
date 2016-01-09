import cleaning
import os.path
import utils

class WikiPage:
  def __init__(self, fname, title, pageType, pageInfo, soup=None):
    self.fname = fname
    self.title = title
    self.pageType = pageType
    self.pageInfo = pageInfo
    self.soup = soup

  def _requireSoup(self):
    if not self.soup:
      raise Exception('Soup has not been loaded for page ' + self.fname)

  def loadSoup(self, dirname=None):
    if dirname:
      fpath = os.path.join(dirname, self.fname)
    else:
      fpath = self.fname
    self.soup = utils.loadFileSoup(fpath)

  def clean(self):
    self._requireSoup()
    cleaning.cleanPageSoup(self.soup)

  def writeContents(self, f):
    self._requireSoup()
    f.write(self.soup.prettify('utf-8', formatter='xml'))

  def toJsonDict(self):
    return {
      'fname': self.fname,
      'title': self.title,
      'pageType': self.pageType,
      'pageInfo': self.pageInfo,
    }

  @staticmethod
  def loadJsonPage(jsonDict):
    return WikiPage(
      fname=jsonDict['fname'],
      title=jsonDict['title'],
      pageType=jsonDict['pageType'],
      pageInfo=jsonDict['pageInfo'],
    )

class WikiPageSet:
  def __init__(self, pages=None):
    self.pagesByFilename = {}
    self.pagesByType = {}
    if pages:
      for page in pages:
        self.addPage(page)

  def addPage(self, page):
    pass

  def toJsonDict(self):
    return {
      'pages': [page.toJsonDict() for page in self.pagesByFilename.values()],
    }

  @staticmethod
  def loadJsonPageSet(jsonDict):
    pages = [WikiPage.loadJsonPage(pageDict) for pageDict in jsonDict.get('pages', [])]
    pageSet = WikiPageSet(pages)
    return pageSet

