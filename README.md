# Carlos Tur · site e painel (carlostur.com.br)

Site de fretamento de ônibus da Carlos Tur + painel para a empresa atualizar a frota.
Um container serve tudo: o site (`site/`), a API (`/api/...`) e o painel (`/painel`). Banco SQLite e mídia em `dados/` (fora do Git).

| Pasta / arquivo | O que é |
|---|---|
| `site/` | Front: `index.html`, `painel.html`, `privacidade.html`, `termos.html`, `fonts/`, `assets/` |
| `app/app.py` | Servidor FastAPI (login, painel, fotos, vídeo, cliques anônimos, limpeza LGPD) |
| `app/testes/` | Testes automáticos (`cd app && python -m pytest -q testes`) |
| `../CONTEXTO-projeto-carlostur.md` (contexto central) | Decisões e tarefas (kanban) · `PUBLICAR.md` checklist LGPD · `TESTE.md` roteiro de aceite |

## Rodar no seu computador
```bash
cd app && pip install -r requirements.txt
CT_HTTPS=0 python app.py usuario voce@exemplo.com "Seu nome"   # mostra a senha temporária
CT_HTTPS=0 uvicorn app:app --port 8002                           # http://localhost:8002 e /painel
```
Sem servidor (`cd site && python -m http.server`) o painel volta ao modo protótipo, que guarda tudo só no navegador.

## Subir no servidor (Ubuntu, mesmo do Erivelto 8080 e Dollar Ads Club 8001)
1. `git clone` do repositório e `cd locacao-carlostur`.
2. `cp .env.example .env` e ajustar `CT_ORIGENS` (inclua `https://teste.carlostur.com.br` enquanto ele existir).
3. `mkdir -p dados && sudo chown -R 1000:1000 dados` (o container roda como usuário 1000, sem root).
4. `docker compose up -d --build` → `curl -s localhost:8002/saude` deve responder `{"ok":true,...}`.
5. Criar o acesso do Carlos (de qualquer pasta): `docker exec -it carlostur python app.py usuario email@do.carlos "Carlos"`. Com `docker compose exec`, rode de dentro da pasta do projeto (senão dá *no configuration file provided*). Mande a senha temporária a ele por um canal privado; na 1ª entrada o painel pede uma senha nova (10+ caracteres) e o aceite do termo.
   - Senha esquecida: `docker compose exec carlostur python app.py senha email@do.carlos`
   - Ver acessos: `docker compose exec carlostur python app.py usuarios`

## Cloudflare (o domínio já está lá; não precisa de Worker)
1. **Túnel (na conta do Cloudflare que tem o carlostur.com.br; o do Erivelto é de outra conta):** Zero Trust → Networks → Tunnels → Create → Cloudflared → copiar o token para `CF_TUNNEL_TOKEN` no `.env`. O `docker compose up -d --build` sobe o túnel (serviço `cloudflared`) junto com o app e não recria o túnel quando só o app muda.
   - *Public hostname*: `carlostur.com.br` e `www.carlostur.com.br` → HTTP → **`carlostur:8000`** (nome do serviço; `localhost` não funciona dentro do container do túnel).
   - Não rode também um `docker run` do cloudflared: dá conflito de nome. Log do túnel: `docker logs --tail 50 cloudflared-carlostur`.
2. **SSL/TLS:** modo *Full (strict)*; *Always Use HTTPS* ligado; HSTS ligado (o app também manda o cabeçalho).
3. **Access (proteção extra do painel):** Zero Trust → Access → Applications → *Self-hosted*:
   - `teste.carlostur.com.br` inteiro (só durante o ensaio) e `carlostur.com.br/painel*` (sempre).
   - Política *Allow* com os e-mails liberados. O login do próprio painel continua valendo por dentro.
4. **Upload grande:** o plano grátis aceita até 100 MB por pedido; o painel já manda o vídeo em partes de 45 MB.

## Backup
`backup.sh` faz cópia consistente do banco + fotos + vídeos, cifra com `age` e guarda 14 dias.
1. `sudo apt install age` e, **fora do servidor**, `age-keygen -o chave-carlostur.txt` (guarde bem; a linha `public key:` vai no `.env` em `CT_BACKUP_CHAVE`).
2. `CT_BACKUP_DESTINO` num disco/pasta que não seja o mesmo dos dados (ou sincronize com rclone).
3. Cron: `10 3 * * * cd /caminho/locacao-carlostur && ./backup.sh >> dados/backup.log 2>&1`
4. Restaurar (testar uma vez assim que ligar o backup): `./restaurar.sh carlostur-AAAA-MM-DD_HHMM.tar.age chave-carlostur.txt` — restaura numa pasta nova, confere o banco e mostra os comandos para pôr no ar.

## Aviso se o site cair (T43)
O endereço `https://carlostur.com.br/saude` responde `{"ok":true,...}` só quando o app **e** o banco estão de pé (aceita GET e HEAD; não entra no registro de acessos). Dois avisos gratuitos, que se completam:

**1. Monitor de fora (pega tudo: servidor desligado, Docker parado, túnel, DNS)** — UptimeRobot, plano gratuito (50 monitores, confere a cada 5 min, aviso por e-mail).
1. Crie a conta em uptimerobot.com com o e-mail que você lê no celular.
2. **New monitor** → tipo **Keyword** → URL `https://carlostur.com.br/saude` → palavra `"ok":true` → alertar quando a palavra **não existir** → intervalo 5 min.
   (Se o tipo Keyword não estiver no plano, use **HTTP(s)** com a mesma URL: avisa quando não vier 200.)
3. Em **Alert contacts**, confirme o e-mail; instale o app do UptimeRobot no celular para receber a notificação na hora.
4. Teste: `sudo docker compose stop carlostur`, espere o aviso (até uns 5–10 min) e `sudo docker compose up -d`. Deve chegar também o aviso de "voltou".
Observação: os termos do plano gratuito já proibiram uso comercial (2024–2025) e voltaram a permitir em 2026; confira a regra atual ao criar a conta. Alternativas gratuitas com uso comercial liberado: HetrixTools (15 monitores, 1 min) e Better Stack (10 monitores, 3 min).

**2. Aviso do próprio Cloudflare quando o túnel cai** (não precisa de conta nova; é na conta do Cloudflare do carlostur.com.br).
1. Painel do Cloudflare → **Notifications** → **Add** → **Tunnel Health Alert**.
2. Nome "Túnel carlostur", seu e-mail → salvar. Avisa quando o túnel muda de saudável para degradado/caído.
Sozinho ele não vê o app travado com o túnel de pé; por isso o monitor de fora é o principal.

**Se o aviso chegar:** `sudo docker compose ps` e `sudo docker compose logs --tail 50 carlostur cloudflared` na pasta `~/carlostur/codigo`; quase sempre `sudo docker compose up -d` resolve. O "Health Checks" do Cloudflare (aba Traffic) não serve aqui: é de plano pago.

## Atualizar
`git pull && docker compose up -d --build`. O banco e a mídia ficam em `dados/` e não são tocados.
