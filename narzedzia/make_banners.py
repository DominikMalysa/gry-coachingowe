"""Rysuje trzy obrazki kafelków (wizualizacje gier) i zapisuje je jako JPG.
Użycie: python3 make_banners.py <katalog app wtyczki> <katalog z obrazami kart dzieci> <content.py gry Stereotyp> <katalog wyjściowy>
"""
import asyncio, base64, importlib.util, json, pathlib, sys
from playwright.async_api import async_playwright
from PIL import Image

app = pathlib.Path(sys.argv[1]).resolve()
img = pathlib.Path(sys.argv[2]).resolve()
content_py = pathlib.Path(sys.argv[3]).resolve()
out = pathlib.Path(sys.argv[4]).resolve()
out.mkdir(parents=True, exist_ok=True)

spec = importlib.util.spec_from_file_location("content", content_py)
content = importlib.util.module_from_spec(spec)
spec.loader.exec_module(content)
fazy = stacje = None
for name in dir(content):
    v = getattr(content, name)
    if isinstance(v, list) and v and isinstance(v[0], dict):
        if "kolor" in v[0] and "opis" in v[0]:
            fazy = v
        if "nr" in v[0] and "faza" in v[0]:
            stacje = v
assert fazy and stacje and len(stacje) == 13, (bool(fazy), stacje and len(stacje))
kol = {f["id"]: f["kolor"] for f in fazy}


def b64(p):
    return "data:image/png;base64," + base64.b64encode(pathlib.Path(p).read_bytes()).decode()


FONT = f"""
@font-face{{font-family:Lora;font-weight:500;src:url(file://{app}/fonts/lora-latin-500-normal.woff2)}}
@font-face{{font-family:Lora;font-weight:500;src:url(file://{app}/fonts/lora-latin-ext-500-normal.woff2);unicode-range:U+0100-02BA}}
@font-face{{font-family:Lora;font-weight:500;font-style:italic;src:url(file://{app}/fonts/lora-latin-500-italic.woff2)}}
@font-face{{font-family:Lora;font-weight:500;font-style:italic;src:url(file://{app}/fonts/lora-latin-ext-500-italic.woff2);unicode-range:U+0100-02BA}}
@font-face{{font-family:Lato;font-weight:700;src:url(file://{app}/fonts/lato-latin-700-normal.woff2)}}
@font-face{{font-family:Lato;font-weight:700;src:url(file://{app}/fonts/lato-latin-ext-700-normal.woff2);unicode-range:U+0100-02BA}}
*{{box-sizing:border-box;margin:0}}
body{{width:1200px;height:630px;overflow:hidden;font-family:Lato,sans-serif}}
"""

# --- Stereotyp: trasa 13 stacji w kolorach pięciu faz, żetony wagi, Karta Przebudowy
pts = []
cols, x0, dx, y0, dy = 5, 150, 150, 150, 165
for i in range(13):
    row, c = divmod(i, cols)
    cx = x0 + (c if row % 2 == 0 else cols - 1 - c) * dx
    pts.append((cx, y0 + row * dy))
path = "M " + " L ".join(f"{x} {y}" for x, y in pts)
circles = "".join(
    f'<circle cx="{x}" cy="{y}" r="44" fill="{kol[s["faza"]]}" stroke="#FFFDF8" stroke-width="6"/>'
    f'<text x="{x}" y="{y + 13}" text-anchor="middle" font-family="Lato" font-weight="700" font-size="36" fill="#FFFDF8">{s["nr"]}</text>'
    for (x, y), s in zip(pts, stacje)
)
legend = "".join(
    f'<span style="display:inline-flex;align-items:center;gap:8px;margin-right:22px"><i style="width:18px;height:18px;border-radius:50%;background:{f["kolor"]};display:inline-block"></i>{f["nazwa"]}</span>'
    for f in fazy
)
tokens = "".join(
    f'<span style="width:{30 + n * 3}px;height:{30 + n * 3}px;border-radius:50%;background:#D9A24E;color:#3A2316;display:inline-flex;align-items:center;justify-content:center;font-weight:700;font-size:{15 + n}px;border:2px solid #B8763A">{n}</span>'
    for n in (1, 4, 7, 10)
)
stereotyp = f"""<style>{FONT}body{{background:#F8F1E3}}</style>
<svg width="1200" height="630" style="position:absolute;inset:0">
<path d="{path}" fill="none" stroke="#E0D3B8" stroke-width="26" stroke-linecap="round" stroke-linejoin="round"/>
<path d="{path}" fill="none" stroke="#5A2D12" stroke-width="3" stroke-dasharray="2 14" stroke-linecap="round"/>
{circles}</svg>
<div style="position:absolute;left:106px;bottom:34px;font-size:22px;font-weight:700;color:#5A2D12;letter-spacing:.06em">{legend}</div>
<div style="position:absolute;right:70px;top:86px;width:250px;height:350px;background:#FFFDF8;border:2px solid #D9A24E;border-radius:22px;transform:rotate(5deg);box-shadow:0 14px 30px rgba(60,40,20,.18);padding:28px 24px">
 <div style="font-size:17px;font-weight:700;letter-spacing:.14em;color:#B8763A">KARTA</div>
 <div style="font-family:Lora;font-size:31px;line-height:1.1;color:#5A2D12;margin-top:6px">Przebudowy</div>
 <div style="margin-top:26px;height:10px;border-radius:5px;background:#E0D3B8"></div>
 <div style="margin-top:14px;height:10px;border-radius:5px;background:#E0D3B8;width:82%"></div>
 <div style="margin-top:14px;height:10px;border-radius:5px;background:#E0D3B8;width:64%"></div>
 <div style="position:absolute;left:24px;bottom:26px;display:flex;align-items:flex-end;gap:8px">{tokens}</div>
</div>"""


