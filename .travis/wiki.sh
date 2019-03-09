#!/usr/bin/env bash

set -e # Exit with nonzero exit code if anything fails

# Save some useful information
SHA=`git rev-parse --verify HEAD`

rm -rf wiki
git clone git@github.com:mahdi13/emerald.wiki.git wiki
GIT="git -C wiki"
$GIT pull origin master
$GIT rm apiv*.md --ignore-unmatch
cp data/api-documents/api/*.md wiki/
$GIT add \*.md
$GIT config user.name "Travis CI"
$GIT config user.email "$COMMIT_AUTHOR_EMAIL"
$GIT commit -am "Deploy to GitHub WIKI: ${SHA}"
$GIT push origin master
