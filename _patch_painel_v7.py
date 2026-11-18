"""Painel novo (artefato "Painel CarlosTur", v7: frota em fotos, cadastro passo a passo, roteiros, site ao vivo) com o
que o painel do Git já tinha para rodar no servidor: login por e-mail + termo, salvar na API, fotos/vídeo/logo pela API,
contatos, sair, sugestão, fontes locais, favicon, noindex, acessibilidade (T32) e a regra de verificação da TLH (T39b).
Uso: python _patch_painel_v7.py ARTEFATO.html site/painel.html   (lê o painel atual do Git para copiar as partes do servidor)"""
import sys, pathlib, re
ART, OUT = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
a = ART.read_text(encoding="utf-8"); p = OUT.read_text(encoding="utf-8")
assert "const SRV=" not in a, "o artefato já tem servidor?"
assert "const SRV=" in p and "/* servidor: termo" in p, "rode sobre o painel do Git (com servidor)"

def cut(s, ini, fim, incl_fim=True):
    i = s.index(ini); j = s.index(fim, i + len(ini)); return s[i:j + (len(fim) if incl_fim else 0)]

def rep(old, new, n=1):
    global a
    c = a.count(old); assert c == n, (c, old[:90]); a = a.replace(old, new)

# ---------- 1) cabeçalho: idioma, noindex, título, fontes locais (sem Google), favicon ----------
head_art = a[:a.index('<link rel="stylesheet" href="https://fonts.googleapis.com')]
boiler = cut(head_art, "<style>:root{color-scheme:light", "</style>")
fim_gf = a.index(">", a.index('<link rel="stylesheet" href="https://fonts.googleapis.com')) + 1
a = ('<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
     '<meta name="robots" content="noindex,nofollow"><title>Painel CarlosTur</title>\n' + boiler +
     '\n<link rel="stylesheet" href="fonts/painel-fontes.css">' + a[fim_gf:])
# estilos do servidor (termo, avisos), favicon e T32 entram antes do <body>
srv_css = cut(p, "<style>/* servidor: termo", "</style>")
fav = "".join(re.findall(r'<link rel="(?:icon|apple-touch-icon)"[^>]*>\n?', p))
t32 = cut(p, "<style>/* T32", "</style>")
t32 = t32.replace("</style>", ".ep1-mvs button{color:#111}\n</style>")
svg0 = '<svg width="0" height="0" style="position:absolute" aria-hidden="true">'
i = a.index(svg0)
a = a[:i].rstrip("\n") + "\n" + srv_css + "\n" + fav + t32 + "\n</head><body>" + a[i:]

# ---------- 2) fotos de exemplo: img/ -> assets/ (pasta do site no servidor) ----------
a = re.sub(r'\bimg/(g8|b2501)-', r'assets/\1-', a)

# ---------- 3) login: no servidor, e-mail + senha temporária -> senha nova -> termo (o protótipo continua igual) ----------
gate_srv = cut(p, "let tmpPw=\"\";async function srvEntrar", "function aceite(){", incl_fim=False)
aceite = cut(p, "function aceite(){", "if(SRV.on&&SRV.eu)segue();", incl_fim=False)
s_entrar = ('function sEntrar(){host.innerHTML=box(\'<form class="ct-gf" novalidate><h5>Entrar</h5>\'+\'<label class="ep1-f"><span class="ep1-l">E-mail</span>'
            '<input class="ep1-in" type="email" autocomplete="username" placeholder="voce@carlostur.com.br" required></label>\'+\'<label class="ep1-f"><span class="ep1-l">Senha'
            '<small>Na primeira vez, use a senha temporária que a TLH mandou.</small></span><input class="ep1-in" type="password" autocomplete="current-password" required></label>\''
            '+\'<button type="submit" class="ep1-b pri big">Entrar</button><button type="button" class="ep1-b ct-esq">Esqueci a senha</button><p class="ct-gm" role="status" aria-live="polite"></p></form>\');'
            'const f=host.querySelector(".ct-gf"),[em,pw]=f.querySelectorAll("input");f.onsubmit=e=>{e.preventDefault();srvEntrar(em.value,pw.value)};'
            'host.querySelector(".ct-esq").onclick=()=>msg("Fale com a TLH: ela gera uma senha temporária nova para o seu e-mail.");em.focus()}'
            'function sCriar(){host.innerHTML=box(\'<form class="ct-gf" novalidate><h5>Crie a sua senha</h5><small class="ep1-h">A senha temporária vale só para esta primeira entrada.</small>\''
            '+\'<label class="ep1-f"><span class="ep1-l">Senha nova<small>10 ou mais caracteres.</small></span><input class="ep1-in" type="password" autocomplete="new-password" required></label>\''
            '+\'<label class="ep1-f"><span class="ep1-l">Repita a senha</span><input class="ep1-in" type="password" autocomplete="new-password" required></label>\''
            '+\'<p class="ct-gm" role="status" aria-live="polite"></p><button type="submit" class="ep1-b pri big">Salvar e entrar</button></form>\');'
            'const f=host.querySelector(".ct-gf"),[x,y]=f.querySelectorAll("input");f.onsubmit=e=>{e.preventDefault();if(x.value.length<10){msg("Use 10 ou mais caracteres.");x.focus();return}'
            'if(x.value!==y.value){msg("As duas senhas não são iguais.");y.focus();return}srvSenha(x.value)};x.focus()}')
