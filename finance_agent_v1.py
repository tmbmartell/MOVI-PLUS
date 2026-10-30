"""Conservative financial agent MVP: opt-in, confirm-before-posting and ephemeral media.

No WAHA message polling, webhook registration or outgoing WhatsApp sending.
A separate WAHA adapter needs verified WhatsApp-to-user linking before activation.
"""
import base64,datetime,json,re,secrets,subprocess,asyncio,fcntl,os,sys,resource
from fastapi import APIRouter,Depends,File,UploadFile,HTTPException
from pathlib import Path
import httpx
from app import db,driver,admin,auth,enc,dec,cents,audit,now,DATA
from finance_agent_core import classify_text,validate_proposal,money_value,tips
from finance_agent_limits_v1 import route,OUT_OF_SCOPE,WELCOME,FINANCE_QUERY,usage,reserve,complete,refund,LIMITS

router=APIRouter()
MODEL_NAME="deepseek-flash"
TRANSCRIPTION_MODEL="gpt-4o-mini-transcribe"
PROVIDER_URL="https://api.deepseek.com"
LOCAL_WHISPER_MODEL=Path(__file__).resolve().parent/"models"/"whisper"/"base.pt"
LOCAL_WHISPER_WORKER=Path(__file__).resolve().parent/"whisper_local_worker.py"
MAX_IMAGE=6*1024*1024
MAX_AUDIO=7*1024*1024
MODEL_TIMEOUT=40

def init(c):
 c.executescript("""
 CREATE TABLE IF NOT EXISTS finance_agent_consent(
   uid INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
   enabled INTEGER NOT NULL DEFAULT 0,media_ai INTEGER NOT NULL DEFAULT 0,
   trends INTEGER NOT NULL DEFAULT 0,offers INTEGER NOT NULL DEFAULT 0,
   changed_at TEXT NOT NULL);
 CREATE TABLE IF NOT EXISTS finance_agent_config(
   id INTEGER PRIMARY KEY CHECK(id=1),
   config BLOB NOT NULL,
   changed_at TEXT NOT NULL);
 CREATE TABLE IF NOT EXISTS finance_agent_proposals(
   id INTEGER PRIMARY KEY,
   uid INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
   origin TEXT NOT NULL,
   status TEXT NOT NULL,
   encrypted BLOB NOT NULL,
   transaction_id INTEGER REFERENCES transactions(id) ON DELETE SET NULL,
   created_at TEXT NOT NULL,
   decided_at TEXT);
 CREATE INDEX IF NOT EXISTS idx_agent_proposals_uid ON finance_agent_proposals(uid,id);
 """)
 c.commit()
with db() as _c:
 init(_c)
 if not any(r["name"]=="text_ai" for r in _c.execute("PRAGMA table_info(finance_agent_consent)")):
  _c.execute("ALTER TABLE finance_agent_consent ADD COLUMN text_ai INTEGER NOT NULL DEFAULT 0")
  _c.commit()

def options(c,uid):
 r=c.execute("SELECT * FROM finance_agent_consent WHERE uid=?",(uid,)).fetchone()
 return dict(r) if r else {"uid":uid,"enabled":0,"media_ai":0,"trends":0,"offers":0,"text_ai":0,"changed_at":None}

def config(c):
 r=c.execute("SELECT config FROM finance_agent_config WHERE id=1").fetchone()
 return dec(r["config"]) if r else {}

def demand(c,uid,feature="enabled"):
 from finance_agent_release_v1 import released
 if not released(c):
  raise HTTPException(503,"O agente financeiro esta pausado para manutencao pelo Clube.")
 result=options(c,uid)
 if not result[feature]:
  msg="Antes de usar este recurso, habilite a autorização correspondente na área Agente financeiro."
  raise HTTPException(403,msg)
 return result

@router.get("/api/finance-agent/consent")
def get_options(u=Depends(driver)):
 with db() as c:return {"options":options(c,u["id"]),"default_disabled":True}

