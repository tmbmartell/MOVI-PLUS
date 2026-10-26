"""MOVI+ V8 · Termos de Uso, Política de Privacidade e Política de Cookies, com aceite registrado.

Fonte única do texto jurídico: a API (/api/legal), a página pública (/termos) e o app usam este
arquivo. Cada aceite guarda versão, data e escolhas (LGPD art. 8º §2º: o ônus da prova é do
controlador). Consentimentos opcionais continuam livres e revogáveis (arts. 8º §5º e 18 IX).

ANTES DE PUBLICAR: preencha CONTROLLER e PARTNERS e peça revisão jurídica do texto.
"""
import json,hashlib,html,re
from fastapi import APIRouter,Depends,HTTPException,Request
from fastapi.responses import HTMLResponse,JSONResponse
from app import db,driver,auth,audit,now,consent

router=APIRouter()

# Mudou o texto ou as finalidades? Aumente a versão: todos os motoristas aceitam de novo (art. 8º §6º).
VERSION="2026-10-26.2"

# Identificação do controlador e do encarregado (arts. 9º III-IV e 41 §1º). Trocar os marcadores.
CONTROLLER={
 "name":"[RAZÃO SOCIAL DO CONTROLADOR]",
 "cnpj":"[CNPJ]",
 "address":"[ENDEREÇO COMPLETO]",
 "contact":"[E-MAIL DE CONTATO]",
 "dpo_name":"[NOME DO ENCARREGADO PELO TRATAMENTO DE DADOS]",
 "dpo_email":"[E-MAIL DO ENCARREGADO]",
 "hosting":"[NOME DO PROVEDOR DE HOSPEDAGEM]",
 "backup_days":"[PRAZO, EM DIAS, DOS BACKUPS]",
}
# Consentimento para parceiros precisa dizer quem são e para quê (arts. 7º §5º, 8º §4º e 9º V).
PARTNERS="[LISTA DE PARCEIROS, por exemplo concessionárias e instituições financeiras do Programa de Renovação de Frota]"
PARTNERS_PURPOSE="apresentar ofertas de troca de carro, financiamento e condições especiais do Programa de Renovação de Frota"

# Itens obrigatórios: não são consentimento para fins extras; são ciência e aceite do contrato
# (art. 7º V), com as análises internas feitas por legítimo interesse (art. 7º IX), sempre informadas.
REQUIRED=[
 ("terms","Li e aceito os Termos de Uso do MOVI+."),
 ("privacy","Li a Política de Privacidade e entendi quais dados são usados, para quê e quais são os meus direitos."),
 ("cookies","Estou ciente de que o MOVI+ usa só um cookie, necessário para manter meu login."),
 ("analytics","Permito que meus dados sejam usados para análises e aprimoramento do sistema MOVI+, de forma agregada, sem divulgar quem eu sou."),
 ("adult","Tenho 18 anos ou mais."),
 ("money","Entendo que o MOVI+ não movimenta meu dinheiro, não acessa minha conta no banco e não é consultoria financeira profissional."),
 ("truth","As informações que eu colocar serão verdadeiras, e meu acesso é pessoal: não vou passar minha senha para ninguém."),
]
# Itens opcionais: consentimento livre, específico e destacado. Chaves iguais à tabela consents.
OPTIONAL=[
 ("marketing","Receber propostas e ofertas novas do MOVI+ dentro do aplicativo. Já vem ligado; você pode desligar quando quiser em Privacidade."),
 ("assisted_entry","O gestor pode ver e preencher o meu cadastro por mim (ele vê minhas respostas e meus totais de ganhos e gastos)."),
 ("insights","Permito que o gestor veja o meu cadastro e os meus totais de ganhos e gastos."),
 ("sharing","Permito que o sistema MOVI+ compartilhe minhas informações de cadastro com os parceiros listados na Política de Privacidade, para "+PARTNERS_PURPOSE+"."),
 ("identity_collection","Permito guardar meus dados pessoais (nome completo, CPF, RG, nascimento, contato, endereço, placa e CNH), com proteção, para o Programa de Renovação de Frota."),
 ("documents","Permito que o gestor consulte os documentos que eu enviar, quando isso estiver liberado."),
]
CONSENT_KEYS=("insights","marketing","sharing","documents","assisted_entry","identity_collection")
# Ofertas do próprio MOVI+ no app: legítimo interesse (art. 7º IX), ligado por padrão e com
# oposição a qualquer momento (art. 18 §2º). Não vale para parceiros, que seguem por consentimento.
DEFAULT_ON=("marketing",)
# Consentimento não pode vir pré-marcado (art. 5º XII): o motorista precisa responder Sim ou Não.
MUST_ANSWER=("assisted_entry",)

