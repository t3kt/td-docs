

def _removeTags(tags):
  for tag in tags:
    tag.extract()

def _removeByTags(soup, *names):
  for name in names:
    _removeTags(soup.find_all(name))

def _removeBySelectors(soup, *selectors):
  for selector in selectors:
    _removeTags(soup.select(selector))

def _removeByIds(soup, *ids):
  for i in ids:
    _removeTags(soup.find_all(id=i))

def _unwrapById(soup, *ids):
  for i in ids:
    elem = soup.find(id=i)
    if elem is not None:
      elem.unwrap()

def cleanPageSoup(soup):
  _removeByTags(soup,
                'meta', 'link', 'style')
  _removeBySelectors(soup,
                     '#globalWrapper div:nth-of-type(1)',
                     '.visualClear')
  _removeByIds(soup,
               'top',
               'column-one',
               'siteSub',
               'contentSub',
               'jump-to-nav',
               'p-TouchDesigner_088',
               "'catlinks'")
  h1 = soup.h1
  if h1:
    span = h1.span
    if span:
      span.unwrap()
  _unwrapById(soup,
              'globalWrapper',
              'column-content')
