"""NOVAGENTE Clube do Motorista V5. Banco e WhatsApp SEM INTEGRAÇÃO."""
import os,re,json,secrets,hashlib,hmac,sqlite3,datetime,time,csv,io,uuid,base64
from pathlib import Path
from decimal import Decimal,InvalidOperation,ROUND_HALF_UP
from contextlib import contextmanager
from collections import defaultdict
from urllib.parse import urlparse
from fastapi import FastAPI,Request,Response,HTTPException,UploadFile,File,Depends
from fastapi.responses import FileResponse,JSONResponse
from fastapi.staticfiles import StaticFiles
from cryptography.fernet import Fernet,InvalidToken
from schema import ORIGINAL,EXTRA,ALL,MAP,SENSITIVE,describe,active_fields,progress
ROOT=Path(__file__).resolve().parent
DATA=Path(os.environ.get("CLUBE_DATA",str(ROOT/"data"))).resolve()
DATA.mkdir(parents=True,exist_ok=True,mode=0o700);os.chmod(DATA,0o700)
DOCS=DATA/"documents";DOCS.mkdir(exist_ok=True,mode=0o700)
DB=DATA/"v5.sqlite3";KEY=DATA/".encryption-key"
if not KEY.exists():KEY.write_bytes(Fernet.generate_key());KEY.chmod(0o600)
cipher=Fernet(KEY.read_bytes())
SENSITIVE_ENABLED=os.getenv("CLUBE_ENABLE_SENSITIVE","0")=="1"
if SENSITIVE_ENABLED and not os.getenv("CLUBE_APPROVED_HOST"):raise RuntimeError("Host validado exigido para coleta protegida.")
app=FastAPI(title="NOVAGENTE Clube do Motorista",version="5.0",docs_url=None,redoc_url=None,openapi_url=None)
app.mount("/assets",StaticFiles(directory=ROOT/"static"),name="assets")
@contextmanager
def db():
 c=sqlite3.connect(str(DB),timeout=15);c.row_factory=sqlite3.Row
 c.execute("PRAGMA foreign_keys=ON");c.execute("PRAGMA busy_timeout=15000")
 try:yield c
 finally:c.close()
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
def stamp():return int(time.time())
def sha(v):return hashlib.sha256(v.encode()).hexdigest()
def password_hash(p):
 salt=secrets.token_bytes(16)
 h=hashlib.scrypt(p.encode(),salt=salt,n=16384,r=8,p=1,dklen=32)
 return "scrypt$"+base64.b64encode(salt).decode()+"$"+base64.b64encode(h).decode()
def password_ok(p,v):
 try:
  algo,s,h=v.split("$")
  return algo=="scrypt" and hmac.compare_digest(hashlib.scrypt(p.encode(),salt=base64.b64decode(s),n=16384,r=8,p=1,dklen=32),base64.b64decode(h))
 except Exception:return False
def enc(v):return cipher.encrypt(json.dumps(v,ensure_ascii=False).encode())
def dec(v):
 try:return json.loads(cipher.decrypt(v))
 except InvalidToken:raise HTTPException(500,"Erro de descriptografia")
def cents(v):
 try:
  d=Decimal(str(v).replace(",","."))
  if not d.is_finite() or d<0 or d>100000000:raise ValueError()
  return int((d*100).quantize(Decimal("1"),rounding=ROUND_HALF_UP))
 except (ValueError,InvalidOperation):raise HTTPException(422,"Valor inválido")
def audit(c,uid,action,target=""):
 c.execute("INSERT INTO audit(actor,action,target,at) VALUES(?,?,?,?)",(uid,action,str(target)[:70],now()))
def init():
 with db() as c:
  c.executescript("""
PRAGMA journal_mode=WAL;
CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, username TEXT UNIQUE NOT NULL, phash TEXT NOT NULL,role TEXT NOT NULL,status TEXT NOT NULL,name TEXT NOT NULL,created_at TEXT NOT NULL,must_change INTEGER NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS sessions(hash TEXT PRIMARY KEY,uid INTEGER REFERENCES users(id) ON DELETE CASCADE,expires INTEGER);
CREATE TABLE IF NOT EXISTS invites(hash TEXT PRIMARY KEY,admin_id INTEGER,expires INTEGER,used_uid INTEGER,created_at TEXT);
CREATE TABLE IF NOT EXISTS consents(uid INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,insights INTEGER DEFAULT 0,marketing INTEGER DEFAULT 0,sharing INTEGER DEFAULT 0,documents INTEGER DEFAULT 0,updated_at TEXT);
CREATE TABLE IF NOT EXISTS privacy_events(id INTEGER PRIMARY KEY,uid INTEGER REFERENCES users(id) ON DELETE CASCADE,choices TEXT,at TEXT);
CREATE TABLE IF NOT EXISTS profiles(uid INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,encrypted BLOB NOT NULL,updated_at TEXT);
CREATE TABLE IF NOT EXISTS transactions(id INTEGER PRIMARY KEY,uid INTEGER REFERENCES users(id) ON DELETE CASCADE,kind TEXT,category TEXT,amount_cents INTEGER,entry_date TEXT,note TEXT,at TEXT);
CREATE INDEX IF NOT EXISTS idx_transactions_user_date ON transactions(uid,entry_date);
CREATE TABLE IF NOT EXISTS documents(id TEXT PRIMARY KEY,uid INTEGER REFERENCES users(id) ON DELETE CASCADE,mime TEXT,bytes INTEGER,at TEXT);
CREATE TABLE IF NOT EXISTS campaigns(id INTEGER PRIMARY KEY,title TEXT,body TEXT,status TEXT,at TEXT);
CREATE TABLE IF NOT EXISTS deletions(id INTEGER PRIMARY KEY,uid INTEGER REFERENCES users(id) ON DELETE CASCADE,status TEXT,at TEXT);
CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY,actor INTEGER,action TEXT,target TEXT,at TEXT);
CREATE TABLE IF NOT EXISTS trial_driver_accounts(uid INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE, expires INTEGER NOT NULL);
""");c.commit()
init()
# Explicitly authorized assisted entry is disabled by default for existing accounts.
with db() as _c:
 if not any(_col["name"]=="assisted_entry" for _col in _c.execute("PRAGMA table_info(consents)")):
  _c.execute("ALTER TABLE consents ADD COLUMN assisted_entry INTEGER NOT NULL DEFAULT 0")
 if not any(_col["name"]=="identity_collection" for _col in _c.execute("PRAGMA table_info(consents)")):
  _c.execute("ALTER TABLE consents ADD COLUMN identity_collection INTEGER NOT NULL DEFAULT 0")
 _c.commit()
