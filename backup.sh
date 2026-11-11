#!/usr/bin/env bash
# Backup diário da Carlos Tur: banco (cópia consistente) + fotos + vídeos, cifrado com age, guarda 14 dias.
# Cron (todo dia 3h10):  10 3 * * * cd /caminho/locacao-carlostur && ./backup.sh >> dados/backup.log 2>&1
# Restaurar: age -d -i chave-privada.txt arquivo.tar.age | tar -x   (depois copiar para dados/ com o container parado)
set -euo pipefail
cd "$(dirname "$0")"
set -a; . ./.env; set +a
: "${CT_BACKUP_CHAVE:?coloque a chave pública do age em CT_BACKUP_CHAVE no .env}"
DEST="${CT_BACKUP_DESTINO:-/mnt/backup/carlostur}"; mkdir -p "$DEST"
QUANDO=$(date +%Y-%m-%d_%H%M)
docker compose exec -T carlostur python -c "import sqlite3; s=sqlite3.connect('/data/carlostur.sqlite3'); d=sqlite3.connect('/data/backup.sqlite3'); s.backup(d); d.close()"
tar -C dados -cf - backup.sqlite3 midia $( [ -d dados/videos ] && echo videos ) | age -r "$CT_BACKUP_CHAVE" > "$DEST/carlostur-$QUANDO.tar.age"
rm -f dados/backup.sqlite3
find "$DEST" -name 'carlostur-*.tar.age' -mtime +14 -delete
echo "$QUANDO backup ok: $(du -h "$DEST/carlostur-$QUANDO.tar.age" | cut -f1)"
