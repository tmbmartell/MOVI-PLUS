"""One-contact driver may VIEW pairing status, not configure session."""
import os,sys,tempfile
from unittest.mock import patch
from fastapi.testclient import TestClient
with tempfile.TemporaryDirectory(prefix="ng_wa_role_handoff_") as d:
 os.environ["CLUBE_DATA"]=d
 sys.path.insert(0,os.path.dirname(os.path.dirname(__file__)))
 import app,finance_agent_waha_v1 as wa
 from whatsapp_bridge_v5 import ensure_table
 from finance_agent_pilot_v1 import state
 with app.db() as c:
  for id,username,role in ((11,"manager","admin"),(21,"pilot","driver"),(22,"other","driver")):
   c.execute("INSERT INTO users(id,username,phash,role,status,name,created_at,must_change) VALUES(?,?,?,?,?,?,?,0)",
    (id,username,"dummy",role,"active","QA",app.now()))
  ensure_table(c)
  c.execute("INSERT INTO whatsapp_bridge_config(id,encrypted,updated_at,actor) VALUES(1,?,?,?)",
   (app.enc({"base_url":"http://127.0.0.1:18182","session":"clube-motorista","api_key":"NOT_REAL"}),app.now(),11))
  c.execute("INSERT INTO finance_agent_wa_pilot(id,uid,enabled,updated_at) VALUES(1,21,1,?)",(app.now(),))
  c.commit()
 user={"id":21,"role":"driver","status":"active","must_change":0}
 app.app.dependency_overrides[app.auth]=lambda:user
 client=TestClient(app.app,base_url="https://qa.test")
 def fake_waha(cfg,method,path):
  assert method=="GET" and path=="/api/sessions/clube-motorista"
  class Resp:
   def json(self):return {"status":"WORKING","me":{"id":"HIDDEN"}}
  return Resp(),200
 with patch("whatsapp_bridge_v5.waha",side_effect=fake_waha):
  r=client.get("/api/finance-agent/whatsapp/session-status")
 assert r.status_code==200,r.text
 a=r.json()
 assert a["connected"] and a["status"]=="WORKING" and a["eligible"]
 assert not a["linked"] and "api_key" not in a and "base_url" not in a and "me" not in a
 print("01 Pilot driver sees WORKING status without session credentials/phone: PASS")
 def paired_waha(cfg,method,path):
  class Resp:
   def json(self):return {"status":"WORKING","me":{"id":"5511999887766@c.us"}}
  return Resp(),200
 with patch("whatsapp_bridge_v5.waha",side_effect=paired_waha):
  reveal=client.get("/api/finance-agent/whatsapp/session-status")
 assert reveal.status_code==200 and reveal.json()["club_whatsapp_number"]=="5511999887766"
 print("01b Pilot sees the actual recipient number, not private WAHA API keys: PASS")
 for endpoint in ["/api/admin/whatsapp-bridge","/api/admin/finance-agent/whatsapp"]:
  assert client.get(endpoint).status_code==403
 assert client.post("/api/admin/whatsapp-bridge/check",headers={"X-Requested-With":"NOVAGENTE-V5"}).status_code==403
 print("02 Driver cannot access privileged WAHA configuration or admin check: PASS")
 user["id"]=22
 r=client.get("/api/finance-agent/whatsapp/session-status")
 assert r.status_code==403
 print("03 Other drivers cannot read exclusive pilot status: PASS")
 user["id"]=11;user["role"]="admin"
 assert client.get("/api/finance-agent/whatsapp/session-status").status_code==403
 print("04 Admin does not masquerade as a driver: PASS")
 user["id"]=21;user["role"]="driver"
 from fastapi import HTTPException
 with patch("whatsapp_bridge_v5.waha",side_effect=HTTPException(503,"Provider reconnecting")):
  r=client.get("/api/finance-agent/whatsapp/session-status")
 assert r.status_code==200 and not r.json()["connected"]
 assert r.json()["status"]=="TEMPORARIAMENTE_INDISPONIVEL"
 print("05 Transient WAHA read outage handled without overriding permissions: PASS")
 with app.db() as c:assert c.execute("PRAGMA integrity_check").fetchone()[0]=="ok"
 app.app.dependency_overrides.clear()
print("5/5 one-number read-only session status security tests PASS")
