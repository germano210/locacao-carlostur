"""T55 (18/11): robô de busca (Google, Bing, Lighthouse...) não cai no aviso de incompatível.
O Google lê o site com placa de vídeo por software e cairia no aviso, que esconde todo o texto.
O robô vê o site em modo leve (o mesmo conteúdo, com a foto do cenário no lugar do 3D). Rodar depois do _patch_t54.py."""
import sys
f = sys.argv[1] if len(sys.argv) > 1 else "site/index.html"
s = open(f, encoding="utf-8").read()
A = "  const n = navigator, incomp = () => { window.CT_INCOMP = true; return true; };\n"
B = ("  if (/googlebot|google-inspectiontool|bingbot|adidxbot|duckduckbot|yandex|baiduspider|applebot|petalbot|slurp|lighthouse|\\bbot\\b|bot\\/|crawler|spider/i.test(navigator.userAgent || '')) return true;   // T55: robô de busca vê o site leve, nunca o aviso\n")
assert s.count(A) == 1, "trecho do CT_LEVE mudou"
assert "T55:" not in s, "já aplicado"
s = s.replace(A, B + A)
open(f, "w", encoding="utf-8").write(s)
print("ok T55")