def profile(c,uid):
 r=c.execute("SELECT encrypted FROM profiles WHERE uid=?",(uid,)).fetchone()
 return dec(r["encrypted"]) if r else {}
def save_profile(c,uid,p):
 c.execute("INSERT INTO profiles(uid,encrypted,updated_at) VALUES(?,?,?) ON CONFLICT(uid) DO UPDATE SET encrypted=excluded.encrypted,updated_at=excluded.updated_at",(uid,enc(p),now()))
def consent(c,uid):
 r=c.execute("SELECT insights,marketing,sharing,documents,assisted_entry,identity_collection,updated_at FROM consents WHERE uid=?",(uid,)).fetchone()
 return dict(r) if r else {"insights":0,"marketing":0,"sharing":0,"documents":0,"assisted_entry":0,"identity_collection":0}
def identity_permission(c,uid):
 # Distinct purpose-specific opt-in; no blanket global unlocking.
 return bool(consent(c,uid)["identity_collection"])
def auth(req:Request):
 token=req.cookies.get("clube_session","")
 if not token or len(token)>150:raise HTTPException(401,"Faça login")
 with db() as c:
  row=c.execute("SELECT u.id,u.username,u.name,u.role,u.status,u.must_change FROM users u JOIN sessions s ON s.uid=u.id WHERE s.hash=? AND s.expires>?",(sha(token),stamp())).fetchone()
  if not row or row["status"]!="active":raise HTTPException(401,"Sessão inválida")
  trial=c.execute("SELECT expires FROM trial_driver_accounts WHERE uid=?",(row["id"],)).fetchone()
  if trial and trial["expires"]<=stamp():
   raise HTTPException(401,"Acesso temporário expirado. Solicite um novo acesso de teste.")
  if row["must_change"] and req.url.path not in ("/api/me","/api/password","/api/logout"):
   raise HTTPException(428,"Troque a senha inicial antes de continuar")
  return dict(row)
def admin(u=Depends(auth)):
 if u["role"]!="admin":raise HTTPException(403,"Acesso restrito")
 return u
def driver(u=Depends(auth)):
 if u["role"]!="driver":raise HTTPException(403,"Acesso restrito")
 return u
@app.middleware("http")
async def secure(req,call_next):
 if req.url.path.startswith("/api/") and req.method in ("POST","PUT","PATCH","DELETE"):
  if req.headers.get("x-requested-with")!="NOVAGENTE-V5":return JSONResponse({"detail":"Proteção de origem obrigatória"},status_code=403)
  origin=req.headers.get("origin")
  if origin:
   parsed=urlparse(origin);host=req.headers.get("x-forwarded-host",req.headers.get("host","")).split(",")[0].split(":")[0]
   if parsed.hostname!=host:return JSONResponse({"detail":"Origem inválida"},status_code=403)
 resp=await call_next(req)
 resp.headers.update({"X-Frame-Options":"DENY","X-Content-Type-Options":"nosniff","Referrer-Policy":"no-referrer","Cache-Control":"no-store","Content-Security-Policy":"default-src 'self';script-src 'self';style-src 'self' 'unsafe-inline';connect-src 'self';img-src 'self' data:;object-src 'none';frame-ancestors 'none'"})
 return resp
@app.get("/")
def home():return FileResponse(ROOT/"static"/"index.html")
@app.get("/health")
def health():return {"ok":True,"version":"5.0","pix":False,"whatsapp":False,"sensitive_collection":"opt_in_only","consent_required":True}
@app.get("/api/me")
def me(req:Request):
 try:u=auth(req)
 except HTTPException:u=None
 return {"user":u,"limits":{"pix":False,"whatsapp":False,"sensitive":SENSITIVE_ENABLED}}
