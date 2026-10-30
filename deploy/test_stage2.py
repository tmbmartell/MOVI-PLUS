"""Stage2 isolated backend tests: no real motorists, funds, campaigns, WhatsApp."""
import os,tempfile,sys,datetime
from fastapi.testclient import TestClient
with tempfile.TemporaryDirectory(prefix="novagente-stage2qa-") as folder:
 os.environ["CLUBE_DATA"]=folder
 sys.path.insert(0,os.path.dirname(os.path.dirname(__file__)))
 import app
 with app.db() as c:
  for i,role in ((101,"admin"),(201,"driver"),(202,"driver"),(203,"driver")):
   c.execute("INSERT INTO users(id,username,phash,role,status,name,created_at,must_change) VALUES(?,?,?,?,?,?,?,0)",
    (i,"qa"+str(i),"placeholder",role,"active","Motorista fictício "+str(i),app.now()))
   if role=="driver":
    c.execute("INSERT INTO consents(uid,insights,marketing,updated_at) VALUES(?,?,?,?)",
      (i,int(i!=203),int(i==201),app.now()))
  app.save_profile(c,201,{"platform":"UBER","gross_income":2500,"weekly_days":5})
  app.save_profile(c,202,{"platform":"99","gross_income":1000})
  app.save_profile(c,203,{"platform":"UBER","gross_income":2500})
  current=datetime.date.today().isoformat()
  c.execute("INSERT INTO transactions(uid,kind,category,amount_cents,entry_date,note,at) VALUES(?,?,?,?,?,?,?)",
   (201,"income","corridas",150000,current,"",app.now()))
  c.execute("INSERT INTO transactions(uid,kind,category,amount_cents,entry_date,note,at) VALUES(?,?,?,?,?,?,?)",
   (201,"expense","combustível",40000,current,"",app.now()))
  c.execute("INSERT INTO transactions(uid,kind,category,amount_cents,entry_date,note,at) VALUES(?,?,?,?,?,?,?)",
   (203,"income","corridas",850000,current,"",app.now()))
  c.commit()
 who={"id":101,"role":"admin","name":"Teste","status":"active","must_change":0}
 app.app.dependency_overrides[app.auth]=lambda:who
 cli=TestClient(app.app,base_url="https://stage2.test")
 H={"X-Requested-With":"NOVAGENTE-V5"}
 def req(m,path,data=None,files=None):
  return cli.request(m,"/api/program/"+path,headers=H,json=data if files is None else None,files=files)
 def good(r):
  assert 200<=r.status_code<300,(r.status_code,r.text[:250])
  return r.json()
 dash=good(req("GET","dashboard"))
 assert dash["drivers"]==3 and dash["authorized"]==2 and dash["income_declared"]==1500
 assert dash["expense_declared"]==400 and dash["net_declared"]==1100
 assert dash["platforms"]=={"UBER":1,"99":1}
 print("01 - dashboard consent isolation and declarations: PASS")
 assert req("GET","dashboard?month=2026-99").status_code==422
 csv=req("GET","report.csv");assert csv.status_code==200 and "Receitas autodeclaradas" in csv.text
 print("02 - monthly aggregate CSV report: PASS")
 ben=good(req("POST","benefits",{"title":"Lavagem de veículo","description":"Solicitação sujeita a aprovação manual.","points_required":0,"stock":1}))
 bid=ben["id"]
 good(req("POST","tasks",{"title":"Conferir inscrições","details":"Cadastro pendente","owner":"Equipe","priority":"high","due_on":""}))
 tasks=good(req("GET","tasks"))["items"];assert len(tasks)==1
 good(req("PUT","tasks/"+str(tasks[0]["id"]),{"status":"done"}))
 print("03 - admin benefits and task kanban: PASS")
 who.update({"id":201,"role":"driver"})
 own=good(req("GET","benefits"))
 assert own["points"]["total"]>=0
 claim=good(req("POST",f"benefits/{bid}/claim"));assert claim["status"]=="pending"
 assert req("POST",f"benefits/{bid}/claim").status_code==409
 who.update({"id":101,"role":"admin"})
 claim_id=good(req("GET","claims"))["items"][0]["id"]
 good(req("POST",f"claims/{claim_id}/decide",{"status":"approved"}))
 b=good(req("GET","benefits"))["items"][0];assert b["remaining"]==0
 print("04 - manual benefit review, inventory and no duplicate redemption: PASS")
 who.update({"id":203,"role":"driver"})
 assert req("POST",f"benefits/{bid}/claim").status_code==403
 who.update({"id":101,"role":"admin"})
 campaign=good(req("POST","campaigns",{"title":"Aviso Uber","body":"Conteúdo interno para quem optou","status":"published","segment":"UBER"}))
 allc=good(req("GET","campaigns"));assert len(allc["items"])==1
 who.update({"id":201,"role":"driver"})
 assert len(good(req("GET","campaigns"))["items"])==1
 who.update({"id":202,"role":"driver"})
 assert len(good(req("GET","campaigns"))["items"])==0
 who.update({"id":203,"role":"driver"})
 assert len(good(req("GET","campaigns"))["items"])==0
 print("05 - campaign filters respect marketing + insights: PASS")
 who.update({"id":101,"role":"admin"})
 png=b"\x89PNG\r\n\x1a\n"+b"\x00"*30
 uploaded=good(req("POST","media",files={"file":("image.png",png,"image/png")}))
 mid=uploaded["id"]
 good(req("POST","campaigns",{"title":"Campanha com imagem","body":"Imagem interna permitida","status":"published","segment":"all","media_id":mid}))
 who.update({"id":201,"role":"driver"})
 data=req("GET","media/"+mid);assert data.status_code==200 and data.content==png
 who.update({"id":202,"role":"driver"})
 assert req("GET","media/"+mid).status_code==403
 print("06 - encrypted media and authenticated consent-based access: PASS")
 who.update({"id":101,"role":"admin"})
 assert req("POST","media",files={"file":("hack.html",b"<html>bad</html>","text/html")}).status_code==422
 print("07 - unsafe uploads rejected: PASS")
 with app.db() as c:
  assert c.execute("PRAGMA integrity_check").fetchone()[0]=="ok"
  assert c.execute("SELECT COUNT(*) FROM program_campaigns").fetchone()[0]==2
 print("08 - SQLite integrity and stored campaigns: PASS")
 app.app.dependency_overrides.clear()
 print("8/8 STAGE 2 backend tests PASSED. Fake data database removed.")