srv_fns = (gate_srv.replace("if(tmpPw)criar();else entrar()", "if(tmpPw)sCriar();else sEntrar()")
           .replace("SRV.carregado=true;ok()", "SRV.carregado=true;seguir()") + aceite)
assert "sCriar()" in srv_fns and "seguir()" in srv_fns
# confere se o formulário do artefato usa a mesma "caixa" de mensagem
assert '.ct-gm' in a
rep("if(!A.login)criar();else entrar()}const LS=",
    s_entrar + srv_fns + "if(SRV.on){if(SRV.eu)segue();else sEntrar();return}if(!A.login)criar();else entrar()}" +
    cut(p, "const SRV=(()=>{", "return S})();") + "\nconst LS=")
# o termo (aceite) do painel do Git usa o box(); o box do artefato tem o mesmo nome

# ---------- 4) dados: defaults numa função (o servidor chama de novo depois de carregar) ----------
rep('if(!D||!Array.isArray(D.frota))D=SEED();if(!Array.isArray(D.roteiros))D.roteiros=RSEED();const EMP0=',
    'if(!D||!Array.isArray(D.frota))D=SEED();const EMP0=')
rep('if(!D.acesso)D.acesso={temp:true};if(!Array.isArray(D.ordemPub))D.ordemPub=D.frota.filter((v=>v.pub)).map((v=>v.id));',
    'function norm(){if(!Array.isArray(D.roteiros))D.roteiros=RSEED().map((r=>(SRV.on&&(r.site=true,r.src="assets/dest/"+r.img+".webp"),r)));if(!D.empresa){D.empresa=Object.assign({},EMP0);D.empresa.pub=Object.assign({},EMP0)}'
    'if(!D.acesso)D.acesso={temp:true};if(!Array.isArray(D.contatos))D.contatos=[];if(!Array.isArray(D.ordemPub))D.ordemPub=D.frota.filter((v=>v.pub)).map((v=>v.id))}norm();')
rep('if(!D.empresa){D.empresa=Object.assign({},EMP0);D.empresa.pub=Object.assign({},EMP0)}function norm(){', 'function norm(){')
# roteiros que já estão no site hoje (no servidor entram ligados; no protótipo, desligados como no artefato)
rep('img:"poa",site:false}]}',
    'img:"poa",site:false},{id:"r5",titulo:"Natal Luz em Gramado",dest:"Gramado",dur:"Bate e volta",inclui:["Cidade iluminada e desfiles","Ingressos dos shows à parte","Volta no mesmo dia"],img:"gramado-natal",site:false},'
    '{id:"r6",titulo:"Beto Carrero World",dest:"Beto Carrero",dur:"2 a 3 dias",inclui:["Ônibus leito ida e volta","Pernoite em Penha (opcional)","Parada em Florianópolis"],img:"beto",site:false},'
    '{id:"r7",titulo:"Fim de semana em Torres",dest:"Torres",dur:"2 dias",inclui:["Guarita e Parque da Itapeva","Pousada perto do mar (opcional)","Ônibus à disposição do grupo"],img:"torres",site:false}]}')
