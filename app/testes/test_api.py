"""Testes da API. Rodar:  cd app && python -m pytest -q testes"""
import io, json, os, sys, tempfile, pathlib

TMP = tempfile.mkdtemp()
os.environ.update(CT_DATA=TMP, CT_HTTPS="0")
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import app as A  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

LOGIN, NOVA = "carlos@exemplo.com", "onibus-grande-2026"


def cliente():
    return TestClient(A.app, base_url="http://localhost")


def cria(login=LOGIN):
    s = A.senha_temporaria()
    A.ex("delete from usuarios where login=?", login)
    A.ex("insert into usuarios(login,nome,senha_hash,temp,papel,criado) values(?,?,?,?,?,?)",
         login, "Carlos", A.hash_senha(s), 1, "empresa", 0)
    A.ex("delete from tentativas")
    return s


def h(c):
    return {"X-CT": c.cookies.get("ct_c") or ""}


def pronto():
    """Usuário com senha definitiva e termo aceito, já logado."""
    s = cria(); c = cliente()
    assert c.post("/api/entrar", json={"login": LOGIN, "senha": s}).status_code == 200
    assert c.post("/api/senha", json={"atual": s, "nova": NOVA}, headers=h(c)).status_code == 200
    assert c.post("/api/aceite", json={"versao": A.ACEITE_VERSAO, "aceito": True}, headers=h(c)).status_code == 200
    return c


def test_hash():
    g = A.hash_senha("abc-def-ghi-123")
    assert A.confere_senha("abc-def-ghi-123", g) and not A.confere_senha("errada", g)
    assert "abc-def" not in g


def test_senha_fraca():
    assert A.senha_fraca("curta")
    assert A.senha_fraca("1234567890")
    assert A.senha_fraca("carlos-2026-xx", "carlos@x.com")
    assert not A.senha_fraca(NOVA, LOGIN)


def test_primeira_entrada_e_bloqueios():
    s = cria(); c = cliente()
    r = c.post("/api/entrar", json={"login": LOGIN, "senha": s})
    assert r.status_code == 200 and r.json()["temp"] is True
    ck = r.headers.get_list("set-cookie")
    assert any("ct_s=" in x and "HttpOnly" in x and "SameSite=strict" in x for x in ck)
    assert c.get("/api/painel").status_code == 403                          # temp: só pode trocar a senha
    assert c.post("/api/senha", json={"atual": s, "nova": NOVA}).status_code == 403   # sem X-CT
    assert c.post("/api/senha", json={"atual": s, "nova": "fraca"}, headers=h(c)).status_code == 400
    assert c.post("/api/senha", json={"atual": s, "nova": NOVA}, headers=h(c)).json()["aceite"] is True
    assert c.get("/api/painel").status_code == 403                          # falta o aceite
    assert c.post("/api/aceite", json={"versao": "x", "aceito": True}, headers=h(c)).status_code == 400
    assert c.post("/api/aceite", json={"versao": A.ACEITE_VERSAO, "aceito": True}, headers=h(c)).status_code == 200
    assert c.get("/api/painel").status_code == 200


def test_cinco_erros_bloqueiam():
    cria(); c = cliente()
    for _ in range(5):
        assert c.post("/api/entrar", json={"login": LOGIN, "senha": "errada-123456"}).status_code == 401
    assert c.post("/api/entrar", json={"login": LOGIN, "senha": "errada-123456"}).status_code == 429
    A.ex("delete from tentativas")


def test_origem_de_fora():
    c = pronto()
    r = c.put("/api/painel", content=b"{}", headers={**h(c), "Origin": "https://malicioso.com"})
    assert r.status_code == 403


