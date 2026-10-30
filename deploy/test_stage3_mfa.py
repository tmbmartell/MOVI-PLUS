import os,sys,tempfile,secrets,time
with tempfile.TemporaryDirectory() as tmp:
 os.environ["CLUBE_DATA"]=tmp
 sys.path.insert(0,os.path.dirname(os.path.dirname(__file__)))
 import app,security_stage3_v5 as m
 from fastapi.testclient import TestClient
 secret=secrets.token_urlsafe(16)+"A4"
 with app.db() as c:
  c.execute("INSERT INTO users(id,username,phash,role,status,name,created_at,must_change) VALUES(?,?,?,?,?,?,?,0)",(1,"qaadmin",app.password_hash(secret),"admin","active","Tester",app.now()))
  c.commit()
 user={"id":1,"role":"admin","status":"active","name":"Tester","username":"qaadmin","must_change":0}
 app.app.dependency_overrides[app.auth]=lambda:user
 client=TestClient(app.app,base_url="https://qa.local")
 h={"X-Requested-With":"NOVAGENTE-V5"}
 def post(p,d):return client.post("/api/security/mfa/"+p,json=d,headers=h)
 r=client.get("/api/security/mfa");print("initial mfa status",r.status_code,r.json());assert r.status_code==200 and r.json()["enabled"] is False
 assert post("setup",{"password":"incorrect"}).status_code==403
 ready=post("setup",{"password":secret})
 assert ready.status_code==200,ready.text[:100]
 key=ready.json()["setup_key"]
 with app.db() as c:assert key.encode() not in c.execute("SELECT pending_secret FROM admin_mfa WHERE uid=1").fetchone()[0]
 confirmed=post("confirm",{"code":m.pin(key,int(time.time())//30)})
 assert confirmed.status_code==200,confirmed.text[:120]
 recovery=confirmed.json()["recovery_codes"]
 assert len(recovery)==8
 print("Admin MFA setup/confirmation and encrypted secret: PASS")
 app.app.dependency_overrides.clear()
 def login(otp=None):
  v={"username":"qaadmin","password":secret}
  if otp is not None:v["otp"]=otp
  return client.post("/api/login",json=v,headers=h)
 assert login().status_code==401
 assert login("invalid").status_code==401
 assert login(m.pin(key,int(time.time())//30)).status_code==401
 assert login(recovery[0]).status_code==200
 assert login(recovery[0]).status_code==401
 print("MFA enforced on login, time-step replay blocked, one-time recovery: PASS")
 app.app.dependency_overrides[app.auth]=lambda:user
 assert post("disable",{"password":secret,"code":recovery[1]}).status_code==200
 app.app.dependency_overrides.clear()
 assert login().status_code==200
 print("Admin can disable MFA with two credentials; login restored: PASS")
print("Stage3 auth end-to-end smoke PASSED")
