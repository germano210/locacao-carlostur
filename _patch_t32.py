"""T32: acessibilidade do painel por dentro (axe WCAG 2.1 AA com usuário logado, tema claro e escuro, PC e celular).
Contraste dos selos e botões e a faixa de fotos da prévia alcançável pelo teclado. Uso: python _patch_t32.py site"""
import sys, pathlib
p = pathlib.Path(sys.argv[1]) / "painel.html"; s = p.read_text(encoding="utf-8")
assert "T32" not in s, "já aplicado"
CSS = """<style>/* T32: contraste mínimo 4,5:1 (WCAG 1.4.3) nos selos e botões do painel */
.ep1-sv{color:color-mix(in srgb,var(--ok) 68%,var(--ink))}
.ep1-sv[data-s=ing]{color:color-mix(in srgb,var(--warn) 68%,var(--ink))}
.ep1-pp.pd{background:#8f5200}.ep1-pp.pr{background:#17703f}
.ct-ft .cp,.cp{background:#b83a12;color:#fff}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]) .ep1-b.dg{color:#ff8f82}}
[data-theme=dark] .ep1-b.dg{color:#ff8f82}
.ep1-b.wa,.wa{background:#17753f;border-color:#17753f;color:#fff}
.sp-g:focus-visible,.ct-ac:focus-visible{outline:2px solid var(--acc);outline-offset:2px}
</style>
</head>"""
R = [("</head>", CSS), ('class="sp-g"', 'class="sp-g" tabindex="0" role="group" aria-label="Fotos, como ficam no site"'),
     ('class="ct-ac"', 'class="ct-ac" tabindex="0" role="group" aria-label="Texto do termo (role para ler)"')]
for a, b in R:
    assert s.count(a) == 1, (s.count(a), a); s = s.replace(a, b)
p.write_text(s, encoding="utf-8", newline="\n"); print("T32 aplicado")
