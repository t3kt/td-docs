#!/usr/bin/python

import argparse
import json
import os.path
import sys

import td_docs.parsing


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument('action', choices=['clean', 'cleanall', 'getinfo', 'buildindex'])
  parser.add_argument('files', type=str, nargs='+')
  parser.add_argument('--outdir')
  parser.add_argument('--index')
  args = parser.parse_args()

  if args.action == 'clean':
    if len(args.files) > 1:
      raise Exception('Cleaning multiple files not currently supported')
    page = td_docs.parsing.loadWikiPage(args.files[0])
    page.clean()
    page.writeContents(sys.stdout)
  elif args.action == 'cleanall':
    if not args.outdir:
      raise Exception('Output directory must be specified')
    if not os.path.exists(args.outdir):
      os.makedirs(args.outdir)
    for fpath in args.files:
      page = td_docs.parsing.loadWikiPage(fpath)
      outfpath = os.path.join(args.outdir, page.fname)
      page.clean()
      print('writing cleaned page %s -> %s' % (fpath, outfpath))
      with open(outfpath, 'w') as outfile:
        page.writeContents(outfile)
  elif args.action == 'buildindex':
    if not args.index:
      raise Exception('Index file must be specified')
    pageSet = td_docs.parsing.loadWikiPageSet(args.files)
    print('writing page set index to %s' % (args.index,))
    with open(args.index, 'w') as f:
      json.dump(pageSet.toDict(), f, indent=2, sort_keys=True)
  elif args.action == 'getinfo':
    pageSet = td_docs.parsing.loadWikiPageSet(args.files)
    pageSet.dumpInfo(sys.stdout)
  else:
    raise Exception('unsupported action: ' + args.action)

if __name__ == '__main__':
  main()