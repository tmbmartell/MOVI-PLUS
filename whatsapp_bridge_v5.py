"""Preparação do emparelhamento WhatsApp WAHA, isolado de mensagens e Pix.

Admin configura a instância. Não conecta número até ação explícita.
Não cadastra webhook e não envia/recebe mensagens.
"""
import base64,ipaddress,json,re,socket,time
from urllib.parse import urlsplit
from fastapi import APIRouter,Depends,HTTPException
import httpx
from app import db,enc,dec,now,audit,admin

router=APIRouter()
PAIRING_PREVIEW=True
SEND_MESSAGES_ENABLED=False
INGEST_MESSAGES_ENABLED=False
_ALLOWED_SESSION=re.compile(r"^[a-z][a-z0-9_-]{2,39}$")
_throttle={}

def validate_host(raw):
 if not isinstance(raw,str):raise HTTPException(422,"Informe o endereço do servidor WAHA.")
 raw=raw.strip().rstrip("/")
 if len(raw)>220 or not raw:raise HTTPException(422,"Endereço inválido")
 u=urlsplit(raw)
 if u.scheme not in ("http","https") or not u.hostname or u.username or u.password or u.path not in ("","/") or u.query or u.fragment:
  raise HTTPException(422,"Informe a URL-base do WAHA, sem caminho, senha ou parâmetros.")
 try:port=u.port
 except ValueError:raise HTTPException(422,"Porta inválida.")
 hostname=u.hostname.lower()
 if u.scheme=="http":
  if hostname not in ("localhost","127.0.0.1","::1"):
   raise HTTPException(422,"Conexão HTTP permitida apenas em localhost.")
 else:
  if hostname in ("localhost","127.0.0.1","::1"):raise HTTPException(422,"Use HTTP em localhost.")
  # Tailscale: nome específico, nunca endereço arbitrário interno.
  if hostname.endswith(".ts.net"):
   if not re.fullmatch(r"[a-z0-9-]+(?:\.[a-z0-9-]+)+\.ts\.net",hostname):raise HTTPException(422,"Host Tailscale inválido")
  else:
   try:
    addresses=socket.getaddrinfo(hostname,port or 443,type=socket.SOCK_STREAM)
   except OSError:raise HTTPException(422,"Não foi possível confirmar o endereço HTTPS.")
   for a in addresses:
    ip=ipaddress.ip_address(a[4][0])
    if not ip.is_global:raise HTTPException(422,"Endereço HTTPS privado ou reservado não aceito.")
 return raw

def validate_session(value):
 if not isinstance(value,str) or not _ALLOWED_SESSION.fullmatch(value):
  raise HTTPException(422,"Sessão inválida. Use 3–40 caracteres, letras minúsculas, números, _ ou -.")
 if value in ("default","main"):raise HTTPException(422,"Use um nome exclusivo; não reutilize sessões compartilhadas.")
 return value

def ensure_table(c):
 c.execute("""CREATE TABLE IF NOT EXISTS whatsapp_bridge_config (
  id INTEGER PRIMARY KEY CHECK(id=1),
  encrypted BLOB NOT NULL,
  updated_at TEXT NOT NULL,
  actor INTEGER NOT NULL
 )""")

def config_get(c):
 ensure_table(c)
 row=c.execute("SELECT encrypted,updated_at FROM whatsapp_bridge_config WHERE id=1").fetchone()
 if not row:return None,None
 result=dec(row["encrypted"])
 return result,row["updated_at"]

def summary(conf,updated=None):
 return {"provider":"WAHA" if conf else None,
         "configured":bool(conf),"session":conf["session"] if conf else "clube-motorista",
         "base_url":conf["base_url"] if conf else "",
         "api_key_set":bool(conf and conf.get("api_key")),
         "updated_at":updated,"pairing_available":PAIRING_PREVIEW and bool(conf),
         "messaging_enabled":False,"webhook_enabled":False,
         "pix_enabled":False,
         "notice":"Conexão apenas para emparelhamento. Sem envio, recebimento automático ou armazenamento de mensagens WhatsApp."}

def throttle(uid,kind,seconds=4):
 k=(uid,kind)
 t=time.monotonic()
 if t-_throttle.get(k,0)<seconds:raise HTTPException(429,"Aguarde alguns segundos antes de tentar novamente.")
 _throttle[k]=t

def waha(conf,method,path,body=None,accept=None):
 headers={"X-Api-Key":conf["api_key"],"Accept":accept or "application/json"}
 # GET is safe to retry when WAHA is reconnecting the paired session.
 # Never retry POST/PUT/DELETE here: those may create sessions or send messages.
 attempts=2 if method.upper()=="GET" else 1
 timeout=httpx.Timeout(connect=4.0,read=12.0,write=7.0,pool=4.0)
 for attempt in range(attempts):
  try:
   with httpx.Client(timeout=timeout,follow_redirects=False,trust_env=False) as client:
    reply=client.request(method,conf["base_url"]+path,headers=headers,json=body)
   break
  except (httpx.RequestError,ValueError):
   if attempt+1<attempts:
    time.sleep(0.6)
    continue
   raise HTTPException(503,"A WAHA demorou para responder. A sessão pode estar reconectando. Aguarde alguns segundos e clique em Verificar conexão; não é necessário parear novamente.")
 if reply.status_code==404:return None,404
 if reply.status_code==401 or reply.status_code==403:
  raise HTTPException(503,"A chave de acesso WAHA foi recusada.")
 if reply.status_code>=300:
  raise HTTPException(503,"O provedor WAHA retornou erro HTTP "+str(reply.status_code)+".")
 return reply,reply.status_code

