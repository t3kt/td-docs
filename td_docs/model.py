import cleaning

class WikiPage:
  def __init__(self, fpath, fname, title, pageType, pageInfo, soup=None):
    self.fname = fname
    self.title = title
    self.pageType = pageType
    self.pageInfo = pageInfo
    self.soup = soup

  def _requireSoup(self):
    if not self.soup:
      raise Exception('Soup has not been loaded for page ' + self.fname)

  def clean(self):
    self._requireSoup()
    cleaning.cleanPageSoup(self.soup)

  def writeContents(self, f):
    self._requireSoup()
    f.write(self.soup.prettify('utf-8', formatter='xml'))