@router.put("/api/finance-agent/consent")
def update_options(data:dict,u=Depends(driver)):
 names=("enabled","media_ai","trends","offers","text_ai")
 if set(data) not in (set(names),set(names[:-1])) or any(type(data[k]) is not bool for k in data):
  raise HTTPException(422,"Escolhas de autorizacao invalidas.")
 with db() as c:
  prior=options(c,u["id"])
  text_ai=bool(data["text_ai"]) if "text_ai" in data else bool(prior.get("text_ai",False))
  c.execute("INSERT INTO finance_agent_consent(uid,enabled,media_ai,trends,offers,text_ai,changed_at) VALUES(?,?,?,?,?,?,?) "
   "ON CONFLICT(uid) DO UPDATE SET enabled=excluded.enabled,media_ai=excluded.media_ai,"
   "trends=excluded.trends,offers=excluded.offers,text_ai=excluded.text_ai,changed_at=excluded.changed_at",
   (u["id"],*[int(data[k]) for k in names[:-1]],int(text_ai),now()))
  audit(c,u["id"],"finance_agent:consent","consentimento atualizado, texto externo:"+str(int(text_ai)))
  c.commit()
 return {"ok":True,"options":{**data,"text_ai":text_ai}}

@router.get("/api/admin/finance-agent/provider")
def admin_provider(u=Depends(admin)):
 with db() as c:cfg=config(c)
 return {"provider":"DeepSeek","key_set":bool(cfg.get("api_key")),
         "vision_model":MODEL_NAME,"model_version":"DeepSeek V4.1 Flash",
         "transcription_model":"whisper-base-local","audio_transcription_ready":whisper_ready(),
         "whatsapp_sending":False,"whatsapp_receiving":False,
         "note":"Texto e imagens: DeepSeek V4.1 Flash. Audio: Whisper local na VPS, seguido de interpretacao pelo DeepSeek; arquivos originais nao sao armazenados."}

@router.put("/api/admin/finance-agent/provider")
def set_provider(data:dict,u=Depends(admin)):
 key=data.get("api_key")
 if not isinstance(key,str) or len(key)>250 or len(key)<25 or not key.startswith("sk-") or any(ch.isspace() for ch in key):
  raise HTTPException(422,"Informe uma chave de API válida. Ela não será devolvida pelo sistema.")
 with db() as c:
  c.execute("INSERT INTO finance_agent_config(id,config,changed_at) VALUES(1,?,?) "
    "ON CONFLICT(id) DO UPDATE SET config=excluded.config,changed_at=excluded.changed_at",
    (enc({"api_key":key,"provider":"deepseek"}),now()))
  audit(c,u["id"],"finance_agent:provider_configured","Chave privada configurada; sem exposicao de segredo")
  c.commit()
 return {"ok":True,"key_set":True}

@router.post("/api/admin/finance-agent/provider/check")
def check_deepseek(u=Depends(admin)):
 with db() as c:
  value=config(c).get("api_key")
 if not value:
  raise HTTPException(409,"Cadastre primeiro a chave do DeepSeek.")
 try:
  with httpx.Client(trust_env=False,follow_redirects=False,timeout=14.0) as client:
   reply=client.get(PROVIDER_URL+"/models",headers={"Authorization":"Bearer "+value})
  if reply.status_code in (401,403):
   raise HTTPException(422,"Credencial nao autorizada no DeepSeek.")
  if reply.status_code!=200:
   raise HTTPException(503,"Falha na verificacao da API DeepSeek, HTTP "+str(reply.status_code))
  matches=[m for m in reply.json().get("data",[]) if m.get("id")==MODEL_NAME]
  if not matches:raise HTTPException(503,"Este acesso nao retornou o modelo deepseek-flash.")
  return {"ok":True,"provider":"DeepSeek","model":MODEL_NAME,
   "vision":"image" in matches[0].get("input_modalities",[]),"audio_input":False}
 except (httpx.RequestError,ValueError):
  raise HTTPException(503,"Nao foi possivel consultar a API DeepSeek agora.")

@router.delete("/api/admin/finance-agent/provider")
def remove_provider(u=Depends(admin)):
 with db() as c:
  c.execute("DELETE FROM finance_agent_config WHERE id=1")
  audit(c,u["id"],"finance_agent:provider_removed");c.commit()
 return {"ok":True,"key_set":False}

