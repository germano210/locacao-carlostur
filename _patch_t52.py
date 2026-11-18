"""T52 (artefato 9HaJSD): fotos enviadas pelo painel (/midia/...) entram direto (AS), sem o atalho '../midia/'; 'Ver por dentro' some em veículo sem passeio (noTour).
Uso: python _patch_t52.py site"""
import sys, pathlib, json
I = pathlib.Path(sys.argv[1]) / "index.html"; s = I.read_text(encoding="utf-8")
TAG = "_patch_t52.py"
assert ("/*" + TAG + "*/") not in s, "já aplicado"
HUNKS = json.loads("[{\"t\": \"insert\", \"old\": \"\", \"new\": \"const AS = n => /^(data:|blob:|https?:|\\\\/|\\\\.)/.test(String(n)) ? String(n) : `assets/${n}.webp`;   // 18/11: foto do painel (enviada) ou do site\", \"pre\": \"const icon = (name, cls = '') => `<svg class=\\\"${cls}\\\" aria-hidden=\\\"true\\\"><use href=\\\"#i-${name}\\\"/></svg>`;\", \"post\": \"const exTag = on => on ? '<span class=\\\"tag-ex\\\" title=\\\"Dado de exemplo: a empresa confirma o real\\\">Exemplo</span>' : '';\", \"k\": 16}, {\"t\": \"insert\", \"old\": \"\", \"new\": \"  { const sem = !!(b.noTour && !b.photos.filter(p => !/-ext$/.test(p[0])).length); ['#insideBtn', '#stInside', '#infoInside'].forEach(k => { const e = $(k); if (e) e.style.display = sem ? 'none' : ''; }); }   // 18/11: ve\u00edculo novo sem fotos de dentro: sem \\\"Ver por dentro\\\"\", \"pre\": \"  $('#heroName').textContent = b.name; $('#heroSub').textContent = b.sub;\", \"post\": \"  { const d = SITE.disp && SITE.disp[b.id], el = $('#heroDisp');\", \"k\": 26}, {\"t\": \"replace\", \"old\": \"  const img = (n) => `assets/${n}.webp`;\", \"new\": \"  const img = (n) => AS(n);\", \"pre\": \"  let bus = null, idx = 0, from = null, closeT = 0;\", \"post\": \"  function media(c) {\", \"k\": 38}]")
for h in HUNKS:   # trechos do artefato 9HaJSD (17/11), aplicados sobre o nosso site
    if h["t"] == "insert":
        a = h["pre"] + "\n" + h["post"]; assert s.count(a) == 1, (h["k"], s.count(a), a[:80])
        s = s.replace(a, h["pre"] + "\n" + h["new"] + "\n" + h["post"])
    else:
        assert s.count(h["old"]) == 1, (h["k"], s.count(h["old"]), h["old"][:80])
        s = s.replace(h["old"], h["new"])
def rep(a, b):
    global s; assert s.count(a) == 1, (s.count(a), a[:80]); s = s.replace(a, b)
for a, b in [
    ("const img = m ? m[1] : k ? '../midia/' + k[1] : null;   // as telas montam assets/<img>.webp", "const img = m ? m[1] : k ? f.s : null;   // T52: /midia/... vai direto (AS)"),
    ("data-cap=\"${esc(d ? t + ' · ' + d : t)}\"><img src=\"assets/${img}.webp\"", "data-cap=\"${esc(d ? t + ' · ' + d : t)}\"><img src=\"${AS(img)}\""),
    ("  $('#lbImg').src = `assets/${img}.webp`;", "  $('#lbImg').src = AS(img);"),
    ("const preloadPhotos = b => Promise.all([...b.photos.map(([img]) => preImg(`assets/${img}.webp`)), ...b.chips.map(c => (c[2] || {}).img).filter(Boolean).map(n => preImg(`assets/${n}.webp`))", "const preloadPhotos = b => Promise.all([...b.photos.map(([img]) => preImg(AS(img))), ...b.chips.map(c => (c[2] || {}).img).filter(Boolean).map(n => preImg(AS(n)))"),
    ("SITE.fleet.forEach(b => { b.photos.forEach(([img]) => L.add(`assets/${img}.webp`)); b.chips.forEach(c => { const n = (c[2] || {}).img; if (n) L.add(`assets/${n}.webp`); });", "SITE.fleet.forEach(b => { b.photos.forEach(([img]) => L.add(AS(img))); b.chips.forEach(c => { const n = (c[2] || {}).img; if (n) L.add(AS(n)); });"),
    ("  const top = new Set([...current.photos.map(([img]) => `assets/${img}.webp`), ...current.chips.map(c => (c[2] || {}).img).filter(Boolean).map(n => `assets/${n}.webp`),", "  const top = new Set([...current.photos.map(([img]) => AS(img)), ...current.chips.map(c => (c[2] || {}).img).filter(Boolean).map(n => AS(n)),"),
    ("  if (Tour3D.stub) { // 360° ainda não publicado: fotos reais do interior em sequência", "  if (Tour3D.stub || current.noTour) { // 360° ainda não publicado (ou veículo sem passeio): fotos reais do interior em sequência"),
]: rep(a, b)
s = s.replace("</html>", "<!--/*" + TAG + "*/-->\n</html>", 1) if "</html>" in s else s + "\n<!--/*" + TAG + "*/-->\n"
I.write_text(s, encoding="utf-8", newline="\n"); print(TAG, "aplicado:", len(HUNKS), "trechos")
