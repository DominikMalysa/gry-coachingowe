# Gry coachingowe — wtyczka WordPress

Wtyczka dla swiadomeslowa.pl. Udostępnia zakładkę „Gry coachingowe" pod adresem
`/gry-coachingowe/` i trzy gry w przeglądarce:

- `/gry-coachingowe/stereotyp/` — Stereotyp na warsztacie (13 stacji),
- `/gry-coachingowe/poznajmy-sie-glebiej/` — Poznajmy się głębiej (150 pytań w 5 kręgach),
- `/gry-coachingowe/z-dziecmi/` — Poznajmy się głębiej z dziećmi (51 pytań).

Stare adresy `/stereotyp/` i `/poznaj-siebie-glebiej/` przenoszą na nowe.

## Zasady

- Gry nie zbierają żadnych danych: bez kont, bez pól do wpisywania w grach karcianych.
  W przeglądarce gracza zapisuje się tylko postęp (które karty już były).
- Tryb ukryty: dopóki `SSW_PS_NOINDEX` jest `true`, wyszukiwarki nie indeksują tych stron.
  Przed publicznym startem ustawić `false`.
- Wygląd: style „Marka" (domyślny) i „Duży druk".

## Aktualizacje

Wtyczka sama sprawdza nowe wydania w tym repozytorium i pokazuje aktualizację
w panelu WordPressa (Wtyczki → Aktualizuj). Nowa wersja = nowe wydanie (release)
z plikiem zip o nazwie `ssw-gry-coachingowe-<wersja>.zip`.

Dla repozytorium prywatnego trzeba raz dodać token do `wp-config.php`:

    define( 'SSW_GC_GITHUB_TOKEN', 'ghp_...' );

Dla repozytorium publicznego token nie jest potrzebny.
