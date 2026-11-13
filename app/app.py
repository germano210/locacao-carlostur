"""Carlos Tur · carlostur.com.br

Um app serve tudo: o site (pasta site/), a API (/api/...) e o painel (/painel).
Banco SQLite e mídia em CT_DATA (padrão ./dados, no Docker /data). Contexto e tarefas: D:\trabalhos\CONTEXTO-projeto-carlostur.md.

Rodar local:   cd app && CT_HTTPS=0 uvicorn app:app --port 8002   ->  http://localhost:8002/
Criar acesso:  python app.py usuario email@exemplo.com "Nome"      (mostra a senha temporária)
Senha nova:    python app.py senha email@exemplo.com                (gera outra senha temporária)
Listar:        python app.py usuarios
Registros:     python app.py registros 2026-11-01 2026-11-30 [ip]  (Marco Civil, só com ordem judicial)
"""
import base64, hashlib, hmac, io, json, os, pathlib, re, secrets, sqlite3, sys, threading, time

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse, Response
from fastapi.staticfiles import StaticFiles

E = lambda k, d=None: os.environ.get(k) or d  # variável vazia = padrão
BASE = pathlib.Path(__file__).resolve().parent
SITE = pathlib.Path(E("CT_SITE", str(BASE.parent / "site"))).resolve()
DATA = pathlib.Path(E("CT_DATA", str(BASE.parent / "dados"))).resolve()
MIDIA = DATA / "midia"; TMP = DATA / "tmp"
for d in (DATA, MIDIA, TMP):
    d.mkdir(parents=True, exist_ok=True)
HTTPS = E("CT_HTTPS", "1") == "1"            # 0 só em teste local sem https (HSTS e cookie Secure)
ORIGENS = {o.strip().rstrip("/") for o in E("CT_ORIGENS", "https://carlostur.com.br,https://www.carlostur.com.br").split(",") if o.strip()}
SESSAO_H = 12                                 # horas sem uso até a sessão expirar
ACEITE_VERSAO = E("CT_ACEITE_VERSAO", "2026-11-11")
FOTO_MAX = 15 * 2**20; VIDEO_MAX = 300 * 2**20; PARTE_MAX = 50 * 2**20; ESTADO_MAX = 2 * 2**20
SENHA_MIN = 10
PROIBIDAS = {"1234567890", "0123456789", "senha12345", "carlostur1", "carlostur123", "qwertyuiop", "abcdefghij",
             "1111111111", "senhasenha", "carlos12345", "123456789a", "a123456789"}

# ---------------- banco (T07) ----------------
DB = sqlite3.connect(DATA / "carlostur.sqlite3", check_same_thread=False, isolation_level=None)
DB.row_factory = sqlite3.Row
DB.execute("pragma journal_mode=wal"); DB.execute("pragma foreign_keys=on")
LOCK = threading.RLock()
DB.executescript("""
create table if not exists usuarios(
  id integer primary key, login text unique not null, nome text, senha_hash text not null,
  temp integer not null default 1,                       -- 1 = senha temporária, obriga trocar na 1ª entrada
  papel text not null default 'empresa' check(papel in ('empresa','tlh')), criado real);
create table if not exists sessoes(
  hash text primary key,                                 -- sha256 do token; o token só existe no cookie
  usuario_id integer not null references usuarios(id) on delete cascade, csrf text not null, expira real, ultimo real);
create table if not exists estado(
  id integer primary key check(id = 1), json text not null, versao integer not null default 1, atualizado real,
  por integer references usuarios(id) on delete set null);
create table if not exists midia(
  id integer primary key, arquivo text unique not null, tipo text not null, bytes integer, criado real,
  por integer references usuarios(id) on delete set null);
create table if not exists eventos(
  id integer primary key, tipo text not null, destino text, dados text, criado real);  -- anônimo: sem IP, sem nome
create table if not exists acessos(
  id integer primary key, usuario_id integer references usuarios(id) on delete set null, login text, ip text,
  acao text not null, criado real);                        -- Marco Civil art. 15: guardar 6 meses
create table if not exists tentativas(chave text primary key, n integer not null, ate real);
create table if not exists aceites(
  id integer primary key, usuario_id integer not null references usuarios(id) on delete cascade,
  versao text not null, ip text, criado real);
create table if not exists registros(
  id integer primary key, ip text, metodo text, caminho text, status integer, criado real);  -- Marco Civil art. 15: 6 meses, sigilo
create index if not exists ix_registros_criado on registros(criado);
create table if not exists sugestoes(id integer primary key, usuario_id integer, texto text not null, criado real);
create index if not exists ix_eventos_criado on eventos(criado);
create index if not exists ix_acessos_criado on acessos(criado);
create index if not exists ix_sessoes_expira on sessoes(expira);
""")


