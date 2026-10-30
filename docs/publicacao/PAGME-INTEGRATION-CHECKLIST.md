# MOVI+ P1 — Pix direto por CNPJ

**Decisão atual:** o Clube envia solicitações de pagamento com a **chave Pix CNPJ do recebedor**, em vez de usar um gateway Pag.me. O valor é calculado por motorista e dividido em três turnos. O responsável deve confirmar no banco que a chave está cadastrada e qual é o titular **antes da liberação**.

## Operação
- O gestor cadastra a chave CNPJ em `/gestao/pix`, informa o nome do titular após verificar no banco e configura o valor mensal do motorista. O armazenamento da chave é criptografado no banco, não hardcoded no código.
- O motorista abre `/meu-pix` para visualizar as três solicitações, copiar o CNPJ/valor da transferência e, se já pagou, registrar uma **declaração pendente**.
- A soma de todos os turnos fecha a parcela mensal exata, com ajuste automático para 28, 29, 30 ou 31 dias. O valor da primeira programação de cada mês fica congelado para evitar mudanças retroativas.
- O canal WhatsApp usa o contato pessoal previamente vinculado ao único piloto e autorização específica. Por padrão, nenhum aviso é enviado. Há templates de serviço/timer, mas **não estão instalados em produção**.

## Conciliação
**Uma chave Pix não é uma API de banco.** O sistema não tem como saber automaticamente se o dinheiro foi recebido. O status "declarado pelo motorista" não é "confirmado no banco". O gestor precisa comparar as declarações com o extrato do recebedor antes de reconhecer qualquer pagamento.

Se o cliente futuramente contratar integração bancária: obter API oficial autenticada, sandbox, identificadores de transação, webhook assinado, controle de eventos repetidos, estorno e teste completo. Não presumir integração por nome comercial semelhante a Pag.me.

## Homologação
1. Recebedor confirma titular/chave Pix no aplicativo bancário.
2. Gestor libera o cadastro da chave, vincula a parcela e testa instruções com motorista fictício.
3. Testar consentimento do piloto e verificar que o WhatsApp não envia antes da liberação.
4. Validar no extrato bancário **realmente recebido** antes de registrar confirmação.
5. Testar revogação, cancelamentos, mudança da chave e fevereiro/meses de 31 dias.
6. Revisão dos termos, LGPD e segurança antes da utilização comercial.

`deploy/test_pix_deposit_v1.py` valida o fluxo com dados sintéticos. Não executa pagamento bancário nem envia mensagens reais.
