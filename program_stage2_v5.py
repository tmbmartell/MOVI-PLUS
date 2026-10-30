"""NOVAGENTE Clube do Motorista / etapa 2: gestão, pontos referenciais, benefícios, tarefas e campanhas internas.

Sem pagamentos, validação bancária, disparos WhatsApp ou acesso a dados de motoristas
sem consentimento. Todas as recompensas dependem de aprovação humana.
"""
import calendar,csv,datetime,io,json,re,secrets
from pathlib import Path
from fastapi import APIRouter,Depends,HTTPException,UploadFile,File
from fastapi.responses import Response
from app import db,admin,driver,auth,profile,progress,consent,now,audit,cipher,ROOT,DATA

router=APIRouter()
STATES={"draft","published"}
SEGMENTS={"all","UBER","99","URBANO NORTE","LEVA EU","IN DRIVE","Outro"}
TASK_STATES={"new","doing","done"}
TASK_PRIORITIES={"low","normal","high"}
MEDIA_DIR=DATA/"program-media"
MEDIA_DIR.mkdir(mode=0o700,exist_ok=True)
MEDIA_LIMIT=8*1024*1024

def init_tables(c):
 c.executescript("""
 CREATE TABLE IF NOT EXISTS program_benefits(
  id INTEGER PRIMARY KEY,title TEXT NOT NULL,description TEXT NOT NULL,points_required INTEGER NOT NULL,
  stock INTEGER NOT NULL,active INTEGER NOT NULL DEFAULT 1,created_at TEXT NOT NULL);
 CREATE TABLE IF NOT EXISTS program_claims(
  id INTEGER PRIMARY KEY,benefit_id INTEGER NOT NULL REFERENCES program_benefits(id) ON DELETE CASCADE,
  uid INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  points_at_request INTEGER NOT NULL,status TEXT NOT NULL DEFAULT 'pending',
  created_at TEXT NOT NULL,decided_at TEXT,decided_by INTEGER);
 CREATE UNIQUE INDEX IF NOT EXISTS uniq_open_claim ON program_claims(benefit_id,uid) WHERE status IN ('pending','approved');
 CREATE INDEX IF NOT EXISTS idx_claims_status ON program_claims(status,created_at);
 CREATE TABLE IF NOT EXISTS program_tasks(
  id INTEGER PRIMARY KEY,title TEXT NOT NULL,details TEXT NOT NULL,owner TEXT NOT NULL,
  priority TEXT NOT NULL,status TEXT NOT NULL,due_on TEXT NOT NULL,created_at TEXT NOT NULL,updated_at TEXT NOT NULL);
 CREATE TABLE IF NOT EXISTS program_media(
  id TEXT PRIMARY KEY,mime TEXT NOT NULL,file_size INTEGER NOT NULL,created_at TEXT NOT NULL);
 CREATE TABLE IF NOT EXISTS program_campaigns(
  id INTEGER PRIMARY KEY,title TEXT NOT NULL,body TEXT NOT NULL,
  status TEXT NOT NULL,segment TEXT NOT NULL,media_id TEXT REFERENCES program_media(id),
  created_at TEXT NOT NULL,updated_at TEXT NOT NULL);
 CREATE INDEX IF NOT EXISTS idx_prog_campaign_state ON program_campaigns(status,segment);
 """)
 c.commit()

# Import app after its database initialization has run; this adds isolated tables.
with db() as _conn:init_tables(_conn)

def verify_enum(v,allowed,label):
 if not isinstance(v,str) or v not in allowed:raise HTTPException(422,label+" inválido")
 return v

def txt(v,label,min_len,max_len):
 if not isinstance(v,str) or not min_len<=len(v.strip())<=max_len:
  raise HTTPException(422,label+" deve ter entre "+str(min_len)+" e "+str(max_len)+" caracteres")
 t=v.strip()
 if any(ord(ch)<32 and ch not in "\n\t" for ch in t):raise HTTPException(422,label+" contém caracteres inválidos")
 return t

def whole(v,label,lo,hi):
 if type(v) is not int or not lo<=v<=hi:raise HTTPException(422,label+" inválido")
 return v

