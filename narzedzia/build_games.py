"""Dokłada do wtyczki dwie gry karciane w przeglądarce i kafelki z obrazkami na stronie głównej.
Użycie: python3 build_games.py <katalog wtyczki> <cards_psg.json> <cards_dzieci.json> <katalog z kafel-*.jpg> <wersja>
"""
import json, pathlib, re, shutil, sys

root = pathlib.Path(sys.argv[1])
app = root / "app"
psg = json.load(open(sys.argv[2], encoding="utf-8"))
kids = json.load(open(sys.argv[3], encoding="utf-8"))
banners = pathlib.Path(sys.argv[4])
version = sys.argv[5]

hub = (app / "index.html").read_text(encoding="utf-8")
styles = re.findall(r"<style>.*?</style>", hub, flags=re.S)
assert len(styles) == 2
font_css = styles[0].replace("url(fonts/", "url(../fonts/")
base_css = styles[1]

# ---------- obrazki kafelków
(app / "img").mkdir(exist_ok=True)
for n in ("kafel-stereotyp", "kafel-psg", "kafel-dzieci"):
    shutil.copy(banners / (n + ".jpg"), app / "img" / (n + ".jpg"))

# ---------- strona gry karcianej (wspólny szablon)
GAME_CSS = """
<style>
.homelink{color:var(--head);font-weight:700;font-size:16px}
.cats{display:flex;gap:8px;flex-wrap:wrap;margin-top:14px}
.cats button{font:inherit;font-size:15px;font-weight:700;border:1px solid var(--line);background:var(--paper);color:var(--head);border-radius:999px;padding:10px 14px;min-height:44px;cursor:pointer}
.cats button[aria-pressed="true"]{background:var(--head);color:var(--on-dark);border-color:var(--head)}
.qcard{position:relative;margin:18px auto 0;max-width:420px;min-height:430px;border-radius:26px;padding:30px 26px 26px;text-align:center;background:var(--qbg);color:var(--qink);border:1px solid var(--qline);box-shadow:0 10px 26px rgba(60,40,20,.16);display:flex;flex-direction:column}
.qcard::before{content:"";position:absolute;inset:12px;border:1.5px solid var(--qline);border-radius:17px;pointer-events:none}
.qcard .chip{align-self:center;background:var(--chip);color:#FFFDF8;font-size:15px;font-weight:700;letter-spacing:.18em;text-transform:uppercase;padding:8px 16px;border-radius:9px;max-width:90%}
.qcard .q{font-family:"Lora",Georgia,serif;font-weight:500;font-size:28px;line-height:1.3;margin:auto 0;padding:26px 4px;text-wrap:balance}
.qcard .hint{font-size:16px;line-height:1.45;min-height:52px}
.qcard .hint b{display:block;font-size:15px;letter-spacing:.08em;text-transform:uppercase;opacity:.8;margin-bottom:4px}
.qcard .tags{display:flex;gap:6px;flex-wrap:wrap;justify-content:center}
.qcard .tags span{border:1px solid var(--qline);border-radius:999px;padding:4px 12px}
.qcard .linkbtn{font:inherit;font-size:16px;font-weight:700;background:none;border:0;color:inherit;text-decoration:underline;cursor:pointer;min-height:44px;padding:8px 12px}
.qcard .brand{font-size:15px;font-weight:700;letter-spacing:.2em;opacity:.7;margin-top:14px}
:root{--qbg:#FBF6EA;--qink:#2C2620;--qline:#E3D2A8;--chip:#5A2D12}
body.kids{--qbg:#2C4C7A;--qink:#FFFDF8;--qline:#D9A24E;--chip:#D9A24E}
body.kids .qcard .chip{color:#1F2F4D}
body.kids .qcard .q{font-family:var(--font);font-weight:700;font-size:27px}
:root[data-skin="duzy"] .qcard{--qbg:#FFFFFF;--qink:#1A1410;--qline:#8F7B63;box-shadow:none;border-width:2px}
:root[data-skin="duzy"] .qcard .chip{background:#3B1D0C;color:#FFFFFF}
:root[data-skin="duzy"] .qcard .q{font-size:32px}
:root[data-skin="duzy"] .qcard .hint{font-size:19px}
.actions{display:flex;gap:10px;flex-wrap:wrap;justify-content:center;margin-top:18px}
.actions .btn{flex:1 1 180px;max-width:300px}
.count{text-align:center;color:var(--muted);font-size:15px;margin-top:12px}
.count button{font:inherit;font-weight:700;color:var(--head);background:none;border:0;text-decoration:underline;cursor:pointer;min-height:44px;padding:8px}
@media (max-width:420px){.qcard{min-height:400px;padding:26px 20px 22px}.qcard .q{font-size:25px}}
@media (prefers-reduced-motion:no-preference){.qcard.flip{animation:flip .28s ease-out}@keyframes flip{from{opacity:0;transform:translateY(10px) rotate(-1.5deg)}to{opacity:1;transform:none}}}
</style>
"""