attempts=defaultdict(list)
@app.post("/api/login")
def login(req:Request,data:dict,response:Response):
 name=str(data.get("username","")).strip().lower();pwd=str(data.get("password",""))
 key=(req.client.host if req.client else "unknown")+"|"+name
 attempts[key]=[x for x in attempts[key] if stamp()-x<900]
 if len(attempts[key])>=8:raise HTTPException(429,"Aguarde 15 minutos")
 attempts[key].append(stamp())
 with db() as c:
  r=c.execute("SELECT * FROM users WHERE username=?",(name,)).fetchone()
  if not r or r["status"]!="active" or not password_ok(pwd,r["phash"]):
   time.sleep(.2);raise HTTPException(401,"Credenciais incorretas")
  trial=c.execute("SELECT expires FROM trial_driver_accounts WHERE uid=?",(r["id"],)).fetchone()
  if trial and trial["expires"]<=stamp():
   raise HTTPException(401,"Acesso temporário expirado. Solicite um novo acesso de teste.")
  if r["role"]=="admin":
   from security_stage3_v5 import enabled as mfa_enabled,verify_login as mfa_verify_login
   if mfa_enabled(c,r["id"]):
    code=data.get("otp","")
    if not isinstance(code,str) or not code.strip():
     raise HTTPException(401,"Código do autenticador ou recuperação necessário")
    if not mfa_verify_login(c,r["id"],code.strip()):
     time.sleep(.2)
     raise HTTPException(401,"Código de autenticação inválido")
  attempts.pop(key,None)
  token=secrets.token_urlsafe(48)
  c.execute("INSERT INTO sessions(hash,uid,expires) VALUES(?,?,?)",(sha(token),r["id"],stamp()+43200))
  audit(c,r["id"],"login");c.commit()
 response.set_cookie("clube_session",token,httponly=True,secure=True,samesite="strict",max_age=43200,path="/")
 return {"ok":True,"must_change":bool(r["must_change"])}
@app.post("/api/logout")
def logout(req:Request,response:Response,u=Depends(auth)):
 with db() as c:
  c.execute("DELETE FROM sessions WHERE hash=?",(sha(req.cookies.get("clube_session","")),));audit(c,u["id"],"logout");c.commit()
 response.delete_cookie("clube_session",path="/",secure=True,samesite="strict")
 return {"ok":True}
@app.post("/api/password")
def change_password(req:Request,data:dict,u=Depends(auth)):
 new=str(data.get("new",""))
 if len(new)<14 or not re.search(r"[A-Za-z]",new) or not re.search(r"\d",new):raise HTTPException(422,"Senha precisa de 14 caracteres, letras e números")
 with db() as c:
  old=c.execute("SELECT phash FROM users WHERE id=?",(u["id"],)).fetchone()["phash"]
  if not password_ok(str(data.get("current","")),old):raise HTTPException(403,"Senha atual incorreta")
  c.execute("UPDATE users SET phash=?,must_change=0 WHERE id=?",(password_hash(new),u["id"]))
  c.execute("DELETE FROM sessions WHERE uid=? AND hash<>?",(u["id"],sha(req.cookies.get("clube_session",""))))
  audit(c,u["id"],"password:changed");c.commit()
 return {"ok":True}

def validate_value(k,v,allow_identity=False):
 if k not in MAP:raise HTTPException(422,"Campo desconhecido")
 f=MAP[k];typ=f[2]
 if f[5] and not allow_identity:
  raise HTTPException(403,"Autorize o cadastro dos dados de identificação em Autorizações antes de preenchê-los.")
 if typ=="file":raise HTTPException(422,"Use a área de documentos")
 if v is None or v=="":return ""
 if typ=="multi":
  if not isinstance(v,list) or len(v)>len(f[4]) or any(x not in f[4] for x in v):raise HTTPException(422,"Seleção múltipla inválida")
  return list(dict.fromkeys(v))
 if not isinstance(v,(str,int,float)):raise HTTPException(422,"Valor inválido")
 s=str(v).strip()
 if len(s)>350:raise HTTPException(422,"Resposta muito extensa")
 if typ=="select" and s not in f[4]:raise HTTPException(422,"Opção inválida")
 if typ in ("number","money"):
  v=cents(s)/100
  if k=="weekly_days" and v>7 or k=="weekly_hours" and v>168:raise HTTPException(422,"Horas/dias fora dos limites")
  return v
 if typ=="date":
  try:datetime.date.fromisoformat(s)
  except ValueError:raise HTTPException(422,"Data inválida")
 if typ=="cpf" and not re.fullmatch(r"\d{11}",re.sub(r"\D","",s)):raise HTTPException(422,"CPF inválido")
 if typ=="email" and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+",s):raise HTTPException(422,"E-mail inválido")
 if typ=="phone" and not re.fullmatch(r"\+?[0-9 ()-]{10,24}",s):raise HTTPException(422,"Telefone inválido")
 return s
@app.get("/api/schema")
def schema(u=Depends(auth)):
 with db() as c:
  authorized=u["role"]=="driver" and identity_permission(c,u["id"])
 return {"fields":[{**describe(f),"protected":bool(f[5] and not authorized)} for f in ALL],
         "original":len(ORIGINAL),"extra":len(EXTRA),
         "sensitive":authorized,"identity_consent_required":True}
@app.get("/api/profile")
def my_profile(u=Depends(driver)):
 with db() as c:
  p=profile(c,u["id"])
  can_identity=identity_permission(c,u["id"])
  return {"answers":p,"progress":progress(p,can_identity),
          "identity_collection_enabled":can_identity}
