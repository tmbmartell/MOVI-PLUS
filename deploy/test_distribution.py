import sys,os,tempfile
from pathlib import Path
with tempfile.TemporaryDirectory(prefix="ng_dist_test_") as tmp:
 os.environ["CLUBE_DATA"]=tmp
 os.environ["CLUBE_ENABLE_SENSITIVE"]="0"
 sys.path.insert(0,os.path.dirname(os.path.dirname(__file__)))
 import app
 from fastapi.testclient import TestClient
 from distribution_v5 import calc
 with app.db() as c:
  for uid,role in ((100,"admin"),(101,"driver"),(102,"driver")):
   c.execute("INSERT INTO users(id,username,phash,role,status,name,created_at,must_change) VALUES(?,?,?,?,?,?,?,0)",
       (uid,"teste_"+str(uid),"nonlogin",role,"active","Teste",app.now()))
  c.commit()
 who={"id":100,"username":"teste_100","role":"admin","name":"Teste","status":"active","must_change":0}
 app.app.dependency_overrides[app.auth]=lambda:who
 client=TestClient(app.app)
 common={"X-Requested-With":"NOVAGENTE-V5"}
 def fetch():return client.get("/api/distribution-plan")
 def write(p):return client.put("/api/distribution-plan",json=p,headers=common)
 r=fetch();assert r.status_code==200,r.text
 default=r.json();assert default["source"]=="exemplo" and len(default["rows"])==5 and default["total"]==100000 and default["reported_sent"]==0
 print("01 / new admin default sample does not invent outgoing transfers: OK")
 payload={"total":100000,"rows":[{"name":a,"percentage":p,"reported_sent":sent} for a,p,sent in
   [("Operação",40,30000),("Comissão",25,17500),("Reserva",20,15000),("Marketing",10,8000),("Taxas",5,2000)]]}
 r=write(payload);assert r.status_code==200,(r.status_code,r.text)
 d=r.json();assert d["reported_sent"]==72500 and d["pending"]==27500 and d["reported_percentage"]==72.5
 assert sum(x["planned"] for x in d["rows"])==100000
 print("02 / 100,000 example: 72,500 declared, 27,500 pending, 72.5%: OK")
 r=fetch();assert r.status_code==200 and r.json()["saved"]==True and r.json()["reported_sent"]==72500
 print("03 / encrypted persistence: OK")
 assert write({"total":100,"rows":[{"name":"A","percentage":80,"reported_sent":0},{"name":"B","percentage":10,"reported_sent":0}]}).status_code==422
 assert write({"total":100,"rows":[{"name":"A","percentage":80,"reported_sent":0},{"name":"B","percentage":20,"reported_sent":80}]}).status_code==422
 assert write({"total":100,"rows":[{"name":"A","percentage":90,"reported_sent":0},{"name":"A","percentage":10,"reported_sent":0}]}).status_code==422
 print("04 / invalid sums, excessive declared values and duplicate categories: OK")
 precise=calc({"total":0.01,"rows":[{"name":"Um","percentage":33.33,"reported_sent":0},{"name":"Dois","percentage":33.33,"reported_sent":0},{"name":"Tres","percentage":33.34,"reported_sent":0}]})
 assert sum(round(x["planned"]*100) for x in precise["rows"])==1
 print("05 / cent-perfect apportionment: OK")
 who["id"]=101;who["role"]="driver"
 r=fetch();assert r.status_code==200 and r.json()["source"]=="exemplo" and r.json()["total"]==5000
 who["id"]=102
 r=fetch();assert r.status_code==200 and not r.json()["saved"]
 who["id"]=100;who["role"]="admin"
 assert fetch().json()["total"]==100000
 print("06 / plans isolated by account and role: OK")
 r=client.delete("/api/distribution-plan",headers=common);assert r.status_code==200
 assert fetch().json()["saved"]==False
 print("07 / reset scenario: OK")
 app.app.dependency_overrides.clear()
 print("END-TO-END: 7 integration tests passed. Temporary DB cleaned.")
