import asyncio, json, sys
from playwright.async_api import async_playwright

BASE = "http://127.0.0.1:8765/gry-coachingowe/"
OUT = sys.argv[1]


async def play(page, path, total, cats):
    r = {}
    await page.goto(BASE + path, wait_until="networkidle")
    await page.evaluate("localStorage.removeItem('ssw-psg-v1');localStorage.removeItem('ssw-psgd-v1')")
    await page.reload(wait_until="networkidle")
    r["start_visible"] = await page.locator("#start").is_visible()
    await page.click("#go")
    first = (await page.locator("#card .q").inner_text()).strip()
    r["first_card"] = first
    r["pass_hidden_on_starter"] = not await page.locator("#pass").is_visible()
    await page.screenshot(path=f"{OUT}/{path.strip('/')}_start_390.png")
    seen, passes = [], 0
    await page.click("#next")
    # podpowiedź
    hb = page.locator("#hintbtn")
    if await hb.count():
        await hb.click()
        r["hint_tags"] = await page.locator("#card .tags span").count()
    await page.screenshot(path=f"{OUT}/{path.strip('/')}_card_390.png")
    # pas: karta wraca do talii
    q1 = (await page.locator("#card .q").inner_text()).strip()
    left1 = await page.locator("#left").inner_text()
    await page.click("#pass")
    left2 = await page.locator("#left").inner_text()
    r["pass_keeps_deck_size"] = (left1 == left2)
    # trwałość po odświeżeniu
    q2 = (await page.locator("#card .q").inner_text()).strip()
    await page.reload(wait_until="networkidle")
    r["persist_after_reload"] = ((await page.locator("#card .q").inner_text()).strip() == q2)
    # przejście całej talii
    for _ in range(total + 5):
        if not await page.locator("#next").is_visible():
            break
        seen.append((await page.locator("#card .q").inner_text()).strip())
        await page.click("#next")
    r["drawn"] = len(seen)
    r["distinct"] = len(set(seen))
    r["end_text"] = (await page.locator("#card .q").inner_text()).strip()
    r["left_at_end"] = await page.locator("#left").inner_text()
    if cats:
        await page.click("#reset")
        await page.click("#go")
        await page.locator("#cats button").nth(2).click()
        name = (await page.locator("#cats button").nth(2).inner_text()).strip()
        chips = set()
        n = 0
        for _ in range(40):
            if not await page.locator("#next").is_visible():
                break
            chips.add((await page.locator("#card .chip").inner_text()).strip().upper())
            n += 1
            await page.click("#next")
        r["cat_test"] = {"cat": name, "cards": n, "chips": sorted(chips)}
    await page.click("#reset")
    r["reset_to_start"] = await page.locator("#start").is_visible()
    r["scroll_x"] = await page.evaluate("document.documentElement.scrollWidth > window.innerWidth")
    r["min_font_px"] = await page.evaluate("Math.min(...[...document.querySelectorAll('body *')].filter(e => e.offsetParent && e.childNodes.length && [...e.childNodes].some(n => n.nodeType === 3 && n.textContent.trim())).map(e => parseFloat(getComputedStyle(e).fontSize)))")
    return r


async def main():
    res, errors, bad, external = {}, [], [], []
    async with async_playwright() as p:
        b = await p.chromium.launch(channel="chrome", args=["--no-proxy-server"])
        ctx = await b.new_context(viewport={"width": 390, "height": 844})
        page = await ctx.new_page()
        page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.on("response", lambda r: bad.append((r.status, r.url)) if r.status >= 400 else None)
        page.on("request", lambda r: external.append(r.url) if not r.url.startswith("http://127.0.0.1:8765") and not r.url.startswith("data:") else None)

        await page.goto(BASE, wait_until="networkidle")
        res["hub_tiles"] = await page.eval_on_selector_all("a.tile", "els => els.map(e => [e.querySelector('.tt').innerText, e.getAttribute('href'), e.querySelector('img').naturalWidth])")
        res["hub_scroll_x_390"] = await page.evaluate("document.documentElement.scrollWidth > window.innerWidth")
        await page.screenshot(path=OUT + "/hub2_390.png", full_page=True)
        await page.set_viewport_size({"width": 1280, "height": 800})
        await page.screenshot(path=OUT + "/hub2_1280.png", full_page=True)
        await page.set_viewport_size({"width": 390, "height": 844})
        await page.evaluate("navigator.serviceWorker.ready")
        await page.wait_for_timeout(1500)

        # wejście kafelkiem
        await page.locator("a.tile").nth(1).click()
        await page.wait_for_load_state("networkidle")
        res["tile2_url"] = page.url
        res["psg"] = await play(page, "poznajmy-sie-glebiej/", 150, True)
        res["dzieci"] = await play(page, "z-dziecmi/", 51, False)
        await page.click("#go")
        await page.click("#next")
        await page.set_viewport_size({"width": 1280, "height": 800})
        await page.screenshot(path=OUT + "/dzieci_card_1280.png")
        await page.set_viewport_size({"width": 390, "height": 844})
        # duży druk
        await page.evaluate("localStorage.setItem('ssw-skin','duzy')")
        await page.goto(BASE + "poznajmy-sie-glebiej/", wait_until="networkidle")
        await page.click("#go")
        await page.screenshot(path=OUT + "/psg_duzy_390.png")
        await page.evaluate("localStorage.setItem('ssw-skin','marka')")
        res["caches"] = await page.evaluate("caches.keys()")

        await ctx.set_offline(True)
        off = {}
        for path in ["", "stereotyp/", "poznajmy-sie-glebiej/", "z-dziecmi/"]:
            try:
                await page.goto(BASE + path, wait_until="load")
                off[path or "/"] = await page.title()
            except Exception as e:
                off[path or "/"] = "BLAD: " + str(e)[:60]
        await page.goto(BASE, wait_until="load")
        off["tile_images_offline"] = await page.eval_on_selector_all("a.tile img", "els => els.map(e => e.naturalWidth)")
        res["offline"] = off
        await b.close()
    res["console_errors"] = errors
    res["responses_ge_400"] = bad
    res["external_requests"] = external
    print(json.dumps(res, ensure_ascii=False, indent=1))


asyncio.run(main())
