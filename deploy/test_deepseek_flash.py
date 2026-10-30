"""DeepSeek Flash provider regression: no real credential or external API calls."""
import os,sys,tempfile,json
from fastapi.testclient import TestClient
with tempfile.TemporaryDirectory(prefix="ng_ds_qa_") as tmp:
 os.environ["CLUBE_DATA"]=tmp
 sys.path.insert(0,os.path.dirname(os.path.dirname(__file__)))
 import app,finance_agent_v1 as agent
 from finance_agent_core import classify_text
 assert agent.MODEL_NAME=="deepseek-flash"
 assert agent.PROVIDER_URL=="https://api.deepseek.com"
 print("01: Official DeepSeek Flash model and endpoint selected")
 class FakeResponse:
  status_code=200
  def json(self):
   return {"choices":[{"message":{"content":json.dumps({
    "kind":"expense","amount":84.9,"category":"Supermercado",
    "summary":"Compra de alimentos","items":[]})}}]}
 class FakeClient:
  def __init__(self,**kwargs):pass
  def __enter__(self):return self
  def __exit__(self,*args):return None
  def post(self,url,headers,json):
   assert url=="https://api.deepseek.com/chat/completions"
   assert json["model"]=="deepseek-flash"
   assert json["response_format"]=={"type":"json_object"}
   assert json["thinking"]=={"type":"disabled"}
   return FakeResponse()
 original=agent.httpx.Client
 agent.httpx.Client=FakeClient
 result=agent.deepseek_text("MOCK_NOT_REAL","Gastei oitenta e quatro reais e noventa centavos no mercado")
 assert result["category"]=="Supermercado"
 assert result["amount"]==84.9
 agent.httpx.Client=original
 print("02: JSON API request targets DeepSeek with proper vision-compatible model; semantic text extraction")
 with app.db() as c:
  for uid,role in ((1,"admin"),(2,"driver")):
   c.execute("INSERT INTO users(id,username,phash,role,status,name,created_at,must_change) VALUES(?,?,?,?,?,?,?,0)",
   (uid,"fake"+str(uid),"unused",role,"active","QA User",app.now()))
  c.commit()
 person={"id":2,"role":"driver","name":"QA","status":"active","must_change":0}
 app.app.dependency_overrides[app.auth]=lambda:person
 client=TestClient(app.app,base_url="https://test.local")
 h={"X-Requested-With":"NOVAGENTE-V5"}
 def put(path,obj):return client.put("/api/"+path,headers=h,json=obj)
 def post(path,obj):return client.post("/api/"+path,headers=h,json=obj)
 c1={"enabled":True,"media_ai":False,"trends":False,"offers":False,"text_ai":False}
 assert put("finance-agent/consent",c1).status_code==200
 assert client.get("/api/finance-agent/consent").json()["options"]["text_ai"]==0
 proposal=post("finance-agent/text",{"text":"Gastei R$ 31 no posto de gasolina"}).json()["proposal"]
 assert proposal["analysis_method"]=="regras locais"
 print("03: External text processing begins OFF, local financial rules still work")
 original=agent.deepseek_text
 calls=[]
 def fake_model(credential,message):
  calls.append((credential,message))
  return {**classify_text("Gastei R$ 31 no posto de gasolina"),"source":"text"}
 agent.deepseek_text=fake_model
 with app.db() as c:
  c.execute("INSERT INTO finance_agent_config(id,config,changed_at) VALUES(1,?,?)",
    (app.enc({"api_key":"UNIT_TEST_ONLY","provider":"deepseek"}),app.now()))
  c.commit()
 assert post("finance-agent/text",{"text":"Gastei R$ 31 no posto de gasolina"}).status_code==200
 assert not calls
 c1["text_ai"]=True
 assert put("finance-agent/consent",c1).status_code==200
 proposal=post("finance-agent/text",{"text":"Gastei R$ 31 no posto de gasolina"}).json()["proposal"]
 assert len(calls)==0 and proposal["analysis_method"]=="regras locais"
 # DeepSeek is only useful for an ambiguous/complex financial message.
 complex_result=post("finance-agent/text",{"text":"Gastei vinte e nove reais no mercado"})
 assert complex_result.status_code==200,complex_result.text
 proposal=complex_result.json()["proposal"]
 assert len(calls)==1 and proposal["analysis_method"]=="DeepSeek V4.1 Flash"
 assert complex_result.json()["quota_used"] is True
 agent.deepseek_text=original
 print("04: Simple messages require no token; ambiguous finance messages use DeepSeek with opt-in and quota")
 c1["media_ai"]=True
 assert put("finance-agent/consent",c1).status_code==200
 original_speech=agent.speech_to_text
 original_interpreter=agent.interpret_transcribed_audio
 calls_audio=[]
 agent.speech_to_text=lambda blob,mime: (calls_audio.append("whisper"),"Gastei 45 reais no posto de gasolina")[1]
 agent.interpret_transcribed_audio=lambda key,text: (calls_audio.append("deepseek"),{**classify_text(text),"source":"audio"})[1]
 sent=client.post("/api/finance-agent/media",headers=h,
   files={"file":("audio.ogg",b"OggS"+b"0"*64,"audio/ogg")})
 agent.speech_to_text=original_speech
 agent.interpret_transcribed_audio=original_interpreter
 assert sent.status_code==200,sent.text
 assert sent.json()["proposal"]["source"]=="audio"
 assert calls_audio==["whisper","deepseek"]
 print("05: Local Whisper transcribes audio before DeepSeek financial interpretation; no speech API key")
 person["id"]=1;person["role"]="admin"
 status=client.get("/api/admin/finance-agent/provider").json()
 assert status["provider"]=="DeepSeek" and status["vision_model"]=="deepseek-flash"
 assert status["key_set"] and status["audio_transcription_ready"]==agent.whisper_ready() and status["transcription_model"]=="whisper-base-local"
 assert "UNIT_TEST_ONLY" not in str(status)
 print("06: Admin UI gets correct provider and no credential disclosure")
 app.app.dependency_overrides.clear()
print("6/6 DeepSeek provider tests passed, temporary database deleted.")
