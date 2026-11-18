"""T53 (painel do artefato 9HaJSD): a tela de entrar do painel põe o site em modo ?cena atrás dela (cenário vivo).
No servidor o site vai com ?emb (versão leve, foto parada) para não pesar no PC fraco. Uso: python _patch_t53_painel.py site"""
import sys, pathlib
S = pathlib.Path(sys.argv[1])
def rep(f, a, b):
    p = S / f; s = p.read_text(encoding="utf-8"); assert s.count(a) == 1, (f, s.count(a), a[:70]); p.write_text(s.replace(a, b), encoding="utf-8", newline="\n")
rep("painel.html", 'addEventListener("message",b._ms);b._rs=()=>band();addEventListener("resize",b._rs);}',
    'addEventListener("message",b._ms);b._rs=()=>band();addEventListener("resize",b._rs);SITEP.then((u=>{if(!u||!document.getElementById("gtSite"))return;const src=u+(u.indexOf("?")<0?"?":"&")+"cena";b.innerHTML=\'<iframe title="" tabindex="-1" aria-hidden="true" src="\'+src+\'"></iframe>\';const f=b.firstChild;f.addEventListener("load",(()=>{band();setTimeout(band,400)}));setTimeout(show,12e3)}))}')
# o site leve (dentro do painel) também avisa que o cenário está pronto
rep("index.html", """      addEventListener('resize', () => st(current.id));
      loadDone($('#stLoad'));""", """      addEventListener('resize', () => st(current.id));
      toParent({ cena: 'ok', modo: 'foto' });   // T53: fundo do login do painel
      loadDone($('#stLoad'));""")
rep("index.html", "    if (window.CT_LEVE && typeof World !== 'undefined' && World.placeStatic) {   // ?emb (site dentro do painel): imagem parada, leve", "    if (window.CT_LEVE && !CENA && typeof World !== 'undefined' && World.placeStatic) {   // ?emb (site dentro do painel): imagem parada, leve; no fundo do login (?cena), o vídeo do cenário")
print("T53 painel aplicado")
