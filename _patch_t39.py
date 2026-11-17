"""T39 no site: veículo publicado no painel que ainda não tem cenário 3D entra sozinho no seletor, com a 1ª foto no
palco no lugar do ônibus animado (até a TLH fazer as imagens). Uso: python _patch_t39.py site"""
import sys, pathlib
p = pathlib.Path(sys.argv[1]) / "index.html"; s = p.read_text(encoding="utf-8")
assert "T39" not in s, "já aplicado"
R = []
# 1) entrada "genérica" para cada veículo publicado sem cenário
R.append((r"""  const keep = SITE.fleet.filter(b => pubIds.includes(b.id)); if (!keep.length) return;
""", r"""  const keep = SITE.fleet.filter(b => pubIds.includes(b.id));
  // T39: veículo publicado que ainda não tem cenário 3D entra "genérico": seletor, fotos e contato; a 1ª foto vai ao palco
  P.frota.forEach(v => {
    if (!v || !v.pub || SITE.cenIds.includes(v.id) || !/^[A-Za-z0-9_-]{1,40}$/.test(String(v.id || ''))) return;
    keep.push({ id: String(v.id), generico: true, tab: '', name: '', short: '', seats: 0, sub: '', groups: [], photos: [], chips: [] });
  });
  if (!keep.length) return;
"""))
R.append((r"""    if (fotos.length) b.photos = fotos;
  });
""", r"""    if (fotos.length) b.photos = fotos;
    if (b.generico) {   // T39: sem os textos da TLH, a ficha sai do que o painel publicou (lugares, itens a bordo, extras)
      const nm = nome || ({ van: 'Van', micro: 'Micro-ônibus' }[d.tipo] || 'Ônibus');
      b.name = nm; b.tab = nm.length > 22 ? nm.slice(0, 21) + '…' : nm; b.short = nm.length > 14 ? nm.slice(0, 13) + '…' : nm;
      if (!b.sub) b.sub = TIPN[d.tipo] || 'fretamento';
      const ICB = { wc: 'wc', gel: 'fridge', copa: 'coffee', bag: 'bag', bagf: 'bag', net: 'wifi', usb: 'usb', ar: 'ac', tv: 'monitor', porta: 'bus', escada: 'walk' };
      const bd = Array.isArray(d.bordo) ? d.bordo : d.bordo && typeof d.bordo === 'object' ? Object.keys(d.bordo).filter(k => d.bordo[k] && d.bordo[k].on).map(k => [k, d.bordo[k].t]) : [];
      const its = bd.filter(x => Array.isArray(x) && ICB[x[0]] && String(x[1] || '').trim()).map(x => [ICB[x[0]], String(x[1]).trim().slice(0, 60)])
        .concat((Array.isArray(d.extras) ? d.extras : []).map(x => String((x && x.n) || (typeof x === 'string' ? x : '')).trim().slice(0, 60)).filter(Boolean).map(t => ['star', t]));
      const pl = POLN[d.pol] ? ' ' + POLN[d.pol] : '', f0 = b.photos[0] ? b.photos[0][0] : '';
      const seat = b.seats ? [['seat2', `${b.seats} lugares${pl}`, Object.assign({ t: `${b.seats} lugares${pl}`, d: '' }, f0 ? { img: f0, f: [0.5, 0.5], z: 1 } : {})]] : [];
      b.chips = seat.concat(its.map(([ic, t]) => [ic, t, { t, d: '' }]));
      if (!b.chips.length) b.chips = [['bus', b.sub, { t: nm, d: '' }]];
      b.groups = [{ title: 'Conforto', items: b.seats ? [['seat2', `${b.seats} poltronas${pl}`]] : [] }, { title: 'A bordo', items: its }].filter(g => g.items.length);
      if (!b.groups.length) b.groups = [{ title: 'Veículo', items: [['bus', b.sub]] }];
    }
  });
"""))
# (T38) o chip de lugares do 2501 usa o ícone seat2 e não era atualizado
R.append((r"""(b.chips || []).forEach(c => { if (c[0] === 'seat') c[1]""", r"""(b.chips || []).forEach(c => { if (c[0] === 'seat' || c[0] === 'seat2') c[1]"""))
R.append((r"""(g.items || []).forEach(it => { if (it[0] === 'seat') it[1]""", r"""(g.items || []).forEach(it => { if (it[0] === 'seat' || it[0] === 'seat2') it[1]"""))
R.append((r"""(() => { try {
  const P = window.CT_PUB !== undefined""", r"""SITE.cenIds = SITE.fleet.map(b => b.id);   // T39: modelos que têm cenário 3D (imagens da TLH)
(() => { try {
  const P = window.CT_PUB !== undefined"""))