def q(sql, *a):
    with LOCK:
        return DB.execute(sql, a).fetchall()


def q1(sql, *a):
    r = q(sql, *a)
    return r[0] if r else None


def ex(sql, *a):
    with LOCK:
        return DB.execute(sql, a)


# ---------------- senhas (T08) ----------------
def hash_senha(s: str) -> str:
    sal = secrets.token_bytes(16)
    h = hashlib.scrypt(s.encode(), salt=sal, n=2**15, r=8, p=1, maxmem=64 * 2**20, dklen=32)
    return "scrypt$32768$8$1$" + base64.b64encode(sal).decode() + "$" + base64.b64encode(h).decode()


def confere_senha(s: str, guardado: str) -> bool:
    try:
        _, n, r, p, sal, h = guardado.split("$")
        x = hashlib.scrypt(s.encode(), salt=base64.b64decode(sal), n=int(n), r=int(r), p=int(p),
                           maxmem=64 * 2**20, dklen=len(base64.b64decode(h)))
        return hmac.compare_digest(x, base64.b64decode(h))
    except Exception:
        return False


HASH_FALSO = hash_senha(secrets.token_urlsafe(16))  # gasta o mesmo tempo quando o login não existe


def senha_fraca(s: str, login: str = "") -> str:
    if len(s) < SENHA_MIN:
        return f"Use {SENHA_MIN} ou mais caracteres."
    if len(s) > 200:
        return "Senha longa demais."
    b = s.lower()
    if b in PROIBIDAS or len(set(b)) < 4 or (login and login.split("@")[0].lower() in b):
        return "Essa senha é fácil de adivinhar. Use outra."
    return ""


def senha_temporaria() -> str:
    a = "abcdefghjkmnpqrstuvwxyz23456789"
    return "-".join("".join(secrets.choice(a) for _ in range(4)) for _ in range(3))  # ex.: k7m2-q9xa-4tr8


# ---------------- utilidades ----------------
def ip_de(req: Request) -> str:
    return (req.headers.get("cf-connecting-ip") or (req.client.host if req.client else "") or "")[:64]


def erro(msg, status=400, **extra):
    return JSONResponse({"erro": msg, **extra}, status_code=status)


def registra(usuario_id, login, ip, acao):
    ex("insert into acessos(usuario_id,login,ip,acao,criado) values(?,?,?,?,?)", usuario_id, login, ip, acao, time.time())


def bloqueado(chave):
    r = q1("select n,ate from tentativas where chave=?", chave)
    return bool(r and r["ate"] and r["ate"] > time.time())


def falhou(chave):
    agora = time.time()
    r = q1("select n,ate from tentativas where chave=?", chave)
    n = 1 if not r or (r["ate"] and r["ate"] <= agora) else r["n"] + 1
    ate = agora + 15 * 60 if n >= 5 else None
    ex("insert into tentativas(chave,n,ate) values(?,?,?) on conflict(chave) do update set n=excluded.n, ate=excluded.ate",
       chave, 0 if ate else n, ate)


def limpa_tentativas(*chaves):
    for c in chaves:
        ex("delete from tentativas where chave=?", c)


def sessao(req: Request):
    tok = req.cookies.get("ct_s")
    if not tok:
        return None
    h = hashlib.sha256(tok.encode()).hexdigest()
    r = q1("select s.hash,s.csrf,s.expira,u.* from sessoes s join usuarios u on u.id=s.usuario_id where s.hash=?", h)
    agora = time.time()
    if not r or r["expira"] < agora:
        if r:
            ex("delete from sessoes where hash=?", h)
        return None
    ex("update sessoes set expira=?, ultimo=? where hash=?", agora + SESSAO_H * 3600, agora, h)
    return r


def aceite_pendente(uid) -> bool:
    return not q1("select 1 from aceites where usuario_id=? and versao=?", uid, ACEITE_VERSAO)


def eu_json(u):
    return {"login": u["login"], "nome": u["nome"], "papel": u["papel"], "temp": bool(u["temp"]),
            "aceite": aceite_pendente(u["id"]), "aceiteVersao": ACEITE_VERSAO, "senhaMin": SENHA_MIN}


