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


## Conferência manual do recebimento (implementada na versão candidata)
- O motorista declara um turno em `/meu-pix`. O sistema registra **declarado**, sem marcar como recebido.
- O gestor acessa `/gestao/pix` > **Conferência manual dos depósitos**, confere o valor e a data no **extrato bancário real** e informa um identificador único da transação.
- Apenas o gestor autenticado registra **confirmado manualmente** após afirmar ter consultado o extrato. Valor divergente não pode ser confirmado silenciosamente: deve ser marcado como **divergência** e analisado.
- Um mesmo identificador não pode ser usado para confirmar duas declarações. O identificador é armazenado **somente como hash**, sem cópia do extrato, e a confirmação entra na auditoria.
- O motorista pode consultar sua própria situação: **pendente**, **confirmado manualmente** ou **divergência**. Uma confirmação é imutável neste piloto; retificações/estornos requerem procedimento próprio antes de produção.
- A rotina de aviso **não envia novo lembrete** para o turno que o motorista já declarou pago, mesmo que ainda esteja em análise.
- Testes: `deploy/test_pix_reconciliation_v1.py` (**7/7**) e `deploy/test_pix_deposit_v1.py` (**11/11**), todos com dados fictícios.
- **Limite:** o teste verifica lógica de revisão e auditoria, **não prova a existência de depósitos reais** nem confirma automaticamente um crédito no banco.

## Titular e chave
O operador informou nome do recebedor e chave CNPJ. Foram armazenados **criptografados em banco de QA isolado na VPS**, com aprovação bancária e disponibilização ao motorista **desligadas**. Dados reais não entram em arquivos do repositório público. Para ativar, é obrigatório confirmar que o próprio aplicativo bancário mostra o mesmo favorecido.

## Consulta de grande volume (em homologação)
- O gestor pode filtrar a conferência de depósitos por **mês** e **situação**, avançar/voltar pelas páginas de 50 registros e consultar totais correspondentes a todo o filtro, não só à página exibida. O limite anterior de 300 registros foi eliminado.
- Para associar uma parcela a um motorista, pesquise pelo **nome**, **usuário** ou **ID**. O resultado é limitado a 25 nomes por busca para evitar uma lista gigantesca. Testado com **4.000 motoristas fictícios**.
- Testes específicos: `deploy/test_pix_reconciliation_v1.py` 8/8 e `deploy/test_pix_driver_search_v1.py` 4/4. Não substituem testes de carga com 4.000 pessoas simultâneas.
