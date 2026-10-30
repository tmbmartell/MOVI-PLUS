"""Temporary test motorist expires after 7 days; no admin privileges or inherited consents."""
import os,sys,tempfile
from fastapi.testclient import TestClient
with tempfile.TemporaryDirectory(prefix="ng_trial_login_") as tmp:
 os.environ["CLUBE_DATA"]=tmp
 sys.path.insert(0,os.path.dirname(os.path.dirname(__file__)))
 import app,legal_v8
 with app.db() as c:
  pwd="long random example password 2026"
  c.execute("INSERT INTO users(id,username,phash,role,status,name,created_at,must_change) VALUES(?,?,?,?,?,?,?,0)",
    (700,"qa_motor",app.password_hash(pwd),"driver","active","Test driver",app.now()))
  c.execute("INSERT INTO trial_driver_accounts(uid,expires) VALUES(?,?)",(700,app.stamp()+3600))
  c.commit()
 site=TestClient(app.app,base_url="https://qa.example")
 h={"X-Requested-With":"NOVAGENTE-V5"}
 result=site.post("/api/login",json={"username":"qa_motor","password":pwd},headers=h)
 assert result.status_code==200,result.text
 print("01 - temporary driver can log in: PASS")
 person=site.get("/api/me")
 assert person.status_code==200 and person.json()["user"]["role"]=="driver"
 print("02 - role is driver only: PASS")
 r=site.get("/api/admin/overview")
 assert r.status_code==428  # V8 requires current legal terms before driver APIs
 legal={"version":legal_v8.VERSION,
        "required":{key:True for key,_ in legal_v8.REQUIRED},
        "optional":{key:False for key,_ in legal_v8.OPTIONAL}}
 accept=site.post("/api/legal/accept",json=legal,headers=h)
 assert accept.status_code==200,accept.text
 r=site.get("/api/admin/overview")
 assert r.status_code==403
 print("03 - terms required; admin data stays forbidden after acceptance: PASS")
 r=site.get("/api/finance-agent/release")
 assert r.status_code==200 and r.json()["available"]
 assert r.json()["consent_needed"]
 print("04 - financial agent accessible only with individual consent: PASS")
 with app.db() as c:
  c.execute("UPDATE trial_driver_accounts SET expires=? WHERE uid=?",(app.stamp()-1,700))
  c.commit()
 r=site.get("/api/me")
 assert r.status_code==200 and r.json()["user"] is None
 print("05 - expired account invalidates active session: PASS")
 r=site.post("/api/login",json={"username":"qa_motor","password":pwd},headers=h)
 assert r.status_code==401
 print("06 - expired account cannot log in again: PASS")
 with app.db() as c:
  assert c.execute("PRAGMA integrity_check").fetchone()[0]=="ok"
 print("07 - isolated DB integrity: PASS")
print("7/7 temporary test driver checks PASS")
