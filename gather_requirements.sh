rm -f 'requirements.all.txt';
touch 'requirements.all.txt';
find . -type f -name requirements.txt -exec cat {} >> requirements.all.txt \;
