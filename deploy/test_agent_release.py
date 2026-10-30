"""Portal launch: driver can opt in, admin can pause; payments and WhatsApp unchanged."""
import os,sys,tempfile
from fastapi.testclient import TestClient
with tempfile.TemporaryDirectory(prefix="novagente_agent_release_test_") as d:
 os.environ["CLUBE_DATA"]=d
 sys.path.insert(0,os.path.dirname(os.path.dirname(__file__)))
 import app
 with app.db() as c:
  for i,role,status in ((11,"admin","active"),(21,"driver","active"),(22,"driver","active")):
   c.execute("INSERT INTO users(id,username,phash,role,status,name,created_at,must_change) VALUES(?,?,?,?,?,?,?,0)",
    (i,"test"+str(i),"mock",role,status,"Conta ficticia",app.now()))
  c.commit()
 identity={"id":11,"role":"admin","status":"active","name":"Admin QA","must_change":0}
 app.app.dependency_overrides[app.auth]=lambda:identity
 client=TestClient(app.app,base_url="https://staging.local")
 headers={"X-Requested-With":"NOVAGENTE-V5"}
 def req(method,url,payload=None):
  return client.request(method,"/api/"+url,json=payload,headers=headers)
 def good(r):
  assert r.status_code==200,(r.status_code,r.text[:350])
  return r.json()
 manager=good(req("GET","admin/finance-agent/release"))
 assert manager["available"] and manager["active_drivers"]==2
 assert manager["authorized_drivers"]==0 and manager["authorized_multimodal"]==0
 assert not manager["whatsapp_automatic"] and not manager["bank_integration"]
 print("01: Portal agent released, no driver opted in automatically: PASS")
 identity.update({"id":21,"role":"driver","name":"Driver QA"})
 release=good(req("GET","finance-agent/release"))
 assert release["available"] and release["consent_needed"]
 assert release["message_types"]["text"]
 assert req("POST","finance-agent/text",{"text":"Gastei R$ 34 no posto"}).status_code==403
 print("02: Driver sees agent but must grant explicit permission: PASS")
 permissions={"enabled":True,"text_ai":False,"media_ai":False,"trends":True,"offers":False}
 good(req("PUT","finance-agent/consent",permissions))
 val=good(req("POST","finance-agent/text",{"text":"Gastei R$ 34 no posto de gasolina"}))
 assert not val["saved"] and val["proposal"]["category"]=="Combustível"
 proposal_id=val["id"]
 with app.db() as c:assert c.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]==0
 print("03: Driver agent makes reversible, uncommitted suggestion: PASS")
 identity.update({"id":11,"role":"admin","name":"Admin QA"})
 data=good(req("GET","admin/finance-agent/release"))
 assert data["authorized_drivers"]==1 and data["proposals"].get("pending")==1
 assert req("PUT","admin/finance-agent/release",{"enabled":"no"}).status_code==422
 stop=good(req("PUT","admin/finance-agent/release",{"enabled":False}))
 assert not stop["available"] and stop["individual_consents_unchanged"]
 print("04: Admin can pause without changing individual privacy choices: PASS")
 identity.update({"id":21,"role":"driver","name":"Driver QA"})
 assert not good(req("GET","finance-agent/release"))["available"]
 assert req("POST","finance-agent/text",{"text":"Gastei R$ 20 na farmácia"}).status_code==503
 assert req("POST",f"finance-agent/proposals/{proposal_id}/confirm",{"kind":"expense","amount":34,"category":"Combustível","note":"QA","date":""}).status_code==503
 assert good(req("GET","finance-agent/consent"))["options"]["enabled"]
 assert len(good(req("GET","finance-agent/proposals"))["items"])==1
 print("05: Pause blocks processing but still permits account data access: PASS")
 identity.update({"id":11,"role":"admin","name":"Admin QA"})
 good(req("PUT","admin/finance-agent/release",{"enabled":True}))
 identity.update({"id":21,"role":"driver","name":"Driver QA"})
 result=good(req("POST",f"finance-agent/proposals/{proposal_id}/confirm",
   {"kind":"expense","amount":34,"category":"Combustível","note":"Registro confirmado","date":""}))
 assert result["transaction_id"]>=1
 assert req("POST",f"finance-agent/proposals/{proposal_id}/confirm",
   {"kind":"expense","amount":34,"category":"Combustível","note":"Registro confirmado","date":""}).status_code==409
 print("06: Resume permits confirmation once; no duplicate expense: PASS")
 identity.update({"id":22,"role":"driver","name":"Other QA"})
 assert good(req("GET","finance-agent/release"))["consent_needed"]
 assert not good(req("GET","finance-agent/consent"))["options"]["enabled"]
 assert not good(req("GET","finance-agent/proposals"))["items"]
 print("07: Each driver's consent and financial data remain isolated: PASS")
 identity.update({"id":11,"role":"admin","name":"Admin QA"})
 state=good(req("GET","admin/finance-agent/release"))
 assert state["authorized_drivers"]==1 and state["proposals"].get("confirmed")==1
 with app.db() as c:
  assert c.execute("PRAGMA integrity_check").fetchone()[0]=="ok"
  assert c.execute("SELECT COUNT(*) FROM finance_agent_consent WHERE enabled=1").fetchone()[0]==1
 print("08: Audit-ready aggregate controls and SQLite integrity: PASS")
 app.app.dependency_overrides.clear()
print("8/8 internal finance agent release tests PASS; no changes to real drivers.")