@app.put("/api/profile")
def update_profile(data:dict,u=Depends(driver)):
 if not isinstance(data,dict) or len(data)>len(ALL):raise HTTPException(422,"Estrutura inválida")
 with db() as c:
  authorized=identity_permission(c,u["id"])
  patch={}
  for k,v in data.items():
   try:patch[k]=validate_value(k,v,authorized)
   except HTTPException as e:
    if k in MAP:raise HTTPException(e.status_code,MAP[k][1]+": "+str(e.detail))
    raise
  p=profile(c,u["id"]);p.update(patch)
  save_profile(c,u["id"],p);audit(c,u["id"],"profile:updated",len(patch));c.commit()
  return {"ok":True,"progress":progress(p,authorized)}
def next_field(p,authorized=False):
 skipped=set(p.get("_skipped",[]))
 for f in active_fields(p):
  if f[2]=="file" or f[5] and not authorized:continue
  if p.get(f[0]) in (None,"",[]) and f[0] not in skipped:return describe(f)
 return None
@app.get("/api/profile/next")
def next_question(u=Depends(driver)):
 with db() as c:
  p=profile(c,u["id"])
  authorized=identity_permission(c,u["id"])
  return {"question":next_field(p,authorized),"progress":progress(p,authorized)}
@app.post("/api/profile/answer")
def answer_question(data:dict,u=Depends(driver)):
 with db() as c:
  p=profile(c,u["id"]);authorized=identity_permission(c,u["id"]);f=next_field(p,authorized)
  if not f:return {"ok":True,"done":True}
  if data.get("key")!=f["key"]:raise HTTPException(409,"Pergunta alterada, recarregue")
  if data.get("skip") is True:
   skipped=set(p.get("_skipped",[]));skipped.add(f["key"]);p["_skipped"]=list(skipped)
  else:p[f["key"]]=validate_value(f["key"],data.get("value"),authorized)
  save_profile(c,u["id"],p);audit(c,u["id"],"interview:answer",f["key"]);c.commit()
  return {"ok":True,"progress":progress(p,authorized)}
@app.get("/api/consents")
def get_consents(u=Depends(driver)):
 with db() as c:return {"choices":consent(c,u["id"])}
@app.put("/api/consents")
def save_consents(data:dict,u=Depends(driver)):
 names=("insights","marketing","sharing","documents","assisted_entry","identity_collection")
 if set(data) not in (set(names),set(names[:-1]),set(names[:-2])) or any(type(data[k]) is not bool for k in data):
  raise HTTPException(422,"Escolhas de consentimento inválidas")
 with db() as c:
  previous=consent(c,u["id"])
  updated={k:data[k] if k in data else bool(previous.get(k,False)) for k in names}
  c.execute("INSERT INTO consents(uid,insights,marketing,sharing,documents,assisted_entry,identity_collection,updated_at) VALUES(?,?,?,?,?,?,?,?) "
   "ON CONFLICT(uid) DO UPDATE SET insights=excluded.insights,marketing=excluded.marketing,sharing=excluded.sharing,"
   "documents=excluded.documents,assisted_entry=excluded.assisted_entry,identity_collection=excluded.identity_collection,"
   "updated_at=excluded.updated_at",
   (u["id"],*[int(updated[k]) for k in names],now()))
  c.execute("INSERT INTO privacy_events(uid,choices,at) VALUES(?,?,?)",(u["id"],json.dumps(updated),now()))
  if bool(previous.get("identity_collection"))!=bool(updated["identity_collection"]):
   audit(c,u["id"],"identity_collection:granted" if updated["identity_collection"] else "identity_collection:revoked","finalidade de cadastro")
  audit(c,u["id"],"consents:updated");c.commit()
 return {"ok":True,"identity_collection_enabled":bool(updated["identity_collection"])}
def summary(c,uid,p,month=""):
 sql="SELECT kind,COALESCE(SUM(amount_cents),0) total FROM transactions WHERE uid=?";params=[uid]
 if month:
  if not re.fullmatch(r"\d{4}-\d{2}",month):raise HTTPException(422,"Mês inválido")
  sql+=" AND substr(entry_date,1,7)=?";params.append(month)
 sql+=" GROUP BY kind"
 counts={r["kind"]:r["total"]/100 for r in c.execute(sql,params)}
 n=lambda k:float(p.get(k) or 0)
 estimate=None
 if all(p.get(k) not in ("",None) for k in ("daily_revenue","daily_fuel","weekly_days")):
  earned=round(n("daily_revenue")*n("weekly_days")*52/12,2)
  fuel=round(n("daily_fuel")*n("weekly_days")*52/12,2)
  other=round(sum(n(k) for k in ("monthly_maintenance","vehicle_installment","household_expenses","other_debts")),2)
  estimate={"revenue":earned,"fuel":fuel,"other":other,"remaining":round(earned-fuel-other,2)}
 return {"income":counts.get("income",0),"expense":counts.get("expense",0),
 "partial":round(counts.get("income",0)-counts.get("expense",0),2),
 "fuel_per_km":round(n("daily_fuel")/n("daily_km"),2) if n("daily_km") and p.get("daily_fuel") not in ("",None) else None,
 "estimate":estimate,"note":"Movimentações lançadas manualmente e estimativas declaradas. Não representam saldo bancário nem aprovação de crédito."}
@app.get("/api/finances")
def get_finances(month:str="",u=Depends(driver)):
 with db() as c:
  sql="SELECT id,kind,category,amount_cents,entry_date,note FROM transactions WHERE uid=?";param=[u["id"]]
  if month:
   if not re.fullmatch(r"\d{4}-\d{2}",month):raise HTTPException(422,"Mês inválido")
   sql+=" AND substr(entry_date,1,7)=?";param.append(month)
  rows=c.execute(sql+" ORDER BY entry_date DESC,id DESC LIMIT 500",param)
  return {"items":[{**dict(r),"amount":r["amount_cents"]/100} for r in rows],"summary":summary(c,u["id"],profile(c,u["id"]),month)}