def points(c,uid):
 p=profile(c,uid)
 pr=progress(p,False)["percent"]
 # Pontuação não monetária: baseada somente em completude e dias distintos com registros
 # autodeclarados, nunca em quantias ou em comprovantes.
 days=c.execute("SELECT COUNT(DISTINCT entry_date) n FROM transactions WHERE uid=? AND entry_date>=?",
                (uid,(datetime.date.today()-datetime.timedelta(days=89)).isoformat())).fetchone()["n"]
 result=min(60,round(pr*0.6))+min(40,days*4)
 return {"total":result,"profile":min(60,round(pr*0.6)),
         "diary":min(40,days*4),"days":days,"progress":pr,
         "note":"Pontos indicativos por preenchimento e registro manual de dias. Não são dinheiro nem comprovam pagamentos; benefícios exigem aprovação do gestor."}

def benefit_out(c,row):
 d=dict(row)
 approved=c.execute("SELECT COUNT(*) AS n FROM program_claims WHERE benefit_id=? AND status='approved'",(d["id"],)).fetchone()["n"]
 d["remaining"]=max(0,d["stock"]-approved)
 return d

def segment_match(c,uid,seg):
 cc=consent(c,uid)
 if not cc["marketing"]:return False
 if seg=="all":return True
 if not cc["insights"]:return False
 return profile(c,uid).get("platform")==seg

def campaigns_for(c,user):
 if user["role"]=="admin":
  return [dict(r) for r in c.execute("SELECT ca.*,me.mime FROM program_campaigns ca LEFT JOIN program_media me ON me.id=ca.media_id ORDER BY ca.id DESC LIMIT 100")]
 rows=c.execute("SELECT ca.*,me.mime FROM program_campaigns ca LEFT JOIN program_media me ON me.id=ca.media_id WHERE ca.status='published' ORDER BY ca.id DESC LIMIT 100").fetchall()
 return [dict(r) for r in rows if segment_match(c,user["id"],r["segment"])]

def month_ok(month):
 if not isinstance(month,str) or not re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])",month):
  raise HTTPException(422,"Mês inválido")
 yr,mo=map(int,month.split("-"))
 if yr<2020 or yr>2100:raise HTTPException(422,"Mês fora do período")
 return month

def stats_data(c,month):
 all_users=c.execute("SELECT u.id,u.status,COALESCE(co.insights,0) insights,"
 "COALESCE(co.marketing,0) marketing FROM users u LEFT JOIN consents co ON co.uid=u.id "
 "WHERE u.role='driver'").fetchall()
 authorized=[x["id"] for x in all_users if x["insights"] and x["status"]=="active"]
 platforms={}; progress_buckets={"0–24%":0,"25–49%":0,"50–74%":0,"75–100%":0}
 for uid in authorized:
  p=profile(c,uid)
  platform=p.get("platform") or "Não informado"
  platforms[platform]=platforms.get(platform,0)+1
  val=progress(p,False)["percent"]
  ix="0–24%" if val<25 else "25–49%" if val<50 else "50–74%" if val<75 else "75–100%"
  progress_buckets[ix]+=1
 transactions=c.execute(
  "SELECT t.kind,COALESCE(SUM(t.amount_cents),0) total,COUNT(*) quantity "
  "FROM transactions t JOIN users u ON u.id=t.uid JOIN consents co ON co.uid=t.uid "
  "WHERE u.role='driver' AND u.status='active' AND co.insights=1 "
  "AND substr(t.entry_date,1,7)=? GROUP BY t.kind",(month,)).fetchall()
 bykind={r["kind"]:dict(r) for r in transactions}
 incoming=bykind.get("income",{}).get("total",0) or 0
 outgoing=bykind.get("expense",{}).get("total",0) or 0
 months=[]
 y,m=map(int,month.split("-"))
 for i in range(5,-1,-1):
  year=y;monthnum=m-i
  while monthnum<=0:monthnum+=12;year-=1
  code=f"{year:04d}-{monthnum:02d}"
  rows=c.execute("SELECT t.kind,COALESCE(SUM(t.amount_cents),0) total "
   "FROM transactions t JOIN users u ON u.id=t.uid JOIN consents co ON co.uid=t.uid "
   "WHERE u.role='driver' AND u.status='active' AND co.insights=1 "
   "AND substr(t.entry_date,1,7)=? GROUP BY t.kind",(code,)).fetchall()
  vals={r["kind"]:r["total"]/100 for r in rows}
  months.append({"month":code,"income":vals.get("income",0),"expense":vals.get("expense",0)})
 benefit_requests=c.execute("SELECT COUNT(*) n FROM program_claims WHERE status='pending'").fetchone()["n"]
 open_tasks=c.execute("SELECT COUNT(*) n FROM program_tasks WHERE status!='done'").fetchone()["n"]
 active_campaigns=c.execute("SELECT COUNT(*) n FROM program_campaigns WHERE status='published'").fetchone()["n"]
 return {"month":month,"drivers":len(all_users),"active":sum(x["status"]=="active" for x in all_users),
  "pending":sum(x["status"]=="pending" for x in all_users),"authorized":len(authorized),
  "marketing_opt_in":sum(bool(x["marketing"]) for x in all_users if x["status"]=="active"),
  "income_declared":incoming/100,"expense_declared":outgoing/100,
  "net_declared":(incoming-outgoing)/100,"entry_count":sum(r["quantity"] for r in transactions),
  "platforms":platforms,"progress":progress_buckets,"months":months,
  "benefit_requests":benefit_requests,"open_tasks":open_tasks,"campaigns_published":active_campaigns,
  "data_scope":"Somente registros autodeclarados de motoristas ativos que autorizaram análise. Sem dados bancários, Pix ou inferência de pagamento."}

