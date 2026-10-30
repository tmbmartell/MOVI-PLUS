# MOVI+ — roteiro de homologação antes de liberar motoristas (30/10/2026)

**Situação:** PR #6 é o candidato V8 consolidado. **Não mesclado, não publicado**. A V5 permanece ativa no servidor. 6 dos 12 marcos concluídos no checklist #3 (50%).

## O que foi verificado no ambiente isolado
- Cadastro/convite, termos, aprovação e acesso individual; consulta financeira, gastos fixos, opt-in WhatsApp: testes funcionais sintéticos aprovados.
- Pix CNPJ: chave e nome do favorecido informados pelo cliente gravados **somente na base de QA criptografada**, sem ativação dos avisos ou verificação bancária presumida. O repositório público não contém o nome/chave reais.
- Três turnos com horas **configuráveis pelo administrador** (valores-padrão 09h, 14h, 19h, America/Porto_Velho); somatório exato da parcela mensal de 28 a 31 dias. As mensagens incluem a chave, o favorecido **informado** e instruções de conferir no banco.
- Motorista declara depósito; gestor pode registrar conferência manual do extrato, divergência e auditoria; referência do pagamento protegida por HMAC. Não há API de banco, recebimento automático nem baixa silenciosa.
- Regras de autorização do WhatsApp, opt-out, idempotência e saída única testadas com **remetente simulado**. Remetentes reais continuam bloqueados.
- Backup local de V5 do dia 30/10/2026: pacote criptografado validado, chave de criptografia interna válida, cópia SQLite `quick_check=ok`, utilizando verificador somente leitura `deploy/verify_backup_v1.py`; quatro testes sintéticos de fraude/corrupção passaram.

## Obrigações para entrega em ambiente real
1. **Pix:** no aplicativo bancário, consultar a chave CNPJ informada e verificar se o favorecido exibido é o titular informado; só depois marcar `bank_verified` no painel do gestor. Conferir cada recebimento no extrato bancário; não considerar mensagem do motorista como confirmação.
2. **WhatsApp piloto:** parear uma sessão exclusiva autorizada e testar uma mensagem real de entrada, confirmação de despesa, relatório JPEG e solicitação Pix de um único destinatário previamente consentido. Validar opt-out. Até lá, manter `MOVI_PIX_REMINDERS_ENABLED=0` e `MOVI_REPORT_DELIVERY_ENABLED=0`.
3. **LGPD/jurídico:** preencher razão social do controlador, CNPJ jurídico, contato do encarregado, prazo de retenção e relação de parceiros; revisar termos antes de coletar dados reais.
4. **Segurança:** ativar MFA em cada conta administrativa efetiva, validar segregação de usuários, revisar GitHub público e histórico por segredos, revisar URLs e CSRF; testar celulares e carga.
5. **Domínio:** publicar URL HTTPS estável com acesso externo controlado e testes de certificados, cookies, roteamento e proteção dos relatórios. A URL interna/temporária não substitui domínio definitivo.
6. **Backup externo:** copiar criptografado a um segundo local independente da VPS, manter chave mestre separada, auditar retenção e executar **restauração operacional em ambiente isolado**; o teste local feito até aqui não demonstra esse requisito.
7. **Entrada em produção:** preparar rollback, snapshot e janela; mesclar **somente PR #6** após revisão e nunca os PRs encadeados simultaneamente. Validação de operações financeiras é manual até existir integração bancária real.

## Linhas vermelhas
- **Não fazer transferência Pix real por comando do sistema**: ele só mostra uma instrução para o usuário pagar no próprio banco.
- Não usar o CNPJ do recebedor real em dados de exemplo, mocks ou repositório público.
- Não habilitar disparos automáticos ou distribuir login real a motoristas antes dos testes físicos e do aceite jurídico.
- Confirmado manualmente no painel = declaração de um **gestor que conferiu o extrato**, jamais confirmação automática do banco.
