"""T57 (18/11): ficha da empresa para o Google (dados estruturados schema.org em JSON-LD, gerados pelo servidor
com o WhatsApp e o ano publicados no painel) e sitemap com a data de cada página (lastmod)."""
f = "app/app.py"
s = open(f, encoding="utf-8").read()
assert "T57" not in s, "já aplicado"
R = [
# sitemap com lastmod
('''    urls = "".join(f"<url><loc>{URL_SITE}{u}</loc></url>" for u in ("/", "/privacidade.html", "/termos.html"))''',
'''    def dia(n):  # T57: data da última mudança de cada página
        try:
            return time.strftime("%Y-%m-%d", time.gmtime((SITE / n).stat().st_mtime))
        except OSError:
            return time.strftime("%Y-%m-%d", time.gmtime())
    urls = "".join(f"<url><loc>{URL_SITE}{u}</loc><lastmod>{dia(n)}</lastmod></url>"
                   for u, n in (("/", "index.html"), ("/privacidade.html", "privacidade.html"), ("/termos.html", "termos.html")))'''),
# JSON-LD na página inicial
('''    return HTMLResponse(_IDX["t"].replace("desde 2001", f"desde {ano_publicado()}"))''',
'''    ano = ano_publicado()
    return HTMLResponse(_IDX["t"].replace("desde 2001", f"desde {ano}").replace("</head>", ficha_google(ano) + "\\n</head>", 1))


WA_PADRAO = "5551997976191"  # WhatsApp da Carlos Tur (o mesmo padrão do site)


def ficha_google(ano: int) -> str:
    """T57: dados estruturados (schema.org) para o Google mostrar a empresa: nome, cidade, WhatsApp e ano do painel."""
    wa = WA_PADRAO
    try:
        d = re.sub(r"\\D", "", str((((estado()[0] or {}).get("empresa") or {}).get("pub") or {}).get("wa") or ""))
        d = re.sub(r"^55(?=\\d{10,11}$)", "", d)
        if len(d) in (10, 11):
            wa = "55" + d
    except Exception:
        pass
    tel = f"+{wa[:2]} {wa[2:4]} {wa[4:-4]}-{wa[-4:]}"
    emp = {
        "@type": "TravelAgency", "@id": f"{URL_SITE}/#empresa", "name": "Carlos Tur", "alternateName": "CarlosTur",
        "legalName": "C. P. dos Santos Transporte Ltda", "taxID": "04.142.546/0001-38",
        "description": "Fretamento de ônibus para excursões e turismo em grupo.",
        "url": f"{URL_SITE}/", "logo": f"{URL_SITE}/apple-touch-icon.png", "image": f"{URL_SITE}/assets/og.jpg",
        "telephone": tel, "foundingDate": str(ano),
        "address": {"@type": "PostalAddress", "addressLocality": "Santo Antônio da Patrulha", "addressRegion": "RS", "addressCountry": "BR"},
        "contactPoint": {"@type": "ContactPoint", "telephone": tel, "contactType": "customer service",
                         "availableLanguage": "Portuguese", "url": f"https://wa.me/{wa}"},
    }
    site = {"@type": "WebSite", "@id": f"{URL_SITE}/#site", "name": "Carlos Tur", "alternateName": "CarlosTur",
            "url": f"{URL_SITE}/", "inLanguage": "pt-BR", "publisher": {"@id": f"{URL_SITE}/#empresa"}}
    j = json.dumps({"@context": "https://schema.org", "@graph": [emp, site]}, ensure_ascii=False).replace("</", "<\\\\/")
    return f'<script type="application/ld+json">{j}</script>\''''),
]
for a, b in R:
    assert s.count(a) == 1, a[:70]
    s = s.replace(a, b)
open(f, "w", encoding="utf-8").write(s)
print("ok T57")