def rate_guard(c,uid):
 # Prevent accidental unbounded proposal queues and multimedia API abuse.
 start=datetime.date.today().isoformat()
 count=c.execute("SELECT COUNT(*) FROM finance_agent_proposals WHERE uid=? AND created_at>=?",(uid,start)).fetchone()[0]
 pending=c.execute("SELECT COUNT(*) FROM finance_agent_proposals WHERE uid=? AND status='pending'",(uid,)).fetchone()[0]
 if count>=100 or pending>=150:
  raise HTTPException(429,"Limite diário ou fila de sugestões atingido. Confirme ou descarte registros antes de continuar.")

def add_proposal(c,uid,body):
 rate_guard(c,uid)
 cur=c.execute("INSERT INTO finance_agent_proposals(uid,origin,status,encrypted,created_at) VALUES(?,?,?,?,?)",
   (uid,body["source"],"pending",enc(body),now()))
 return cur.lastrowid

def deepseek_text(credential,message):
 result=llm_json(credential,[
  {"role":"system","content":SYSTEM_PROMPT+" A origem e texto escrito pelo motorista. Nao invente numeros. Retorne somente JSON."},
  {"role":"user","content":"Interprete a mensagem financeira: "+message[:1100]}
 ],max_tokens=350)
 result["source"]="text"
 result["summary"]=message[:350]
 return validate_proposal(result)

@router.get("/api/finance-agent/limits")
def finance_agent_limits(u=Depends(driver)):
 with db() as c:
  demand(c,u["id"])
  return usage(c,u["id"])

@router.post("/api/finance-agent/text")
def text_analyze(data:dict,u=Depends(driver)):
 if set(data)!={"text"} or not isinstance(data["text"],str):
  raise HTTPException(422,"Envie uma mensagem de texto.")
 raw=data["text"].strip()
 if not 1<=len(raw)<=1500:
  raise HTTPException(422,"Informe uma mensagem entre 1 e 1500 caracteres.")
 with db() as c:
  demand(c,u["id"])
  topic=route(raw)
  if topic!="record":
   reply={"out_of_scope":OUT_OF_SCOPE,"greeting":WELCOME,"query":FINANCE_QUERY}[topic]
   return {"saved":False,"in_scope":topic!="out_of_scope","reply":reply,
           "analysis_method":"resposta pronta (sem IA)","quota_used":False}
  try:proposal=classify_text(raw)
  except ValueError as e:raise HTTPException(422,str(e))
  grant=options(c,u["id"])
  credential=config(c).get("api_key") if grant.get("text_ai") and proposal["status"]!="ready" else None
 # Only financial messages requiring interpretation can spend an AI call.
 if credential:
  ticket=reserve(u["id"],"text_ai")
  try:
   proposal=deepseek_text(credential,raw)
   proposal["analysis_method"]="DeepSeek V4.1 Flash"
   with db() as c:
    demand(c,u["id"])
    uid=add_proposal(c,u["id"],proposal)
    audit(c,u["id"],"finance_agent:proposal","texto:ia")
    c.commit()
   complete(ticket)
  except Exception:
   refund(ticket)
   raise
  charged=True
 else:
  proposal["analysis_method"]="regras locais"
  with db() as c:
   demand(c,u["id"])
   uid=add_proposal(c,u["id"],proposal)
   audit(c,u["id"],"finance_agent:proposal","texto:local")
   c.commit()
  charged=False
 return {"id":uid,"proposal":proposal,"saved":False,"in_scope":True,
         "quota_used":charged,
         "notice":"Confira a sugestão. Nada será lançado até a sua confirmação."}

def read_mime(data):
 if data.startswith(b"\x89PNG\r\n\x1a\n"):return "image/png"
 if data.startswith(b"\xff\xd8\xff"):return "image/jpeg"
 if data.startswith(b"RIFF") and data[8:12]==b"WEBP":return "image/webp"
 if data.startswith(b"OggS"):return "audio/ogg"
 if data.startswith(b"ID3") or data[:2] in (b"\xff\xfb",b"\xff\xf3"):return "audio/mpeg"
 if data.startswith(b"RIFF") and data[8:12]==b"WAVE":return "audio/wav"
 if len(data)>12 and data[4:8]==b"ftyp":return "audio/mp4"
 raise HTTPException(422,"Use foto PNG/JPG/WebP ou áudio OGG/MP3/WAV/M4A.")

