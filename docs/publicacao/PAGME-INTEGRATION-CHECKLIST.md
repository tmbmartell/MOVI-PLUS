# MOVI+ P1 — integração com o provedor de cobrança (pendente)

**Status em 30/10/2026:** não há credenciais ou documentação oficial confirmando qual serviço o cliente chama de **“Pag.me”**. **Não assumir que seja Pagar.me, Pagou, PagBank ou outra empresa** só porque os nomes são semelhantes. Nenhum pagamento, cobrança automática ou conciliação real está autorizado até a identificação do serviço e assinatura contratual.

## Dependências que precisam ser confirmadas pelo responsável financeiro
- Nome jurídico e domínio oficial da plataforma contratada e **documentação da API em produção e sandbox**, com versão.
- Conta beneficiária, titular da conta/chave Pix e termos que autorizam cobrança diária.
- Credenciais de sandbox e credenciais de produção fornecidas por canal privado (NUNCA por GitHub, log ou print público).
- Endpoints e esquema para criar cobrança, consultar status, cancelar, reembolsar e conciliar.
- Mecanismo oficial de assinatura de webhook, segredo de assinatura, validade do timestamp, replay e identificador idempotente.
- Taxas, vencimento, horários, fuso **America/Porto_Velho**, dias úteis/feriados, reprocessamento e política de falhas.
- Tratamento de chargebacks/estornos, valor parcial, pagamento duplicado e divergências, política de reconciliação com extrato da conta recebedora.
- Identidade do recebedor, regras de consentimento e responsabilidade por dados financeiros do motorista.
- Política de antecipação de parcelas sem duplicar a obrigação mensal.

## Regra financeira de planejamento já definida
Para evitar cobranças indevidas, **um mês com 28, 29, 30 ou 31 dias nunca pode gerar cobrança acima do valor da parcela**. O exemplo de 3 cobranças por dia (R$ 15 + R$ 15 + R$ 20) fecha R$ 1.500 somente em meses de 30 dias. O módulo puro `finance_deposit_planner_v1.py` distribui uma parcela mensal exata entre os dias do mês e os três turnos sem perda de centavos. É um **plano matemático**, não execução de cobrança.

## Contrato de dados sugerido (sem ativação)
`driver_id`, `month`, `installment_cents`, `due_date`, `slot` (manhã/tarde/noite), `expected_cents`, `provider_reference`, `provider_event_id`, `status` (previsto/emitido/pago/estornado/falhou), `created_at`, `paid_at`, `refund_at`.

- Motorista dizer **“já paguei”** ou enviar comprovante: registrar **declaração**, nunca marcar **confirmado pelo banco**.
- Reconciliação real só mediante evento assinado do provedor **ou** consulta autenticada do provedor e comparação com valores/idempotência.
- Webhook repetido ou fora de ordem: processe exatamente uma vez, sem pagar/duplicar o mesmo lançamento.
- Guardar comprovantes e dados sensíveis com proteção adequada, em ciclo de retenção LGPD.

## Plano de homologação
1. Confirmar exatamente a plataforma e revisar o contrato com o cliente.
2. Criar uma integração de **sandbox**, com IDs de pagamento fictícios e webhook assinado.
3. Simular duplicidade, pagamento parcial, estorno e indisponibilidade.
4. Conciliar com um extrato financeiro de sandbox e revisão humana.
5. Validar limite de cobranças para fevereiro e meses de 31 dias.
6. Ativar em produção **somente com autorização formal do responsável e prova de segurança.**

**Não realizar transações bancárias reais, nem inferir pagamento de texto ou comprovante.**
