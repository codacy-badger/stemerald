#!/usr/bin/env bash

rm -rf wiki
git clone git@github.com:mahdi13/monostacrypt/staemerald.wiki.git wiki
GIT="git -C wiki"
$GIT pull origin master
$GIT rm apiv*.md --ignore-unmatch
cp data/api-documents/api/*.md wiki/
$GIT add \*.md
$GIT commit -am "Wiki updated automatically."
$GIT push origin master