R.append((r"""const busById = id => SITE.fleet.find(b => b.id === id);
""", r"""const busById = id => SITE.fleet.find(b => b.id === id);
// T39: foto do cartão (a lateral da TLH ou, no veículo sem cenário, a 1ª foto publicada) e o ônibus que fica no cenário 3D
const busImg = b => b.side ? `assets/bus/${b.side}.webp` : (b.photos && b.photos[0] ? `assets/${b.photos[0][0]}.webp` : '');
const sceneBusId = id => { const b = busById(id); return b && !b.generico ? id : ((SITE.fleet.find(x => !x.generico) || {}).id || SITE.cenIds[0]); };
function stageFoto() {
  const g = $('#stGen'); if (!g) return;
  const on = !!current.generico, f = current.photos[0], im = g.querySelector('img'), tx = g.querySelector('p');
  g.hidden = !on; root.classList.toggle('gen-on', on);
  const lb = on ? 'Ver fotos' : 'Ver por dentro', none = on && !f;
  [['#stInside', 'span'], ['#insideBtn'], ['#infoInside']].forEach(([q, k]) => { const el = $(q); if (!el) return; (k ? el.querySelector(k) : el).textContent = lb; el.hidden = none; });
  if (!on) return;
  im.hidden = !f; tx.hidden = !!f;
  if (f) { const src = `assets/${f[0]}.webp`; if (im.getAttribute('src') !== src) im.src = src; im.alt = `Foto do ${current.name}`; }
  else tx.textContent = `${current.name}: fotos em breve`;
}
"""))
# 2) cartões da viagem
R.append((r"""      <span class="tpc-img"><img src="assets/bus/${bus.side}.webp" alt="" loading="lazy" decoding="async"></span>""",
          r"""      <span class="tpc-img${bus.generico ? ' gen' : ''}">${busImg(bus) ? `<img src="${busImg(bus)}" alt="" loading="lazy" decoding="async">` : ''}</span>"""))
R.append((r"""<span class="pc-tag">${esc(pr.bus[id].tag)}</span><img src="assets/bus/${bus.side}.webp" alt="" loading="lazy" decoding="async"></span>""",
          r"""<span class="pc-tag">${esc((pr.bus[id] || {}).tag || '')}</span>${busImg(bus) ? `<img src="${busImg(bus)}" alt="" loading="lazy" decoding="async">` : ''}</span>"""))
R.append((r"""  const j = id === 'g8' ? 2 : 3, bus = busById(id);
  return (SITE.compare || [])""", r"""  const j = id === 'g8' ? 2 : 3, bus = busById(id);
  if (bus.generico) return bus.chips.map((c, i) => {   // T39: sem a tabela de comparação da TLH, a ficha lista o que o painel publicou
    const inner = `${icon(c[0])}<span><small>${i === 0 && bus.seats ? 'Lugares' : 'A bordo'}</small>${esc(c[1])}</span>`;
    return `<li class="${(c[2] || {}).img ? 'cp' : ''}">${(c[2] || {}).img ? `<button type="button" data-cp="${id}:${i}" aria-haspopup="dialog">${inner}${icon('photos', 'tpc-z')}</button>` : inner}</li>`;
  }).join('');
  return (SITE.compare || [])"""))
R.append((r"""    <ul class="tp-cards" aria-label="Os dois ônibus">${BUS_ORDER().map(pickCardHTML).join('')}</ul>
    <p class="tp-swipe">${icon('swipe')}deslize para ver o outro ônibus</p>
    <p class="tp-both">${esc(SITE.compareBoth || '')} Sem compromisso""", r"""    <ul class="tp-cards" aria-label="${SITE.fleet.length === 2 ? 'Os dois ônibus' : 'Os veículos'}">${BUS_ORDER().map(pickCardHTML).join('')}</ul>
    ${SITE.fleet.length > 1 ? `<p class="tp-swipe">${icon('swipe')}${SITE.fleet.length === 2 ? 'deslize para ver o outro ônibus' : 'deslize para ver os outros'}</p>` : ''}
    <p class="tp-both">${SITE.fleet.length === 2 && !SITE.fleet.some(b => b.generico) ? esc(SITE.compareBoth || '') : ''} Sem compromisso"""))
# 3) troca de ônibus, palco e "ver por dentro"
R.append((r"""  placeInk(); refreshWaLinks(); renderHero(); renderPhotos(); renderOps(); renderPackages();
  if (lastRoute.r)""", r"""  placeInk(); refreshWaLinks(); renderHero(); renderPhotos(); renderOps(); renderPackages(); stageFoto();
  if (lastRoute.r)"""))