@app.post("/api/finances")
def add_finance(data:dict,u=Depends(driver)):
 kind=str(data.get("kind",""))
 if kind not in ("income","expense"):raise HTTPException(422,"Tipo inválido")
 cat=str(data.get("category","")).strip()[:60]
 if not cat:raise HTTPException(422,"Categoria obrigatória")
 amt=cents(data.get("amount"))
 if amt<=0:raise HTTPException(422,"Valor deve ser positivo")
 date=str(data.get("date",datetime.date.today().isoformat()))
 try:dt=datetime.date.fromisoformat(date)
 except ValueError:raise HTTPException(422,"Data inválida")
 if dt>datetime.date.today()+datetime.timedelta(days=1) or dt<datetime.date.today()-datetime.timedelta(days=730):raise HTTPException(422,"Data fora dos limites")
 note=str(data.get("note","")).strip()[:220]
 with db() as c:
  c.execute("INSERT INTO transactions(uid,kind,category,amount_cents,entry_date,note,at) VALUES(?,?,?,?,?,?,?)",(u["id"],kind,cat,amt,date,note,now()))
  audit(c,u["id"],"finance:created",kind);c.commit()
 return {"ok":True}
@app.delete("/api/finances/{fid}")
def delete_finance(fid:int,u=Depends(driver)):
 with db() as c:
  x=c.execute("DELETE FROM transactions WHERE id=? AND uid=?",(fid,u["id"]))
  if x.rowcount==0:raise HTTPException(404,"Não encontrado")
  audit(c,u["id"],"finance:removed",fid);c.commit()
 return {"ok":True}

@app.get("/api/admin/overview")
def overview(u=Depends(admin)):
 with db() as c:
  rows=c.execute("SELECT u.id,u.name,u.username,u.status,u.created_at,co.insights,co.marketing,co.sharing FROM users u LEFT JOIN consents co ON co.uid=u.id WHERE u.role='driver' ORDER BY u.id DESC").fetchall()
  users=[]
  for r in rows:
   x=dict(r);p=profile(c,x["id"]) if x["insights"] else {}
   users.append({**x,"platform":p.get("platform"),"car":p.get("car_model_interest"),
    "completion":progress(p,SENSITIVE_ENABLED)["percent"] if x["insights"] else None})
  return {"items":users,"pending":sum(r["status"]=="pending" for r in users),"authorized":sum(bool(r["insights"]) for r in users)}
@app.get("/api/admin/driver/{uid}")
def detail(uid:int,u=Depends(admin)):
 with db() as c:
  row=c.execute("SELECT id,name,username,status FROM users WHERE id=? AND role='driver'",(uid,)).fetchone()
  if not row:raise HTTPException(404,"Não encontrado")
  if not consent(c,uid)["insights"]:return {"driver":dict(row),"authorized":False}
  p=profile(c,uid)
  # Não expor CPF, endereço ou CNH automaticamente no painel comercial.
  safe={k:v for k,v in p.items() if k not in SENSITIVE and not k.startswith("_")}
  return {"driver":dict(row),"authorized":True,"assisted_entry":bool(consent(c,uid)["assisted_entry"]),"answers":safe,"summary":summary(c,uid,p),"completion":progress(p,SENSITIVE_ENABLED)}
@app.get("/api/admin/export")
def export_admin(u=Depends(admin)):
 with db() as c:
  rows=c.execute("SELECT u.id,u.name,u.username FROM users u JOIN consents co ON co.uid=u.id WHERE u.role='driver' AND co.insights=1 ORDER BY u.id").fetchall()
  fields=[f for f in ALL if not f[5]]
  stream=io.StringIO();writer=csv.writer(stream,delimiter=";")
  writer.writerow(["Motorista","Conta"]+[f[1] for f in fields])
  def clean(v):
   if isinstance(v,list):v=", ".join(v)
   v=str(v if v is not None else "")
   return "'"+v if v.startswith(("=","+","-","@","\t","\r","\n")) else v
  for row in rows:
   p=profile(c,row["id"])
   writer.writerow([clean(row["name"]),clean(row["username"])]+[clean(p.get(f[0],"")) for f in fields])
  audit(c,u["id"],"export:authorized",len(rows));c.commit()
 return Response("\ufeff"+stream.getvalue(),media_type="text/csv; charset=utf-8",headers={"Content-Disposition":"attachment; filename=novagente_motores_autorizados.csv"})
@app.post("/api/admin/invites")
def invite(u=Depends(admin)):
 secret=secrets.token_urlsafe(24)
 with db() as c:
  c.execute("INSERT INTO invites(hash,admin_id,expires,created_at) VALUES(?,?,?,?)",(sha(secret),u["id"],stamp()+172800,now()))
  audit(c,u["id"],"invite:created");c.commit()
 return {"invite":secret,"hours":48}