GAME_JS = r"""
<script>
(function () {
  var CFG = __CFG__;
  var CARDS = __CARDS__;
  var KEY = CFG.key, TC = { marka: "#F3BF69", duzy: "#FFFFFF" };
  try { var s = localStorage.getItem("ssw-skin"); if (s && TC[s]) { document.documentElement.dataset.skin = s; document.querySelector('meta[name="theme-color"]').content = TC[s]; } } catch (e) {}
  var lg = document.getElementById("logo"), im = lg.querySelector("img"); var bad = function () { lg.classList.add("noimg"); }; im.onerror = bad; if (im.complete && !im.naturalWidth) bad();

  var byId = {}; CARDS.forEach(function (c) { byId[c.id] = c; });
  var starter = CARDS.filter(function (c) { return c.s; })[0];
  var deck = CARDS.filter(function (c) { return !c.s; });
  var st = { seen: [], cur: null, cat: "all", hint: false };
  try { var raw = JSON.parse(localStorage.getItem(KEY) || "null"); if (raw && Array.isArray(raw.seen)) { st.seen = raw.seen.filter(function (id) { return byId[id]; }); st.cur = byId[raw.cur] ? raw.cur : null; st.cat = raw.cat || "all"; } } catch (e) {}
  function save() { try { localStorage.setItem(KEY, JSON.stringify({ seen: st.seen, cur: st.cur, cat: st.cat })); } catch (e) {} }
  function pool() { return deck.filter(function (c) { return st.seen.indexOf(c.id) < 0 && c.id !== st.cur && (st.cat === "all" || c.c === st.cat); }); }
  function esc(t) { return String(t).replace(/[&<>"]/g, function (m) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[m]; }); }
  var $ = function (id) { return document.getElementById(id); };

  function draw(countCurrent) {
    if (st.cur && countCurrent && st.seen.indexOf(st.cur) < 0) st.seen.push(st.cur);
    var p = pool();
    if (!p.length) { st.cur = null; save(); render(); return; }
    st.cur = p[Math.floor(Math.random() * p.length)].id; st.hint = false; save(); render(true);
  }
  function render(anim) {
    var playing = st.cur !== null || st.seen.length > 0;
    $("start").hidden = playing; $("play").hidden = !playing;
    if (!playing) return;
    if (CFG.cats) {
      $("cats").innerHTML = [["all", "Wszystkie"]].concat(CFG.cats).map(function (k) { return "<button type='button' data-c='" + esc(k[0]) + "' aria-pressed='" + (st.cat === k[0]) + "'>" + esc(k[1]) + "</button>"; }).join("");
      $("cats").querySelectorAll("button").forEach(function (b) { b.onclick = function () { st.cat = b.dataset.c; var c = byId[st.cur]; if (c && !c.s && st.cat !== "all" && c.c !== st.cat) { draw(false); } else { save(); render(); } }; });
    }
    var c = byId[st.cur], left = pool().length, card = $("card");
    if (!c) {
      card.style.setProperty("--chip", "");
      card.innerHTML = "<span class='chip'>Koniec talii</span><p class='q'>" + (st.cat === "all" ? "To już wszystkie karty." : "W tym kręgu to już wszystkie karty.") + "</p><p class='hint'>Możesz przetasować talię i zacząć od nowa" + (st.cat === "all" ? "." : " albo wybrać inny krąg.") + "</p><p class='brand'>ŚWIADOME SŁOWA</p>";
      $("next").hidden = true; $("pass").hidden = true;
    } else {
      if (!document.body.classList.contains("kids") && c.k) card.style.setProperty("--chip", c.k); else card.style.setProperty("--chip", "");
      var tags = c.h && c.h.length ? "<span class='tags'>" + c.h.map(function (h) { return "<span>" + esc(h) + "</span>"; }).join("") + "</span>" : "";
      card.innerHTML = "<span class='chip'>" + esc(c.l) + "</span><p class='q'>" + esc(c.q) + "</p><div class='hint'>" +
        (tags ? (st.hint ? "<b>Podpowiedź może dotyczyć</b>" + tags : "<button type='button' class='linkbtn' id='hintbtn'>Pokaż podpowiedź</button>") : "") + "</div><p class='brand'>ŚWIADOME SŁOWA</p>";
      var hb = $("hintbtn"); if (hb) hb.onclick = function () { st.hint = true; render(); };
      $("next").hidden = false; $("pass").hidden = !!c.s;
      $("next").textContent = left ? "Następna karta" : "Zakończ talię";
    }
    if (anim) { card.classList.remove("flip"); void card.offsetWidth; card.classList.add("flip"); }
    var total = deck.filter(function (x) { return st.cat === "all" || x.c === st.cat; }).length;
    $("left").textContent = "W talii zostało " + left + " z " + total + " kart.";
  }
  $("go").onclick = function () { st.cur = starter ? starter.id : null; st.hint = false; if (!starter) { draw(false); return; } save(); render(true); };
  $("next").onclick = function () { draw(true); };
  $("pass").onclick = function () { draw(false); };
  $("reset").onclick = function () { st.seen = []; st.cur = null; st.cat = "all"; save(); render(); window.scrollTo(0, 0); };
  render();
  if ("serviceWorker" in navigator && location.protocol !== "file:") { window.addEventListener("load", function () { navigator.serviceWorker.register("../sw.js").catch(function () {}); }); }
})();
</script>
"""


