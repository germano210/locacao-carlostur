"""T54 (pedido do John, 18/11): sem roteiros de exemplo no código. O site e o painel começam sem nenhum roteiro;
o Carlos cadastra no painel (aba Roteiros). Uso: python _patch_t54.py site"""
import sys, pathlib, re
S = pathlib.Path(sys.argv[1])
I = S / "index.html"; s = I.read_text(encoding="utf-8")
i = s.index("  packages: ["); j = s.index("\n  ],", i) + len("\n  ],")
assert "titulo:" in s[i:j] and s.count("  packages: [") == 1
s = s[:i] + "  packages: [],   // T54: sem roteiros de exemplo; vêm do painel (aba Roteiros)" + s[j:]
a = "vars: { roteiros: true, "; assert s.count(a) == 1; s = s.replace(a, "vars: { roteiros: false, ")   # o bloco só aparece com roteiro do painel
I.write_text(s, encoding="utf-8", newline="\n")
P = S / "painel.html"; p = P.read_text(encoding="utf-8")
k = p.index("function RSEED(){return["); e = p.index("}]}", k) + 3
assert p.count("function RSEED(){return[") == 1 and "titulo:" in p[k:e]
p = p[:k] + "function RSEED(){return[]}" + p[e:]
P.write_text(p, encoding="utf-8", newline="\n")
print("T54 aplicado")