def llm_json(key,payload,max_tokens=900):
 try:
  with httpx.Client(trust_env=False,follow_redirects=False,timeout=MODEL_TIMEOUT) as client:
   r=client.post(PROVIDER_URL+"/chat/completions",
     headers={"Authorization":"Bearer "+key},
     json={"model":MODEL_NAME,"response_format":{"type":"json_object"},"thinking":{"type":"disabled"},
           "max_tokens":max_tokens,"messages":payload})
  if r.status_code!=200:raise HTTPException(503,"Leitura de imagem indisponível. A mídia não foi salva.")
  return json.loads(r.json()["choices"][0]["message"]["content"])
 except (httpx.RequestError,KeyError,ValueError,IndexError):
  raise HTTPException(503,"Não foi possível interpretar a imagem. Tente uma foto mais nítida.")

SYSTEM_PROMPT=(
 "Você extrai dados financeiros de comprovantes, notas de supermercado, posto de gasolina, farmácia, etc. "
 "Não copie nomes de pacientes, CPF, endereço, telefone ou dados de cartão. Não invente informações ausentes. "
 "Retorne SOMENTE JSON com as chaves: kind ('expense'|'income'|null), amount (número real ou null), "
 "merchant (string|null), date (AAAA-MM-DD|null), summary (breve texto em português), "
 "category (em despesas: 'Combustível','Supermercado','Farmácia','Manutenção do veículo',"
 "'Alimentação fora','Transporte','Casa e contas','Educação','Lazer e compras pessoais','Outros / a confirmar';"
 " em ENTRADAS: 'APLICATIVO' para Uber, 99, inDrive, Urbano Norte, corridas e passageiros,"
 " ou 'OUTROS' para valores extras, gorjetas, receitas avulsas e cliente particular),"
 "items ([{name,amount,nature}] apenas se itens legíveis). Se total estiver ilegível, amount=null. "
 "Não trate toda compra de supermercado como supérflua. Farmácia pode conter medicamentos essenciais e cosméticos. "
 "Posto de gasolina pode ser gasto de trabalho ou pessoal. Se não souber, marque 'a_confirmar'. "
 "Essencialidade de produtos depende do contexto da pessoa. "
 "Prefira pedir confirmação a afirmar um valor ou categoria duvidosos."
)

def image_analyze(key,blob,mime,caption):
 result=llm_json(key,[
  {"role":"system","content":SYSTEM_PROMPT},
  {"role":"user","content":[
    {"type":"text","text":"Leia a imagem anexada. Contexto fornecido pelo usuário: "+caption[:300]},
    {"type":"image_url","image_url":{"url":"data:"+mime+";base64,"+base64.b64encode(blob).decode(),"detail":"high"}}
  ]}
 ])
 result["source"]="image"
 return validate_proposal(result)

def interpret_transcribed_audio(key,text):
 # Audio already requires an independent consent and is processed via the same
 # explicitly configured provider. Returned figures are still unconfirmed.
 try:
  output=llm_json(key,[
   {"role":"system","content":SYSTEM_PROMPT+" A origem é uma transcrição falada, não uma imagem. Valores por extenso podem ser convertidos somente se inequívocos. Não crie valores não ditos."},
   {"role":"user","content":"Transcrição em português brasileiro: "+text[:1200]}
  ])
  output["source"]="audio"
  output["summary"]=text[:350]
  return validate_proposal(output)
 except HTTPException:
  # A provider/transcript parsing failure is not grounds to guess a number.
  proposal=classify_text(text)
  proposal["source"]="audio"
  proposal["summary"]=text[:350]
  return proposal

def whisper_ready():
 return LOCAL_WHISPER_MODEL.is_file() and LOCAL_WHISPER_WORKER.is_file()