def test_estado_publico_e_conflito():
    c = pronto()
    v = c.get("/api/painel").json()["versao"]
    D = {"frota": [{"id": "g8", "nome": "G8", "pub": {"nome": "G8"}}, {"id": "nova", "nome": "rascunho"}],
         "ordemPub": ["g8"], "disp": {"g8": {"tot": 1, "livre": 1}}, "empresa": {"nome": "Carlos Tur", "pub": {"nome": "Carlos Tur"}},
         "acesso": {"temp": False}, "contatos": [{"x": 1}]}
    r = c.put("/api/painel", json={"dados": D, "versao": v}, headers=h(c))
    assert r.status_code == 200
    assert c.put("/api/painel", json={"dados": D, "versao": v}, headers=h(c)).status_code == 409
    salvo = c.get("/api/painel").json()["dados"]
    assert "acesso" not in salvo and "contatos" not in salvo
    pub = cliente().get("/api/site").json()
    assert pub["frota"] == [{"id": "g8", "pub": True}] and pub["disp"]["g8"]["livre"] == 1
    js = cliente().get("/api/site.js").text
    assert js.startswith("window.CT_PUB=") and "rascunho" not in js


def test_foto_sem_gps():
    from PIL import Image
    c = pronto()
    im = Image.new("RGB", (3000, 2000), (200, 100, 50))
    ex = Image.Exif(); ex[0x8825] = {2: (30.0, 1.0, 0.0)}; ex[0x010F] = "Camera"
    b = io.BytesIO(); im.save(b, "JPEG", exif=ex)
    assert Image.open(io.BytesIO(b.getvalue())).getexif()
    r = c.post("/api/midia", files={"arquivo": ("f.jpg", b.getvalue(), "image/jpeg")}, headers=h(c))
    assert r.status_code == 200, r.text
    out = Image.open(io.BytesIO(c.get(r.json()["url"]).content))
    assert max(out.size) == 1600 and not out.getexif() and not out.info.get("exif")
    assert c.post("/api/midia", files={"arquivo": ("x.txt", b"oi", "text/plain")}, headers=h(c)).status_code == 400


def test_video_em_partes():
    c = pronto()
    base = "/api/video?id=abc&total=2&tipo=video/mp4&veiculo=G8"
    assert c.post(base + "&parte=0", content=b"a" * 1000, headers=h(c)).json() == {"ok": True, "parte": 0}
    assert c.post(base + "&parte=1", content=b"b" * 10, headers=h(c)).json()["recebido"] is True
    vids = list((pathlib.Path(TMP) / "videos").glob("passeio-g8-*.mp4"))
    assert vids and vids[0].stat().st_size == 1010


def test_evento_anonimo_e_contatos():
    c = pronto()
    p = cliente()
    assert p.post("/api/evento", json={"tipo": "wa", "destino": "Gramado", "dados": {"o": "Porto Alegre", "p": 40, "b": "G8"}}).status_code == 204
    assert p.post("/api/evento", json={"tipo": "hack", "destino": "x"}).status_code == 204
    r = A.q1("select * from eventos order by id desc limit 1")
    assert r["destino"] == "Gramado" and "testclient" not in (r["dados"] or "")
    L = c.get("/api/contatos").json()["contatos"]
    assert L[0]["d"] == "Gramado" and L[0]["p"] == 40


def test_sair_e_cabecalhos():
    c = pronto()
    assert c.post("/api/sair", headers=h(c)).status_code == 200
    assert c.get("/api/painel").status_code == 401
    r = cliente().get("/")
    assert "frame-ancestors 'none'" in r.headers["content-security-policy"]
    assert cliente().get("/painel").headers["x-robots-tag"].startswith("noindex")
    assert "Disallow: /painel" in cliente().get("/robots.txt").text


def test_registro_marco_civil():
    A.ex("delete from registros")
    c = cliente()
    c.get("/", headers={"CF-Connecting-IP": "203.0.113.7"})
    c.get("/assets/map/vec23.json", headers={"CF-Connecting-IP": "203.0.113.7"})
    c.post("/api/evento", json={"tipo": "wa", "destino": "Torres"}, headers={"CF-Connecting-IP": "203.0.113.7"})
    rows = A.q("select ip,caminho from registros")
    assert [(r["ip"], r["caminho"]) for r in rows] == [("203.0.113.7", "/")]