def _sections():
 c=CONTROLLER
 return [
 {"id":"termos","title":"Termos de Uso","parts":[
  ("1. O que é o MOVI+","O MOVI+ (Clube do Motorista) é um aplicativo para motoristas de aplicativo organizarem o que ganham e o que gastam, planejarem o próprio dinheiro e participarem do Clube. Ele é oferecido por "+c["name"]+", CNPJ "+c["cnpj"]+", "+c["address"]+"."),
  ("2. O que o MOVI+ não é","O MOVI+ não é banco, não guarda nem movimenta dinheiro, não faz Pix, não acessa sua conta bancária e não dá consultoria financeira ou de investimentos. Os valores que aparecem são os que você mesmo anotou. Eles não provam renda e não garantem crédito."),
  ("3. Quem pode usar","Só pessoas com 18 anos ou mais, convidadas pelo Clube. Depois do pedido de acesso, o gestor aprova o cadastro. O acesso é pessoal: não compartilhe sua senha. Se desconfiar que alguém usou sua conta, troque a senha e avise o Clube."),
  ("4. Suas responsabilidades","Colocar informações verdadeiras, não usar o MOVI+ para fraude ou para prejudicar outras pessoas, não tentar invadir ou sobrecarregar o sistema e não enviar documentos de outras pessoas."),
  ("5. Assistente e leitura de fotos e áudios","O assistente sugere como anotar o que você escreve, fotografa ou fala. Ele pode errar: confira sempre antes de salvar. Nada é salvo sem a sua confirmação. Fotos e áudios só são lidos se você ligar essa opção em Foto e áudio, onde explicamos para onde eles vão."),
  ("6. Benefícios e pontos","Os pontos medem sua participação (cadastro respondido e dias com anotações). Pontos não são dinheiro, não podem ser trocados por dinheiro e não dão direito automático a benefícios. Cada pedido de benefício é analisado por uma pessoa do Clube, conforme a quantidade disponível."),
  ("7. Funcionamento","Trabalhamos para o MOVI+ funcionar bem e com segurança, mas ele pode ficar fora do ar para manutenção ou por falhas. Quando isso acontecer, vamos trabalhar para normalizar o serviço o quanto antes. Nada nestes termos tira os direitos que a lei garante a você, incluindo o Código de Defesa do Consumidor."),
  ("8. Preço","Nesta fase, o uso do MOVI+ é gratuito para o motorista convidado. Se algum dia houver cobrança, você será avisado antes e poderá recusar e encerrar a conta."),
  ("9. Encerrar a conta","Você pode pedir para apagar sua conta e seus dados a qualquer momento, em Mais › Privacidade. O Clube pode suspender um acesso usado de forma irregular ou contra estes termos, avisando o motivo."),
  ("10. Mudanças nestes termos","Se os termos mudarem, você será avisado no aplicativo, com as mudanças em destaque, e precisará aceitar de novo para continuar. Se não concordar, pode encerrar a conta."),
  ("11. Lei e foro","Estes termos seguem as leis do Brasil. Eventuais disputas podem ser levadas ao foro da cidade onde você mora."),
 ]},
 {"id":"privacidade","title":"Política de Privacidade","parts":[
  ("1. Quem cuida dos seus dados","Controlador: "+c["name"]+", CNPJ "+c["cnpj"]+", "+c["address"]+". Contato: "+c["contact"]+". Encarregado pelo tratamento de dados pessoais: "+c["dpo_name"]+", e-mail "+c["dpo_email"]+"."),
  ("2. Quais dados usamos","(a) Conta: nome, usuário e senha (a senha fica guardada de forma que nem nós conseguimos ler). (b) Anotações: ganhos, gastos, datas e observações que você colocar. (c) Cadastro: respostas sobre trabalho, renda, bancos, carro e metas. (d) Dados pessoais e documentos, só se você permitir: nome completo, CPF, RG, nascimento, e-mail, endereço, celular, placa e CNH. (e) Conversas com o assistente e, se você ligar, fotos e áudios enviados. (f) Registros de acesso: data, hora e endereço IP de cada acesso, e o cookie de login."),
  ("3. Para que usamos e com qual base legal","Para criar e manter sua conta e mostrar suas anotações e totais: execução do contrato (LGPD art. 7º, V). Para segurança, prevenção de fraude e para analisar e melhorar o sistema com dados agregados, sem divulgar quem você é: legítimo interesse (art. 7º, IX); você pode se opor, falando com o encarregado. Para guardar registros de acesso por 6 meses: obrigação legal (Marco Civil da Internet, art. 15). Para mostrar ofertas e propostas do próprio MOVI+ dentro do aplicativo: legítimo interesse (art. 7º, IX); essa opção já vem ligada e você pode desligar quando quiser em Mais › Privacidade. Para o gestor ver ou preencher seu cadastro, para compartilhar com parceiros, para guardar dados pessoais e documentos e para ler fotos e áudios: só com o seu consentimento (art. 7º, I), que você pode retirar quando quiser."),
  ("4. Com quem compartilhamos","(a) Gestor do Clube: vê seus números e seu cadastro só se você permitir. (b) Parceiros: só se você permitir. Parceiros: "+PARTNERS+". Finalidade: "+PARTNERS_PURPOSE+". (c) Serviço de inteligência artificial DeepSeek: recebe fotos e textos só quando você liga a leitura de fotos e áudios, o que pode envolver envio dos dados para fora do Brasil; por isso pedimos esse consentimento em destaque, na hora (art. 33, VIII). (d) Empresas que nos prestam serviço, como hospedagem ("+c["hosting"]+"), seguindo nossas instruções. (e) Autoridades, quando a lei ou um juiz exigir. Não vendemos seus dados."),
  ("5. Por quanto tempo guardamos","Enquanto sua conta existir. Se você pedir para apagar, apagamos do sistema, salvo o que a lei manda guardar (como os registros de acesso por 6 meses). Cópias de segurança são apagadas em até "+c["backup_days"]+" dias."),
  ("6. Como protegemos","Senhas guardadas com proteção forte, dados de cadastro e documentos criptografados, acesso separado por pessoa e registro de ações sensíveis. Nenhum sistema é 100% seguro: se acontecer um incidente que possa causar risco ou dano relevante, avisaremos você e a ANPD."),
  ("7. Seus direitos (LGPD art. 18)","Saber se tratamos seus dados; ver e baixar seus dados; corrigir; pedir anonimização, bloqueio ou eliminação do que for desnecessário; portabilidade; apagar dados tratados com consentimento; saber com quem compartilhamos; saber o que acontece se não consentir; retirar o consentimento a qualquer momento; e se opor a tratamentos. Muita coisa você faz sozinho em Mais › Privacidade; o resto, pelo e-mail do encarregado. Você também pode reclamar à Autoridade Nacional de Proteção de Dados (ANPD)."),
  ("8. Se você não consentir","Os itens opcionais não são obrigatórios. Sobre o gestor preencher seu cadastro, você responde Sim ou Não: sem eles, você continua usando o MOVI+ para anotar e acompanhar seu dinheiro. Só deixa de ter a função ligada a cada um (por exemplo, sem permitir dados pessoais, não dá para enviar a CNH)."),
  ("9. Decisões automáticas","O MOVI+ não toma decisões só automáticas que afetem seus direitos. O assistente apenas sugere, e os benefícios são decididos por uma pessoa. Se quiser, pode pedir revisão de qualquer sugestão ou cálculo pelo e-mail do encarregado."),
  ("10. Idade","O MOVI+ é só para maiores de 18 anos."),
  ("11. Mudanças nesta política","Se mudarmos finalidades, dados ou compartilhamentos, avisaremos com destaque no aplicativo antes, e você poderá retirar seu consentimento."),
 ]},
 {"id":"cookies","title":"Política de Cookies","parts":[
  ("1. O que usamos","O MOVI+ usa um único cookie, chamado clube_session. Ele guarda um código de sessão para você continuar logado por até 12 horas. Ele é protegido (HttpOnly, Secure e SameSite) e não guarda seus dados pessoais."),
  ("2. Por que não pedimos para aceitar cookies","Esse cookie é estritamente necessário: sem ele não dá para entrar no aplicativo. Por isso ele não depende de consentimento, mas informamos aqui o que ele faz."),
  ("3. O que não usamos","Não usamos cookies de propaganda, rastreamento ou estatísticas de terceiros. Se isso mudar, vamos pedir sua permissão antes, com a opção de recusar."),
  ("4. Como apagar","Você pode apagar os cookies no seu navegador quando quiser. Ao apagar, você sai da conta e precisa entrar de novo."),
 ]},
 ]

