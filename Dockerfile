# Carlos Tur · site + painel + API (FastAPI) num container só
FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 CT_DATA=/data CT_SITE=/srv/site
WORKDIR /srv/app
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app/app.py .
COPY site /srv/site
RUN useradd -u 1000 -m ct && mkdir -p /data && chown ct /data
USER ct
EXPOSE 8000
HEALTHCHECK --interval=60s --timeout=5s CMD python -c "import urllib.request;urllib.request.urlopen('http://127.0.0.1:8000/saude')"
# só o cloudflared (na mesma máquina) fala com o container; ele manda o IP real em CF-Connecting-IP
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "*"]
