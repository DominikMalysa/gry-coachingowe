/* Gry coachingowe: praca bez internetu dla strony głównej i wszystkich gier. Przy każdej zmianie plików zwiększ numer wersji. */
const V = "gc-v3";
const FONTS = ["fonts/lora-latin-500-normal.woff2", "fonts/lora-latin-700-normal.woff2", "fonts/lora-latin-500-italic.woff2", "fonts/lora-latin-ext-500-normal.woff2", "fonts/lora-latin-ext-700-normal.woff2", "fonts/lora-latin-ext-500-italic.woff2", "fonts/source-sans-3-latin-400-normal.woff2", "fonts/source-sans-3-latin-600-normal.woff2", "fonts/source-sans-3-latin-700-normal.woff2", "fonts/source-sans-3-latin-ext-400-normal.woff2", "fonts/source-sans-3-latin-ext-600-normal.woff2", "fonts/source-sans-3-latin-ext-700-normal.woff2", "fonts/lato-latin-400-normal.woff2", "fonts/lato-latin-ext-400-normal.woff2", "fonts/lato-latin-700-normal.woff2", "fonts/lato-latin-ext-700-normal.woff2", "fonts/cinzel-latin-700-normal.woff2", "fonts/cinzel-latin-ext-700-normal.woff2"];
const SHELL = ["./", "index.html", "stereotyp/", "stereotyp/index.html", "poznajmy-sie-glebiej/", "poznajmy-sie-glebiej/index.html", "z-dziecmi/", "z-dziecmi/index.html", "img/kafel-stereotyp.jpg", "img/kafel-psg.jpg", "img/kafel-dzieci.jpg", "manifest.webmanifest", "icon-192.png", "icon-512.png",
  "icon-maskable-512.png", "apple-touch-icon.png", "favicon-32.png", "logo.png"].concat(FONTS);

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(V).then((c) => c.addAll(SHELL)).then(() => self.skipWaiting()));
});
self.addEventListener("activate", (e) => {
  e.waitUntil(caches.keys().then((ks) => Promise.all(ks.filter((k) => k !== V).map((k) => caches.delete(k))))
    .then(() => self.clients.claim()));
});
self.addEventListener("fetch", (e) => {
  const req = e.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);
  if (url.origin !== location.origin) return;
  if (req.mode === "navigate") {
    // Strona: najpierw sieć (limit 6 s), bez sieci kopia z pamięci. Do pamięci trafia tylko poprawna odpowiedź HTML (200).
    e.respondWith((async () => {
      const cache = await caches.open(V);
      const fallback = async () => (await cache.match(req, { ignoreSearch: true })) || (await cache.match(new URL("./", self.registration.scope).href));
      try {
        const ctl = new AbortController();
        const t = setTimeout(() => ctl.abort(), 6000);
        const r = await fetch(req, { signal: ctl.signal });
        clearTimeout(t);
        if (r.ok) {
          if (r.status === 200 && !r.redirected && (r.headers.get("content-type") || "").includes("text/html")) cache.put(req, r.clone());
          return r;
        }
        return (await fallback()) || r;
      } catch (err) {
        return (await fallback()) || Response.error();
      }
    })());
    return;
  }
  e.respondWith(caches.match(req).then((hit) => hit || fetch(req).then((r) => {
    if (r.ok) { const copy = r.clone(); caches.open(V).then((c) => c.put(req, copy)); }
    return r;
  })));
});