rep('function store(){try{localStorage.setItem(LS,JSON.stringify(D));return true}catch(e){return false}}',
    'function store(){if(SRV.on){SRV.save();return true}try{localStorage.setItem(LS,JSON.stringify(D));return true}catch(e){return false}}')
rep('let entrou=false;try{entrou=sessionStorage.getItem(IN)==="1"}catch(e){}',
    'let entrou=false;if(SRV.on)entrou=!!(SRV.eu&&!SRV.eu.temp&&!SRV.eu.aceite&&SRV.carregado);else try{entrou=sessionStorage.getItem(IN)==="1"}catch(e){}')
rep('const PN=mountPainel($("#pn"));',
    'let PN=null;(async()=>{await SRV.boot();if(SRV.on&&SRV.eu&&!SRV.eu.temp&&!SRV.eu.aceite){try{await SRV.load();SRV.carregado=true}catch(e){}}PN=mountPainel($("#pn"))})();')
rep("document.addEventListener('click',function(e){var a=", "document.addEventListener('click',function(e){if(typeof SRV!=='undefined'&&SRV.on)return;var a=")

# ---------- 5) fotos, vídeo e logo sobem pela API (no protótipo seguem no navegador) ----------
UP = ('function upFotos(t,v,fim){const fs=[...t.files||[]].slice(0,12);t.value="";if(!fs.length)return;SRV.aviso("Enviando "+fs.length+(fs.length>1?" fotos…":" foto…"),true);'
      'Promise.all(fs.map((f=>SRV.foto(f)))).then((us=>{us.forEach((u=>v.fotos.push({s:u,l:""})));SRV.aviso("Fotos enviadas.",true);fim()})).catch((er=>SRV.aviso(er.message)))}'
      'function upVideo(t,v,fim){const f=t.files&&t.files[0];t.value="";if(!f)return;SRV.aviso("Enviando o vídeo… 0%",true,"");'
      'SRV.video(f,nomeOf(v),(p=>SRV.aviso("Enviando o vídeo… "+Math.round(p*100)+"% (não feche esta tela)",true,""))).then((()=>{SRV.aviso("Vídeo recebido. A TLH trata e avisa quando o passeio estiver pronto.",true);v.passeio="recebido";fim()})).catch((er=>SRV.aviso(er.message)))}\nconst LS=')
UP = UP.replace("\nconst LS=", "")
rep('if(t.dataset.a==="up"){[...t.files].slice(0,12).forEach((f=>v.fotos.push({s:URL.createObjectURL(f),l:""})));save(true);qed()}',
    'if(t.dataset.a==="up"){if(SRV.on){upFotos(t,v,(()=>{save(true);qed()}));return}[...t.files].slice(0,12).forEach((f=>v.fotos.push({s:URL.createObjectURL(f),l:""})));save(true);qed()}')
rep('else if(t.dataset.a==="up"){[...t.files].slice(0,12).forEach((f=>v.fotos.push({s:URL.createObjectURL(f),l:""})));chg(v,true);editor()}else if(t.dataset.a==="vid"){if(t.files&&t.files[0]){v.passeio="recebido";chg(v,true);editor()}}',
    'else if(t.dataset.a==="up"){if(SRV.on){upFotos(t,v,(()=>{chg(v,true);editor()}));return}[...t.files].slice(0,12).forEach((f=>v.fotos.push({s:URL.createObjectURL(f),l:""})));chg(v,true);editor()}'
    'else if(t.dataset.a==="vid"){if(SRV.on){upVideo(t,v,(()=>{chg(v,true);editor()}));return}if(t.files&&t.files[0]){v.passeio="recebido";chg(v,true);editor()}}')