R.append((r"""  if (typeof Tour3D !== 'undefined' && Tour3D.isOpen()) { loadShow""", r"""  if (typeof Tour3D !== 'undefined' && Tour3D.isOpen() && !b.generico) { loadShow"""))
R.append((r"""  if (entering) return;
  if (Tour3D.stub) {""", r"""  if (entering) return;
  if (current.generico) {   // T39: sem passeio por dentro ainda: abre as fotos publicadas no painel
    tutDone('tour'); track('tour_open', { bus: current.id, mode: 'fotos' });
    if (current.photos.length) openLightbox(current.photos, 0); return;
  }
  if (Tour3D.stub) {"""))
R.append((r"""bus.chips[idx + 1][1] : 'Ver por dentro';""", r"""bus.chips[idx + 1][1] : bus.generico ? (bus.photos.length ? 'Ver fotos' : 'Fechar') : 'Ver por dentro';"""))
R.append((r"""  renderHero(); renderPhotos(); renderPackages(); renderOps();
}""", r"""  renderHero(); renderPhotos(); renderPackages(); renderOps(); stageFoto();
}"""))
R.append((r"""preImg(`assets/bus/${b.side}.webp`)]);""", r"""...(busImg(b) ? [preImg(busImg(b))] : [])]);"""))
R.append((r"""L.add(`assets/bus/${b.side}.webp`); });""", r"""if (busImg(b)) L.add(busImg(b)); });"""))
R.append((r"""`assets/bus/${current.side}.webp`]);""", r"""busImg(current)]);"""))
R.append((r"""    World.setBus(current.id); activeBlk = null; onScroll(); World.start();""", r"""    World.setBus(sceneBusId(current.id)); activeBlk = null; onScroll(); World.start();"""))
R.append((r"""      World.placeStatic(sc, sb, current.id);
      window.__noGlBus = id => World.placeStatic(sc, sb, id);
      addEventListener('resize', () => World.placeStatic(sc, sb, current.id));""", r"""      const st = id => { World.placeStatic(sc, sb, sceneBusId(id)); if ((busById(id) || {}).generico) sb.hidden = true; };   // T39: veículo sem cenário não mostra o ônibus de outro modelo
      st(current.id);
      window.__noGlBus = st;
      addEventListener('resize', () => st(current.id));"""))
R.append((r"""      $('#scene').appendChild(v); World.placeLoop(v, current.id);
      window.__noGlBus = id => World.placeLoop(v, id);
      addEventListener('resize', () => World.placeLoop(v, current.id));""", r"""      $('#scene').appendChild(v); World.placeLoop(v, sceneBusId(current.id));
      window.__noGlBus = id => World.placeLoop(v, sceneBusId(id));
      addEventListener('resize', () => World.placeLoop(v, sceneBusId(current.id)));"""))
R.append((r"""World.placeStatic($('#scene'), $('#sceneBus'), current.id);
    loadDone""", r"""World.placeStatic($('#scene'), $('#sceneBus'), sceneBusId(current.id));
    loadDone"""))
# 4) a foto no palco
R.append((r"""  <div class="st-veil" aria-hidden="true"></div>
""", r"""  <div class="st-gen" id="stGen" hidden><img alt="" decoding="async"><p hidden></p></div>
  <div class="st-veil" aria-hidden="true"></div>
"""))
R.append(("</head>", """<style>/* T39: veículo sem cenário 3D — a 1ª foto publicada ocupa o palco */
.st-gen{position:absolute;z-index:1;left:0;top:0;width:100%;height:var(--stage-vis);background:#0b1626;display:grid;place-items:center;pointer-events:none;opacity:.999}/* .999: com a foto 100 % opaca por cima, o Chromium deixava de pintar o resto do cenário (ficava preto atrás dos blocos) */
.st-gen[hidden]{display:none}
.st-gen img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;object-position:50% 55%}
.st-gen p{margin:0;padding:0 24px;color:#fff;font-weight:600;font-size:15px;text-align:center}
.tpc-img.gen img{object-fit:cover;width:100%;height:100%;border-radius:12px}
</style>
</head>"""))
# 5) painel: o aviso ao publicar modelo novo (T40) passa a dizer a verdade de agora
PA = pathlib.Path(sys.argv[1]) / "painel.html"; ps = PA.read_text(encoding="utf-8")
pa = '"Publicado no painel: "+nomeOf(v)+". Ele aparece no site quando a TLH terminar as imagens do cenário"+(SRV.on?"; o pedido já está na fila da TLH.":".")'
pb = '"Publicado: "+nomeOf(v)+" já está no site, com a 1ª foto no lugar do ônibus animado. O cenário animado e o passeio por dentro entram quando a TLH terminar as imagens"+(SRV.on?"; o pedido já está na fila da TLH.":".")'
assert ps.count(pa) == 1; PA.write_text(ps.replace(pa, pb), encoding="utf-8", newline="\n")
for old, new in R:
    assert s.count(old) == 1, (s.count(old), old[:70])
    s = s.replace(old, new)
p.write_text(s, encoding="utf-8", newline="\n")
print("T39 aplicado:", len(R), "trocas")