def speech_to_text(blob,mime):
 """Run Whisper as a CPU-limited, memory-only subprocess; no external STT key."""
 if not whisper_ready():
  raise HTTPException(503,"O modelo local de voz nao esta disponivel.")
 # Guard the shared VPS against swap thrashing and protect other projects.
 try:
  meminfo=Path("/proc/meminfo").read_text()
  available_kb=int(next(l.split()[1] for l in meminfo.splitlines() if l.startswith("MemAvailable:")))
  if available_kb<1500000:
   raise HTTPException(503,"Servidor ocupado para transcrever audio. Tente novamente.")
 except (OSError,ValueError,StopIteration):
  raise HTTPException(503,"Nao foi possivel verificar os recursos do servidor.")
 lockpath=DATA/"finance_whisper.lock"
 with open(lockpath,"a+b") as lock:
  try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  except BlockingIOError:
   raise HTTPException(429,"Ja existe um audio sendo processado. Aguarde e tente novamente.")
  def limit():
   resource.setrlimit(resource.RLIMIT_CPU,(88,90))
   os.nice(8)
  try:
   result=subprocess.run(["/usr/bin/python3",str(LOCAL_WHISPER_WORKER)],
     input=blob,capture_output=True,timeout=105,
     env={**os.environ,"OMP_NUM_THREADS":"2","MKL_NUM_THREADS":"2",
          "OPENBLAS_NUM_THREADS":"2","TOKENIZERS_PARALLELISM":"false"},
     preexec_fn=limit,check=False)
  except subprocess.TimeoutExpired:
   raise HTTPException(503,"A transcricao ultrapassou o limite de tempo. Tente um audio mais curto.")
  except OSError:
   raise HTTPException(503,"O mecanismo de transcricao nao iniciou.")
  finally:fcntl.flock(lock,fcntl.LOCK_UN)
 if result.returncode!=0:
  raise HTTPException(422,"Nao foi possivel transcrever este audio. Tente falar mais claramente e evite ruido.")
 try:
  value=json.loads(result.stdout)
  text=value.get("text")
  if not isinstance(text,str) or not text.strip():
   raise ValueError("no transcript")
 except (json.JSONDecodeError,ValueError,AttributeError):
  raise HTTPException(503,"O transcritor retornou uma resposta invalida.")
 return text[:1500]

@router.post("/api/finance-agent/media")
async def media_analyze(file:UploadFile=File(...),u=Depends(driver)):
 with db() as c:
  demand(c,u["id"])
  demand(c,u["id"],"media_ai")
  rate_guard(c,u["id"])
  key=config(c).get("api_key")
 if not key:raise HTTPException(409,"O administrador ainda precisa configurar o provedor de IA para áudio e imagens.")
 blob=await file.read(MAX_AUDIO+1)
 if not blob or len(blob)>MAX_AUDIO:raise HTTPException(413,"O arquivo deve ter até 7MB.")
 mime=read_mime(blob)
 kind="image" if mime.startswith("image/") else "audio"
 ticket=reserve(u["id"],kind)
 try:
  if kind=="image":
   proposal=image_analyze(key,blob,mime,"")
  else:
   recognized=await asyncio.to_thread(speech_to_text,blob,mime)
   proposal=interpret_transcribed_audio(key,recognized)
  with db() as c:
   demand(c,u["id"])
   demand(c,u["id"],"media_ai")
   idx=add_proposal(c,u["id"],proposal)
   audit(c,u["id"],"finance_agent:proposal",mime)
   c.commit()
  complete(ticket)
 except Exception:
  refund(ticket)
  raise
 # The original media is not persisted; driver must confirm separately.
 return {"id":idx,"proposal":proposal,"saved":False,
  "quota_used":True,
  "notice":"Esta leitura é uma sugestão. Confirme ou corrija os dados antes de registrar."}

@router.get("/api/finance-agent/proposals")
def proposals(u=Depends(driver)):
 with db() as c:
  rows=c.execute("SELECT id,status,origin,encrypted,transaction_id,created_at FROM finance_agent_proposals "
   "WHERE uid=? ORDER BY id DESC LIMIT 60",(u["id"],)).fetchall()
  return {"items":[{"id":r["id"],"status":r["status"],"origin":r["origin"],
       "proposal":dec(r["encrypted"]),"created_at":r["created_at"],
       "transaction_id":r["transaction_id"]} for r in rows]}

