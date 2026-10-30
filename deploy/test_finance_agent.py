"""Isolated financial agent test: fake accounts, zero model calls, zero WhatsApp messages."""
import os,sys,tempfile,datetime
from fastapi.testclient import TestClient
with tempfile.TemporaryDirectory(prefix="novagente_finagentqa_") as temp:
 os.environ["CLUBE_DATA"]=temp
 sys.path.insert(0,os.path.dirname(os.path.dirname(__file__)))
 import app,finance_agent_v1 as agent
 from finance_agent_core import classify_text,validate_proposal
 assert classify_text("Gastei R$ 152,45 no supermercado hoje")["category"]=="Supermercado"
 assert classify_text("Comprei remédio R$ 25,80 na farmácia")["category"]=="Farmácia"
 assert classify_text("Abasteci R$ 110 no posto de gasolina")["category"]=="Combustível"
 assert classify_text("Fiz R$ 250 em corridas na Uber")["kind"]=="income"
 assert classify_text("Fiz R$ 250 em corridas na Uber")["category"]=="APLICATIVO"
 assert classify_text("Fiz R$ 250 em corridas na Uber")["merchant"]=="Uber"
 from finance_agent_core import income_label
 for phrase,expected,origin in (
  ("Recebi R$ 100 da Uber","APLICATIVO","Uber"),
  ("Recebi R$ 80 da 99","APLICATIVO","99"),
  ("Recebi R$ 90 na inDrive","APLICATIVO","inDrive"),
  ("Ganhei R$ 55 da Urbano Norte","APLICATIVO","Urbano Norte"),
  ("Ganhei R$ 20 de um passageiro","APLICATIVO",None),
  ("Peguei um cliente de 40 reais","APLICATIVO",None),
  ("Recebi R$ 30 a mais","OUTROS","Extra"),
  ("Recebi R$ 15 de gorjeta do Uber","OUTROS","Extra"),
  ("Ganhei R$ 70 de um cliente particular","OUTROS","Particular"),
  ("Recebi R$ 60 de trabalho extra","OUTROS","Extra"),
  ("Recebi R$ 100","OUTROS",None),
  ("Recebi R$ 99","OUTROS",None),
  ("Recebi R$ 99 da 99","APLICATIVO","99")):
  actual=classify_text(phrase)
  assert actual["kind"]=="income" and actual["status"]=="ready",(phrase,actual)
  assert (actual["category"],actual["merchant"])==(expected,origin),(phrase,actual)
 assert classify_text("Recebi um valor a mais")["status"]=="needs_review"
 assert classify_text("Paguei R$ 70 de combustível")["kind"]=="expense"
 assert validate_proposal({"kind":"income","amount":100,"category":"Corridas",
   "summary":"Recebi R$ 100 da Uber"})["category"]=="APLICATIVO"
 assert validate_proposal({"kind":"income","amount":20,"category":"Corridas",
   "summary":"Ganhei R$ 20 de gorjeta da Uber"})["category"]=="OUTROS"
 assert validate_proposal({"kind":"income","amount":99,"category":"Corridas 99",
   "summary":"Recebi R$ 99"})["category"]=="OUTROS"
 assert classify_text("Fui ao mercado e comprei")["status"]=="needs_review"
 assert classify_text("Paguei 25 em jogo")["nature"]=="opcional"
 assert validate_proposal({"kind":"expense","amount":None,"category":"Farmácia"})["status"]=="needs_review"
 print("01 - categories, nature, unknown amounts, revenue recognition: PASS")
 pw=app.password_hash("exampleLongPassword2026")
 with app.db() as c:
  for uid,role in ((1,"admin"),(2,"driver"),(3,"driver")):
   c.execute("INSERT INTO users(id,username,phash,role,status,name,created_at,must_change) VALUES(?,?,?,?,?,?,?,0)",
      (uid,"agentqa"+str(uid),pw,role,"active","Fake account",app.now()))
  c.commit()
 user={"id":2,"role":"driver","name":"Fake","status":"active","must_change":0}
 app.app.dependency_overrides[app.auth]=lambda:user
 cli=TestClient(app.app,base_url="https://local.example")
 headers={"X-Requested-With":"NOVAGENTE-V5"}
 def req(method,path,payload=None,files=None):
  return cli.request(method,"/api/finance-agent/"+path,json=payload if files is None else None,
   files=files,headers=headers)
 def ok(r):assert r.status_code==200,(r.status_code,r.text[:200]);return r.json()
 denied=req("POST","text",{"text":"Gastei R$ 20 no supermercado"})
 assert denied.status_code==403
 opts=ok(req("GET","consent"))["options"]
 assert not opts["enabled"] and not opts["media_ai"] and not opts["offers"]
 print("02 - off by default, separate agent and media consent: PASS")
 consent={"enabled":True,"media_ai":False,"trends":False,"offers":False}
 ok(req("PUT","consent",consent))
 first=ok(req("POST","text",{"text":"Gastei R$ 152,45 no supermercado hoje"}))
 assert first["proposal"]["amount"]==152.45 and not first["saved"]
 pid=first["id"]
 with app.db() as c:
  assert c.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]==0
  encrypted=c.execute("SELECT encrypted FROM finance_agent_proposals WHERE id=?",(pid,)).fetchone()[0]
  assert b"supermercado" not in encrypted
 print("03 - encrypted pending proposal, not an automatic expense: PASS")
 assert req("POST","media",files={"file":("test.png",b"\x89PNG\r\n\x1a\n"+b"0"*30,"image/png")}).status_code==403
 print("04 - media processing forbidden without explicit consent: PASS")
 ok(req("PUT","consent",{**consent,"media_ai":True}))
 assert req("POST","media",files={"file":("test.png",b"\x89PNG\r\n\x1a\n"+b"0"*30,"image/png")}).status_code==409
 print("05 - no model key means no image/audio processing or false success: PASS")
 user.update({"id":1,"role":"admin"})
 conf=ok(req("GET","/../admin/finance-agent/provider")) if False else cli.get("/api/admin/finance-agent/provider")
 assert conf.status_code==200 and not conf.json()["key_set"]
 fakekey="sk-"+"x"*40
 rr=cli.put("/api/admin/finance-agent/provider",json={"api_key":fakekey},headers=headers)
 assert rr.status_code==200
 body=cli.get("/api/admin/finance-agent/provider").json()
 assert body["key_set"] and fakekey not in str(body)
 print("06 - model credentials encrypted and redacted from API: PASS")
 user.update({"id":2,"role":"driver"})
 # fake AI adapter for testing without API calls
 agent.image_analyze=lambda key,blob,mime,caption:validate_proposal(
  {"kind":"expense","amount":89.4,"category":"Supermercado","merchant":"MERCEARIA DE TESTE","items":[{"name":"Arroz","amount":20,"nature":"essencial"},{"name":"Refrigerante","amount":9,"nature":"opcional"}],"summary":"Nota de supermercado"})
 mock=ok(req("POST","media",files={"file":("fake.png",b"\x89PNG\r\n\x1a\n"+b"0"*30,"image/png")}))
 assert mock["proposal"]["items"][1]["nature"]=="opcional" and not mock["saved"]
 print("07 - media suggestion supports mixed essential/optional items: PASS")
 cc={"kind":"expense","amount":152.45,"category":"Supermercado","note":"Compra validada","date":datetime.date.today().isoformat()}
 recorded=ok(req("POST",f"proposals/{pid}/confirm",cc))
 assert recorded["transaction_id"]>0
 assert req("POST",f"proposals/{pid}/confirm",cc).status_code==409
 with app.db() as c:
  assert c.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]==1
 print("08 - confirmation posts exactly one ledger entry, no duplicates: PASS")
 user.update({"id":3,"role":"driver"})
 assert req("POST",f"proposals/{pid}/confirm",cc).status_code==403 or req("POST",f"proposals/{pid}/confirm",cc).status_code==404
 assert not ok(req("GET","proposals"))["items"]
 print("09 - strict account separation: PASS")
 user.update({"id":2,"role":"driver"})
 assert req("GET","insights").status_code==403
 ok(req("PUT","consent",{**consent,"media_ai":True,"trends":True}))
 trends=ok(req("GET","insights"))
 assert trends["expenses"].get("Supermercado")==152.45
 assert trends["offers_used"] is False
 print("10 - opt-in trends, only confirmed expenses, no targeting/offers: PASS")
 ok(req("PUT","consent",{"enabled":False,"media_ai":False,"trends":False,"offers":False}))
 assert req("POST","text",{"text":"Gastei R$ 30 com gasolina"}).status_code==403
 print("11 - revocation stops new classifications: PASS")
 user.update({"id":1,"role":"admin"})
 assert req("GET","proposals").status_code==403
 print("12 - administrator cannot impersonate driver on private agent API: PASS")
 with app.db() as c:assert c.execute("PRAGMA integrity_check").fetchone()[0]=="ok"
 print("13 - database integrity: PASS")
 app.app.dependency_overrides.clear()
print("13/13 financial agent isolated tests passed.")
