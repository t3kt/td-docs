#!/bin/sh

for f in TouchDesignerDocs088/*.html
do
   echo 'converting ' $f
  #html2xhtml $f -o converted/$f
  tidy -o converted/$f -config tidy_config $f
done
