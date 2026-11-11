# Carlos Tur · o que fazer antes de publicar (LGPD + painel seguro)

Estado em 2026-11-11: site estático, sem servidor. O painel guarda tudo no navegador de quem usa (localStorage) e o login aceita qualquer senha de 6+ caracteres; o que se muda nele **não chega ao site de outras pessoas**. O site não tem Google Analytics nem Pixel; carrega a fonte Poppins do Google.

> Isto é um roteiro técnico, não parecer jurídico. A política de privacidade e os termos precisam de revisão de um advogado antes de ir ao ar.

## Fase 1 — publicar só o site (sem o painel)
- [ ] Não publicar o `painel.html` no servidor até a Fase 2 (deixar só no Git ou fora do deploy).
- [ ] Trocar todos os dados de exemplo por reais (preços, datas, vagas, frota, fotos marcadas como "exemplo") ou manter o selo "exemplo" bem visível.
- [ ] Conferir CNPJ, endereço, WhatsApp e Instagram da Carlos Tur com o Carlos.
- [ ] Mostrar no rodapé os registros da empresa para fretamento (ANTT/DAER) e Cadastur, se ela tiver.
- [x] Domínio: fica com a TLH (decisão do John, 11/11); a entrega ao fim da parceria está no termo do painel.
- [x] Fotos de destinos: conferido em 11/11 — as 107 fotos são do Wikimedia Commons com licença livre (CC BY, CC BY-SA, domínio público) e crédito do autor. Kayak, Melhores Destinos etc. aparecem só como fonte de texto (preços, hotéis, eventos). Manter os créditos.
- [x] Autorização do Carlos (marca, fotos) e cláusula LGPD TLH × Carlos Tur: viraram o termo aceito na 1ª entrada do painel (registrado com data, hora e IP). Valores e prazos ficam na proposta comercial.
- [ ] Hospedar a fonte Poppins junto do site (sem Google Fonts), para não enviar o IP de cada visitante ao Google.
- [ ] Página `privacidade.html` (modelo abaixo) e link para ela no rodapé.
- [ ] Página `termos.html`: orçamento sem compromisso, preço final só na conversa, cancelamento, responsabilidade.
- [ ] HTTPS com Cloudflare (SSL "Full (strict)"), HSTS ligado, redirecionar http → https.
- [ ] Cabeçalhos de segurança: Content-Security-Policy, X-Content-Type-Options: nosniff, Referrer-Policy: strict-origin-when-cross-origin, Permissions-Policy, frame-ancestors 'none'.
- [ ] Servidor: origem só aceita o Cloudflare (acesso direto dá 403, como no Dollar Ads Club), sem listagem de pastas, firewall, sistema atualizado.
- [ ] Testar no celular e no PC: rota, roteiros, orçamento no WhatsApp, passeio dentro do ônibus.

## Política de privacidade — o que ela precisa dizer
- [ ] Quem é o controlador: Carlos Tur (razão social, CNPJ, endereço). A The Loud House é operadora (hospeda e mantém).
- [ ] Canal do titular: e-mail ou WhatsApp para pedidos de dados. (Empresa de pequeno porte pode não nomear encarregado/DPO — Res. CD/ANPD nº 2/2022 —, mas precisa do canal.)
- [ ] Quais dados: (a) no site, só o que a pessoa escreve no orçamento, que vai para o WhatsApp; (b) cliques anônimos (destino, hora, viagem montada), sem nome, número ou IP; (c) no painel, WhatsApp e senha da empresa.
- [ ] Para quê e com qual base legal (art. 7º): orçamento = procedimentos preliminares de contrato (V); métricas anônimas = legítimo interesse (IX); registros de acesso do painel = obrigação legal (II, Marco Civil art. 15).
- [ ] Por quanto tempo: métricas 12 meses; registros de acesso 6 meses; conta do painel enquanto houver contrato.
- [ ] Com quem compartilha: WhatsApp/Meta (conversa), Cloudflare (hospedagem/segurança). Avisar que há transferência internacional (art. 33).
- [ ] Direitos do titular (art. 18): confirmar, acessar, corrigir, apagar, revogar consentimento, e como pedir.
- [ ] Armazenamento no navegador: só o essencial (tutorial visto, sessão). Sem cookies de propaganda → não precisa de banner. Se um dia entrar Pixel/Analytics, **antes** precisa de banner com aceite.
- [ ] Data da última atualização.

## Fase 2 — painel com login de verdade
- [ ] Servidor próprio para o painel (como o Dollar Ads Club: Docker no servidor Ubuntu, porta própria, atrás do Cloudflare). O painel passa a salvar no servidor e o site lê de lá.
- [ ] Endereço não óbvio e fora do Google: `noindex` no HTML e `Disallow` no robots.txt.
- [ ] Camada extra na frente: Cloudflare Access (grátis até 50 pessoas) liberando só o e-mail do Carlos e o seu.
- [ ] Senhas: guardar só o hash (Argon2id ou bcrypt), mínimo 10 caracteres, bloquear senhas comuns.
- [ ] Limite de tentativas: 5 erros → espera de 15 min por conta e por IP.
- [ ] Sessão em cookie `HttpOnly`, `Secure`, `SameSite=Strict`; expira em 12 h parado; botão sair apaga no servidor.
- [ ] Proteção CSRF em todo formulário que altera algo.
- [ ] "Esqueci a senha" pelo WhatsApp: código de uso único, guardado em hash, vale 15 min; avisar o Carlos quando a senha mudar.
- [ ] Opcional (recomendado): segundo fator com app autenticador (TOTP).
- [ ] Contas separadas: Carlos (dono) e TLH (suporte), com registro de quem fez cada mudança.
- [ ] Uploads de fotos e vídeos: aceitar só imagem/vídeo, limite de tamanho, renomear o arquivo, **apagar EXIF/GPS** das fotos.
- [ ] Registros de acesso (data, hora, IP da conta) guardados 6 meses (Marco Civil art. 15) e depois apagados.
- [ ] Backup diário criptografado, fora do servidor, e testar a restauração uma vez.
- [ ] Segredos só no `.env` (já fora do Git pelo `.gitignore`).
- [ ] Nada de lista de passageiros, CPF ou RG no painel enquanto não houver necessidade; se precisar (lista do fretamento), criptografar e apagar depois da viagem + prazo legal.

## Papéis e documentos
- [ ] Contrato TLH × Carlos Tur com cláusula de proteção de dados (TLH como operadora: só trata dados por ordem da Carlos Tur, sigilo, segurança, aviso de incidente, devolução/apagamento no fim).
- [ ] Plano de incidente: quem avisa quem; incidente com risco aos titulares vai para a ANPD e para as pessoas em até 3 dias úteis (Res. CD/ANPD nº 15/2024).
- [ ] Registro simples das operações de tratamento (planilha: dado, finalidade, base legal, onde fica, prazo).

## No dia de publicar
- [ ] Última revisão do advogado em privacidade e termos.
- [ ] Teste de cabeçalhos em securityheaders.com e SSL em ssllabs.com.
- [ ] Teste de login: senha errada 5×, sessão expirando, sair, esqueci a senha.
- [ ] Carlos aprova o site no ar.
