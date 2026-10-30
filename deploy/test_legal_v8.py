"""Termos V8 em banco isolado: cadastro só com aceite completo, aceite registrado, trava até aceitar,
opcionais livres e revogáveis, página pública e exportação com histórico."""
import os,sys,tempfile,types,importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
for name in ("fcntl","resource"):
 if importlib.util.find_spec(name) is None:sys.modules[name]=types.ModuleType(name)  # só para rodar no Windows
from fastapi.testclient import TestClient
with tempfile.TemporaryDirectory(prefix="movi-legal-qa-") as folder:
 os.environ["CLUBE_DATA"]=folder
 sys.path.insert(0,str(ROOT))
 import app,legal_v8
 H={"X-Requested-With":"NOVAGENTE-V5"}
 cli=TestClient(app.app,base_url="https://legal.test")
 def invite(tok):
  with app.db() as c:
   c.execute("INSERT INTO invites(hash,admin_id,expires,used_uid,created_at) VALUES(?,?,?,?,?)",(app.sha(tok),1,app.stamp()+3600,None,app.now()));c.commit()
 doc=cli.get("/api/legal").json()
 assert doc["version"]==legal_v8.VERSION and len(doc["required"])==len(legal_v8.REQUIRED)
 assert any("análises e aprimoramento" in x["text"] for x in doc["required"])
 assert any(x["id"]=="sharing" for x in doc["optional"]),"Parceiros deve ser opcional"
 everything={x["id"]:True for x in doc["required"]}
 base={"name":"Motorista Teste","password":"senhaforte12345","accepted_rules":True}
 # 1. Sem aceite, com item obrigatório faltando ou versão velha: não cria conta.
 invite("tok1")
 r=cli.post("/api/enroll",json={**base,"invite":"tok1","username":"semtermo"},headers=H);assert r.status_code==422,r.text
 r=cli.post("/api/enroll",json={**base,"invite":"tok1","username":"faltaitem","legal":{"version":doc["version"],"required":{**everything,"adult":False},"optional":{}}},headers=H)
 assert r.status_code==422,r.text
 r=cli.post("/api/enroll",json={**base,"invite":"tok1","username":"velho","legal":{"version":"2000-01-01","required":everything,"optional":{}}},headers=H)
 assert r.status_code==409,r.text
 # Sem responder Sim/Não sobre o gestor: não cria conta (consentimento não pode vir pré-marcado).
 r=cli.post("/api/enroll",json={**base,"invite":"tok1","username":"semresposta","legal":{"version":doc["version"],"required":everything,"optional":{"marketing":True}}},headers=H)
 assert r.status_code==422 and "gestor" in r.json()["detail"],r.text
 assert doc["default_on"]==["marketing"] and doc["must_answer"]==["assisted_entry"]
 # 2. Aceite completo, ofertas ligadas e gestor "Não": conta criada, aceite gravado, parceiros desligados.
 legal={"version":doc["version"],"required":everything,"optional":{"marketing":True,"assisted_entry":False}}
 r=cli.post("/api/enroll",json={**base,"invite":"tok1","username":"comtermo","legal":legal},headers=H);assert r.status_code==200,r.text
 with app.db() as c:
  uid=c.execute("SELECT id FROM users WHERE username='comtermo'").fetchone()[0]
  row=c.execute("SELECT version,origin FROM legal_acceptances WHERE uid=?",(uid,)).fetchone()
  assert row["version"]==legal_v8.VERSION and row["origin"]=="cadastro"
  cs=app.consent(c,uid);assert cs["marketing"]==1 and cs["sharing"]==0 and cs["identity_collection"]==0
  c.execute("UPDATE users SET status='active' WHERE id=?",(uid,))
  # Conta antiga, sem aceite registrado (como as criadas antes da V8).
  c.execute("INSERT INTO users(username,phash,role,status,name,created_at,must_change) VALUES(?,?,?,?,?,?,0)",("antigo",app.password_hash("senhaforte12345"),"driver","active","Antigo",app.now()))
  old=c.execute("SELECT id FROM users WHERE username='antigo'").fetchone()[0]
  c.execute("INSERT INTO consents(uid,sharing,updated_at) VALUES(?,?,?)",(old,1,app.now()));c.commit()
 # 3. Conta antiga: travada até aceitar; direitos (exportar, retirar permissão) continuam livres.
 r=cli.post("/api/login",json={"username":"antigo","password":"senhaforte12345"},headers=H);assert r.status_code==200,r.text
 assert cli.get("/api/finances").status_code==428
 assert cli.get("/api/schema").status_code==200,"O app precisa da lista de perguntas ao abrir"
 assert cli.get("/api/legal/status").json()["needs"] is True
 assert cli.get("/api/privacy/export").status_code==200
 assert cli.get("/api/consents").status_code==200
 r=cli.post("/api/legal/accept",json={"version":doc["version"],"required":{**everything,"truth":False},"optional":{}},headers=H);assert r.status_code==422
 r=cli.post("/api/legal/accept",json={"version":doc["version"],"required":everything,"optional":{"assisted_entry":True}},headers=H);assert r.status_code==200,r.text
 assert cli.get("/api/finances").status_code==200
 st=cli.get("/api/legal/status").json();assert st["needs"] is False and st["choices"]["sharing"] is False and st["choices"]["assisted_entry"] is True
 assert st["choices"]["insights"] is True,"Sim para o gestor preencher liga também ver o cadastro"
 # 4. Revogação continua possível depois do aceite (LGPD art. 8º §5º).
 ch=cli.get("/api/consents").json()["choices"]
 r=cli.put("/api/consents",json={**{k:bool(ch[k]) for k in legal_v8.CONSENT_KEYS},"assisted_entry":False},headers=H);assert r.status_code==200,r.text
 assert cli.get("/api/consents").json()["choices"]["assisted_entry"]==0
 # 5. Exportação traz o histórico de aceites; página pública abre sem login.
 assert cli.get("/api/privacy/export").json()["legal_acceptances"][0]["version"]==legal_v8.VERSION
 cli.post("/api/logout",json={},headers=H)
 page=cli.get("/termos");assert page.status_code==200 and "Política de Cookies" in page.text and "clube_session" in page.text
 # 6. Gestor não é travado pelos termos do motorista.
 with app.db() as c:
  c.execute("INSERT INTO users(username,phash,role,status,name,created_at,must_change) VALUES(?,?,?,?,?,?,0)",("chefe",app.password_hash("senhaforte12345"),"admin","active","Gestor",app.now()));c.commit()
 cli.post("/api/login",json={"username":"chefe","password":"senhaforte12345"},headers=H)
 assert cli.get("/api/admin/overview").status_code==200
 print("Termos V8: aceite obrigatório, registro, trava, revogação, página pública e exportação: PASS")
