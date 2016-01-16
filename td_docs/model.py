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
    self.categories = {}
    if pages:
      for page in pages:
        self.addPage(page)
      self.linkPages()

  def addPage(self, page):
    self.pagesByFilename[page.fname] = page
    utils.addToMultiDict(self.pagesByType, page.pageType, page)
    if page.pageType == 'category':
      categoryName = page.pageInfo['name']
      category = self.categories.get(categoryName)
      if not category:
        category = self.categories[categoryName] = WikiCategory(categoryName)
      category.addPage(page)

  def toJsonDict(self):
    return {
      'pages': [page.toJsonDict() for page in self.pagesByFilename.values()],
      'categories': [category.toJsonDict() for category in self.categories.values()],
    }

  def linkPages(self):
    for page in self.pagesByFilename.values():
      prevName = page.pageInfo.get('prev')
      page.prevPage = self.pagesByFilename[prevName] if prevName else None
      nextName = page.pageInfo.get('next')
      page.nextPage = self.pagesByFilename[nextName] if nextName else None

  @staticmethod
  def loadJsonPageSet(jsonDict):
    pages = [WikiPage.loadJsonPage(pageDict) for pageDict in jsonDict.get('pages', [])]
    pageSet = WikiPageSet(pages)
    return pageSet


class WikiCategory:
  def __init__(self, name):
    self.name = name
    self.pagesByFilename = {}
    self.pagesBySubject = {}

  def addPage(self, page):
    self.pagesByFilename[page.fname] = page

  def indexSubjects(self):
    for page in self.pagesByFilename.values():
      contents = page.pageInfo.get('contents', [])
      for subject in contents:
        utils.addToMultiDict(self.pagesBySubject, subject, page)

  def toJsonDict(self):
    return {
      'name': self.name,
      'pages': [page.toJsonDict() for page in self.pagesByFilename.values()],
      'subjects': {
        subject: [page.fname for page in pages]
        for (subject, pages) in self.pagesBySubject.items()
      }
    }

  @staticmethod
  def loadJsonCategory(jsonDict, pageSet):
    category = WikiCategory(jsonDict['name'])
    for pageName in jsonDict['pages']:
      page = pageSet.pagesByFilename[pageName]
      category.addPage(page)
    subjects = jsonDict.get('subjects')
    if subjects is not None:
      for (subject, subjPages) in subjects.items():
        category.pagesBySubject[subject] = [pageSet.pagesByFilename[pageName] for pageName in subjPages]
    else:
      category.indexSubjects()
    return category