def legal_payload():
 return {"version":VERSION,"controller":CONTROLLER,"sections":[{"id":s["id"],"title":s["title"],"parts":[{"title":t,"text":x} for t,x in s["parts"]]} for s in _sections()],
  "required":[{"id":k,"text":t} for k,t in REQUIRED],"optional":[{"id":k,"text":t} for k,t in OPTIONAL],
  "default_on":list(DEFAULT_ON),"must_answer":list(MUST_ANSWER)}

def init(c):
 c.execute("""CREATE TABLE IF NOT EXISTS legal_acceptances(
  id INTEGER PRIMARY KEY,uid INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  version TEXT NOT NULL,accepted_at TEXT NOT NULL,required TEXT NOT NULL,optional TEXT NOT NULL,
  origin TEXT NOT NULL,ip_hash TEXT)""")
 c.execute("CREATE INDEX IF NOT EXISTS idx_legal_uid ON legal_acceptances(uid,id)")
with db() as _c:init(_c);_c.commit()

def validate(data):
 """Confere o aceite enviado pelo app. Devolve (obrigatórios, opcionais)."""
 if not isinstance(data,dict):
  raise HTTPException(422,"Para continuar, é preciso ler e aceitar os Termos de Uso.")
 if data.get("version")!=VERSION:
  raise HTTPException(409,"Os termos foram atualizados. Abra e aceite a versão nova.")
 req=data.get("required");opt=data.get("optional")
 if not isinstance(req,dict) or any(req.get(k) is not True for k,_ in REQUIRED):
  raise HTTPException(422,"Para continuar, é preciso marcar todos os itens obrigatórios dos termos.")
 if not isinstance(opt,dict) or any(k not in dict(OPTIONAL) or type(v) is not bool for k,v in opt.items()):
  raise HTTPException(422,"Escolhas opcionais inválidas.")
 if any(type(opt.get(k)) is not bool for k in MUST_ANSWER):
  raise HTTPException(422,"Responda se o gestor pode ver e preencher o seu cadastro.")
 chosen={k:bool(opt.get(k,False)) for k,_ in OPTIONAL}
 # O servidor só deixa o gestor preencher quem também permite que ele veja o cadastro.
 if chosen["assisted_entry"]:chosen["insights"]=True
 return {k:True for k,_ in REQUIRED},chosen