def extract_status(data):
 if not isinstance(data,dict):return {"status":"INDEFINIDO","connected":False}
 status=str(data.get("status","INDEFINIDO")).upper()[:40]
 me=data.get("me")
 # Não divulga número completo/identificador do titular.
 label="Conta vinculada" if isinstance(me,dict) and me.get("id") else None
 return {"status":status,"connected":status=="WORKING","account":label}

@router.get("/api/admin/whatsapp-bridge")
def bridge_config(u=Depends(admin)):
 with db() as c:
  cfg,updated=config_get(c)
 return summary(cfg,updated)

@router.put("/api/admin/whatsapp-bridge")
def bridge_save(data:dict,u=Depends(admin)):
 if not isinstance(data,dict) or data.get("provider") not in ("WAHA",None):
  raise HTTPException(422,"Provedor suportado nesta etapa: WAHA")
 url=validate_host(data.get("base_url",""))
 session=validate_session(data.get("session","clube-motorista"))
 key=data.get("api_key")
 if key is not None and (not isinstance(key,str) or len(key)>250 or "\n" in key or "\r" in key):
  raise HTTPException(422,"Chave de API inválida.")
 with db() as c:
  existing,_=config_get(c)
  if (not key) and existing:key=existing.get("api_key")
  if not key or len(key)<8:raise HTTPException(422,"Informe a chave de API WAHA (mínimo oito caracteres).")
  packed={"base_url":url,"session":session,"api_key":key}
  c.execute("INSERT INTO whatsapp_bridge_config(id,encrypted,updated_at,actor) VALUES(1,?,?,?) "
    "ON CONFLICT(id) DO UPDATE SET encrypted=excluded.encrypted,updated_at=excluded.updated_at,actor=excluded.actor",
    (enc(packed),now(),u["id"]))
  audit(c,u["id"],"whatsapp:config_saved","sem dados de credenciais")
  c.commit()
  return summary(packed,now())

@router.delete("/api/admin/whatsapp-bridge")
def bridge_clear(u=Depends(admin)):
 with db() as c:
  ensure_table(c)
  c.execute("DELETE FROM whatsapp_bridge_config WHERE id=1")
  audit(c,u["id"],"whatsapp:config_removed","nenhuma sessão WAHA foi apagada")
  c.commit()
 return {"ok":True,"notice":"Configuração local apagada. A sessão WAHA, se existente, não foi desligada nem excluída."}

def stored():
 with db() as c:conf,_=config_get(c)
 if not conf:raise HTTPException(409,"Configure primeiro URL, sessão e chave WAHA.")
 return conf

@router.post("/api/admin/whatsapp-bridge/check")
def bridge_check(u=Depends(admin)):
 throttle(u["id"],"check",3)
 cfg=stored()
 path="/api/sessions/"+cfg["session"]
 reply,status=waha(cfg,"GET",path)
 if status==404:return {"provider_reachable":True,"session_exists":False,"status":"NAO_CRIADA","connected":False}
 try:state=extract_status(reply.json())
 except ValueError:raise HTTPException(503,"WAHA respondeu em formato inesperado.")
 return {"provider_reachable":True,"session_exists":True,**state}

@router.post("/api/admin/whatsapp-bridge/create")
def bridge_create(u=Depends(admin)):
 throttle(u["id"],"create",5)
 cfg=stored()
 # A sessão exclusiva é criada PARADA; não gera QR automaticamente.
 r,code=waha(cfg,"GET","/api/sessions/"+cfg["session"])
 if code!=404:raise HTTPException(409,"A sessão já existe. Consulte seu status antes de prosseguir.")
 created,_=waha(cfg,"POST","/api/sessions",{"name":cfg["session"],"start":False})
 with db() as c:
  audit(c,u["id"],"whatsapp:session_prepared","dedicada, sem envio")
  c.commit()
 return {"ok":True,"status":"STOPPED","notice":"Sessão preparada em modo parado. Inicie manualmente para gerar o QR."}

@router.post("/api/admin/whatsapp-bridge/start")
def bridge_start(u=Depends(admin)):
 throttle(u["id"],"start",5)
 cfg=stored()
 reply,code=waha(cfg,"POST","/api/sessions/"+cfg["session"]+"/start",{})
 if code==404:raise HTTPException(404,"A sessão ainda não existe; crie-a antes.")
 with db() as c:
  audit(c,u["id"],"whatsapp:pairing_started","sem mensagens")
  c.commit()
 return {"ok":True,"notice":"Sessão iniciada apenas para autenticação. Abra o QR para emparelhar quando quiser."}

