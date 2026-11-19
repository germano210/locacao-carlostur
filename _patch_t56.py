"""T56 (18/11): título e descrição com o que as pessoas buscam (fretamento de ônibus, excursão, turismo, Carlos Tur, cidade).
Rodar depois do _patch_t55.py."""
import sys
f = sys.argv[1] if len(sys.argv) > 1 else "site/index.html"
s = open(f, encoding="utf-8").read()
R = [
    ("<title>Carlos Tur | Fretamento e turismo de ônibus</title>",
     "<title>Carlos Tur · Fretamento de ônibus e turismo | Santo Antônio da Patrulha, RS</title>"),
    ('<meta name="description" content="Veja o ônibus da Carlos Tur, a rota real até o destino, roteiros prontos e monte o orçamento da viagem do seu grupo direto no WhatsApp.">',
     '<meta name="description" content="Fretamento de ônibus para excursões e turismo em grupo com a Carlos Tur, de Santo Antônio da Patrulha (RS). Veja o ônibus por dentro, a rota e peça o orçamento no WhatsApp.">'),
    ('<meta property="og:description" content="Ônibus inteiro para o seu grupo. Orçamento no WhatsApp.">',
     '<meta property="og:description" content="Fretamento de ônibus para o seu grupo. Orçamento no WhatsApp.">'),
]
for a, b in R:
    assert s.count(a) == 1, a[:60]
    s = s.replace(a, b)
open(f, "w", encoding="utf-8").write(s)
print("ok T56")
