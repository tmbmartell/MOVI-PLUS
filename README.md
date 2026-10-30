# MOVI+ — NOVAGENTE

Aplicativo de gestão financeira e acompanhamento do Clube do Motorista. Base atual: **V5 em produção privada**; **V8 redesenhada e novos módulos financeiros em revisão no GitHub**.

> **Atenção:** este repositório já está publicado no GitHub e sua visibilidade precisa ser tratada como **PÚBLICA** até uma mudança de configuração ser comprovada. Não subir chaves, senhas, dados de motoristas, documentos, backup, tokens ou mensagens reais. Uma revisão de histórico/segredos e decisão de visibilidade são obrigatórias antes da divulgação.

## Estado das versões (30/10/2026)
- **Produção:** V5 no servidor Hostinger, ainda sem Pix/conciliação bancária nem relatórios proativos ativados.
- **PR #1** — redesenho V8 do Arthur, termos com controladores/parceiros ainda não preenchidos.
- **PR #2** — página de fluxo financeiro e cadastro de despesas recorrentes.
- **PR #4** — integração da V8 aos módulos financeiros.
- **PR #5** — entrega automática opcional de relatório financeiro WhatsApp, link de acesso individual e timer **desligado por padrão**.
- **Issue #3** — única lista de marcos e percentual. **6/12 = 50% de desenvolvimento/marcos verificados**, não de habilitação da produção.

**Sequência:** as PRs estão encadeadas. **Não mesclar #1, #2, #4 e #5 independentemente** sem consolidar dependências para evitar conflitos e versões parciais.

## Segurança e liberação
- `python deploy/preflight_movi.py --data /caminho/do/data`: inspeção conservadora **somente leitura**, sem revelar credenciais.
- `python deploy/test_preflight_movi.py`: testes do verificador.
- `python deploy/test_release_journey.py`: prova funcional com dados fictícios: gestor, convite, aceite, aprovação, motorista e financeiro.
- `python deploy/test_finance_auto_report_v1.py`: WhatsApp **simulado** e autorização específica; sem contato real.
- O serviço `deploy/novagente-movi-report.service` e seu timer são **modelos não instalados**. Disparos reais exigem autorização e homologação.
- Termos legais no `legal_v8.py` contêm campos entre colchetes até que a pessoa jurídica responsável confirme as informações. Revisão jurídica ainda é mandatória.
- **Sem hostname público estável, sem liberação de MFA em todas as contas administrativas, sem prova de backup externo/restore e sem teste de celular e WAHA reais, não publicar.**
- `Pag.me` precisa ser identificado pelo contrato/API do cliente; **não confundir com Pagar.me, Pagou ou outros serviços**. Sem credencial oficial, homologação e assinatura de webhook, pagamento só pode ser autodeclarado.

## Documentação
- [Organograma e arquitetura](docs/arquitetura/ORGANOGRAMA.md)
- [Capturas de tela](docs/prints/INDICE-PRINTS.md)
- [Publicação e domínio](docs/publicacao/DOMINIO-E-DEPLOY.md)
- [Proteção contra segredos no Git](docs/publicacao/SEGURANCA.md)
- [Guia do relatório agendado](deploy/README_MOVI_AUTO_REPORT.md)
- [Especificação para integrar o provedor de cobrança](docs/publicacao/PAGME-INTEGRATION-CHECKLIST.md)
- [Mapa visual de arquitetura](docs/arquitetura/ARQUITETURA-VISUAL.svg)

**MOVI+** é a marca do aplicativo. **NOVAGENTE** é a empresa desenvolvedora.