@app.post("/api/enroll")
def enroll(data:dict):
 token=str(data.get("invite",""))
 username=str(data.get("username","")).strip().lower()
 name=str(data.get("name","")).strip()[:80]
 pwd=str(data.get("password",""))
 if not re.fullmatch(r"[a-z0-9_]{4,32}",username) or len(name)<2 or len(pwd)<14 or not re.search("[A-Za-z]",pwd) or not re.search(r"\d",pwd):
  raise HTTPException(422,"Nome, usuário ou senha inválidos; senha precisa de 14 caracteres com letras e números")
 if data.get("accepted_rules") is not True:raise HTTPException(422,"É necessário confirmar ciência das condições do programa")
 with db() as c:
  c.execute("BEGIN IMMEDIATE")
  r=c.execute("SELECT hash FROM invites WHERE hash=? AND used_uid IS NULL AND expires>?",(sha(token),stamp())).fetchone()
  if not r:raise HTTPException(400,"Convite não encontrado ou expirado")
  if c.execute("SELECT id FROM users WHERE username=?",(username,)).fetchone():raise HTTPException(409,"Usuário existente")
  c.execute("INSERT INTO users(username,phash,role,status,name,created_at) VALUES(?,?,?,?,?,?)",(username,password_hash(pwd),"driver","pending",name,now()))
  uid=c.execute("SELECT last_insert_rowid()").fetchone()[0]
  c.execute("INSERT INTO consents(uid,updated_at) VALUES(?,?)",(uid,now()))
  save_profile(c,uid,{})
  c.execute("UPDATE invites SET used_uid=? WHERE hash=?",(uid,sha(token)))
  audit(c,uid,"enroll:requested");c.commit()
 return {"ok":True,"pending":True}
@app.post("/api/admin/activate/{uid}")
def activate(uid:int,u=Depends(admin)):
 with db() as c:
  r=c.execute("SELECT status FROM users WHERE id=? AND role='driver'",(uid,)).fetchone()
  if not r or r["status"]!="pending":raise HTTPException(409,"Cadastro não está pendente")
  c.execute("UPDATE users SET status='active' WHERE id=?",(uid,))
  audit(c,u["id"],"enroll:activated",uid);c.commit()
 return {"ok":True}
@app.post("/api/admin/suspend/{uid}")
def suspend(uid:int,u=Depends(admin)):
 with db() as c:
  r=c.execute("SELECT id FROM users WHERE id=? AND role='driver'",(uid,)).fetchone()
  if not r:raise HTTPException(404,"Não encontrado")
  c.execute("UPDATE users SET status='suspended' WHERE id=?",(uid,))
  c.execute("DELETE FROM sessions WHERE uid=?",(uid,))
  audit(c,u["id"],"driver:suspended",uid);c.commit()
 return {"ok":True}
@app.get("/api/campaigns")
def campaigns(u=Depends(auth)):
 with db() as c:
  if u["role"]=="driver" and not consent(c,u["id"])["marketing"]:return {"items":[],"notice":"Você não autorizou campanhas"}
  where="" if u["role"]=="admin" else " WHERE status='published'"
  return {"items":[dict(r) for r in c.execute("SELECT id,title,body,status,at FROM campaigns"+where+" ORDER BY id DESC LIMIT 100")]}
@app.post("/api/admin/campaigns")
def create_campaign(data:dict,u=Depends(admin)):
 title=str(data.get("title","")).strip()[:100]
 body=str(data.get("body","")).strip()[:800]
 state=str(data.get("status","draft"))
 if not title or not body or state not in ("draft","published"):raise HTTPException(422,"Campanha inválida")
 with db() as c:
  c.execute("INSERT INTO campaigns(title,body,status,at) VALUES(?,?,?,?)",(title,body,state,now()))
  audit(c,u["id"],"campaign:created",title[:50]);c.commit()
 return {"ok":True,"messages_sent":0}
@app.get("/api/admin/audit")
def get_audit(u=Depends(admin)):
 with db() as c:return {"items":[dict(r) for r in c.execute("SELECT action,target,at FROM audit ORDER BY id DESC LIMIT 200")]}

@app.get("/api/documents")
def list_documents(u=Depends(driver)):
 with db() as c:
  rows=[dict(r) for r in c.execute("SELECT id,mime,bytes,at FROM documents WHERE uid=? ORDER BY at DESC",(u["id"],))]
  return {"items":rows,"enabled":identity_permission(c,u["id"]),
          "identity_consent_required":True}
def file_type(data:bytes):
 if data.startswith(b"%PDF-"):return "application/pdf"
 if data.startswith(b"\xff\xd8\xff"):return "image/jpeg"
 if data.startswith(b"\x89PNG\r\n\x1a\n"):return "image/png"
 raise HTTPException(422,"Formato não aceito. Envie PDF, JPG ou PNG")
@app.post("/api/documents")
async def upload_document(file:UploadFile=File(...),u=Depends(driver)):
 with db() as c:
  if not identity_permission(c,u["id"]):
   raise HTTPException(403,"Autorize o cadastro de identificação antes de enviar CNH.")
 data=await file.read(8*1024*1024+1)
 if not data or len(data)>8*1024*1024:raise HTTPException(413,"Arquivo deve ter até 8 MB")
 mime=file_type(data);fid=uuid.uuid4().hex
 with db() as c:
  if c.execute("SELECT COUNT(*) FROM documents WHERE uid=?",(u["id"],)).fetchone()[0]>=5:raise HTTPException(422,"Máximo 5 documentos")
  dest=DOCS/(fid+".bin");dest.write_bytes(cipher.encrypt(data));dest.chmod(0o600)
  c.execute("INSERT INTO documents(id,uid,mime,bytes,at) VALUES(?,?,?,?,?)",(fid,u["id"],mime,len(data),now()))
  audit(c,u["id"],"document:uploaded",fid[:8]);c.commit()
 return {"ok":True,"id":fid}
