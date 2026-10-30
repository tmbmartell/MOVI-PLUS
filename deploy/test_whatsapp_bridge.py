"""WAHA bridge regression tests. Uses isolated database and a mocked provider."""
import os,sys,tempfile,base64
from unittest.mock import patch
from fastapi.testclient import TestClient
with tempfile.TemporaryDirectory(prefix="ng_wa_bridge_") as temp:
 os.environ["CLUBE_DATA"]=temp
 os.environ["CLUBE_ENABLE_SENSITIVE"]="0"
 sys.path.insert(0,os.path.dirname(os.path.dirname(__file__)))
 import app
 import whatsapp_bridge_v5 as wa
 with app.db() as c:
  c.execute("INSERT INTO users(id,username,phash,role,status,name,created_at,must_change) VALUES(?,?,?,?,?,?,?,0)",
   (333,"gestor_teste","nologin","admin","active","Gestor Fictício",app.now()))
  c.commit()
 user={"id":333,"username":"gestor_teste","role":"admin","status":"active","name":"Teste","must_change":0}
 app.app.dependency_overrides[app.auth]=lambda:user
 client=TestClient(app.app,base_url="https://example.org")
 H={"X-Requested-With":"NOVAGENTE-V5"}
 def put(obj):return client.put("/api/admin/whatsapp-bridge",json=obj,headers=H)
 def post(path):return client.post("/api/admin/whatsapp-bridge/"+path,json={},headers=H)
 def status():return client.get("/api/admin/whatsapp-bridge")
 def assertcode(r,code):assert r.status_code==code,(r.status_code,r.text)
 d=status();assertcode(d,200);assert not d.json()["configured"]
 print("01 - config initially unconfigured: OK")
 assertcode(put({"provider":"WAHA","base_url":"http://169.254.169.254/latest","session":"clube-motorista","api_key":"FAKE_API_KEY_TEST_ONLY"}),422)
 assertcode(put({"provider":"WAHA","base_url":"http://127.0.0.1:3000","session":"default","api_key":"FAKE_API_KEY_TEST_ONLY"}),422)
 print("02 - SSRF and shared sessions prevented: OK")
 p={"provider":"WAHA","base_url":"http://127.0.0.1:3000","session":"clube-motorista","api_key":"FAKE_API_KEY_TEST_ONLY"}
 assertcode(put(p),200)
 d=status();assertcode(d,200)
 assert d.json()["configured"] and d.json()["api_key_set"] and "api_key" not in d.json()
 with app.db() as c:
  encrypted=c.execute("SELECT encrypted FROM whatsapp_bridge_config WHERE id=1").fetchone()[0]
  assert b"FAKE_API_KEY_TEST_ONLY" not in encrypted
 print("03 - credential encrypted and never exposed by status: OK")
 assertcode(put({**p,"api_key":""}),200)
 with app.db() as c:
  conf,_=wa.config_get(c)
  assert conf["api_key"]=="FAKE_API_KEY_TEST_ONLY"
 print("04 - unchanged API key retained: OK")
 who={"id":334,"role":"driver","name":"Driver","must_change":0}
 user.clear();user.update(who)
 assertcode(status(),403)
 assertcode(post("check"),403)
 user.clear();user.update({"id":333,"role":"admin","name":"Admin","must_change":0})
 print("05 - admin role enforced: OK")
 class Response:
  content=b""
  def __init__(self,value):
   self.value=value
   self.content=b"x" if isinstance(value,dict) else value
  def json(self):return self.value
 png=b"\x89PNG\r\n\x1a\n"+b"\0"*100
 calls=[]
 def fake_waha(conf,method,path,body=None,accept=None):
  calls.append((method,path,body))
  if method=="GET" and path=="/api/sessions/clube-motorista":
   return None,404
  if method=="POST" and path=="/api/sessions":
   assert body["name"]=="clube-motorista" and body["start"] is False
   return Response({"status":"STOPPED"}),201
  if method=="POST" and path.endswith("/start"):return Response({"status":"STARTING"}),200
  if path.endswith("auth/qr?format=image"):
   b64=base64.b64encode(png).decode()
   return Response({"mimetype":"image/png","data":b64}),200
  raise AssertionError(str((method,path)))
 with patch.object(wa,"waha",side_effect=fake_waha):
  assertcode(post("create"),200)
  assertcode(post("start"),200)
  q=post("qr");assertcode(q,200)
  assert q.json()["data_url"].startswith("data:image/png;base64,")
 assert all("/sendText" not in x[1] and "/api/messages" not in x[1] for x in calls)
 print("06 - session prepared stopped, QR returned, no messages sent: OK")
 pair_phone="5511999999999"
 def fake_pair(conf,method,path,body=None,accept=None):
  calls.append((method,path,body))
  if method=="GET" and path.endswith("/api/sessions/clube-motorista"):
   return Response({"status":"SCAN_QR_CODE","me":None,"engine":{"engine":"WEBJS"}}),200
  if method=="POST" and path.endswith("/restart"):
   return Response({"status":"STARTING"}),200
  if method=="POST" and path.endswith("/auth/request-code"):
   assert body=={"phoneNumber":pair_phone}
   return Response({"code":"ABCD-1234"}),200
  raise AssertionError("Unexpected operation")
 with patch.object(wa,"waha",side_effect=fake_pair):
  assertcode(client.post("/api/admin/whatsapp-bridge/request-code",json={"phone_number":"fake"},headers=H),422)
  assertcode(client.post("/api/admin/whatsapp-bridge/request-code",json={"phone_number":pair_phone},headers=H),200)
  assert client.post("/api/admin/whatsapp-bridge/request-code",json={"phone_number":pair_phone},headers=H).status_code==429
  recovered=post("refresh-qr")
  assertcode(recovered,200)
  assert recovered.json()["status"]=="STARTING"
 print("07 - code and refresh require admin and unpaired session; temporary phone not persisted: OK")
 with app.db() as c:
  audit_items=[x["target"] for x in c.execute("SELECT target FROM audit")]
  assert all(pair_phone not in x and "ABCD-1234" not in x for x in audit_items)
 def paired(conf,method,path,body=None,accept=None):
  if method=="GET" and path.endswith("/api/sessions/clube-motorista"):
   return Response({"status":"WORKING","me":{"id":"MASKED"}}),200
  raise AssertionError("Paired account must not be reset")
 wa._throttle.pop((333,"refresh_qr"),None)
 wa._throttle.pop((333,"request_code"),None)
 with patch.object(wa,"waha",side_effect=paired):
  assertcode(post("refresh-qr"),409)
  assertcode(client.post("/api/admin/whatsapp-bridge/request-code",json={"phone_number":pair_phone},headers=H),409)
 print("08 - WORKING account protected against refresh and pairing requests: OK")
 assertcode(client.delete("/api/admin/whatsapp-bridge",headers=H),200)
 assert not status().json()["configured"]
 print("09 - remove local config without deleting remote session: OK")
 assert wa.SEND_MESSAGES_ENABLED is False and wa.INGEST_MESSAGES_ENABLED is False
 print("10 - messaging remains OFF: OK")
 app.app.dependency_overrides.clear()
print("SUCCESS: 10 tests, isolated temporary database, no real WAHA calls.")
