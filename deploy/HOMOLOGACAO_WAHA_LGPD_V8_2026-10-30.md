# MOVI+ · Etapa WAHA, LGPD e V8 em celular (30/10/2026)

## Situação WAHA (produção V5)
- Container `novagente-clube-motorista-waha` já ativo e restrito à porta local `127.0.0.1:18182`.
- Configuração cifrada no banco V5: URL local, sessão exclusiva `clube-motorista`, API key presente. **Não enviar chaves ou QR em texto ou logs.**
- Sessão consultada ao vivo em 30/10/2026: `SCAN_QR_CODE` (ainda não `WORKING`). A API WAHA retornou código 200 e base64 de imagem QR válido. O motor atual é WEBJS, com log `Cmd.refreshQR is not a function`: falha de renovação do QR.
- Patch pontual testado em QA (**10/10 casos**) e aplicado à V5, com cópia de rollback local: botões **Renovar QR travado** (somente sessão não conectada) e **Gerar código de pareamento** (telefone DDI+DDD, não persistido). O backend protege `WORKING`, exige administrador e não envia mensagem.
- Link do painel V5 autenticado: `https://rhythm-father-vacuum-spouse.trycloudflare.com/` → área **WhatsApp · Conexão**. A URL quick-tunnel é temporária, não usar como domínio de produção.
- Para finalizar: titular do telefone faz o vínculo no app WhatsApp, depois operador verifica `WORKING` no painel. Somente então realizar piloto autorizado de ida e volta. **Nunca ativar envios automáticos ou campanhas antes da homologação.**
- Se o WEBJS continuar falhando, avaliar engine GOWS em ambiente separado/backup, sem alterar containers WAHA de outros projetos. Referência: https://waha.devlike.pro/docs/how-to/engines/

## V8 — privacidade e LGPD
- Código candidata PR #6: `legal_v8.py` versão de aceite `2026-10-30.1`.
- Feitas correções de minimização/consentimento: marketing **opt-in OFF por padrão**, análises agregadas apresentadas como transparência contratual em vez de anuência de tratamento extra disfarçada de item obrigatório. 
- Testes sintéticos aprovados: `test_legal_v8.py`, `test_release_journey.py` 7/7, `test_finance_agent_waha.py` 9/9, `test_whatsapp_bridge.py` 10/10. A alteração jurídica permanece **somente no PR #6**; não foi implantada na V5 ativa.
- Falta: identificação jurídica do controlador, encarregado/DPO, contatos e endereço, prestadores e parceiros, finalidades, base legal por finalidade, retenção, políticas de acesso e aprovação jurídica independente. Revisar os fluxos de transparência de acesso do gestor a dados financeiros.
- Segurança V5: uma conta admin ativa, **0 administradores com MFA ativo** na verificação do banco de 30/10/2026. Titular deve vincular próprio autenticador; não gerar/reter seu TOTP em automação.
- Backup local criptografado verificado separadamente; cópia externa e recuperação operacional integral continuam pendentes.
- Repositório público: CNPJ de recebedor apareceu em commit antigo, ainda que HEAD use fixtures sintéticas. Avaliar reescrita do histórico com plano coordenado; não expor novamente ou reescrever automaticamente.

## V8 — homologação de celular (prévia privada)
- Instância QA isolada com **dois usuários fictícios**, duas transações sintéticas; flags WhatsApp e Pix OFF, sem dados reais. Serviço `novagente-movi-v8-qa.service` na porta `127.0.0.1:8894`, sem auto-start no reboot.
- **Tailnet only**, sem Funnel público: `https://srv1767127.tail508f09.ts.net:8455/`. Acesso exige Tailscale autorizado no celular.
- Contas: `moviqa_gestor` e `moviqa_motorista`. Senhas aleatórias em arquivo `/srv/margot/movi-v8-mobile-qa-20261030/access.txt` com permissão 0600; **não commitadas**.
- HTTPS e arquivos das telas V8 responderam 200. API administrativa sem login respondeu 401. A prévia ainda necessita QA de interação no celular físico, acessibilidade, zoom, teclado, contraste, formulários e navegação real.
- `deploy/test_browser_mobile_v1.py` foi tentado: `SKIP`, porque Chrome headless da VPS não iniciou sequer em `about:blank` dentro do limite operacional. **Não chamar isso de teste visual aprovado.**
- Verificar com celular: entrar em ambas contas; testar consentimento, entradas/despesas, relatório, menu do gestor, fluxo Pix sem valores reais e ausência de cortes/rolagem lateral. Registrar screenshots e problemas antes de mesclar PR #6.

## Critério de aceite de produção
Sem `WORKING` e piloto WAHA autorizado, MFA, revisão jurídica, domínio estável, cópia externa/restore e QA físico, **não mesclar nem publicar PR #6**. Percentual 6/12 = 50% dos marcos do projeto, inalterado.
