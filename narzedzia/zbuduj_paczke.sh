#!/bin/bash
# Buduje paczkę wtyczki do katalogu wtyczka/ i aktualizuje wersja.json.
# Użycie: bash narzedzia/zbuduj_paczke.sh
set -e
cd "$(dirname "$0")/.."
V=$(grep -m1 '^ \* Version:' ssw-poznaj-siebie.php | sed 's/.*Version: *//')
rm -rf /tmp/ssw_pack && mkdir -p /tmp/ssw_pack/ssw-poznaj-siebie
tar cf - --exclude=.git --exclude=narzedzia --exclude=wtyczka --exclude=README.md --exclude=.gitignore . \
  | (cd /tmp/ssw_pack/ssw-poznaj-siebie && tar xf -)
rm -f wtyczka/*.zip
(cd /tmp/ssw_pack && zip -q -r -X "ssw-gry-coachingowe-$V.zip" ssw-poznaj-siebie)
mv "/tmp/ssw_pack/ssw-gry-coachingowe-$V.zip" wtyczka/
printf '{\n  "wersja": "%s",\n  "plik": "ssw-gry-coachingowe-%s.zip"\n}\n' "$V" "$V" > wtyczka/wersja.json
unzip -tq "wtyczka/ssw-gry-coachingowe-$V.zip"
echo "Zbudowano wersję $V"