def poe_cookies(resp: Response, token: str, csrf: str):
    kw = dict(httponly=True, secure=HTTPS, samesite="strict", path="/", max_age=SESSAO_H * 3600)
    resp.set_cookie("ct_s", token, **kw)
    resp.set_cookie("ct_c", csrf, **{**kw, "httponly": False})


def tira_cookies(resp: Response):
    for c in ("ct_s", "ct_c"):
        resp.delete_cookie(c, path="/", secure=HTTPS, samesite="strict")


# ---------------- app ----------------
from contextlib import asynccontextmanager


@asynccontextmanager
async def _vida(app):
    threading.Thread(target=_rotina, daemon=True).start()  # limpeza diária (definida mais abaixo)
    yield


app = FastAPI(title="Carlos Tur", docs_url=None, redoc_url=None, openapi_url=None, lifespan=_vida)

CSP = "; ".join([
    "default-src 'self'",
    "script-src 'self' 'unsafe-inline'",        # o site tem scripts inline; sem 'unsafe-eval'
    "style-src 'self' 'unsafe-inline'",
    "img-src 'self' data: blob:",
    "media-src 'self' blob:",
    "font-src 'self'",
    "connect-src 'self'",
    "worker-src 'self' blob:",
    "object-src 'none'",
    "base-uri 'self'",
    "form-action 'self'",
    "frame-ancestors 'none'",
])
LIVRES_CSRF = {"/api/entrar", "/api/evento"}  # entrar ainda não tem sessão; evento é público e anônimo


