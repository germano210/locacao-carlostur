"""T58 (18/11): "Ver por dentro" e "Contato rápido" sem estourar o cartão no celular.
Antes: duas colunas fixas (1fr 1fr) com texto sem quebra; em tela de 360 px ou menos, ou com a fonte do celular
aumentada, o "Contato rápido" passava da borda. Agora: lado a lado quando cabem; quando não cabem, um embaixo do outro,
cada um na largura toda. Rodar depois do _patch_t56.py."""
import sys
f = sys.argv[1] if len(sys.argv) > 1 else "site/index.html"
s = open(f, encoding="utf-8").read()
A = ".hero-cta > * { margin: 0; min-width: 0; }\n"
B = (".hero-cta > * { margin: 0; min-width: 0; }\n"
     "/* T58: lado a lado quando cabem; senão um embaixo do outro (tela estreita ou fonte do celular aumentada) */\n"
     ".hero-cta { display: flex; flex-wrap: wrap; }\n"
     ".hero-cta .pill-ghost svg { width: clamp(18px, 5vw, 21px); height: clamp(18px, 5vw, 21px); }\n"
     ".hero-cta > .pill { flex: 1 1 0; min-width: max-content; max-width: 100%; padding-inline: clamp(10px, 3vw, 16px); gap: 8px; font-size: clamp(13px, 3.7vw, 15px); }\n")
assert s.count(A) == 1, "bloco 12u mudou"
assert "T58:" not in s, "já aplicado"
s = s.replace(A, B)
open(f, "w", encoding="utf-8").write(s)
print("ok T58")
