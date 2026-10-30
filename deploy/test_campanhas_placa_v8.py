"""Regressões isoladas para edição de campanhas e placa obrigatória na identificação opt-in.
Dados fictícios. NÃO envia WhatsApp, não acessa banco ou Pix reais.
Executar: python deploy/test_campanhas_placa_v8.py
"""
import os
import sys
import tempfile
from fastapi.testclient import TestClient

with tempfile.TemporaryDirectory(prefix="movi-campanhas-placa-qa-") as folder:
 os.environ["CLUBE_DATA"]=folder
 sys.path.insert(0,os.path.dirname(os.path.dirname(__file__)))
 import app
 from schema import active_fields
 with app.db() as c:
  for uid,role in ((10,"admin"),(20,"driver"),(21,"driver")):
   c.execute("INSERT INTO users(id,username,phash,role,status,name,created_at,must_change) VALUES(?,?,?,?,?,?,?,0)",
    (uid,"fake"+str(uid),"test_only",role,"active","Conta Fictícia "+str(uid),app.now()))
   if role=="driver":
    c.execute("INSERT INTO consents(uid,insights,marketing,identity_collection,updated_at) VALUES(?,?,?,?,?)",
     (uid,1,1,1,app.now()))
  app.save_profile(c,20,{"bid_resources":"não tenho","platform":"UBER"})
  app.save_profile(c,21,{"bid_resources":"não tenho","platform":"99"})
  c.commit()
 role={"id":10,"role":"admin","name":"Gestão Fictícia","status":"active","must_change":0}
 app.app.dependency_overrides[app.auth]=lambda:role
 cli=TestClient(app.app,base_url="https://qa.example.test")
 h={"X-Requested-With":"NOVAGENTE-V5"}
 def req(method,path,data=None,files=None):
  return cli.request(method,"/api/"+path,headers=h,json=data if files is None else None,files=files)
 def ok(r):
  assert r.status_code==200,(r.status_code,r.text[:300])
  return r.json()

 draft=ok(req("POST","program/campaigns",{
  "title":"Banner fictício","body":"Apenas um teste interno","segment":"UBER","status":"draft"}))
 cid=draft["id"]
 assert req("PUT",f"program/campaigns/{cid}",{"title":""}).status_code==422
 assert req("PUT",f"program/campaigns/{cid}",{"segment":"grupo inexistente"}).status_code==422
 assert req("PUT",f"program/campaigns/{cid}",{"media_id":"id-invalido"}).status_code==422
 pic=b"\x89PNG\r\n\x1a\n"+b"\x00"*40
 media=ok(req("POST","program/media",files={"file":("banner-ficticio.png",pic,"image/png")}))
 mid=media["id"]
 ok(req("PUT",f"program/campaigns/{cid}",{
  "title":"Oferta revisada","body":"Texto alterado pelo gestor",
  "segment":"99","status":"published","media_id":mid}))
 saved=ok(req("GET","program/campaigns"))["items"][0]
 assert saved["title"]=="Oferta revisada" and saved["segment"]=="99"
 assert saved["media_id"]==mid and saved["mime"]=="image/png"
 role.update({"id":20,"role":"driver"})
 assert ok(req("GET","program/campaigns"))["items"]==[]
 assert req("GET","program/media/"+mid).status_code==403
 role.update({"id":21,"role":"driver"})
 assert len(ok(req("GET","program/campaigns"))["items"])==1
 assert req("GET","program/media/"+mid).content==pic
 role.update({"id":10,"role":"admin"})
 ok(req("PUT",f"program/campaigns/{cid}",{"status":"draft"}))
 assert ok(req("GET","program/campaigns"))["items"][0]["title"]=="Oferta revisada"
 ok(req("PUT",f"program/campaigns/{cid}",{"media_id":None}))
 assert ok(req("GET","program/campaigns"))["items"][0]["media_id"] is None
 print("01 - Criar, editar, segmentar, publicar, retirar mídia e voltar a rascunho: PASS")

 keys=[f[0] for f in active_fields({"bid_resources":"não tenho"})]
 assert "vehicle_plate" in keys
 assert req("PUT","profile",{"vehicle_plate":"ABC1234"}).status_code==403 if role["role"]=="admin" else True
 role.update({"id":20,"role":"driver"})
 assert req("PUT","profile",{"vehicle_plate":""}).status_code==422
 assert req("PUT","profile",{"vehicle_plate":"ABC-XX"}).status_code==422
 ok(req("PUT","profile",{"vehicle_plate":"abc-1234"}))
 prof=ok(req("GET","profile"))["answers"]
 assert prof["vehicle_plate"]=="ABC1234"
 print("02 - Placa universal no formulário consentido, normalização e validação: PASS")
 with app.db() as c:
  p={f[0]:"respondido" for f in active_fields({"bid_resources":"não tenho"}) if f[0]!="vehicle_plate"}
  p["bid_resources"]="não tenho"
  app.save_profile(c,20,p);c.commit()
 q=ok(req("GET","profile/next"))["question"]
 assert q and q["key"]=="vehicle_plate",q
 assert req("POST","profile/answer",{"key":"vehicle_plate","skip":True}).status_code==422
 ok(req("POST","profile/answer",{"key":"vehicle_plate","value":"ABC1D23"}))
 assert ok(req("GET","profile"))["answers"]["vehicle_plate"]=="ABC1D23"
 print("03 - Não é possível pular a placa no questionário consentido: PASS")
 app.app.dependency_overrides.clear()
 print("3/3 grupos de regressão previstos; somente dados fictícios.")