@app.middleware("http")
async def guarda(request: Request, call_next):
    p = request.url.path
    # T11 · CSRF: escrita na API exige Origin do próprio site + header X-CT igual ao cookie ct_c
    if p.startswith("/api/") and request.method not in ("GET", "HEAD", "OPTIONS"):
        org = (request.headers.get("origin") or "").rstrip("/")
        proprio = f"{request.url.scheme}://{request.headers.get('host', '')}"
        if org and org != proprio and org not in ORIGENS:
            return erro("Origem não permitida.", 403)
        if p not in LIVRES_CSRF:
            c = request.cookies.get("ct_c") or ""
            if not c or not hmac.compare_digest(c, request.headers.get("x-ct") or ""):
                return erro("Sessão inválida. Recarregue a página.", 403)
    r = await call_next(request)
    h = r.headers
    h["Content-Security-Policy"] = CSP
    h["X-Content-Type-Options"] = "nosniff"
    h["Referrer-Policy"] = "strict-origin-when-cross-origin"
    h["Permissions-Policy"] = "camera=(), microphone=(), geolocation=(), payment=(), usb=()"
    h["X-Frame-Options"] = "DENY"
    h["Cross-Origin-Opener-Policy"] = "same-origin"
    if HTTPS:
        h["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    if p.startswith("/api/") or p.startswith("/painel"):
        h["X-Robots-Tag"] = "noindex, nofollow"
        h["Cache-Control"] = "no-store"
    if registrar(p):
        try:
            ex("insert into registros(ip,metodo,caminho,status,criado) values(?,?,?,?,?)",
               ip_de(request), request.method, p[:200], r.status_code, time.time())
        except Exception as e:
            print("registro de acesso falhou:", e, file=sys.stderr)
    return r


# Marco Civil (Lei 12.965/2014, art. 15): guardar por 6 meses data, hora e IP do uso da aplicação, em sigilo.
# Só páginas e API; arquivos estáticos não. /api/evento fica de fora para o clique continuar anônimo.
NAO_REGISTRA = ("/assets/", "/fonts/", "/midia/", "/api/evento", "/saude", "/api/site.js")
EXT_ESTATICA = (".webp", ".jpg", ".jpeg", ".png", ".svg", ".ico", ".css", ".js", ".json", ".woff2", ".mp4", ".webm", ".txt")


def registrar(p: str) -> bool:
    return not p.startswith(NAO_REGISTRA) and not p.lower().endswith(EXT_ESTATICA)


def logado(req: Request, completo=True):
    """Usuário da sessão. completo=True exige senha definitiva e aceite em dia."""
    u = sessao(req)
    if not u:
        return None, erro("Entre no painel de novo.", 401)
    if completo and (u["temp"] or aceite_pendente(u["id"])):
        return None, erro("Termine a primeira entrada.", 403)
    return u, None


@app.api_route("/saude", methods=["GET", "HEAD"])
def saude():
    q1("select 1")
    return {"ok": True, "t": int(time.time())}


@app.get("/robots.txt")
def robots():
    return PlainTextResponse("User-agent: *\nDisallow: /painel\nDisallow: /api/\n")


@app.api_route("/painel", methods=["GET", "HEAD"])
@app.api_route("/painel/", methods=["GET", "HEAD"])
@app.api_route("/painel.html", methods=["GET", "HEAD"])
def painel():
    return FileResponse(SITE / "painel.html")


# ---------------- T09/T10 · entrar, sair, senha, aceite ----------------
@app.post("/api/entrar")
async def entrar(req: Request):
    try:
        b = await req.json()
    except Exception:
        return erro("Pedido inválido.")
    login = str(b.get("login") or "").strip().lower()[:200]
    senha = str(b.get("senha") or "")[:200]
    ip = ip_de(req)
    kl, ki = "l:" + login, "i:" + ip
    if bloqueado(kl) or bloqueado(ki):
        registra(None, login, ip, "bloqueado")
        return erro("Muitas tentativas. Espere 15 minutos e tente de novo.", 429)
    u = q1("select * from usuarios where login=?", login)
    if not u or not confere_senha(senha, u["senha_hash"] if u else HASH_FALSO):
        falhou(kl); falhou(ki)
        registra(u["id"] if u else None, login, ip, "senha errada")
        return erro("E-mail ou senha não conferem.", 401)
    limpa_tentativas(kl, ki)
    token, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(24)
    agora = time.time()
    ex("insert into sessoes(hash,usuario_id,csrf,expira,ultimo) values(?,?,?,?,?)",
       hashlib.sha256(token.encode()).hexdigest(), u["id"], csrf, agora + SESSAO_H * 3600, agora)
    registra(u["id"], login, ip, "entrou")
    resp = JSONResponse(eu_json(u))
    poe_cookies(resp, token, csrf)
    return resp


@app.post("/api/sair")
def sair(req: Request):
    u = sessao(req)
    if u:
        ex("delete from sessoes where hash=?", u["hash"])
        registra(u["id"], u["login"], ip_de(req), "saiu")
    resp = JSONResponse({"ok": True})
    tira_cookies(resp)
    return resp


@app.get("/api/eu")
def eu(req: Request):
    u = sessao(req)
    if not u:
        return erro("Não entrou.", 401)
    return eu_json(u)


@app.post("/api/senha")
async def senha(req: Request):
    u, e = logado(req, completo=False)
    if e:
        return e
    b = await req.json()
    atual, nova = str(b.get("atual") or ""), str(b.get("nova") or "")
    ip = ip_de(req)
    if bloqueado("l:" + u["login"]):
        return erro("Muitas tentativas. Espere 15 minutos e tente de novo.", 429)
    if not confere_senha(atual, u["senha_hash"]):
        falhou("l:" + u["login"])
        registra(u["id"], u["login"], ip, "troca de senha: atual errada")
        return erro("A senha atual não confere.", 401)
    if atual == nova:
        return erro("A senha nova precisa ser diferente da atual.")
    m = senha_fraca(nova, u["login"])
    if m:
        return erro(m)
    ex("update usuarios set senha_hash=?, temp=0 where id=?", hash_senha(nova), u["id"])
    ex("delete from sessoes where usuario_id=? and hash<>?", u["id"], u["hash"])  # derruba outros aparelhos
    registra(u["id"], u["login"], ip, "trocou a senha")
    return eu_json(q1("select * from usuarios where id=?", u["id"]))


@app.post("/api/aceite")
async def aceite(req: Request):
    u, e = logado(req, completo=False)
    if e:
        return e
    if u["temp"]:
        return erro("Crie a senha primeiro.", 403)
    b = await req.json()
    if b.get("versao") != ACEITE_VERSAO or b.get("aceito") is not True:
        return erro("Confirme o termo para continuar.")
    ip = ip_de(req)
    ex("insert into aceites(usuario_id,versao,ip,criado) values(?,?,?,?)", u["id"], ACEITE_VERSAO, ip, time.time())
    registra(u["id"], u["login"], ip, "aceitou o termo " + ACEITE_VERSAO)
    return eu_json(u)


# ---------------- T12 · estado do painel e dados públicos do site ----------------
def estado():
    r = q1("select json,versao,atualizado from estado where id=1")
    return (json.loads(r["json"]), r["versao"], r["atualizado"]) if r else (None, 0, None)


def publico(D):
    if not D or not isinstance(D.get("frota"), list):
        return None
    pub = [{"id": v.get("id"), "pub": True} for v in D["frota"] if isinstance(v, dict) and v.get("pub")]
    emp = (D.get("empresa") or {}).get("pub") or None
    return {"frota": pub, "ordemPub": D.get("ordemPub") or [p["id"] for p in pub], "disp": D.get("disp") or {},
            "empresa": emp}


@app.get("/api/painel")
def painel_ler(req: Request):
    u, e = logado(req)
    if e:
        return e
    D, versao, quando = estado()
    return {"dados": D, "versao": versao, "atualizado": quando}


@app.put("/api/painel")
async def painel_salvar(req: Request):
    u, e = logado(req)
    if e:
        return e
    corpo = await req.body()
    if len(corpo) > ESTADO_MAX:
        return erro("Dados grandes demais. Fotos e vídeos sobem separados.", 413)
    try:
        b = json.loads(corpo)
        D, versao = b["dados"], int(b.get("versao") or 0)
        assert isinstance(D, dict) and isinstance(D.get("frota"), list)
    except Exception:
        return erro("Dados inválidos.")
    for k in ("acesso", "contatos"):  # login fica no servidor; contatos vêm dos eventos
        D.pop(k, None)
    texto = json.dumps(D, ensure_ascii=False, separators=(",", ":"))
    if "data:" in texto and len(texto) > 200_000:
        return erro("Imagem embutida nos dados. Envie a foto pelo botão de fotos.", 413)
    with LOCK:
        _, atual, _ = estado()
        if versao != atual:
            return erro("Outra pessoa salvou antes. Recarregue o painel para ver a versão nova.", 409, versao=atual)
        ex("insert into estado(id,json,versao,atualizado,por) values(1,?,?,?,?) on conflict(id) do update set "
           "json=excluded.json, versao=excluded.versao, atualizado=excluded.atualizado, por=excluded.por",
           texto, atual + 1, time.time(), u["id"])
    return {"ok": True, "versao": atual + 1}


@app.get("/api/site")
def site_dados():
    return publico(estado()[0]) or {}


@app.get("/api/site.js")
def site_js():
    # carregado de forma síncrona pelo index antes do script principal (o site monta a frota na largada)
    d = publico(estado()[0])
    js = "window.CT_PUB=" + json.dumps(d, ensure_ascii=False).replace("</", "<\\/") + ";"
    return Response(js, media_type="application/javascript; charset=utf-8", headers={"Cache-Control": "no-cache"})


# ---------------- T13 · fotos (sem EXIF/GPS) ----------------
@app.post("/api/midia")
async def midia(req: Request):
    u, e = logado(req)
    if e:
        return e
    from PIL import Image, ImageOps
    form = await req.form()
    f = form.get("arquivo")
    if f is None or not hasattr(f, "read"):
        return erro("Escolha uma foto.")
    dados = await f.read(FOTO_MAX + 1)
    if len(dados) > FOTO_MAX:
        return erro("Foto grande demais (máximo 15 MB).", 413)
    try:
        try:
            import pillow_heif  # opcional: fotos HEIC do iPhone
            pillow_heif.register_heif_opener()
        except Exception:
            pass
        im = Image.open(io.BytesIO(dados))
        if im.format not in ("JPEG", "PNG", "WEBP", "HEIF", "MPO"):
            return erro("Envie JPG, PNG, WEBP ou HEIC.")
        im = ImageOps.exif_transpose(im)              # deita a foto certa antes de jogar o EXIF fora
        logo = form.get("tipo") == "logo"
        im = im.convert("RGBA" if logo or im.mode in ("RGBA", "LA", "P") else "RGB")
        im.thumbnail((800, 800) if logo else (1600, 1600))
        out = io.BytesIO()
        im.save(out, "WEBP", quality=82, method=5)    # salvar de novo descarta EXIF, GPS e metadados
    except Exception:
        return erro("Não deu para abrir essa imagem.")
    nome = secrets.token_urlsafe(12) + ".webp"
    (MIDIA / nome).write_bytes(out.getvalue())
    ex("insert into midia(arquivo,tipo,bytes,criado,por) values(?,?,?,?,?)", nome, "foto", out.tell(), time.time(), u["id"])
    return {"url": "/midia/" + nome}


# ---------------- T14 · vídeo do passeio (em partes de até 50 MB: o Cloudflare grátis limita 100 MB por pedido) ----------------
VIDEO_TIPOS = {"mp4": "mp4", "webm": "webm", "mov": "mov", "quicktime": "mov"}


@app.post("/api/video")
async def video(req: Request):
    u, e = logado(req)
    if e:
        return e
    p = req.query_params
    up = re.sub(r"[^A-Za-z0-9_-]", "", p.get("id", ""))[:40]
    try:
        parte, total = int(p.get("parte", "0")), int(p.get("total", "1"))
    except ValueError:
        return erro("Parte inválida.")
    ext = VIDEO_TIPOS.get((p.get("tipo") or "").split("/")[-1].lower())
    veiculo = str(p.get("veiculo") or "")[:60]
    if not up or not ext or not (0 <= parte < total <= VIDEO_MAX // PARTE_MAX + 1):
        return erro("Envie um vídeo MP4, WEBM ou MOV.")
    corpo = await req.body()
    if len(corpo) > PARTE_MAX:
        return erro("Parte grande demais.", 413)
    arq = TMP / f"{u['id']}-{up}.{ext}"
    if parte == 0 and arq.exists():
        arq.unlink()
    if (arq.stat().st_size if arq.exists() else 0) + len(corpo) > VIDEO_MAX:
        arq.unlink(missing_ok=True)
        return erro("Vídeo grande demais (máximo 300 MB).", 413)
    with open(arq, "ab") as fh:
        fh.write(corpo)
    if parte < total - 1:
        return {"ok": True, "parte": parte}
    nome = f"passeio-{re.sub(r'[^a-z0-9]+', '-', veiculo.lower()).strip('-') or 'veiculo'}-{secrets.token_hex(4)}.{ext}"
    destino = DATA / "videos"; destino.mkdir(exist_ok=True)
    arq.rename(destino / nome)  # fora de /midia: a TLH trata o vídeo antes de ir ao site
    ex("insert into midia(arquivo,tipo,bytes,criado,por) values(?,?,?,?,?)", "videos/" + nome, "video",
       (destino / nome).stat().st_size, time.time(), u["id"])
    registra(u["id"], u["login"], ip_de(req), "enviou vídeo do passeio " + veiculo)
    return {"ok": True, "recebido": True}


# ---------------- T15 · cliques anônimos ----------------
EVENTOS_OK = {"wa"}
_ritmo = {}  # ip -> [janela, contagem]  (só em memória, nunca vai ao banco)


@app.post("/api/evento")
async def evento(req: Request):
    ip, agora = ip_de(req), time.time()
    j = _ritmo.get(ip)
    if not j or agora - j[0] > 60:
        j = _ritmo[ip] = [agora, 0]
    j[1] += 1
    if j[1] > 30:
        return Response(status_code=204)
    if len(_ritmo) > 5000:
        _ritmo.clear()
    try:
        b = json.loads((await req.body())[:4000] or b"{}")
    except Exception:
        return Response(status_code=204)
    tipo = str(b.get("tipo") or "")
    if tipo not in EVENTOS_OK:
        return Response(status_code=204)
    limpo = lambda v, n=80: re.sub(r"[\x00-\x1f<>]", "", str(v or ""))[:n]
    d = b.get("dados") if isinstance(b.get("dados"), dict) else {}
    try:
        pessoas = max(0, min(999, int(d.get("p") or 0)))
    except (TypeError, ValueError):
        pessoas = 0
    dados = {"o": limpo(d.get("o")), "b": limpo(d.get("b")), "p": pessoas, "f": limpo(d.get("f"), 20)}
    ex("insert into eventos(tipo,destino,dados,criado) values(?,?,?,?)", tipo, limpo(b.get("destino")) or "Sem destino",
       json.dumps(dados, ensure_ascii=False), agora)
    return Response(status_code=204)


@app.get("/api/contatos")
def contatos(req: Request):
    u, e = logado(req)
    if e:
        return e
    rows = q("select destino,dados,criado from eventos where tipo='wa' order by criado desc limit 500")
    out = []
    for r in rows:
        d = json.loads(r["dados"] or "{}")
        out.append({"t": int(r["criado"] * 1000), "d": r["destino"], "o": d.get("o") or "—", "p": d.get("p") or 0,
                    "b": d.get("b") or "—"})
    return {"contatos": out}


@app.post("/api/sugestao")
async def sugestao(req: Request):
    u, e = logado(req)
    if e:
        return e
    t = str((await req.json()).get("texto") or "").strip()[:2000]
    if not t:
        return erro("Escreva a sugestão primeiro.")
    ex("insert into sugestoes(usuario_id,texto,criado) values(?,?,?)", u["id"], t, time.time())
    return {"ok": True}


# ---------------- limpeza diária (prazos da política de privacidade) ----------------
def limpeza():
    agora = time.time()
    ex("delete from eventos where criado < ?", agora - 365 * 86400)    # cliques: 12 meses
    ex("delete from acessos where criado < ?", agora - 183 * 86400)    # registros de acesso: 6 meses
    ex("delete from registros where criado < ?", agora - 183 * 86400)  # Marco Civil: 6 meses
    ex("delete from sessoes where expira < ?", agora)
    ex("delete from tentativas where (ate is null or ate < ?) and n = 0", agora)
    for f in TMP.glob("*"):                                             # envios de vídeo largados no meio
        if f.stat().st_mtime < agora - 86400:
            f.unlink(missing_ok=True)


def _rotina():
    while True:
        try:
            limpeza()
        except Exception as e:
            print("limpeza falhou:", e, file=sys.stderr)
        time.sleep(24 * 3600)




@app.api_route("/api/{resto:path}", methods=["GET", "POST", "PUT", "DELETE"])
def api_404(resto: str):
    return erro("não encontrado", 404)


app.mount("/midia", StaticFiles(directory=MIDIA), name="midia")
app.mount("/", StaticFiles(directory=SITE, html=True), name="site")  # por último: pega o resto


# ---------------- linha de comando ----------------
def _cli(a):
    if len(a) >= 2 and a[0] == "usuario":
        login = a[1].strip().lower(); nome = a[2] if len(a) > 2 else ""
        papel = "tlh" if "--tlh" in a else "empresa"
        if q1("select 1 from usuarios where login=?", login):
            sys.exit(f"{login} já existe. Para gerar senha nova: python app.py senha {login}")
        s = senha_temporaria()
        ex("insert into usuarios(login,nome,senha_hash,temp,papel,criado) values(?,?,?,?,?,?)",
           login, nome, hash_senha(s), 1, papel, time.time())
        print(f"Criado: {login} ({papel})\nSenha temporária: {s}\nNa 1ª entrada o painel pede uma senha nova.")
    elif len(a) == 2 and a[0] == "senha":
        login = a[1].strip().lower(); s = senha_temporaria()
        if not ex("update usuarios set senha_hash=?, temp=1 where login=?", hash_senha(s), login).rowcount:
            sys.exit("Usuário não encontrado.")
        ex("delete from sessoes where usuario_id=(select id from usuarios where login=?)", login)
        limpa_tentativas("l:" + login)
        print(f"Senha temporária nova de {login}: {s}")
    elif a == ["usuarios"]:
        for r in q("select login,nome,papel,temp from usuarios order by id"):
            print(f"{r['login']:<40} {r['papel']:<8} {'senha temporária' if r['temp'] else 'ok'}  {r['nome'] or ''}")
    elif len(a) >= 3 and a[0] == "registros":
        # Para ordem judicial: python app.py registros 2026-11-01 2026-11-30 [ip]  -> CSV na tela
        import csv, datetime as dt
        de = dt.datetime.fromisoformat(a[1]).timestamp(); ate = dt.datetime.fromisoformat(a[2]).timestamp() + 86400
        sql, par = "select criado,ip,metodo,caminho,status from registros where criado>=? and criado<?", [de, ate]
        if len(a) > 3:
            sql += " and ip=?"; par.append(a[3])
        w = csv.writer(sys.stdout); w.writerow(["data_hora_utc", "ip", "metodo", "caminho", "status"])
        for r in q(sql + " order by criado", *par):
            w.writerow([dt.datetime.utcfromtimestamp(r["criado"]).isoformat(timespec="seconds"), r["ip"], r["metodo"], r["caminho"], r["status"]])
    elif a == ["limpar"]:
        limpeza(); print("Limpeza feita.")
    else:
        print(__doc__)


if __name__ == "__main__":
    _cli(sys.argv[1:])