def _ip_hash(req):
 ip=(req.headers.get("x-forwarded-for","").split(",")[0].strip() or (req.client.host if req.client else "")) if req else ""
 return hashlib.sha256(("movi8|"+ip).encode()).hexdigest() if ip else None

def record(c,uid,req_items,opt_items,origin,req=None):
 """Grava o aceite e aplica as escolhas opcionais nas permissões do motorista."""
 init(c)
 c.execute("INSERT INTO legal_acceptances(uid,version,accepted_at,required,optional,origin,ip_hash) VALUES(?,?,?,?,?,?,?)",
  (uid,VERSION,now(),json.dumps(req_items),json.dumps(opt_items),origin,_ip_hash(req)))
 if not c.execute("SELECT uid FROM consents WHERE uid=?",(uid,)).fetchone():
  c.execute("INSERT INTO consents(uid,updated_at) VALUES(?,?)",(uid,now()))
 previous=consent(c,uid)
 c.execute("UPDATE consents SET "+",".join(k+"=?" for k in CONSENT_KEYS)+",updated_at=? WHERE uid=?",
  (*[int(opt_items[k]) for k in CONSENT_KEYS],now(),uid))
 c.execute("INSERT INTO privacy_events(uid,choices,at) VALUES(?,?,?)",(uid,json.dumps({"legal_version":VERSION,**opt_items}),now()))
 if bool(previous.get("identity_collection"))!=opt_items["identity_collection"]:
  audit(c,uid,"identity_collection:granted" if opt_items["identity_collection"] else "identity_collection:revoked","aceite dos termos")
 audit(c,uid,"legal:accepted",VERSION)