def page(title, desc, lead, rules, footnote, cfg, cards, kids_mode):
    data = [
        {"id": c["id"], "q": c["question"], "h": c.get("hint") or [], "s": bool(c.get("isStarter")),
         "c": c["deck"] if not kids_mode else "D",
         "l": (c["deckName"] if not kids_mode else c["category"]), "k": c.get("deckColor", "")}
        for c in cards
    ]
    js = GAME_JS.replace("__CFG__", json.dumps(cfg, ensure_ascii=False)).replace("__CARDS__", json.dumps(data, ensure_ascii=False, separators=(",", ":")))
    rules_html = "".join(f"<li>{r}</li>" for r in rules)
    return f"""<!doctype html>
<html lang="pl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="theme-color" content="#F3BF69">
<meta name="robots" content="noindex">
<meta name="description" content="{desc}">
<link rel="manifest" href="../manifest.webmanifest">
<link rel="icon" type="image/png" sizes="32x32" href="../favicon-32.png">
<link rel="apple-touch-icon" href="../apple-touch-icon.png">
<title>{title}</title>
{font_css}
{base_css}
{GAME_CSS}
</head>
<body{' class="kids"' if kids_mode else ''}>
<div class="wrap">
  <header class="top"><div class="toprow"><a class="logo" id="logo" href="../" aria-label="Gry coachingowe: strona główna"><img src="../logo.png" alt="Świadome Słowa" height="40"><span class="alt">Świadome Słowa</span></a></div></header>
  <main>
    <p style="margin:14px 0 0"><a class="homelink" href="../">← Wszystkie gry coachingowe</a></p>
    <h1 style="margin-top:8px">{title}</h1>
    <section id="start">
      <p class="lead">{lead}</p>
      <div class="card">
        <h2>Jak grać</h2>
        <ul class="rules">{rules_html}</ul>
        <p style="margin:16px 0 0"><button type="button" class="btn" id="go">Zacznij rozmowę</button></p>
      </div>
    </section>
    <section id="play" hidden>
      <div class="cats" id="cats" role="group" aria-label="Krąg pytań"></div>
      <div class="qcard" id="card" aria-live="polite"></div>
      <div class="actions"><button type="button" class="btn" id="next">Następna karta</button><button type="button" class="btn ghost" id="pass">Pas</button></div>
      <p class="count"><span id="left"></span> <button type="button" id="reset">Przetasuj od nowa</button></p>
    </section>
    <section class="card">
      <h2>Dobrze wiedzieć</h2>
      <ul class="rules">{''.join(f'<li>{f}</li>' for f in footnote)}</ul>
    </section>
  </main>
  <p class="brandfoot">Lepsze i bardziej świadome życie<br><a href="https://swiadomeslowa.pl/" target="_blank" rel="noopener">swiadomeslowa.pl</a></p>
</div>
{js}
</body>
</html>
"""