@router.get("/api/program/dashboard")
def dashboard(month:str="",u=Depends(admin)):
 if not month:month=datetime.date.today().strftime("%Y-%m")
 month_ok(month)
 with db() as c:return stats_data(c,month)

@router.get("/api/program/report.csv")
def report(month:str="",u=Depends(admin)):
 if not month:month=datetime.date.today().strftime("%Y-%m")
 month_ok(month)
 with db() as c:
  d=stats_data(c,month)
  audit(c,u["id"],"program:aggregate_export",month);c.commit()
 buff=io.StringIO()
 w=csv.writer(buff,delimiter=";")
 w.writerow(["Indicador","Valor","Observação"])
 for title,key in [("Motoristas totais","drivers"),("Ativos","active"),("Aguardando aprovação","pending"),
    ("Análise autorizada","authorized"),("Campanhas autorizadas","marketing_opt_in"),
    ("Receitas autodeclaradas","income_declared"),("Despesas autodeclaradas","expense_declared"),
    ("Resultado autodeclarado","net_declared"),("Lançamentos manuais","entry_count"),
    ("Solicitações de benefícios pendentes","benefit_requests"),("Tarefas em aberto","open_tasks")]:
  w.writerow([title,d[key],d["data_scope"]])
 for row in d["months"]:
  w.writerow(["Mês "+row["month"]+" entradas",row["income"],"Valores autodeclarados"])
  w.writerow(["Mês "+row["month"]+" despesas",row["expense"],"Valores autodeclarados"])
 return Response("\ufeff"+buff.getvalue(),media_type="text/csv; charset=utf-8",
     headers={"Content-Disposition":f'attachment; filename="novagente_resumo_{month}.csv"'})

@router.get("/api/program/benefits")
def benefits(u=Depends(auth)):
 with db() as c:
  if u["role"]=="admin":
   rows=c.execute("SELECT * FROM program_benefits ORDER BY id DESC LIMIT 150")
  else:
   rows=c.execute("SELECT * FROM program_benefits WHERE active=1 ORDER BY id DESC LIMIT 150")
  vals=[benefit_out(c,r) for r in rows]
  data={"items":vals,"no_cash_value":True}
  if u["role"]=="driver":
   data["points"]=points(c,u["id"])
   data["claims"]=[dict(r) for r in c.execute(
    "SELECT cl.id,cl.benefit_id,b.title,cl.status,cl.points_at_request,cl.created_at "
    "FROM program_claims cl JOIN program_benefits b ON b.id=cl.benefit_id "
    "WHERE cl.uid=? ORDER BY cl.id DESC LIMIT 100",(u["id"],))]
  return data