@app.get("/api/documents/{fid}")
def get_document(fid:str,u=Depends(auth)):
 with db() as c:
  r=c.execute("SELECT * FROM documents WHERE id=?",(fid,)).fetchone()
  if not r:raise HTTPException(404,"Arquivo não encontrado")
  if r["uid"]!=u["id"] and (u["role"]!="admin" or not (
    consent(c,r["uid"])["documents"] and consent(c,r["uid"])["assisted_entry"] and consent(c,r["uid"])["identity_collection"])):
   raise HTTPException(403,"Acesso não permitido")
  try:plain=cipher.decrypt((DOCS/(fid+".bin")).read_bytes())
  except InvalidToken:raise HTTPException(500,"Documento corrompido")
  audit(c,u["id"],"document:read",fid[:8]);c.commit()
 return Response(plain,media_type=r["mime"],headers={"Content-Disposition":"attachment;filename=CNH."+("pdf" if r["mime"]=="application/pdf" else "jpg" if r["mime"]=="image/jpeg" else "png")})
@app.delete("/api/documents/{fid}")
def remove_document(fid:str,u=Depends(driver)):
 with db() as c:
  r=c.execute("DELETE FROM documents WHERE id=? AND uid=?",(fid,u["id"]))
  if not r.rowcount:raise HTTPException(404,"Arquivo não encontrado")
  audit(c,u["id"],"document:removed",fid[:8]);c.commit()
 (DOCS/(fid+".bin")).unlink(missing_ok=True)
 return {"ok":True}
@app.get("/api/privacy/export")
def export_self(u=Depends(driver)):
 with db() as c:
  p=profile(c,u["id"])
  finance=[dict(r) for r in c.execute("SELECT kind,category,amount_cents,entry_date,note FROM transactions WHERE uid=? ORDER BY id",(u["id"],))]
  from finance_agent_v1 import options as agent_options
  agent_choices=agent_options(c,u["id"])
  agent_suggestions=[{"id":r["id"],"status":r["status"],"created_at":r["created_at"],"proposal":dec(r["encrypted"])}
   for r in c.execute("SELECT id,status,created_at,encrypted FROM finance_agent_proposals WHERE uid=? ORDER BY id",(u["id"],))]
  audit(c,u["id"],"privacy:export");c.commit()
  return {"profile":p,"consents":consent(c,u["id"]),"finances":finance,
   "finance_agent_authorizations":agent_choices,"finance_agent_proposals":agent_suggestions,
   "note":"Exportação individual, sem senhas, documentos, mídia original ou chaves externas"}
@app.post("/api/privacy/delete-request")
def request_delete(u=Depends(driver)):
 with db() as c:
  if not c.execute("SELECT id FROM deletions WHERE uid=? AND status='pending'",(u["id"],)).fetchone():
   c.execute("INSERT INTO deletions(uid,status,at) VALUES(?,'pending',?)",(u["id"],now()))
   audit(c,u["id"],"privacy:delete_request");c.commit()
 return {"ok":True,"status":"pending"}
@app.get("/api/admin/delete-requests")
def requests(u=Depends(admin)):
 with db() as c:
  return {"items":[dict(r) for r in c.execute("SELECT d.id,d.status,d.at,u.name,u.username FROM deletions d JOIN users u ON u.id=d.uid ORDER BY d.id DESC")]}
@app.post("/api/admin/delete-requests/{rid}/complete")
def fulfill_delete(rid:int,u=Depends(admin)):
 with db() as c:
  r=c.execute("SELECT uid FROM deletions WHERE id=? AND status='pending'",(rid,)).fetchone()
  if not r:raise HTTPException(404,"Solicitação não encontrada")
  uid=r["uid"]
  ids=[q["id"] for q in c.execute("SELECT id FROM documents WHERE uid=?",(uid,))]
  c.execute("UPDATE invites SET used_uid=NULL WHERE used_uid=?",(uid,))
  c.execute("DELETE FROM users WHERE id=? AND role='driver'",(uid,))
  c.execute("UPDATE audit SET actor=NULL WHERE actor=?",(uid,))
  audit(c,u["id"],"privacy:fulfilled",rid);c.commit()
 for fid in ids:(DOCS/(fid+".bin")).unlink(missing_ok=True)
 return {"ok":True}

# Conversa financeira local. Não depende de WhatsApp ou de provedor LLM.
@app.get("/api/chat")
def chat_history(u=Depends(driver)):
 with db() as c:
  c.execute("""CREATE TABLE IF NOT EXISTS chat_messages
   (id INTEGER PRIMARY KEY,uid INTEGER REFERENCES users(id) ON DELETE CASCADE,
    speaker TEXT NOT NULL,encrypted BLOB NOT NULL,at TEXT NOT NULL)""");c.commit()
  rows=c.execute("SELECT speaker,encrypted,at FROM chat_messages WHERE uid=? ORDER BY id DESC LIMIT 80",(u["id"],)).fetchall()
  return {"items":[{"speaker":x["speaker"],"body":dec(x["encrypted"]), "at":x["at"]} for x in reversed(rows)],
   "notice":"Interpretação por regras; não é uma IA de aconselhamento financeiro profissional."}
