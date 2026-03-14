#!/bin/bash
set -e

# checking if I have the latest files from github
echo "Checking for newer files online first"
git pull

#add all file and folder for commit
git add .

# Give a comment to the commit if you want
echo "####################################"
echo "Write your commit comment!"
echo "####################################"
read input

# Committing to the local repository with a message containing the time details and commit text
git commit -m "$input"

#Push the local files to github
if grep -q main .git/config; then
	echo "Using main"
		git push -u origin main
fi

if grep -q master .git/config; then
	echo "Using master"
		git push -u origin master
fi

echo
tput setaf 6
echo "######################################################"
echo "###################  $(basename $0) done"
echo "######################################################"
tput sgr0
echo


