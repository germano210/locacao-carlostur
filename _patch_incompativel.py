"""Pedido do John (17/11): a "versão leve" do site sai. Aparelho sem força para o cenário (pouca memória, poucos núcleos,
sem WebGL2 ou GPU por software) vê só um aviso de incompatível e o WhatsApp da Carlos Tur. A versão leve continua só
dentro do painel (site "ao vivo", ?emb). "Reduzir movimento" (acessibilidade, LBI) e "economia de dados" NÃO bloqueiam:
essas pessoas veem o site inteiro (ele já respeita o reduzir movimento). Uso: python _patch_incompativel.py site"""
import sys, pathlib
S = pathlib.Path(sys.argv[1])
def rep(f, a, b):
    p = S / f; s = p.read_text(encoding="utf-8"); assert s.count(a) == 1, (f, a[:70]); p.write_text(s.replace(a, b), encoding="utf-8", newline="\n")

# 1) decisão logo no começo da página
rep("index.html", """/* Modo leve (17/11): aparelho fraco não carrega o cenário 3D nem o vídeo do topo. */
window.CT_LEVE = (() => {
  try {
    const q = new URLSearchParams(location.search);
    if (q.has('emb')) return true;   // painel v7: o site "ao vivo" dentro do painel vai sempre leve, sem lembrar
    if (q.has('completo')) { localStorage.setItem('ct-leve', '0'); return false; }
    if (q.has('leve')) { localStorage.setItem('ct-leve', '1'); return true; }
    const m = localStorage.getItem('ct-leve'); if (m === '1') return true; if (m === '0') return false;
  } catch (e) { /* sem armazenamento */ }
  const n = navigator, c = n.connection || {};
  if ((n.deviceMemory || 8) <= 2 || (n.hardwareConcurrency || 8) <= 2 || c.saveData) return true;
  if (matchMedia('(prefers-reduced-motion: reduce)').matches) return true;
  try {""", """/* 17/11 (pedido do John): a "versão leve" saiu do site. Aparelho sem força para o cenário vê só o aviso de incompatível
   e o WhatsApp da Carlos Tur (window.CT_INCOMP). O modo leve ficou só para o site "ao vivo" dentro do painel (?emb).
   ?completo força o site inteiro (teste da TLH); ?leve mostra o aviso. */
window.CT_INCOMP = false;
window.CT_LEVE = (() => {
  try {
    const q = new URLSearchParams(location.search);
    if (q.has('emb')) return true;   // painel v7: o site "ao vivo" dentro do painel vai sempre leve, sem lembrar
    if (q.has('completo')) { localStorage.setItem('ct-leve', '0'); return false; }
    if (q.has('leve')) { window.CT_INCOMP = true; return true; }
    const m = localStorage.getItem('ct-leve'); if (m === '1') localStorage.removeItem('ct-leve'); if (m === '0') return false;   // quem escolheu "Versão leve" antes não fica preso no aviso
  } catch (e) { /* sem armazenamento */ }
  const n = navigator, incomp = () => { window.CT_INCOMP = true; return true; };
  if ((n.deviceMemory || 8) <= 2 || (n.hardwareConcurrency || 8) <= 2) return incomp();
  try {""")
rep("index.html", """    const g = document.createElement('canvas').getContext('webgl2'); if (!g) return true;""",
    """    const g = document.createElement('canvas').getContext('webgl2'); if (!g) return incomp();""")