order = ["I", "II", "III", "IV", "V"]
names = {c["deck"]: c["deckName"] for c in psg}
n_psg = sum(1 for c in psg if not c.get("isStarter"))
n_kids = sum(1 for c in kids if not c.get("isStarter"))
assert n_psg == 150 and n_kids == 51, (n_psg, n_kids)

(app / "poznajmy-sie-glebiej").mkdir(exist_ok=True)
(app / "poznajmy-sie-glebiej" / "index.html").write_text(page(
    "Poznajmy się głębiej",
    "Gra rozmów: 150 pytań w pięciu kręgach. Od Świadome Słowa.",
    "150 pytań, które zbliżają: o sobie, emocjach, relacjach, drodze i sensie. Dla par, przyjaciół, rodziny i zespołów.",
    ["Zaczynacie od karty otwarcia. Każdy odpowiada po kolei.",
     "Potem losujecie kolejne karty. Możecie wybrać jeden krąg pytań albo grać wszystkimi.",
     "Słuchacie bez oceniania i bez rad. Podpowiedź na karcie pomaga, gdy nie wiadomo, od czego zacząć.",
     "Zawsze możesz powiedzieć „pas”, bez tłumaczenia się. Karta wraca wtedy do talii."],
    ["Ta gra niczego o Tobie nie zbiera: nie ma pól do wpisywania ani kont. W tej przeglądarce zapisuje się tylko to, które karty już były.",
     "To nie terapia. Gdy emocje są bardzo silne, zatrzymajcie grę. Pomoc w kryzysie: 116 123 (wsparcie emocjonalne dla dorosłych), 112 (zagrożenie życia)."],
    {"key": "ssw-psg-v1", "cats": [[d, names[d]] for d in order]}, psg, False), encoding="utf-8")

(app / "z-dziecmi").mkdir(exist_ok=True)
(app / "z-dziecmi" / "index.html").write_text(page(
    "Poznajmy się głębiej z dziećmi",
    "Gra rozmów dla rodzica i dziecka: 51 pytań. Od Świadome Słowa.",
    "51 prostych pytań do wspólnej rozmowy z dzieckiem: o tym, co lubi, co je złości, o kolegach, domu i marzeniach.",
    ["Grajcie razem: dorosły czyta pytanie, a odpowiadają wszyscy po kolei, dorosły też.",
     "Nie ma dobrych i złych odpowiedzi. Słuchajcie do końca, bez poprawiania i bez ocen.",
     "Podpowiedź na karcie pomaga, gdy dziecko nie wie, od czego zacząć.",
     "Każdy, także dziecko, może powiedzieć „pas”. Karta wraca wtedy do talii."],
    ["Gra jest dla rodzica lub opiekuna razem z dzieckiem. Telefon lub komputer obsługuje dorosły.",
     "Ta gra niczego nie zbiera: nie ma pól do wpisywania, kont ani statystyk. W tej przeglądarce zapisuje się tylko to, które karty już były.",
     "Jeśli odpowiedź dziecka Cię niepokoi, porozmawiaj o tym spokojnie po grze. Telefon zaufania dla dzieci i młodzieży: 116 111. Zagrożenie życia: 112."],
    {"key": "ssw-psgd-v1", "cats": None}, kids, True), encoding="utf-8")

