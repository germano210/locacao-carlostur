"""T47 no site: mapa no celular como o Google Maps. Tocar no mapa (ou arrastar de lado) abre o mapa grande, onde UM dedo
move em qualquer direção, com inércia; dois toques aproximam; pinça continua. Sair: botão "Sair do mapa", o voltar do
celular/navegador ou Esc. Para cima e para baixo sobre o mapa pequeno segue rolando a página. Uso: python _patch_t47.py site"""
import sys, pathlib
p = pathlib.Path(sys.argv[1]) / "index.html"; s = p.read_text(encoding="utf-8")
assert "T47" not in s, "já aplicado"
R = []
R.append((r"""    const pickHere = (x, y) => { const k = pickAt(x, y); if (k && onPick) onPick(k, x, y); };
    let t1 = null, pinch = null;""", r"""    const pickHere = (x, y) => { const k = pickAt(x, y); if (k && onPick) onPick(k, x, y); return k; };
    let t1 = null, pinch = null;
    // T47: no toque, o mapa pequeno abre o mapa grande (um dedo move, como no Google Maps); dentro da folha do orçamento fica como antes
    const inSheet = () => !!cv.closest('.qb-map');
    const wantFull = () => { if (!fullOn && !inSheet()) cv.dispatchEvent(new CustomEvent('rmwantfull', { bubbles: true })); };
    let flRaf = 0, vx = 0, vy = 0, tap0 = null;
    const flStop = () => { cancelAnimationFrame(flRaf); flRaf = 0; };
    const fling = () => {   // inércia: o mapa continua um pouco depois de soltar
      if (matchMedia('(prefers-reduced-motion: reduce)').matches) return;
      let last = performance.now();
      const step = now => { const dt = Math.min(40, now - last); last = now; panBy(vx * dt, vy * dt); const k = Math.exp(-dt / 320); vx *= k; vy *= k; flRaf = Math.hypot(vx, vy) > 0.02 && fullOn ? requestAnimationFrame(step) : 0; };
      flStop(); flRaf = requestAnimationFrame(step);
    };"""))
R.append((r"""      if (e.touches.length === 1) { const [x, y] = tp(e.touches[0]); t1 = { x, y, t: performance.now(), moved: false }; pinch = null; }""",
          r"""      flStop(); vx = vy = 0;
      if (e.touches.length === 1) { const [x, y] = tp(e.touches[0]); t1 = { x, y, t: performance.now(), moved: false }; pinch = null; }"""))
R.append((r"""        if (fullOn) { if (!t1.moved && Math.hypot(x - t1.x, y - t1.y) > 6) t1.moved = true; if (t1.moved) { e.preventDefault(); panBy(x - t1.x, y - t1.y); t1.x = x; t1.y = y; } }""",
          r"""        if (fullOn) { if (!t1.moved && Math.hypot(x - t1.x, y - t1.y) > 6) t1.moved = true; if (t1.moved) { e.preventDefault(); const now = performance.now(), dt = Math.max(1, now - (t1.vt || now - 16)), dx = x - t1.x, dy = y - t1.y; vx = vx * 0.4 + dx / dt * 0.6; vy = vy * 0.4 + dy / dt * 0.6; t1.vt = now; panBy(dx, dy); t1.x = x; t1.y = y; } }"""))
R.append((r"""          if (t1.moved && t1.pan) { e.preventDefault(); panBy(x - t1.x, y - t1.y); t1.x = x; t1.y = y; } }""",
          r"""          if (t1.moved && t1.pan) { e.preventDefault(); if (inSheet()) { panBy(x - t1.x, y - t1.y); t1.x = x; t1.y = y; } else { wantFull(); t1 = null; } } }"""))
R.append((r"""      if (t1 && !t1.moved && performance.now() - t1.t < 600 && e.touches.length === 0) { e.preventDefault(); pickHere(t1.x, t1.y); }""",
          r"""      if (t1 && !t1.moved && performance.now() - t1.t < 600 && e.touches.length === 0) {
        e.preventDefault(); const now = performance.now(), hit = pickHere(t1.x, t1.y);
        if (!hit && !fullOn) wantFull();   // T47: tocar fora das cidades abre o mapa grande
        else if (!hit) { if (tap0 && now - tap0.t < 350 && Math.hypot(t1.x - tap0.x, t1.y - tap0.y) < 40) { zoomAt(t1.x, t1.y, 0.5); tap0 = null; } else tap0 = { x: t1.x, y: t1.y, t: now }; }   // dois toques aproximam
      } else if (t1 && t1.moved && fullOn && e.touches.length === 0 && performance.now() - (t1.vt || 0) < 90 && Math.hypot(vx, vy) > 0.25) fling();"""))
# MapFull: abrir pelo toque, voltar do celular fecha
R.append((r"""    if (on) return; on = true; onClose = opts.onClose || null; manual = null;
    dock.appendChild(map); full.hidden = false; root.classList.add('rm-full-on');""",
          r"""    if (on) return; on = true; onClose = opts.onClose || null; manual = null;
    try { history.scrollRestoration = 'manual'; history.pushState({ ctMap: 1 }, ''); } catch (e) { /* T47: o "voltar" do celular fecha o mapa em vez de sair do site */ }
    dock.appendChild(map); full.hidden = false; root.classList.add('rm-full-on'); mapHint();"""))
R.append((r"""    if (!on) return; on = false; manual = null;
    full.classList.remove('on'); root.classList.remove('rm-full-on');""",
          r"""    if (!on) return; on = false; manual = null;
    try { if (history.state && history.state.ctMap) history.back(); } catch (e) { /* sem histórico */ }
    full.classList.remove('on'); root.classList.remove('rm-full-on'); mapHint();"""))
R.append((r"""  $('#rmExpand').addEventListener('click', () => open());""",
          r"""  $('#rmExpand').addEventListener('click', () => open());
  map.addEventListener('rmwantfull', () => { if (!on) { open({ focus: false }); track('map_full_touch', {}); } });   // T47
  addEventListener('popstate', () => { if (on) close(false); });"""))
R.append((r"""  $('#rmHint').textContent = o ? (d ? 'Toque numa cidade: saída, destino ou parada' : 'Toque no destino, ou numa cidade do mapa') : (coarse ? 'Toque na cidade de saída · dois dedos movem o mapa' : 'Clique na cidade de saída · arraste para mover');
  $('#rmHint').classList.toggle('off', !!d);""", r"""  mapHint();"""))
R.append((r"""function paintRoute() {""", r"""// T47: o aviso do mapa diz como mexer (no celular: tocar abre o mapa grande; lá, um dedo move)
function mapHint() {
  const o = RouteMap.origin, d = RouteMap.dest, h = $('#rmHint'), big = root.classList.contains('rm-full-on');
  const como = !coarse ? 'arraste para mover' : big ? 'arraste com um dedo para mover' : 'toque no mapa para abrir e mover';
  h.textContent = (o ? (d ? 'Toque numa cidade: saída, destino ou parada' : 'Toque no destino') : (coarse ? 'Toque na cidade de saída' : 'Clique na cidade de saída')) + ' · ' + como;
  h.classList.toggle('off', !!d && !(coarse && !big));
}
function paintRoute() {"""))
for old, new in R:
    assert s.count(old) == 1, (s.count(old), old[:70])
    s = s.replace(old, new)
p.write_text(s, encoding="utf-8", newline="\n")
print("T47 aplicado:", len(R), "trocas")