rep("index.html", """    if (/swiftshader|llvmpipe|software|basic render|gma/i.test(r)) return true;   // GPU por software ou muito antiga
  } catch (e) { return true; }
  return false;
})();
if (window.CT_LEVE) document.documentElement.classList.add('leve');
</script>""", """    if (/swiftshader|llvmpipe|software|basic render|gma/i.test(r)) return incomp();   // GPU por software ou muito antiga
  } catch (e) { return incomp(); }
  return false;
})();
if (window.CT_LEVE) document.documentElement.classList.add('leve');
if (window.CT_INCOMP) {
  document.documentElement.classList.add('incomp');
  // o script principal do site não roda (ver o começo dele); este aviso ignora só esse erro proposital
  addEventListener('error', e => { if (String(e.message || '').indexOf('CT_INCOMP') >= 0) e.preventDefault(); });
  document.addEventListener('DOMContentLoaded', () => {
    let wa = '5551997976191';
    try { const d = String(((window.CT_PUB || {}).empresa || {}).wa || '').replace(/\\D/g, '').replace(/^55(?=\\d{10,11}$)/, ''); if (d.length === 10 || d.length === 11) wa = '55' + d; } catch (e) { /* sem dados */ }
    const href = 'https://wa.me/' + wa + '?text=' + encodeURIComponent('Olá, Carlos Tur! Vim pelo site e quero um orçamento de fretamento.');
    const m = document.createElement('main'); m.id = 'incomp'; m.setAttribute('aria-labelledby', 'incompT');
    m.innerHTML = '<div class="ic-box"><svg class="ic-wm" viewBox="0 0 1339.3 100" role="img" aria-label="Carlos Tur"><use href="#wmSymbolPath" clip-path="url(#wmClip)" fill="none" stroke="currentColor" stroke-width="23" stroke-linejoin="miter" stroke-miterlimit="3"/></svg>'
      + '<h1 id="incompT">Notamos que seu dispositivo é incompatível com nossa idealização.</h1><p>Tente novamente em outro dispositivo.</p>'
      + '<a class="ic-wa" href="' + href + '" target="_blank" rel="noopener">Falar com a Carlos Tur no WhatsApp</a>'
      + '<nav class="ic-leg" aria-label="Informações"><a href="privacidade.html">Privacidade</a><a href="termos.html">Termos de uso</a></nav></div>';
    document.body.prepend(m);
    m.querySelector('.ic-wa').addEventListener('click', () => {   // conta o contato no painel, sem nome, número ou IP (como os outros botões)
      try { navigator.sendBeacon && navigator.sendBeacon('api/evento', new Blob([JSON.stringify({ tipo: 'wa', destino: '', dados: { f: 'incompativel' } })], { type: 'application/json' })); } catch (e) { /* sem servidor */ }
    });
  });
}
</script>
<style>
html.incomp, html.incomp body { overflow: auto !important; background: #0b1626; }
html.incomp body > *:not(#incomp):not(svg) { display: none !important; }
#incomp { min-height: 100vh; min-height: 100svh; display: grid; place-items: center; padding: 24px 18px; box-sizing: border-box; background: #0b1626 url(assets/scene3/plate23-lo.webp) center / cover no-repeat; font-family: Poppins, system-ui, sans-serif; }
#incomp .ic-box { width: min(100%, 420px); background: #fff; color: #0b0b0c; border-radius: 24px; padding: 26px 22px 20px; display: grid; gap: 14px; text-align: center; box-shadow: 0 24px 60px rgba(0, 0, 0, .35); }
#incomp .ic-wm { width: 180px; height: auto; justify-self: center; color: #0b0b0c; }
#incomp h1 { margin: 4px 0 0; font-size: 19px; line-height: 1.35; font-weight: 600; }
#incomp p { margin: 0; font-size: 15px; color: #3d3d42; }
#incomp .ic-wa { display: block; margin-top: 6px; padding: 15px 18px; border-radius: 999px; background: #17753f; color: #fff; font-weight: 600; font-size: 16px; text-decoration: none; }
#incomp .ic-wa:focus-visible { outline: 3px solid #0b0b0c; outline-offset: 3px; }
#incomp .ic-leg { display: flex; justify-content: center; gap: 16px; font-size: 13px; }
#incomp .ic-leg a { color: #3d3d42; }
</style>""")
# 2) o script principal não roda no aparelho incompatível (nada de cenário, mapa ou fotos)
rep("index.html", """<script src="api/site.js"></script>
<script>
""", """<script src="api/site.js"></script>
<script>
if (window.CT_INCOMP) throw new Error('CT_INCOMP: aparelho incompatível, só o aviso e o WhatsApp');
""")
# 3) rodapé: sai o "Versão leve" / "Versão completa"
rep("index.html", """${window.CT_LEVE ? '<a href="?completo">Versão completa</a>' : '<a href="?leve">Versão leve</a>'}""", "")
# 4) guia do Carlos
rep("guia-painel.html", "<li>Computador antigo ficou lento? No rodapé do site, toque em <b>Versão leve</b>.</li>",
    "<li>Computador ou celular muito antigo: o site mostra um aviso de incompatível com o botão do WhatsApp da Carlos Tur. O painel funciona normalmente nele.</li>")
print("ok: aviso de incompatível no lugar da versão leve")