rep('if(t.dataset.up==="vid"){if(t.files&&t.files[0]){v.passeio="recebido";re()}return}if(t.dataset.up){',
    'if(t.dataset.up==="vid"){if(SRV.on){upVideo(t,v,re);return}if(t.files&&t.files[0]){v.passeio="recebido";re()}return}'
    'if(t.dataset.up&&SRV.on){const lado=t.dataset.up==="lado";if(lado){const f=t.files&&t.files[0];t.value="";if(!f)return;SRV.aviso("Enviando a foto…",true);'
    'SRV.foto(f).then((u=>{v.cena={s:u,st:"conf",at:Date.now()};SRV.aviso("Foto enviada. A TLH confere.",true);re()})).catch((er=>SRV.aviso(er.message)));return}upFotos(t,v,re);return}if(t.dataset.up){')
rep('const r=new FileReader;r.onload=()=>{E.logo=String(r.result);save(true);conf()};r.readAsDataURL(f)};',
    'if(SRV.on){SRV.foto(f,"logo").then((u=>{E.logo=u;save(true);conf()})).catch((er=>SRV.aviso(er.message)));return}const r=new FileReader;r.onload=()=>{E.logo=String(r.result);save(true);conf()};r.readAsDataURL(f)};')

# ---------- 6) Empresa: senha (10+ no servidor), sair, sugestão ----------
rep('if(b.value.length<6){m.textContent="A senha nova tem 6 ou mais caracteres.";',
    'if(b.value.length<(SRV.on?10:6)){m.textContent="A senha nova tem "+(SRV.on?10:6)+" ou mais caracteres.";')
srv_senha = cut(p, 'if(SRV.on){m.textContent="Trocando…";', 'm.textContent=er.message}));')
i = a.index('if(b.value.length<(SRV.on?10:6))'); j = a.index("return}", a.index("As duas", i) if "As duas" in a[i:i+600] else i + 120)
# insere logo depois da última conferência da troca de senha
k = a.index('return}', a.index('c.value', i)) + len('return}')
a = a[:k] + srv_senha + "return}" + a[k:]
rep('q("#ctSair",body).onclick=()=>{try{sessionStorage.removeItem(IN)}',
    'q("#ctSair",body).onclick=()=>{if(SRV.on){SRV.api("POST","api/sair",{}).catch((()=>{})).finally((()=>location.reload()));return}try{sessionStorage.removeItem(IN)}')
srv_sug = cut(p, 'if(SRV.on){SRV.api("POST","api/sugestao"', 'm.textContent=er.message}));') + "return}"
k = a.index('if(!db){m.textContent="Por enquanto')
a = a[:k] + srv_sug + a[k:]
for s in ('"10 ou mais"', 'Senha nova<small>6 ou mais caracteres.</small>'):
    pass
rep("6 ou mais caracteres.</small>", "'+(SRV.on?10:6)+' ou mais caracteres.</small>")
# suporte da TLH: o número da TLH (no artefato ficou o da Carlos Tur por engano)
rep("Número: <b>(51) 99797-6191</b>", "Número: <b>(51) 99952-2296</b>")
rep("https://wa.me/5551997976191?text='+encodeURIComponent(\"Oi, TLH!", "https://wa.me/5551999522296?text='+encodeURIComponent(\"Oi, TLH!")

# ---------- 7) T39b: modelo novo passa pela TLH antes de ir ao site ----------
CEN = 'const CEN=()=>(SRV.on&&SRV.eu&&SRV.eu.cenario)||["g8","b2501"];const pubMsg=(v,nv)=>!CEN().includes(v.id)?"Publicado no painel. Ele entra no site depois que a TLH conferir e fizer as imagens no padrão dos outros ônibus"+(SRV.on?"; o pedido já está na fila da TLH.":"."):nv?"Publicado: "+nomeOf(v)+" já está no site.":"Publicado: o site já mostra as mudanças.";'
i = a.index("const nomeOf=", a.index("function mountPainel(host){")); j = a.index(";", a.index("=>", i)) + 1
assert a[i:j].count("const nomeOf=") == 1, a[i:j]
a = a[:j] + UP + CEN + a[j:]
rep('V.ok=nv?"Publicado: "+nomeOf(v)+" já está no site.":"Publicado: o site já mostra as mudanças.";', 'V.ok=pubMsg(v,nv);')
rep('V.toast=nv?"Publicado. Já está no site.":"Publicado.";', 'V.toast=pubMsg(v,nv);')
rep('save(true);store();V.toast="Publicado.";qed();return}', 'save(true);store();V.toast=pubMsg(v,nv);qed();return}')
rep('<i class="dot am"></i>A TLH confere o recorte. Até lá, o site mostra no lugar um ônibus de \'+(v.tipo==="dd"?"2 andares":"1 andar")+\'.</figcaption>',
    '<i class="dot am"></i>A TLH confere o recorte e faz as imagens. Ele entra no site depois disso.</figcaption>')
