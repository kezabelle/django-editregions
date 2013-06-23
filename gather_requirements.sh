rm -f 'requirements.txt';
touch 'requirements.txt';
find editregions -type f -name requirements.txt -exec cat {} >> requirements.txt \;