def accepted_version(c,uid):
 init(c)
 r=c.execute("SELECT version,accepted_at FROM legal_acceptances WHERE uid=? ORDER BY id DESC LIMIT 1",(uid,)).fetchone()
 return dict(r) if r else None

@router.get("/api/legal")
def get_legal():return legal_payload()

@router.get("/api/legal/status")
def status(u=Depends(driver)):
 with db() as c:last=accepted_version(c,u["id"]);choices=consent(c,u["id"])
 return {"current":VERSION,"accepted":last,"needs":not last or last["version"]!=VERSION,
  "choices":{k:bool(choices[k]) for k in CONSENT_KEYS}}

@router.post("/api/legal/accept")
def accept(data:dict,req:Request,u=Depends(driver)):
 req_items,opt_items=validate(data)
 with db() as c:
  record(c,u["id"],req_items,opt_items,"login",req);c.commit()
 return {"ok":True,"version":VERSION}

@router.get("/api/legal/history")
def history(u=Depends(driver)):
 with db() as c:
  init(c)
  rows=[{**dict(r),"required":json.loads(r["required"]),"optional":json.loads(r["optional"])} for r in
   c.execute("SELECT version,accepted_at,required,optional,origin FROM legal_acceptances WHERE uid=? ORDER BY id",(u["id"],))]
 return {"items":rows}

@router.get("/termos",response_class=HTMLResponse)
def public_page():
 """Termos e políticas abertos ao público, sem login (LGPD art. 9º; Marco Civil art. 7º XI)."""
 e=html.escape
 body="".join('<section id="'+s["id"]+'"><h2>'+e(s["title"])+'</h2>'+"".join('<h3>'+e(t)+'</h3><p>'+e(x)+'</p>' for t,x in s["parts"])+'</section>' for s in _sections())
 nav=" · ".join('<a href="#'+s["id"]+'">'+e(s["title"])+'</a>' for s in _sections())
 page=('<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
  '<meta name="robots" content="noindex"><title>Termos e Privacidade · MOVI+</title><link rel="icon" type="image/svg+xml" href="/assets/movi-icon.svg"><style>'
  ':root{color-scheme:dark}body{margin:0;background:#061a24;color:#f5f3ee;font:18px/1.6 ui-sans-serif,-apple-system,"Segoe UI",Roboto,Arial,sans-serif}'
  'main{max-width:760px;margin:0 auto;padding:24px 18px 64px}h1{font-size:32px;margin:8px 0}h2{font-size:26px;margin:40px 0 8px;color:#f2ae40}'
  'h3{font-size:19px;margin:22px 0 4px}p{margin:0;color:#d3dde1}a{color:#f2ae40}.v{color:#bacbd2;font-size:16px}</style></head><body><main>'
  '<h1>Termos e Privacidade do MOVI+</h1><p class="v">Versão '+e(VERSION)+'</p><p>'+nav+'</p>'+body+'</main></body></html>')
 return HTMLResponse(page)

# Caminhos liberados para quem ainda não aceitou a versão atual: ler e aceitar os termos,
# sair, trocar senha e exercer direitos (baixar dados, pedir exclusão, retirar permissões).
# /api/schema é só a lista de perguntas (sem dados pessoais) e o app precisa dela ao abrir.
OPEN=re.compile(r"^/api/(me|login|logout|enroll|password|schema|legal(/.*)?|privacy/.*|consents)$")

def install(app):
 @app.middleware("http")
 async def legal_gate(req,call_next):
  path=req.url.path
  if path.startswith("/api/") and not OPEN.match(path) and req.cookies.get("clube_session"):
   try:u=auth(req)
   except HTTPException:u=None
   if u and u["role"]=="driver":
    with db() as c:last=accepted_version(c,u["id"])
    if not last or last["version"]!=VERSION:
     return JSONResponse({"detail":"Aceite os termos atualizados para continuar.","legal_required":True},status_code=428)
  return await call_next(req)