@app.post("/api/chat")
def chat_message(data:dict,u=Depends(driver)):
 raw=str(data.get("text","")).strip()[:400]
 if not raw:raise HTTPException(422,"Mensagem vazia")
 lower=raw.lower()
 income_words=bool(re.search(r"\b(ganhei|recebi|faturei|fiz|entrou)\b",lower))
 expense_words=bool(re.search(r"\b(gastei|paguei|abasteci|comprei|custou)\b",lower))
 match=re.search(r"(?:r\$\s*)?(\d{1,6}(?:[.,]\d{1,2})?)",lower)
 with db() as c:
  c.execute("""CREATE TABLE IF NOT EXISTS chat_messages
   (id INTEGER PRIMARY KEY,uid INTEGER REFERENCES users(id) ON DELETE CASCADE,
    speaker TEXT NOT NULL,encrypted BLOB NOT NULL,at TEXT NOT NULL)""")
  c.execute("INSERT INTO chat_messages(uid,speaker,encrypted,at) VALUES(?,?,?,?)",(u["id"],"motorista",enc(raw),now()))
  response=None
  if match and income_words!=expense_words:
   value=cents(match.group(1))
   if value:
    kind="expense" if expense_words else "income"
    if kind=="income":
     from finance_agent_core import income_label
     category,app_source=income_label(raw)
     if app_source in ("Uber","99","inDrive","Urbano Norte","iFood","Rappi","Loggi","Extra","Particular"):
      raw_note=("Origem: "+app_source+" | "+raw)[:220]
     else:raw_note=raw[:220]
    else:
     category=("Combustível" if any(x in lower for x in ["gasolina","etanol","diesel","abastec","combust"]) else
      "Manutenção" if any(x in lower for x in ["oficina","manuten","pneu"]) else
      "Alimentação" if any(x in lower for x in ["café","almoc","almoç","janta","lanche"]) else "Outras despesas")
    c.execute("INSERT INTO transactions(uid,kind,category,amount_cents,entry_date,note,at) VALUES(?,?,?,?,?,?,?)",
     (u["id"],kind,category,value,datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=-4))).date().isoformat(),raw_note if kind=="income" else raw[:220],now()))
    response="Registrei R$ "+f"{value/100:.2f}".replace(".",",")+" em "+category+". É uma declaração sua, sem confirmação bancária."
    audit(c,u["id"],"chat:finance",kind)
  if response is None and (any(k in lower for k in ["saldo","sobrou","resultado","ganhei no mês","resumo","resumo financeiro"]) or "quanto" in lower):
   s=summary(c,u["id"],profile(c,u["id"]))
   response=f"Você informou R$ {s['income']:.2f} de entradas e R$ {s['expense']:.2f} de despesas. O resultado parcial é R$ {s['partial']:.2f}. Não representa saldo bancário nem considera despesas ainda não lançadas."
  if response is None and any(k in lower for k in ["meta","objetivo","guardar","economizar"]):
   p=profile(c,u["id"])
   if p.get("monthly_saving_goal") not in ("",None):
    response="Sua meta mensal de economia é R$ "+f"{float(p['monthly_saving_goal']):.2f}".replace(".",",")+". Registre despesas para acompanhar o que sobra."
   else:response="Você ainda não informou sua meta de economia. Abra Meu cadastro e responda quanto deseja guardar por mês."
  if response is None:
   response="Posso registrar mensagens como 'Ganhei R$ 250 na Uber', 'Gastei R$ 70 de gasolina' ou mostrar seu resumo: 'Quanto sobrou?'. É um apoio inicial por regras, sem acesso a banco ou WhatsApp."
  c.execute("INSERT INTO chat_messages(uid,speaker,encrypted,at) VALUES(?,?,?,?)",(u["id"],"agente",enc(response),now()))
  c.commit()
  return {"ok":True,"answer":response}

# Visualização e planejamento interno, sem conexão a bancos ou WhatsApp.
from distribution_v5 import router as distribution_router
app.include_router(distribution_router)

# Emparelhamento WAHA apenas sob acao administrativa explicita. Sem mensageria.
from whatsapp_bridge_v5 import router as whatsapp_bridge_router
app.include_router(whatsapp_bridge_router)

# Escrita assistida pelo gestor apenas com consentimento independente do motorista.
from socio_assisted_v5 import router as assisted_router
app.include_router(assisted_router)

# Gestão do Clube: indicadores consentidos, campanhas internas, benefícios e tarefas.
from program_stage2_v5 import router as program_stage2_router
app.include_router(program_stage2_router)

# Autenticação administrativa em duas etapas, ativada apenas com confirmação pessoal.
from security_stage3_v5 import router as security_stage3_router
app.include_router(security_stage3_router)

# Agente financeiro consentido: leitura conservadora e confirmação humana; WhatsApp ainda sem disparos.
from finance_agent_v1 import router as finance_agent_router
app.include_router(finance_agent_router)

# WAHA inbound protegido: desligado até autorização; sem mensagens de saída.
from finance_agent_waha_v1 import router as finance_agent_waha_router
app.include_router(finance_agent_waha_router)

# Disponibilidade do agente no portal, independente dos consentimentos e do WhatsApp.
from finance_agent_release_v1 import router as finance_agent_release_router
app.include_router(finance_agent_release_router)

from finance_agent_pilot_v1 import router as finance_agent_pilot_router
app.include_router(finance_agent_pilot_router)

# Driver-only financial-flow web page and read-only API. No automatic WhatsApp sends.
from finance_flow_v1 import router as finance_flow_router
app.include_router(finance_flow_router)