@router.post("/api/program/benefits")
def create_benefit(data:dict,u=Depends(admin)):
 title=txt(data.get("title"),"Título",3,90)
 description=txt(data.get("description"),"Descrição",3,500)
 required=whole(data.get("points_required"),"Pontuação",0,100)
 stock=whole(data.get("stock"),"Quantidade",0,100000)
 with db() as c:
  cur=c.execute("INSERT INTO program_benefits(title,description,points_required,stock,created_at) VALUES(?,?,?,?,?)",
    (title,description,required,stock,now()))
  audit(c,u["id"],"program:benefit_created",str(cur.lastrowid));c.commit()
  return {"ok":True,"id":cur.lastrowid}

@router.put("/api/program/benefits/{bid}")
def edit_benefit(bid:int,data:dict,u=Depends(admin)):
 if set(data)!={"active","stock"} or type(data["active"]) is not bool:raise HTTPException(422,"Informe ativo e estoque")
 stock=whole(data["stock"],"Quantidade",0,100000)
 with db() as c:
  approved=c.execute("SELECT COUNT(*) n FROM program_claims WHERE status='approved' AND benefit_id=?",(bid,)).fetchone()["n"]
  if stock<approved:raise HTTPException(422,"Estoque não pode ser menor que os benefícios já aprovados")
  row=c.execute("UPDATE program_benefits SET active=?,stock=? WHERE id=?",(int(data["active"]),stock,bid))
  if not row.rowcount:raise HTTPException(404,"Benefício não encontrado")
  audit(c,u["id"],"program:benefit_updated",str(bid));c.commit()
 return {"ok":True}

@router.post("/api/program/benefits/{bid}/claim")
def claim_benefit(bid:int,u=Depends(driver)):
 with db() as c:
  c.execute("BEGIN IMMEDIATE")
  if not consent(c,u["id"])["insights"]:
   raise HTTPException(403,"Para solicitar um benefício, autorize análise socioeconômica na aba Autorizações.")
  row=c.execute("SELECT * FROM program_benefits WHERE id=? AND active=1",(bid,)).fetchone()
  if not row:raise HTTPException(404,"Benefício indisponível")
  b=benefit_out(c,row)
  if b["remaining"]<=0:raise HTTPException(409,"Benefício sem disponibilidade")
  score=points(c,u["id"])["total"]
  if score<b["points_required"]:raise HTTPException(403,"Pontuação insuficiente neste momento")
  existing=c.execute("SELECT 1 FROM program_claims WHERE benefit_id=? AND uid=? AND status IN ('pending','approved')",(bid,u["id"])).fetchone()
  if existing:raise HTTPException(409,"Você já solicitou ou recebeu este benefício")
  cur=c.execute("INSERT INTO program_claims(benefit_id,uid,points_at_request,status,created_at) VALUES(?,?,?,'pending',?)",
    (bid,u["id"],score,now()))
  audit(c,u["id"],"program:claim_requested",str(bid));c.commit()
  return {"ok":True,"id":cur.lastrowid,"status":"pending","note":"Solicitação registrada. A entrega exige revisão e aprovação humana."}

@router.get("/api/program/claims")
def admin_claims(u=Depends(admin)):
 with db() as c:
  rows=c.execute("SELECT cl.id,cl.benefit_id,cl.uid,cl.status,cl.points_at_request,cl.created_at,"
    " b.title,u.name FROM program_claims cl JOIN program_benefits b ON b.id=cl.benefit_id "
    "JOIN users u ON u.id=cl.uid ORDER BY cl.id DESC LIMIT 200").fetchall()
  return {"items":[dict(r) for r in rows]}

@router.post("/api/program/claims/{cid}/decide")
def decide_claim(cid:int,data:dict,u=Depends(admin)):
 state=verify_enum(data.get("status"),{"approved","rejected"},"Decisão")
 with db() as c:
  c.execute("BEGIN IMMEDIATE")
  row=c.execute("SELECT cl.status,cl.benefit_id,b.stock,b.active FROM program_claims cl "
   "JOIN program_benefits b ON b.id=cl.benefit_id WHERE cl.id=?",(cid,)).fetchone()
  if not row:raise HTTPException(404,"Solicitação não encontrada")
  if row["status"]!="pending":raise HTTPException(409,"Solicitação já foi avaliada")
  if state=="approved":
   if not row["active"]:raise HTTPException(409,"Benefício desativado")
   approved=c.execute("SELECT COUNT(*) n FROM program_claims WHERE status='approved' AND benefit_id=?",
      (row["benefit_id"],)).fetchone()["n"]
   if approved>=row["stock"]:raise HTTPException(409,"Estoque esgotado")
  c.execute("UPDATE program_claims SET status=?,decided_at=?,decided_by=? WHERE id=?",
   (state,now(),u["id"],cid))
  audit(c,u["id"],"program:claim_"+state,str(cid));c.commit()
 return {"ok":True,"status":state,"no_automatic_delivery":True}

