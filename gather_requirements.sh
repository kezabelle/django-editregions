rm -f 'requirements.all.txt';
touch 'requirements.all.txt';
find . -type f -name requirements.txt ! -path "./.tox/*" -exec cat {} \; | sort -f -d | uniq -u >> requirements.all.txt