@router.post("/api/finance-agent/proposals/{pid}/confirm")
def confirm(pid:int,data:dict,u=Depends(driver)):
 if set(data)!={"kind","amount","category","note","date"}:
  raise HTTPException(422,"Informe tipo, valor, categoria, observação e data.")
 kind=data["kind"]
 if kind not in ("income","expense"):raise HTTPException(422,"Escolha entrada ou despesa.")
 from finance_agent_core import CATEGORIES
 cat=data["category"]
 allowed=[x[0] for x in CATEGORIES]+["Outros","Outros / a confirmar","Corridas","Outras receitas","APLICATIVO","OUTROS"]
 if not isinstance(cat,str) or cat not in allowed:raise HTTPException(422,"Categoria inválida.")
 amount=cents(data["amount"])
 if amount<=0:raise HTTPException(422,"Valor deve ser maior que zero.")
 note=str(data["note"] or "")[:200]
 day=data["date"] or datetime.date.today().isoformat()
 try:record_date=datetime.date.fromisoformat(day)
 except (TypeError,ValueError):raise HTTPException(422,"Data inválida.")
 if record_date>datetime.date.today()+datetime.timedelta(days=1) or record_date<datetime.date.today()-datetime.timedelta(days=730):
  raise HTTPException(422,"Data fora do intervalo.")
 with db() as c:
  demand(c,u["id"])
  c.execute("BEGIN IMMEDIATE")
  r=c.execute("SELECT uid,status FROM finance_agent_proposals WHERE id=?",(pid,)).fetchone()
  if not r or r["uid"]!=u["id"]:raise HTTPException(404,"Sugestão não encontrada.")
  if r["status"]!="pending":raise HTTPException(409,"Esta sugestão já foi decidida. Não será lançada de novo.")
  cur=c.execute("INSERT INTO transactions(uid,kind,category,amount_cents,entry_date,note,at) VALUES(?,?,?,?,?,?,?)",
       (u["id"],kind,cat,amount,record_date.isoformat(),note,now()))
  c.execute("UPDATE finance_agent_proposals SET status='confirmed',transaction_id=?,decided_at=? WHERE id=?",
       (cur.lastrowid,now(),pid))
  audit(c,u["id"],"finance_agent:confirmed",str(pid))
  c.commit()
 return {"ok":True,"transaction_id":cur.lastrowid,"note":"Registro autodeclarado e confirmado por você. Não houve transferência bancária."}

@router.post("/api/finance-agent/proposals/{pid}/discard")
def discard(pid:int,u=Depends(driver)):
 with db() as c:
  row=c.execute("UPDATE finance_agent_proposals SET status='discarded',decided_at=? "
   "WHERE id=? AND uid=? AND status='pending'",(now(),pid,u["id"]))
  if not row.rowcount:raise HTTPException(409,"Sugestão não disponível ou já decidida.")
  audit(c,u["id"],"finance_agent:discarded",str(pid))
  c.commit()
 return {"ok":True}

@router.get("/api/finance-agent/insights")
def insights(u=Depends(driver)):
 with db() as c:
  demand(c,u["id"])
  demand(c,u["id"],"trends")
  month=datetime.date.today().strftime("%Y-%m")
  prior=(datetime.date.today().replace(day=1)-datetime.timedelta(days=1)).strftime("%Y-%m")
  def sums(code):
   return {r["category"]:round(r["total"]/100,2) for r in c.execute(
      "SELECT category,SUM(amount_cents) total FROM transactions WHERE uid=? AND kind='expense' "
      "AND substr(entry_date,1,7)=? GROUP BY category",(u["id"],code))}
  amounts=sums(month)
  prev=sums(prior)
  total=round(sum(amounts.values()),2)
  advice=tips(list(amounts),amounts)
  return {"month":month,"expenses":amounts,"last_month":prev,"total":total,
          "advice":advice,"source":"Registros manuais/confirmados; sem integração bancária",
          "offers_used":False,"notice":"Sugestões educativas baseadas em seus registros. Não substituem orientação profissional ou aconselhamento médico."}
