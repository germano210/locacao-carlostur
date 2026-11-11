# Roteiro de aceite · Carlos Tur

Automático: `cd app && python -m pytest -q testes` (10 testes: senha, bloqueio, CSRF, origem, painel, site público, foto sem GPS, vídeo em partes, cliques, sair).

## No ensaio (teste.carlostur.com.br, protegido pelo Access)
### Site
- [ ] Abre no celular e no PC; ônibus, rota, orçamento e passeio por dentro funcionam.
- [ ] Rodapé com CNPJ, ANTT, Privacidade e Termos; as duas páginas abrem.
- [ ] Botão do WhatsApp abre a conversa com a mensagem pronta.
- [ ] securityheaders.com dá A ou A+; ssllabs.com dá A.

### Painel (`/painel`)
- [ ] Criar usuário pelo terminal; entrar com a senha temporária → pede senha nova (10+) → pede o aceite do termo → abre.
- [ ] Senha errada 5 vezes → "Muitas tentativas" por 15 min.
- [ ] Editar um veículo e publicar → o site mostra a mudança ao recarregar.
- [ ] Marcar disponibilidade ("em viagem, volta dia X") → aparece no topo do site.
- [ ] Subir 2 fotos de celular → aparecem no veículo; baixar uma e conferir que não tem localização (EXIF).
- [ ] Subir um vídeo de passeio (>100 MB) → "Vídeo recebido"; arquivo em `dados/videos/`.
- [ ] Tocar no WhatsApp do site → aparece em Contatos (sem nome e sem telefone).
- [ ] Abrir o painel em 2 abas, salvar nas duas → a segunda avisa "Outra pessoa salvou antes".
- [ ] Trocar senha em Configurações → outra aba/aparelho sai.
- [ ] Sair → voltar ao painel pede login.

### Dados e LGPD
- [ ] `dados/` fora do Git; `.env` fora do Git.
- [ ] Backup rodou e foi restaurado uma vez.
- [ ] Carlos aprovou o layout; revisão jurídica de privacidade e termos feita.