def qcard(cat, color, q, rot, left, top, z):
    return f"""<div style="position:absolute;left:{left}px;top:{top}px;width:300px;height:450px;background:#FBF6EA;border-radius:24px;transform:rotate({rot}deg);z-index:{z};box-shadow:0 18px 40px rgba(0,0,0,.35);padding:34px 30px;text-align:center">
 <div style="position:absolute;inset:14px;border:1.5px solid #E3D2A8;border-radius:16px"></div>
 <span style="display:inline-block;background:{color};color:#FFFDF8;font-size:17px;font-weight:700;letter-spacing:.24em;padding:8px 18px;border-radius:8px">{cat}</span>
 <div style="font-family:Lora;font-style:italic;font-size:35px;line-height:1.28;color:#2C2620;margin-top:74px">{q}</div>
 <div style="position:absolute;left:0;right:0;bottom:36px;font-size:13px;font-weight:700;letter-spacing:.3em;color:#8A6B3C">ŚWIADOME SŁOWA</div>
</div>"""


psg_cards = json.load(open(sys.argv[5], encoding="utf-8"))
pick = {c["id"]: c for c in psg_cards}
a, b, c3 = pick["III_01"], pick["start"], pick["V_30"]
psg = f"""<style>{FONT}body{{background:linear-gradient(160deg,#16264D,#0B1733)}}</style>
{qcard(a["deckName"], a["deckColor"], a["question"], -11, 180, 96, 1)}
{qcard(c3["deckName"], c3["deckColor"], c3["question"], 10, 720, 96, 1)}
{qcard(b["deckName"], "#B8763A", b["question"], 0, 450, 70, 2)}"""

dzieci = f"""<style>{FONT}body{{background:linear-gradient(160deg,#F6CF86,#EDB357)}}
img{{position:absolute;height:500px;border-radius:26px;box-shadow:0 18px 40px rgba(40,30,10,.35)}}</style>
<img src="{b64(img / 'B1_rewers.png')}" style="left:300px;top:70px;transform:rotate(-9deg)">
<img src="{b64(img / 'B1_awers.png')}" style="left:610px;top:62px;transform:rotate(7deg)">"""


async def main():
    async with async_playwright() as p:
        br = await p.chromium.launch(channel="chrome", args=["--allow-file-access-from-files"])
        pg = await br.new_page(viewport={"width": 1200, "height": 630})
        for name, html in (("kafel-stereotyp", stereotyp), ("kafel-psg", psg), ("kafel-dzieci", dzieci)):
            tmp = out / (name + ".html")
            tmp.write_text("<!doctype html><meta charset=utf-8>" + html, encoding="utf-8")
            await pg.goto("file://" + str(tmp))
            await pg.evaluate("document.fonts.ready")
            await pg.wait_for_timeout(300)
            await pg.screenshot(path=str(out / (name + ".png")))
            Image.open(out / (name + ".png")).convert("RGB").resize((960, 504), Image.LANCZOS).save(out / (name + ".jpg"), quality=84, optimize=True)
            print(name, (out / (name + ".jpg")).stat().st_size)
        await br.close()


asyncio.run(main())
