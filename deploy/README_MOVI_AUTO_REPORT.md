# MOVI+ relatório financeiro programado (piloto)

Esta funcionalidade tem **três travas independentes** e sai de fábrica desligada. Não instalar/ativar o timer no servidor de produção antes de homologar o WhatsApp com um motorista voluntário, o domínio HTTPS, os termos LGPD e os testes de segurança.

## Requisitos
- O motorista entra no MOVI+, autoriza o agente financeiro, vincula seu próprio WhatsApp e marca **Quero receber o relatório automaticamente** na página **Meu Fluxo Financeiro**.
- Gestor autenticado precisa ativar a chave de operação na API `PUT /api/admin/finance/auto-report` com `{"armed":true}`, usando cabeçalho `X-Requested-With: NOVAGENTE-V5` (após homologação).
- A unidade de agendamento instalada precisa receber `MOVI_REPORT_DELIVERY_ENABLED=1` e `MOVI_REPORT_PUBLIC_BASE_URL=https://dominio-real-publico.example` por `/etc/novagente/movi-report.env`. NÃO configurar até o domínio estar publicado, HTTPS confiável e acesso individual testado. Substituir `example` pelo domínio real; não deixar endereço demonstrativo.
- Sessão WAHA dedicada **clube-motorista**, recebimento HMAC e piloto individual ativos e conectados.

## Segurança operacional
1. Rodar o modo **dry-run** manualmente, por padrão: `python -m finance_auto_report_v1`. Este modo nunca envia mensagem.
2. Após homologação, instalar `deploy/novagente-movi-report.service` e `deploy/novagente-movi-report.timer` em `/etc/systemd/system/`. O timer consulta a cada hora.
3. O serviço tem `MOVI_REPORT_DELIVERY_ENABLED=0` por padrão; o arquivo de ambiente, administrado pelo operador, só passa para `1` quando tudo estiver pronto.
4. Apenas motoristas com consentimento específico e vínculo criptografado podem receber. Piloto atual: um motorista autorizado. Sem grupo, sem busca de contatos e sem divulgação de dados de outros motoristas.
5. Mensagens usam `finance_agent_pilot_v1.send_once` e imagens `send_chart_once`; existe reserva idempotente para motorista/frequência/período. Em falha incerta **não reenvia automaticamente**; verificar manualmente os logs.
6. O link `/relatorio/{token}` expira em 60 minutos e **exige login do próprio motorista**. Depois redireciona para `/meu-fluxo?month=AAAA-MM`. O endereço de relatório não é extrato bancário.
7. Mensal: dia 1, fechamento do mês anterior. Semanal: dia escolhido, visão do mês atual até a data. Apenas registros confirmados geram envio.
8. Para interromper imediatamente: desativar o gate administrativo (armed=false) e a flag do serviço. Alterações de consentimento e desvinculação do WhatsApp impedem futuras entregas.

## Testes
`deploy/test_finance_auto_report_v1.py` valida travas, autenticação, preferências, endereço HTTPS, relatórios semanal/mensal, vínculo, consentimento, duplicidade e links expirados **com transporte simulado e dados fictícios**.

**Limites:** não há conciliação Pix/ Pag.me, disparos reais em massa, ensaio de carga ou homologação de aparelho físico. A integração V8 e o timer não devem entrar em produção antes da revisão jurídica/segurança.