@router.get("/api/program/tasks")
def tasks(u=Depends(admin)):
 with db() as c:
  return {"items":[dict(r) for r in c.execute("SELECT * FROM program_tasks ORDER BY CASE status WHEN 'new' THEN 0 WHEN 'doing' THEN 1 ELSE 2 END, id DESC LIMIT 200")]}

@router.post("/api/program/tasks")
def create_task(data:dict,u=Depends(admin)):
 title=txt(data.get("title"),"Título",3,110)
 desc=txt(data.get("details",""),"Descrição",0,700)
 owner=txt(data.get("owner","Equipe"),"Responsável",2,70)
 priority=verify_enum(data.get("priority","normal"),TASK_PRIORITIES,"Prioridade")
 due=str(data.get("due_on",""))
 if due:
  try:datetime.date.fromisoformat(due)
  except ValueError:raise HTTPException(422,"Data inválida")
 with db() as c:
  cur=c.execute("INSERT INTO program_tasks(title,details,owner,priority,status,due_on,created_at,updated_at) VALUES(?,?,?,?,'new',?,?,?)",
  (title,desc,owner,priority,due,now(),now()))
  audit(c,u["id"],"program:task_created",str(cur.lastrowid));c.commit()
  return {"ok":True,"id":cur.lastrowid}

@router.put("/api/program/tasks/{tid}")
def update_task(tid:int,data:dict,u=Depends(admin)):
 if set(data)!={"status"}:raise HTTPException(422,"Atualize apenas o status")
 state=verify_enum(data["status"],TASK_STATES,"Status")
 with db() as c:
  result=c.execute("UPDATE program_tasks SET status=?,updated_at=? WHERE id=?",(state,now(),tid))
  if not result.rowcount:raise HTTPException(404,"Tarefa não encontrada")
  audit(c,u["id"],"program:task_status",str(tid)+":"+state);c.commit()
 return {"ok":True}

def sniff_media(data):
 if data.startswith(b"\x89PNG\r\n\x1a\n"):return "image/png"
 if data.startswith(b"\xff\xd8\xff"):return "image/jpeg"
 if data.startswith((b"GIF87a",b"GIF89a")):return "image/gif"
 if len(data)>=12 and data[:4]==b"RIFF" and data[8:12]==b"WEBP":return "image/webp"
 if len(data)>12 and data[4:8]==b"ftyp":return "video/mp4"
 if data.startswith(b"ID3") or data[:2] in (b"\xff\xfb",b"\xff\xf3",b"\xff\xf2"):return "audio/mpeg"
 raise HTTPException(422,"Use PNG, JPG, GIF, WebP, MP4 ou MP3")

@router.post("/api/program/media")
async def upload_media(file:UploadFile=File(...),u=Depends(admin)):
 b=await file.read(MEDIA_LIMIT+1)
 if not b or len(b)>MEDIA_LIMIT:raise HTTPException(413,"Arquivo máximo: 8 MB")
 mime=sniff_media(b)
 name=secrets.token_hex(16)
 file_path=MEDIA_DIR/(name+".enc")
 with db() as c:
  try:
   file_path.write_bytes(cipher.encrypt(b));file_path.chmod(0o600)
   c.execute("INSERT INTO program_media(id,mime,file_size,created_at) VALUES(?,?,?,?)",
    (name,mime,len(b),now()))
   audit(c,u["id"],"program:media_uploaded",name[:8]);c.commit()
  except Exception:
   file_path.unlink(missing_ok=True)
   raise
 return {"ok":True,"id":name,"mime":mime,"bytes":len(b)}

