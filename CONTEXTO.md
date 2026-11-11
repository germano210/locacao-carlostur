# Contexto do projeto · Carlos Tur (carlostur.com.br)

Atualizado em 11/11/2026. **Ler antes de continuar o trabalho.** Quadro: artefato "CarlosTur · Quadro" — https://claude.ai/artifact/8fYcYip8Hfhn45AXQZtYTz (atualizar com publish na mesma URL). Chat "CarlosTur" do projeto TLH · Sites.

## Como trabalhar (vale para qualquer modelo que pegar a próxima tarefa)
1. Ler este arquivo e `PUBLICAR.md`.
2. Pegar **a primeira tarefa de "A fazer"** da lista abaixo (ordem = dependência). Uma tarefa por vez.
3. Fazer só o que a tarefa pede; rodar o teste indicado nela.
4. Marcar aqui `[x]`, escrever 1 linha em "Diário" e atualizar o quadro (mover o cartão).
5. Dúvida que só o John/Carlos responde → cartão em "Precisa de você", seguir para a próxima tarefa que não dependa dela.
6. Nunca pôr segredo, senha ou dado de cliente no Git (ver `.gitignore`). O John faz os commits.

## Decisões tomadas
- Mesmo modelo do Dollar Ads Club: **FastAPI + SQLite + Docker** no servidor Ubuntu do John, publicado pelo **Cloudflare Tunnel** (cloudflared). Origem só aceita o túnel.
- Porta local **8002** (Erivelto 8080, Dollar Ads Club 8001) — confirmada pelo John em 11/11.
- Domínio carlostur.com.br já está no Cloudflare (nameservers trocados, 11/11). **Não precisa de Worker**: o domínio inteiro vai para o túnel (hostname público carlostur.com.br → http://localhost:8002). O Worker só existiu no Dollar Ads Club porque lá a raiz é do Pages e só um subcaminho vai ao túnel.
- Um único app serve tudo em `carlostur.com.br`: site (`site/`), API (`/api/...`) e painel (`/painel`).
- Banco: `dados/carlostur.sqlite3`. Uploads: `dados/midia/`. Pasta `dados/` fora do Git, com backup diário.
- O site já foi feito esperando API (comentário no index: "No servidor, isto vem da API; aqui vem do navegador"). Hoje lê `localStorage['ct-painel-v1']`; o painel grava nesse mesmo objeto `D`.
- Sem Google Fonts (fontes em `site/fonts/`, licença OFL). Sem Analytics/Pixel. `track()` do index só empurra para `window.dataLayer` (nada sai do navegador).
- Login do painel por **e-mail**: contas criadas pelo John via linha de comando (`python app.py usuario email "Nome"`). 1ª entrada: senha temporária → senha nova (10+) → **aceite do termo do painel** (substitui o contrato agora: autorização de marca/fotos, LGPD controladora × operadora, domínio com a TLH; fica registrado com data, hora e IP; versão em `CT_ACEITE_VERSAO`).
- Domínios ficam com a TLH (decisão do John, 11/11).
- O site é só consulta de fretamento (sem venda de passagem avulsa).
- Fotos de destinos: todas do Wikimedia com licença livre e crédito (conferido 11/11). Kayak etc. só como fonte de texto.
- Painel e site funcionam nos dois modos: **com servidor** (detecta `api/eu` → login real, salva na API) e **protótipo** (aberto sem servidor: tudo no navegador, como antes).
- Ligação front ↔ servidor foi feita por `_patch_front.py` (substituições exatas e conferidas); se o site vier de novo do artefato, rodar `python _patch_front.py site` de novo.

## Estrutura
```
site/            index.html, painel.html, privacidade.html, termos.html, legal.css, fonts/, assets/
app/             app.py (servidor), requirements.txt, testes/test_api.py (10 testes)
Dockerfile, docker-compose.yml, .env.example, backup.sh
dados/           sqlite + midia/ + videos/ (fora do Git)
README.md (instalação)  CONTEXTO.md  PUBLICAR.md  TESTE.md (roteiro de aceite)
```

## API (app/app.py)
| Rota | Quem | O quê |
|---|---|---|
| POST /api/entrar · /api/sair · GET /api/eu | — / logado | Sessão em cookie `ct_s` (HttpOnly, Secure, Strict, 12 h); `ct_c` = token CSRF |
| POST /api/senha · /api/aceite | logado | Trocar senha (10+, derruba outros aparelhos) · aceite do termo |
| GET/PUT /api/painel | logado completo | Objeto `D` com `versao` (409 se outra pessoa salvou) |
| GET /api/site · /api/site.js | público | Só o publicado (frota publicada, ordem, disponibilidade, empresa) |
| POST /api/midia | logado | Foto → webp 1600 px (logo 800), sem EXIF/GPS, em /midia/ |
| POST /api/video | logado | Partes de 45 MB até 300 MB → dados/videos/ (a TLH trata) |
| POST /api/evento · GET /api/contatos | público · logado | Clique no WhatsApp sem IP/nome; contatos agregados |
| POST /api/sugestao | logado | Sugestão para a TLH (tabela sugestoes) |
Limpeza diária: eventos 12 meses, acessos 6 meses, sessões vencidas, uploads largados.

## O objeto `D` do painel (o que a API guarda)
`D = { frota:[veículo], ordemPub:[id], disp:{id:{tot,livre,volta}}, empresa:{nome,desde,wa,logo,pub:{...}}, contatos:[{d,t,...}], acesso:{temp} }`
Veículo: `{id, tipo, nome, lugares, pol, bordo:{chave:{on,t}}, extras:[{n,o}], emdia:{...}, fotos:[{s,l}], passeio, pub:{cópia publicada}}`.
O site usa só o que está **publicado** (`v.pub`, `ordemPub`, `disp`, `empresa.pub`). `acesso` sai do objeto e vira tabela de usuários no servidor.

## Tarefas (em ordem)
### Fase 0 · organização e legal
- [x] T01 Estrutura `site/` + CONTEXTO.md + quadro.
- [x] T02 Fontes locais (Poppins no site; Sora, Inter, Source Sans 3, DM Mono, Poppins no painel). Teste: nenhuma requisição a fonts.googleapis/gstatic.
- [x] T03 `privacidade.html` (modelo; campos `.ph` entre colchetes).
- [x] T04 `termos.html` (modelo).
- [x] T05 Links Privacidade/Termos no rodapé do index.

### Fase 1 · servidor (back + banco)
- [x] T06 `app/app.py` esqueleto: FastAPI serve `site/` como estático, `GET /saude`, middleware com cabeçalhos de segurança (CSP sem 'unsafe-eval'; HSTS; nosniff; Referrer-Policy strict-origin-when-cross-origin; Permissions-Policy; frame-ancestors 'none'), cria tabelas SQLite. `requirements.txt` (fastapi, uvicorn, pillow, python-multipart). Teste: `uvicorn app:app --port 8002` e abrir `/`, `/painel`, `/saude`.
- [x] T07 Tabelas: `usuarios(id,login,nome,senha_hash,temp,papel,criado)`, `sessoes(hash,usuario_id,expira,ultimo)`, `estado(id=1,json,versao,atualizado,por)`, `midia(id,arquivo,tipo,bytes,criado,por)`, `eventos(id,tipo,destino,dados,criado)`, `acessos(id,usuario_id,ip,acao,criado)`, `tentativas(chave,n,ate)`.
- [x] T08 Senhas: `hashlib.scrypt` (n=2**15,r=8,p=1, sal 16 bytes) como no Dollar Ads Club; mínimo 10 caracteres; lista curta de senhas proibidas. CLI: `python app.py usuario LOGIN NOME` → gera e mostra senha temporária. Teste unitário de hash/verificação.
- [x] T09 Login/logout/sessão: `POST /api/entrar`, `POST /api/sair`, `GET /api/eu`. Cookie `ct_s` HttpOnly, Secure, SameSite=Strict, Path=/; token aleatório, no banco só o sha256; expira 12 h sem uso. Limite: 5 erros → 15 min por login e por IP. Registrar em `acessos`. Teste: senha errada 5×, expirar, sair.
- [x] T10 Trocar senha: `POST /api/senha` (atual + nova). Com `temp=1` o painel só deixa trocar a senha. Teste.
- [x] T11 CSRF: todo POST/PUT/DELETE exige header `X-CT` igual ao cookie `ct_c` (double submit) e `Origin` = domínio. Teste: sem header → 403.
- [x] T12 Estado do painel: `GET /api/painel` (logado, `D` inteiro sem `acesso`), `PUT /api/painel` (logado, valida JSON e tamanho ≤ 2 MB, versão otimista → 409 se mudou). `GET /api/site` público: só o publicado (frota publicada em ordem, disp, empresa.pub). Teste com curl.
- [x] T13 Upload de fotos: `POST /api/midia` (logado) aceita jpeg/png/webp/heic até 15 MB; Pillow abre, corrige rotação, **remove EXIF/GPS**, redimensiona 1600 px, salva webp com nome aleatório em `dados/midia/`; servida em `/midia/<nome>`. Teste: foto com GPS → saída sem EXIF.
- [x] T14 Upload de vídeo do passeio: `POST /api/video` aceita mp4/webm/mov até 300 MB em pedaços; só guarda e marca `passeio="recebido"` (o tratamento continua manual pela TLH). Teste.
- [x] T15 Eventos anônimos: `POST /api/evento` público aceita só `{tipo, destino, dados}` de uma lista branca, sem IP; limite 30/min por IP em memória; `GET /api/contatos` (logado) devolve agregados. Limpeza diária: eventos > 12 meses, acessos > 6 meses, sessões vencidas. Teste.
- [x] T16 `robots.txt` (Disallow /painel e /api) e `X-Robots-Tag: noindex` no painel e na API.

### Fase 2 · ligar o front no servidor
- [x] T17 index.html: no carregamento, `fetch('/api/site')` e aplicar como hoje aplica o localStorage (manter localStorage só como reserva quando abrir sem servidor). `track()` do WhatsApp também chama `POST /api/evento` (com `navigator.sendBeacon`). Teste no navegador.
- [x] T18 painel.html: trocar o `gate` local pelo login do servidor (`/api/entrar`, `/api/eu`, senha temporária → tela de troca). Tirar "qualquer senha de 6+ caracteres".
- [x] T19 painel.html: `store()` passa a `PUT /api/painel` (com debounce e aviso de conflito 409); carregar de `GET /api/painel`.
- [x] T20 painel.html: fotos e logo sobem por `/api/midia` (hoje usam `URL.createObjectURL`/dataURL); vídeo por `/api/video`.
- [x] T21 painel.html: aba Contatos lê `/api/contatos`; "Sair do painel" chama `/api/sair`.

### Fase 3 · servidor e publicação
- [x] T22 `Dockerfile` (python:3.12-slim, usuário sem root, healthcheck `/saude`) e `docker-compose.yml` (porta `127.0.0.1:8002:8000`, volume `./dados:/data`, `restart: unless-stopped`). `.env.example` sem segredos reais.
- [x] T23 Backup: `backup.sh` (sqlite `.backup` + tar da mídia, cifrado com `age`, mantém 14 dias, copia para fora do servidor). Cron diário. Testar restauração.
- [x] T24 README: passo a passo (DNS no Cloudflare, `cloudflared tunnel` → localhost:8002, SSL Full strict, HSTS, Cloudflare Access em `/painel*`, criar usuário).
- [x] T25 TESTE.md: roteiro de aceite (site, orçamento, painel, segurança, LGPD) + testes automáticos com pytest em `app/testes/`.
- [ ] T26 Ensaio geral num subdomínio de teste (ex.: teste.carlostur.com.br protegido pelo Access) antes de virar o domínio.

## Precisa do John / Carlos
- **T26 ensaio:** subir no servidor (README), túnel `teste.carlostur.com.br` + Access, criar o usuário, rodar TESTE.md; testar a restauração do backup.
- **Aprovação do layout pelo Carlos** (no ensaio).
- **Roteiros prontos:** a seção mostra vagas e preço por pessoa (cara de venda de passagem avulsa). Tirar, ou virar "ideias de roteiro para fretar"?
- **Número da TLH** no suporte do painel está igual ao da Carlos Tur, (51) 99797-6191. Qual é o da TLH?
- Dados para as páginas legais (quando o layout for aprovado): endereço completo, e-mail de contato, regras de cancelamento/sinal, razão social e CNPJ da TLH, Cadastur (se tiver).
- E-mails e senhas dos acessos (o John cadastra pelo terminal; os mesmos e-mails vão no Cloudflare Access).
- Revisão jurídica de privacidade, termos e termo do painel (depois da aprovação).

## Diário
- 11/11 · T08–T25 feitos: senhas scrypt + bloqueio, sessão, CSRF, aceite do termo, API do painel/site, fotos sem GPS, vídeo em partes, cliques anônimos, limpeza, robots; site e painel ligados (modo protótipo preservado); Docker, backup.sh, README, TESTE.md. Testes: 10/10 no pytest + ponta a ponta no navegador (login → senha nova → aceite → painel → disponibilidade publicada → site mostra → clique no WhatsApp vira contato). Corrigido: as fotos de destinos já eram do Wikimedia com licença.
- 11/11 · Porta 8002 confirmada. T06 (app/app.py: site, /painel, /saude, CSP e cabeçalhos; testado sem violação de CSP em celular e PC) e T07 (7 tabelas criadas) feitos.
- 11/11 · Exportado do artefato; `.gitignore` de proteção; `PUBLICAR.md`; T01–T05 feitos (site em `site/`, fontes locais, páginas legais modelo, links no rodapé).