def _unpaired_conf():
 cfg=stored()
 resp,status=waha(cfg,"GET","/api/sessions/"+cfg["session"])
 if status==404:raise HTTPException(409,"Sessão não criada. Configure e inicie a sessão antes.")
 try:state=extract_status(resp.json())
 except ValueError:raise HTTPException(503,"Resposta WAHA inválida.")
 if state["connected"] or state["status"]=="WORKING":
  raise HTTPException(409,"WhatsApp já conectado. Não reinicie nem peça outro código.")
 if state["status"] not in ("SCAN_QR_CODE","STARTING","FAILED","STOPPED"):
  raise HTTPException(409,"Sessão não está aguardando pareamento.")
 return cfg,state

@router.post("/api/admin/whatsapp-bridge/refresh-qr")
def bridge_refresh_qr(u=Depends(admin)):
 """Explicit bounded recovery only for unpaired sessions when WEBJS QR is stale."""
 throttle(u["id"],"refresh_qr",12)
 cfg,state=_unpaired_conf()
 if state["status"]=="STARTING":
  raise HTTPException(409,"Sessão ainda iniciando. Consulte o status antes de reiniciar.")
 _,code=waha(cfg,"POST","/api/sessions/"+cfg["session"]+"/restart",{})
 if code==404:raise HTTPException(409,"Sessão não existe; crie-a antes.")
 with db() as c:
  audit(c,u["id"],"whatsapp:qr_manual_refresh","unpaired_session_only")
  c.commit()
 return {"ok":True,"status":"STARTING","notice":
  "Reinício solicitado apenas para a sessão não pareada. Aguarde SCAN_QR_CODE e mostre o novo QR."}

@router.post("/api/admin/whatsapp-bridge/request-code")
def bridge_request_pairing_code(data:dict,u=Depends(admin)):
 """Phone pairing fallback, with no phone or pairing code persistence or logging."""
 if not isinstance(data,dict) or set(data)!={"phone_number"}:
  raise HTTPException(422,"Informe apenas o telefone para vincular.")
 raw=data.get("phone_number")
 if not isinstance(raw,str) or not re.fullmatch(r"\+?[0-9]{10,15}",raw.strip()):
  raise HTTPException(422,"Informe DDI, DDD e telefone, somente números.")
 phone=raw.strip().lstrip("+")
 throttle(u["id"],"request_code",30)
 cfg,state=_unpaired_conf()
 if state["status"]!="SCAN_QR_CODE":
  raise HTTPException(409,"Aguarde a sessão indicar SCAN_QR_CODE antes de pedir código.")
 resp,code=waha(cfg,"POST","/api/"+cfg["session"]+"/auth/request-code",{"phoneNumber":phone})
 if not resp:raise HTTPException(503,"WAHA não retornou código de pareamento.")
 try:payload=resp.json()
 except ValueError:raise HTTPException(503,"WAHA retornou resposta inválida.")
 token=payload.get("code") if isinstance(payload,dict) else None
 if not isinstance(token,str) or not re.fullmatch(r"[A-Za-z0-9-]{4,20}",token):
  raise HTTPException(503,"Código não disponível nesta sessão. Use o QR Code.")
 with db() as c:
  audit(c,u["id"],"whatsapp:pairing_code_requested","no_phone_or_code_stored")
  c.commit()
 return {"code":token,"notice":"Código temporário. Digite no próprio WhatsApp, em Aparelhos conectados. Não compartilhe."}

@router.post("/api/admin/whatsapp-bridge/qr")
def bridge_qr(u=Depends(admin)):
 throttle(u["id"],"qr",4)
 cfg=stored()
 # QR expira rapidamente; nunca persistir nem logar base64 ou código.
 reply,code=waha(cfg,"GET","/api/"+cfg["session"]+"/auth/qr?format=image",accept="application/json")
 if code==404:raise HTTPException(409,"QR indisponível. Inicie a sessão e aguarde SCAN_QR_CODE.")
 if len(reply.content)>300000:raise HTTPException(503,"Imagem QR excedeu o tamanho permitido.")
 try:payload=reply.json()
 except ValueError:raise HTTPException(503,"Formato de QR incompatível com o WAHA.")
 encoded=payload.get("data") if isinstance(payload,dict) else None
 if not isinstance(encoded,str) or len(encoded)>270000:raise HTTPException(503,"WAHA não retornou imagem QR válida.")
 try:image=base64.b64decode(encoded,validate=True)
 except (ValueError,base64.binascii.Error):raise HTTPException(503,"QR retornado é inválido.")
 if not image.startswith(b"\x89PNG\r\n\x1a\n"):raise HTTPException(503,"QR não está em PNG.")
 return {"data_url":"data:image/png;base64,"+encoded,"expires_soon":True,
  "notice":"QR de autenticação temporário. Não compartilhe ou fotografe fora do pareamento."}