@router.get("/api/program/media/{mid}")
def read_media(mid:str,u=Depends(auth)):
 if not re.fullmatch(r"[0-9a-f]{32}",mid):raise HTTPException(404,"Mídia não encontrada")
 with db() as c:
  row=c.execute("SELECT mime FROM program_media WHERE id=?",(mid,)).fetchone()
  if not row:raise HTTPException(404,"Mídia não encontrada")
  if u["role"]!="admin":
   campaigns=c.execute("SELECT segment FROM program_campaigns WHERE media_id=? AND status='published'",(mid,)).fetchall()
   if not any(segment_match(c,u["id"],r["segment"]) for r in campaigns):
    raise HTTPException(403,"Esta mídia não está disponível para sua conta")
 try:decoded=cipher.decrypt((MEDIA_DIR/(mid+".enc")).read_bytes())
 except Exception:raise HTTPException(503,"Arquivo protegido indisponível")
 return Response(decoded,media_type=row["mime"],headers={"Content-Disposition":"inline"})

@router.get("/api/program/campaigns")
def get_campaigns(u=Depends(auth)):
 with db() as c:return {"items":campaigns_for(c,u),"internal_only":True,"messages_sent":0}

@router.post("/api/program/campaigns")
def add_campaign(data:dict,u=Depends(admin)):
 title=txt(data.get("title"),"Título",3,100)
 body=txt(data.get("body"),"Mensagem",3,1200)
 status=verify_enum(data.get("status","draft"),STATES,"Situação")
 segment=verify_enum(data.get("segment","all"),SEGMENTS,"Segmento")
 mid=data.get("media_id") or None
 if mid is not None and (not isinstance(mid,str) or not re.fullmatch(r"[0-9a-f]{32}",mid)):
  raise HTTPException(422,"Arquivo de mídia inválido")
 with db() as c:
  if mid and not c.execute("SELECT id FROM program_media WHERE id=?",(mid,)).fetchone():
   raise HTTPException(422,"Arquivo de mídia inexistente")
  cur=c.execute("INSERT INTO program_campaigns(title,body,status,segment,media_id,created_at,updated_at) VALUES(?,?,?,?,?,?,?)",
    (title,body,status,segment,mid,now(),now()))
  audit(c,u["id"],"program:campaign_created",str(cur.lastrowid));c.commit()
  return {"ok":True,"id":cur.lastrowid,"messages_sent":0}

@router.put("/api/program/campaigns/{cid}")
def publish_campaign(cid:int,data:dict,u=Depends(admin)):
 # Compatível com a ação antiga de publicar/arquivar, mas também permite ao gestor
 # editar título, texto, público e banner sem recriar a campanha.
 allowed={"title","body","status","segment","media_id"}
 if not isinstance(data,dict) or not data or set(data)-allowed:
  raise HTTPException(422,"Campos de campanha inválidos")
 with db() as c:
  previous=c.execute("SELECT * FROM program_campaigns WHERE id=?",(cid,)).fetchone()
  if not previous:raise HTTPException(404,"Campanha não encontrada")
  title=txt(data["title"],"Título",3,100) if "title" in data else previous["title"]
  body=txt(data["body"],"Mensagem",3,1200) if "body" in data else previous["body"]
  status=verify_enum(data["status"],STATES,"Situação") if "status" in data else previous["status"]
  segment=verify_enum(data["segment"],SEGMENTS,"Segmento") if "segment" in data else previous["segment"]
  mid=previous["media_id"]
  if "media_id" in data:
   mid=data["media_id"] or None
   if mid is not None and (not isinstance(mid,str) or not re.fullmatch(r"[0-9a-f]{32}",mid)):
    raise HTTPException(422,"Arquivo de mídia inválido")
   if mid and not c.execute("SELECT id FROM program_media WHERE id=?",(mid,)).fetchone():
    raise HTTPException(422,"Arquivo de mídia inexistente")
  c.execute("UPDATE program_campaigns SET title=?,body=?,status=?,segment=?,media_id=?,updated_at=? WHERE id=?",
   (title,body,status,segment,mid,now(),cid))
  event="program:campaign_edited" if set(data)!={"status"} else "program:campaign_status"
  audit(c,u["id"],event,str(cid)+":"+status);c.commit()
 return {"ok":True,"messages_sent":0}
