# Test przebiegu gry Stereotyp (kolejność 13 przystanków, karty specjalne, waga, karta przebudowy, migracja stanu).
# Użycie: PLUGIN=<ścieżka>/ssw-poznaj-siebie.php php -S 127.0.0.1:8765 narzedzia/router.php &  potem: python3 narzedzia/stereotyp_test.py <katalog_wyjscia>
import asyncio, json, sys
from playwright.async_api import async_playwright
URL = "http://127.0.0.1:8765/gry-coachingowe/stereotyp/"
OUT = sys.argv[1]
EXP = ["Nazwij to", "Pierwszy raz", "Kto mi to dał", "Głos pokoleń", "Początek historii", "Tarcza", "Czy nadal aktualne",
       "Inne sfery życia", "Otoczenie", "Nauczyciel i ślepa plamka", "Na wagę", "Przebuduj", "Eksperyment 7 dni"]

async def main():
    r = {"errors": []}
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
        ctx = await b.new_context(viewport={"width": 390, "height": 844}, service_workers="block")
        pg = await ctx.new_page()
        pg.on("pageerror", lambda e: r["errors"].append(str(e)[:120]))
        pg.on("console", lambda m: r["errors"].append(m.text[:120]) if m.type == "error" else None)
        await pg.goto(URL, wait_until="networkidle")
        await pg.evaluate("localStorage.clear()"); await pg.reload(wait_until="networkidle")
        await pg.fill("textarea, input[type=text]", "Jak proszę o pomoc, to jestem ciężarem.")
        await pg.click("#next")
        names, phases, special, nrs = [], [], [], []
        for i in range(13):
            names.append((await pg.locator("#app h2").first.inner_text()).strip())
            phases.append((await pg.locator("#phase span").first.inner_text()).split("·")[0].strip())
            nrs.append((await pg.locator("#phase span").nth(1).inner_text()).strip())
            special.append(await pg.locator("#spbox").count() > 0)
            if i + 1 in (8, 11, 12):
                await pg.wait_for_timeout(700)
                await pg.screenshot(path=f"{OUT}/stereotyp_krok{i+1}.png")
            if i < 12: await pg.click("#next")
        r["names"] = names; r["phases"] = phases; r["nrs"] = nrs
        r["names_ok"] = [n.startswith(e) or e in n for n, e in zip(names, EXP)]
        r["special_at"] = [i + 1 for i, s in enumerate(special) if s]
        r["special_ok"] = r["special_at"] == [3, 6, 9, 12]
        await pg.click("#next")  # karta przebudowy
        txt = await pg.locator("#app").inner_text()
        r["summary_has_stacja12_hint"] = "stacja 12" in txt
        await pg.screenshot(path=f"{OUT}/stereotyp_karta.png", full_page=True)
        # migracja starego stanu: step=8 (stary 'Na wagę') -> nowe 11, odpowiedź stacji k=8 zostaje
        await pg.evaluate("""localStorage.setItem('ssw-stereotyp-v2', JSON.stringify({step:8, stereo:'Test', a:{8:'odp wagi'}, mode:'solo'}))""")
        await pg.reload(wait_until="networkidle")
        r["migr_step_name"] = (await pg.locator("#app h2").first.inner_text()).strip()
        r["migr_phase_nr"] = (await pg.locator("#phase span").nth(1).inner_text()).strip()
        st = json.loads(await pg.evaluate("localStorage.getItem('ssw-stereotyp-v2')"))
        r["migr_v"] = st.get("v"); r["migr_step"] = st.get("step")
        # drugie wczytanie nie przesuwa ponownie
        await pg.reload(wait_until="networkidle")
        r["migr_stable"] = (await pg.locator("#phase span").nth(1).inner_text()).strip() == r["migr_phase_nr"]
        await b.close()
    print(json.dumps(r, ensure_ascii=False, indent=1))
asyncio.run(main())
