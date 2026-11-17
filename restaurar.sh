#!/usr/bin/env bash
# Restaura um backup feito pelo backup.sh numa pasta NOVA e confere se o banco está inteiro.
# Uso: ./restaurar.sh carlostur-AAAA-MM-DD_HHMM.tar.age chave-carlostur.txt [pasta-destino]
# Não mexe no site no ar. Para colocar no ar depois de conferir, siga as linhas que ele mostra no fim.
set -euo pipefail
ARQ="${1:?informe o arquivo .tar.age}"; CHAVE="${2:?informe a chave privada do age}"
DEST="${3:-restaurado-$(date +%Y%m%d-%H%M)}"
[ -e "$DEST" ] && { echo "A pasta $DEST já existe; escolha outra."; exit 1; }
mkdir -p "$DEST"
age -d -i "$CHAVE" "$ARQ" | tar -x -C "$DEST"
mv "$DEST/backup.sqlite3" "$DEST/carlostur.sqlite3"
python3 - "$DEST/carlostur.sqlite3" <<'PY'
import sqlite3, sys
db = sqlite3.connect(sys.argv[1])
ok = db.execute("pragma integrity_check").fetchone()[0]
n = lambda t: db.execute(f"select count(*) from {t}").fetchone()[0]
est = db.execute("select versao from estado where id=1").fetchone()
print(f"Banco: {ok} · usuários {n('usuarios')} · versão do painel {est[0] if est else 'vazio'} · cliques {n('eventos')}")
if ok != "ok":
    sys.exit("Banco com problema: NÃO use este backup.")
PY
echo "Fotos: $(find "$DEST/midia" -type f 2>/dev/null | wc -l) · vídeos: $(find "$DEST/videos" -type f 2>/dev/null | wc -l)"
cat <<FIM

Conferido. Para colocar no ar (o site fica fora por alguns segundos):
  sudo docker compose down
  mv dados dados-antes-$(date +%Y%m%d-%H%M)
  mv "$DEST" dados && sudo chown -R 1000:1000 dados
  sudo docker compose up -d
FIM
