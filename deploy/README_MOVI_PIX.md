# MOVI+ — chave Pix CNPJ e solicitação de depósito, sem gateway

**Configuração recebida para homologação:** o responsável informou um CNPJ com dígitos verificadores válidos. A chave é cadastrada na **área do gestor** em `/gestao/pix` (gravada criptografada no banco), **não codificada em arquivos públicos**. É preciso confirmar no aplicativo bancário que a chave Pix pertence ao recebedor correto.

## Fluxo
1. Gestor entra no MOVI+ → **Cobranças Pix** e salva o CNPJ com o envio desativado.
2. Responsável confere no próprio banco **se a chave Pix está registrada e qual nome o banco exibe**. Depois preenche o nome, salva e finalmente marca confirmação do banco e liberação.
3. Gestor associa um valor de parcela mensal a cada motorista. O sistema calcula **3 solicitações por dia** às 9h, 14h e 19h em **America/Porto_Velho**, respeitando 28/29/30/31 dias. A primeira programação de um mês **congela o total daquela competência**.
4. Motorista vê `/meu-pix`, copia o CNPJ/aviso com valor de cada turno e pode declarar que pagou. A declaração **não comprova recebimento** e é exibida ao gestor para verificação no extrato bancário.
5. O aviso automático depende de autorização **separada** do motorista, vínculo prévio ao número WhatsApp piloto, consentimento financeiro, aceite jurídico V8 e travas de operação (inclusive `MOVI_PIX_REMINDERS_ENABLED=1`). Tudo inicia **desligado**.

## Publicação
- Não instalar nem ativar `deploy/novagente-movi-pix.service` e `deploy/novagente-movi-pix.timer` antes de homologação do piloto. São apenas templates versionados, não serviços ativos na V5.
- O serviço verifica a cada hora e só envia nos horários fixos, mediante gates. Em erro incerto reserva a tentativa e **não reenvia automaticamente**.
- `python -m pix_deposit_v1` realiza simulação e **não envia**.
- `python -m pix_deposit_v1 --send` só tenta enviar quando a flag técnica, a chave validada, a configuração do gestor, o consentimento individual e o piloto WAHA estão todos ativos.
- Sem API bancária, a conciliação segue **manual**, revisando realmente o extrato/identificação da conta recebedora. Não existe baixa bancária automática nem garantia de que a chave foi registrada no DICT.
- Se a chave ou titular mudar, o sistema bloqueia a liberação e desativa consentimentos anteriores de aviso. O banco deve ser consultado novamente.

## Testes isolados
`deploy/test_pix_deposit_v1.py`: valida CNPJ, criptografia do registro, três mensagens com chave, separação entre clientes, depósito declarado, revogação, envio simulado idempotente, e revogação após alteração da chave.

**Regra de negócio:** solicitar um Pix por chave é **instrução para transferência** e não uma operação bancária. A ativação real exige confirmação do recebedor e homologação jurídica e operacional.