rep('pronto:v=>({q:v.pub?"Assim fica no site":"Pronto. Assim fica no site",', 'pronto:v=>({q:!CEN().includes(v.id)?"Pronto. O site hoje; ele entra depois da TLH":v.pub?"Assim fica no site":"Pronto. Assim fica no site",')
rep('go:v.pub?mudou(v)?"Publicar mudanças":"":"Publicar no site",', 'go:v.pub?mudou(v)?"Publicar mudanças":"":CEN().includes(v.id)?"Publicar no site":"Enviar para a TLH",')
rep('v.cena?"Foto enviada · a TLH confere":"Parecido ("+(v.tipo==="dd"?"2 andares":"1 andar")+")"', 'v.cena?"Foto enviada · a TLH confere":"Falta a foto de lado"')

# ---------- 8) site ao vivo dentro do painel: no servidor é o próprio endereço, em versão leve (?emb) ----------
rep('const SITEP=(async()=>{', 'const SITEP=(async()=>{if(/^https?:$/.test(location.protocol)&&/\\/painel(\\.html)?$/.test(location.pathname))return location.origin+"/?emb";')
rep('let SITEURL=null;(async()=>{', 'let SITEURL=null;(async()=>{if(/^https?:$/.test(location.protocol)&&/\\/painel(\\.html)?$/.test(location.pathname)){SITEURL=location.origin+"/?emb";return}')
rep('SITEURL+"?prev="+encodeURIComponent(id||"")', 'SITEURL+(SITEURL.includes("?")?"&":"?")+"prev="+encodeURIComponent(id||"")')
rep('const SB=()=>SITEURL?SITEURL.replace(/index\\.html$/,""):"";', 'const SB=()=>SITEURL?SITEURL.replace(/\\?emb$/,"").replace(/index\\.html$/,""):"";')

# ---------- 9) acessibilidade (T32): o axe (WCAG 2.1 AA) com usuário logado acusou estes pontos no painel novo ----------
rep(".ep1.tl{--bg:#ECEEF1;--surf:#FFFFFF;--surf2:#F3F3F4;--ink:#0B0B0C;--mut:rgba(0,0,0,.52)", ".ep1.tl{--bg:#ECEEF1;--surf:#FFFFFF;--surf2:#F3F3F4;--ink:#0B0B0C;--mut:rgba(0,0,0,.6)")
rep('<div class="wz-pr" aria-label', '<div class="wz-pr" role="img" aria-label')
a = a.replace('class="fb-tile" data-qe="\'+v.id+\'" aria-label="\'+esc(nomeOf(v))+\'"', 'class="fb-tile" data-qe="\'+v.id+\'"')
a = a.replace('data-f="nome" value=', 'data-f="nome" aria-label="Nome no site" value=')
a = a.replace("</style>\n</head><body>", ".ep1.v7.tl .fb-tile .fb-pos{background:rgba(0,0,0,.6);color:#fff}.ep1.tl .lv-seg button{color:var(--ink)}"
              "@media (prefers-color-scheme:dark){:root:not([data-theme=light]) .ep1.v7.tl .hb-row.dg{color:#ff8f82}}[data-theme=dark] .ep1.v7.tl .hb-row.dg{color:#ff8f82}\n</style>\n</head><body>", 1)
rep('<div class="sp-g">', '<div class="sp-g" tabindex="0" role="group" aria-label="Fotos, como ficam no site">')

OUT.write_text(a, encoding="utf-8", newline="\n")
print("painel v7 gerado:", OUT, len(a), "bytes")
