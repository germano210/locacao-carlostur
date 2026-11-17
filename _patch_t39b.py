"""T39b (pedido do John, 17/11): modelo novo NÃO entra sozinho no site. Vai primeiro para a fila /tlh; só aparece
depois que a TLH conferir e fizer as imagens no padrão dos outros ônibus (id em SITE.fleet). O código da T39 fica
no index, desligado por SITE.vars.generico = false. Aplicar depois do _patch_t39.py. Uso: python _patch_t39b.py site"""
import sys, pathlib
S = pathlib.Path(sys.argv[1])
def rep(f, a, b):
    p = S / f; s = p.read_text(encoding="utf-8"); assert s.count(a) == 1, (f, a[:60]); p.write_text(s.replace(a, b), encoding="utf-8", newline="\n")
rep("index.html", "vars: { roteiros: true, preco: false, emdia: false },", "vars: { roteiros: true, preco: false, emdia: false, generico: false },   // T39b: generico = mostrar modelo sem cenário (com a foto); desligado: só entra depois da TLH")
rep("index.html", "    if (!v || !v.pub || SITE.cenIds.includes(v.id)", "    if (!SITE.vars.generico || !v || !v.pub || SITE.cenIds.includes(v.id)")
rep("painel.html", '"Publicado: "+nomeOf(v)+" já está no site, com a 1ª foto no lugar do ônibus animado. O cenário animado e o passeio por dentro entram quando a TLH terminar as imagens"+(SRV.on?"; o pedido já está na fila da TLH.":".")',
    '"Publicado no painel: "+nomeOf(v)+". Ele entra no site depois que a TLH conferir e fizer as imagens no padrão dos outros ônibus"+(SRV.on?"; o pedido já está na fila da TLH.":".")')
rep("guia-painel.html", "Ele entra no site na hora, com a 1ª foto no lugar do ônibus animado (capriche nela); o cenário animado e o passeio por dentro entram quando a Loud House terminar as imagens.",
    "Ele entra no site depois que a Loud House conferir e fizer as imagens no padrão dos outros ônibus.")
print("T39b aplicado (o filtro do servidor fica em app/app.py, função publico)")
