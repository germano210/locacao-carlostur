"""T49 (site do artefato 9HaJSD, 17/11): "Ideias de roteiro para fretar" vêm só do painel, sem roteiros iniciais.
O bloco some até o Carlos ligar um roteiro no painel; cartão com crédito da foto; sem a nota "Exemplo".
Uso: python _patch_t49.py site   (também ajusta app/app.py: /api/site manda roteiros = [] quando o painel ainda não tem)"""
import sys, pathlib
S = pathlib.Path(sys.argv[1]); APP = S.parent / "app" / "app.py"
def rep(p, a, b):
    s = p.read_text(encoding="utf-8"); assert s.count(a) == 1, (p.name, s.count(a), a[:70]); p.write_text(s.replace(a, b), encoding="utf-8", newline="\n")
I, P = S / "index.html", S / "painel.html"
assert "T49" not in I.read_text(encoding="utf-8"), "já aplicado"
# CSS do crédito no cartão (artefato)
rep(I, "html.incomp, html.incomp body {", ".pk-cred { position: absolute; right: 8px; bottom: 6px; z-index: 2; max-width: 80%; font-size: 9px; line-height: 1.2; color: #fff; opacity: .8; text-shadow: 0 1px 2px rgba(0,0,0,.7); text-align: right; pointer-events: none; }   /* T49 */\nhtml.incomp, html.incomp body {")
# sem a nota "Exemplo" dos roteiros
rep(I, """    <p class="ex-note" id="pkEx"><span class="tag-ex">Exemplo</span><span>Ideias para inspirar. O grupo monta o roteiro e a Carlos Tur faz o orçamento do fretamento no WhatsApp.</span></p>
""", "")
rep(I, "  $('#pkEx').hidden = !SITE.packages.some(p => p.ex);\n", "")
# roteiros do painel: no servidor sempre vêm do painel (lista vazia = bloco escondido)
rep(I, """  // painel v7: roteiros ligados na aba "Roteiros" do painel substituem os do site (sem a aba, ficam os do site)
  if (Array.isArray(P.roteiros)) {""", """  // T49: os roteiros vêm só do painel (os ligados); sem nenhum ligado, o bloco "Ideias de roteiro" some
  if (Array.isArray(P.roteiros)) {""")
rep(I, """        img: r.img || o.img || '', src: r.src || '', kind: KD[r.kind] || o.kind || 'cidade', ex: o.ex };
    });
  }""", """        img: r.img || o.img || '', src: r.src || '', cred: r.src ? r.cred || '' : '', kind: KD[r.kind] || o.kind || 'cidade', painel: true };
    });
    SITE.rtPainel = true; SITE.vars.roteiros = SITE.packages.length > 0;
  }""")
# no servidor (api/site.js carregou), começa sem roteiros mesmo que o painel ainda não tenha salvo nada
rep(I, """// 11/11: no protótipo (site e painel no mesmo endereço), o site segue a ordem e as exclusões publicadas no painel.""",
       """if (window.CT_PUB !== undefined) { SITE.packages = []; SITE.rtPainel = true; SITE.vars.roteiros = false; }   // T49: no ar, roteiros só do painel
// 11/11: no protótipo (site e painel no mesmo endereço), o site segue a ordem e as exclusões publicadas no painel.""")
# renderPackages: com roteiros do painel, sem abas nem sugestões montadas (artefato)
rep(I, """  $('#sPkgs').hidden = false;
  const dk = RouteMap.dest && !RouteMap.isStop(RouteMap.dest) ? RouteMap.dest : null, dll = dk ? RouteMap.ll(dk) : null;""",
"""  $('#sPkgs').hidden = false;
  if (SITE.rtPainel) {   // T49: só os roteiros do painel, sem as abas e sem sugestões montadas
    pkTab = 'grupo'; { const sg = $('#pkSeg'); if (sg) sg.hidden = true; } $('#pkTitle').textContent = 'Ideias de roteiro para fretar'; PKX = [];
    SITE.packages.forEach(p => { const r = RouteMap.find(p.dest); if (!r) return; p.kind = { praia: 'praia', serra: 'serra', neve: 'serra', parque: 'parque' }[RouteMap.kind(r.key)] || p.kind || 'cidade';
      if (!p.img && !p.src) { const d = PL[r.key]; if (d && d.h && d.h[0]) p.src = `assets/ilus/${d.h[0].il}.webp`; } });
  }
  const dk = RouteMap.dest && !RouteMap.isStop(RouteMap.dest) ? RouteMap.dest : null, dll = dk ? RouteMap.ll(dk) : null;""")
rep(I, "  PKX = dk && pkTab === 'grupo' && !list.some(p => distTo(p) < 15) ? [destPkg(dk)] : [];",
       "  PKX = SITE.rtPainel ? [] : dk && pkTab === 'grupo' && !list.some(p => distTo(p) < 15) ? [destPkg(dk)] : [];")
rep(I, "  $('#pkTitle').textContent = dk ? `Ideias para ${RouteMap.short(dk)}` : 'Ideias de roteiro para fretar';",
       "  if (!SITE.rtPainel) $('#pkTitle').textContent = dk ? `Ideias para ${RouteMap.short(dk)}` : 'Ideias de roteiro para fretar';")
rep(I, """      <div class="pk-img">${img}<div class="pk-top">""", """      <div class="pk-img">${img}${p.cred && img ? `<small class="pk-cred">${esc(p.cred)}</small>` : ''}<div class="pk-top">""")
# painel: no servidor começa sem roteiros (o Carlos cadastra); no protótipo segue o do artefato
rep(P, 'D.roteiros=RSEED().map((r=>(SRV.on&&(r.site=true,r.src="assets/dest/"+r.img+".webp"),r)))', 'D.roteiros=SRV.on?[]:RSEED()')
# servidor: painel sem a lista ainda = nenhum roteiro no site
rep(APP, '''    L = D.get("roteiros")
    if not isinstance(L, list):
        return None''', '''    L = D.get("roteiros")
    if not isinstance(L, list):
        return []  # T49: sem roteiro cadastrado no painel, o site não mostra nenhum''')
rep(APP, '''    """Painel v7: roteiros ligados no painel ("no site"); None = o painel ainda não tem a aba e o site usa os dele."""''',
         '''    """Painel v7 + T49: só os roteiros ligados no painel ("no site"); sem nenhum, o site esconde o bloco."""''')
print("T49 aplicado")
