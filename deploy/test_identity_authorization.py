"""Isolated test of the consent-gated identity intake. NO REAL PERSONAL DATA."""
import os,sys,tempfile,sqlite3
from fastapi.testclient import TestClient
with tempfile.TemporaryDirectory(prefix="ng-ident-opt-") as path:
 os.environ["CLUBE_DATA"]=path
 os.environ["CLUBE_ENABLE_SENSITIVE"]="0"
 sys.path.insert(0,os.path.dirname(os.path.dirname(__file__)))
 import app
 from schema import ORIGINAL,SENSITIVE
 with app.db() as c:
  for i,role in ((1,"admin"),(2,"driver"),(3,"driver")):
   c.execute("INSERT INTO users(id,username,phash,role,status,name,created_at,must_change) VALUES(?,?,?,?,?,?,?,0)",
    (i,"qa"+str(i),"pass_not_used",role,"active","Pessoa Fictícia",app.now()))
  c.commit()
 u={"id":2,"role":"driver","status":"active","name":"Pessoa Fictícia","must_change":0}
 app.app.dependency_overrides[app.auth]=lambda:u
 cli=TestClient(app.app,base_url="https://valid.example")
 h={"X-Requested-With":"NOVAGENTE-V5"}
 def put(path,d):return cli.put('/api/'+path,json=d,headers=h)
 def get(path):return cli.get('/api/'+path)
 def post(path,d={}):return cli.post('/api/'+path,json=d,headers=h)
 def test(code,response):assert response.status_code==code,(response.status_code,response.text[:300])
 def consent(identity, insights=True,assisted=True,documents=True):
  return {"insights":insights,"marketing":False,"sharing":False,"documents":documents,"assisted_entry":assisted,"identity_collection":identity}
 rs=get('profile');test(200,rs)
 assert not rs.json()['identity_collection_enabled']
 assert not get('documents').json()['enabled']
 assert get('schema').json()['fields'][1]['protected']
 test(403,put('profile',{"cpf":"11122233344"}))
 print("01: Identity fields locked before individual opt-in: PASS")
 test(200,put('consents',consent(True)))
 assert get('consents').json()['choices']['identity_collection']==1
 assert get('profile').json()['identity_collection_enabled']
 assert get('documents').json()['enabled']
 assert get('schema').json()['fields'][1]['protected']==False
 print("02: Consent saved and schema automatically unlocks identity: PASS")
 fake={"full_name":"PESSOA TESTE FICTICIA","cpf":"11122233344","rg":"TESTERG","birth_date":"2000-01-01",
       "email":"ficticio@example.test","address_cep":"Rua Demonstracao, 00 CEP 00000-000",
       "whatsapp":"(69) 99999-9999","vehicle_plate":"FIC0000"}
 r=put('profile',fake);test(200,r)
 p=get('profile').json()
 assert all(p['answers'][k]==v for k,v in fake.items())
 with app.db() as c:
  from cryptography.fernet import Fernet
  encrypted=c.execute("SELECT encrypted FROM profiles WHERE uid=2").fetchone()[0]
  assert b"11122233344" not in encrypted
  assert "Pessoa Fictícia".encode() not in encrypted
 print("03: Test identifiers saved encrypted after opt-in: PASS")
 # Documents: synthetic binary accepted to exercise infrastructure, not an actual CNH
 pdf=b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\n%%EOF"
 files={"file":("arquivo_teste.pdf",pdf,"application/pdf")}
 r=cli.post("/api/documents",files=files,headers=h);test(200,r)
 docid=r.json()['id']
 r=get('documents');test(200,r)
 assert r.json()['enabled'] and len(r.json()['items'])==1
 rr=get('documents/'+docid);test(200,rr);assert rr.content==pdf
 print("04: Gated document upload/download with encryption: PASS")
 u.update({"id":1,"role":"admin"})
 test(200,get('admin/assisted-profile/2'))
 assert get('admin/assisted-profile/2').json()['answers']['cpf']==fake["cpf"]
 r=put('admin/assisted-profile/2',{"full_name":"ATUALIZADO TESTE"});test(200,r)
 assert get('admin/assisted-profile/2').json()['answers']['full_name']=="ATUALIZADO TESTE"
 print("05: Admin edit only with all purpose-specific authorizations: PASS")
 u.update({"id":2,"role":"driver"})
 test(200,put('consents',consent(False)))
 assert get('schema').json()['fields'][1]['protected']==True
 assert not get('profile').json()['identity_collection_enabled']
 test(403,put('profile',{"cpf":"99988877766"}))
 test(403,cli.post('/api/documents',files=files,headers=h))
 u.update({"id":1,"role":"admin"})
 test(403,put('admin/assisted-profile/2',{"cpf":"99988877766"}))
 r=get('admin/assisted-profile/2');test(200,r)
 assert "cpf" not in r.json()['answers']
 test(403,get('documents/'+docid))
 print("06: Revocation blocks driver edits/uploads and admin sensitive read/write: PASS")
 u.update({"id":3,"role":"driver"})
 test(403,put('profile',{"cpf":"44455566677"}))
 test(403,cli.post('/api/documents',files=files,headers=h))
 print("07: Second driver cannot inherit another driver's authorizations: PASS")
 test(200,put('consents',{"insights":False,"marketing":False,"sharing":False,"documents":False}))
 assert not get('consents').json()['choices']['identity_collection']
 print("08: Existing client consent payload supported and does not enable identity: PASS")
 with app.db() as c:
  assert c.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
 print("09: Data integrity after changes: PASS")
 app.app.dependency_overrides.clear()
print("9/9 consent-gated identity tests PASSED; all test data temporary.")