# ---------- strona główna: kafelki z obrazkami
start = hub.index('<section class="card" aria-labelledby="g1">')
end = hub.index('<section class="card soon" aria-labelledby="g2">')
tiles = f"""<div class="tiles">
      <a class="tile" href="stereotyp/" aria-labelledby="g1">
        <img src="img/kafel-stereotyp.jpg" width="960" height="504" alt="Plansza gry: trasa 13 stacji i Karta Przebudowy">
        <span class="tb"><span class="tt" id="g1">Stereotyp na warsztacie</span>
        <span class="meta">13 stacji · około 45 minut · solo albo w grupie</span>
        <span class="td">Gra o przekonaniach, które prowadzą nas za rękę. Badasz własny stereotyp, a na końcu dostajesz Kartę Przebudowy.</span>
        <span class="btn">Zagraj</span></span>
      </a>
      <a class="tile" href="poznajmy-sie-glebiej/" aria-labelledby="g3">
        <img src="img/kafel-psg.jpg" width="960" height="504" alt="Trzy karty z pytaniami do rozmowy">
        <span class="tb"><span class="tt" id="g3">Poznajmy się głębiej</span>
        <span class="meta">{n_psg} pytań w 5 kręgach · od 2 osób</span>
        <span class="td">Pytania, które zbliżają: o sobie, emocjach, relacjach, drodze i sensie. Zawsze możesz spasować.</span>
        <span class="btn">Zagraj</span></span>
      </a>
      <a class="tile" href="z-dziecmi/" aria-labelledby="g4">
        <img src="img/kafel-dzieci.jpg" width="960" height="504" alt="Dwie granatowe karty gry dla dzieci">
        <span class="tb"><span class="tt" id="g4">Poznajmy się głębiej z dziećmi</span>
        <span class="meta">{n_kids} pytań · dla rodzica i dziecka</span>
        <span class="td">Proste pytania do wspólnej rozmowy z dzieckiem: o tym, co lubi, co je złości i o czym marzy.</span>
        <span class="btn">Zagraj</span></span>
      </a>
    </div>

    """
hub = hub[:start] + tiles + hub[end:]
TILE_CSS = """
.wrap{max-width:1040px}
.lead,main>.card,.brandfoot{max-width:640px}
.tiles{display:grid;grid-template-columns:1fr;gap:18px;margin-top:20px}
@media (min-width:720px){.tiles{grid-template-columns:repeat(3,1fr)}}
.tile{display:flex;flex-direction:column;background:var(--paper);border:1px solid var(--line);border-radius:18px;overflow:hidden;text-decoration:none;color:var(--ink);box-shadow:0 2px 10px rgba(60,40,20,.07);transition:transform .15s ease,box-shadow .15s ease}
.tile:hover{transform:translateY(-3px);box-shadow:0 10px 24px rgba(60,40,20,.14)}
.tile img{display:block;width:100%;height:auto;aspect-ratio:960/504;object-fit:cover;background:var(--line)}
.tile .tb{display:flex;flex-direction:column;flex:1;padding:16px 18px 18px}
.tile .tt{font-weight:700;font-size:22px;line-height:1.25;color:var(--head)}
.tile .meta{display:block;margin:4px 0 10px}
.tile .td{flex:1;margin-bottom:14px}
.tile .btn{align-self:flex-start}
:root[data-skin="duzy"] .tile{border:2px solid var(--line);box-shadow:none}
:root[data-skin="duzy"] .tile .tt{font-size:25px}
@media (prefers-reduced-motion:reduce){.tile{transition:none}.tile:hover{transform:none}}
</style>"""
i = hub.index("</style>", hub.index(":root{--bg"))
hub = hub[:i] + TILE_CSS.rstrip()[:-len("</style>")] + hub[i:]
hub = hub.replace("<li>Twoje odpowiedzi zapisują się tylko w tej przeglądarce. Autor ich nie widzi i nie przechowuje. Nie trzeba zakładać konta.</li>",
                  "<li>Twoje odpowiedzi w grze Stereotyp zapisują się tylko w tej przeglądarce. Autor ich nie widzi i nie przechowuje. Gry z kartami niczego nie zbierają. Nie trzeba zakładać konta.</li>")
assert "wkrótce" not in hub.split('aria-labelledby="g2"')[0]
(app / "index.html").write_text(hub, encoding="utf-8")

# ---------- praca bez internetu i numer wersji
sw = (app / "sw.js").read_text(encoding="utf-8")
m = re.search(r'const V = "gc-v(\d+)";', sw)
sw = sw.replace(m.group(0), 'const V = "gc-v%d";' % (int(m.group(1)) + 1))
old = '"stereotyp/", "stereotyp/index.html",'
assert sw.count(old) == 1
sw = sw.replace(old, old + ' "poznajmy-sie-glebiej/", "poznajmy-sie-glebiej/index.html", "z-dziecmi/", "z-dziecmi/index.html", "img/kafel-stereotyp.jpg", "img/kafel-psg.jpg", "img/kafel-dzieci.jpg",')
(app / "sw.js").write_text(sw, encoding="utf-8")

php = root / "ssw-poznaj-siebie.php"
t = php.read_text(encoding="utf-8")
t, n = re.subn(r"Version: [0-9.]+", "Version: " + version, t)
assert n == 1
php.write_text(t, encoding="utf-8")
print("ok", n_psg, n_kids)
