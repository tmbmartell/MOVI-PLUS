"""Isolated financial topic router and per-driver budgets; no live provider or WAHA."""
import os,sys,tempfile
from fastapi import HTTPException
from fastapi.testclient import TestClient
with tempfile.TemporaryDirectory(prefix="novagente_scope_qa_") as d:
 os.environ["CLUBE_DATA"]=d
 sys.path.insert(0,os.path.dirname(os.path.dirname(__file__)))
 import app,finance_agent_v1 as agent,finance_agent_limits_v1 as guard
 from finance_agent_core import classify_text
 assert guard.LIMITS=={"text_ai":20,"audio":5,"image":5,"chart":3}
 assert guard.route("Me conta uma piada")=="out_of_scope"
 assert guard.route("Qual o placar do futebol?")=="out_of_scope"
 assert guard.route("Oi")=="greeting"
 assert guard.route("Onde foram meus gastos?")=="query"
 assert guard.route("Quanto gastei hoje?")=="query"
 assert guard.route("Me conta uma piada sobre gasolina")=="out_of_scope"
 for t in ("Abasteci R$ 100 de gasolina","Gastei R$ 80 no supermercado",
           "Recebi 250 reais pelas corridas","Gastei vinte reais em combustível",
           "Paguei 15 de mercado"):
  assert guard.route(t)=="record",(t,guard.route(t))
 print("01: Topic router handles expenses/income/questions/greetings and rejects unrelated subjects: PASS")
 with app.db() as c:
  for uid in [1,2]:
   c.execute("INSERT INTO users(id,username,phash,role,status,name,created_at,must_change) VALUES(?,?,?,?,?,?,?,0)",
    (uid,"qa"+str(uid),"fake","driver","active","QA",app.now()))
  c.execute("INSERT INTO finance_agent_config(id,config,changed_at) VALUES(1,?,?)",
   (app.enc({"api_key":"MOCK_ONLY_KEY"}),app.now()))
  c.commit()
 person={"id":1,"role":"driver","name":"QA","status":"active","must_change":0}
 app.app.dependency_overrides[app.auth]=lambda:person
 cli=TestClient(app.app,base_url="https://qa.example")
 h={"X-Requested-With":"NOVAGENTE-V5"}
 consent={"enabled":True,"text_ai":True,"media_ai":True,"trends":True,"offers":False}
 assert cli.put("/api/finance-agent/consent",json=consent,headers=h).status_code==200
 calls=[]
 model=agent.deepseek_text
 agent.deepseek_text=lambda key,text:(calls.append(text),{**classify_text("Gastei R$ 31 com gasolina"),"source":"text"})[1]
 for t in ("Me conta uma piada", "Qual placar do jogo?", "Oi!"):
  res=cli.post("/api/finance-agent/text",json={"text":t},headers=h)
  assert res.status_code==200,(t,res.status_code,res.text)
  value=res.json()
  assert "reply" in value and "id" not in value and not value["quota_used"]
 assert not calls
 assert cli.get("/api/finance-agent/proposals").json()["items"]==[]
 print("02: Off-topic and greeting replies are canned; zero model calls and no proposals: PASS")
 res=cli.post("/api/finance-agent/text",json={"text":"Gastei R$ 89 com combustível"},headers=h)
 assert res.status_code==200 and res.json()["quota_used"] is False
 assert not calls
 print("03: Easy financial entries use zero DeepSeek tokens but await confirmation: PASS")
 for i in range(20):
  res=cli.post("/api/finance-agent/text",json={"text":f"Gastei vinte e sete reais no supermercado teste {i}"},headers=h)
  assert res.status_code==200,(i,res.status_code,res.text[:250])
  assert res.json()["quota_used"] is True
 assert len(calls)==20
 extra=cli.post("/api/finance-agent/text",json={"text":"Gastei vinte e oito reais na farmácia"},headers=h)
 assert extra.status_code==429 and len(calls)==20
 status=cli.get("/api/finance-agent/limits").json()
 assert status["used"]["text_ai"]==20 and status["remaining"]["text_ai"]==0
 assert status["timezone"]=="America/Porto_Velho"
 assert status["limits"]["chart"]==3
 print("04: Exactly 20 AI text calls/day, 21st refused BEFORE API; Porto Velho timezone: PASS")
 for t in ("Qual a minha situação financeira?","Me conta uma piada","Gastei R$ 25 de gasolina"):
  res=cli.post("/api/finance-agent/text",json={"text":t},headers=h)
  assert res.status_code==200,res.text
 assert len(calls)==20
 print("05: Out-of-scope, queries and simple bookkeeping still work after AI quota exhausted: PASS")
 # Multimedia fake extraction; note these are test bytes, not actual image/audio contents.
 img_model,audio_stt,audio_model=agent.image_analyze,agent.speech_to_text,agent.interpret_transcribed_audio
 from finance_agent_core import validate_proposal
 def fake_media(*args,**kwargs):
  return validate_proposal({"kind":"expense","amount":50,"category":"Supermercado","summary":"QA test"})
 agent.image_analyze=fake_media
 agent.speech_to_text=lambda b,m:"Gastei 40 reais no mercado"
 agent.interpret_transcribed_audio=lambda key,t:fake_media()
 for index in range(5):
  res=cli.post("/api/finance-agent/media",files={"file":("fake.png",bytes.fromhex("89504e470d0a1a0a")+b"0"*25,"image/png")},headers=h)
  assert res.status_code==200,(index,res.status_code,res.text)
 res=cli.post("/api/finance-agent/media",files={"file":("fake.png",bytes.fromhex("89504e470d0a1a0a")+b"0"*25,"image/png")},headers=h)
 assert res.status_code==429
 print("06: 5 images/day enforced independently and before model call: PASS")
 for index in range(5):
  res=cli.post("/api/finance-agent/media",files={"file":("fake.ogg",b"OggS"+b"0"*25,"audio/ogg")},headers=h)
  assert res.status_code==200,(index,res.status_code,res.text)
 res=cli.post("/api/finance-agent/media",files={"file":("fake.ogg",b"OggS"+b"0"*25,"audio/ogg")},headers=h)
 assert res.status_code==429
 print("07: 5 audio clips/day independent from text and images: PASS")
 with app.db() as c:
  assert c.execute("SELECT COUNT(*) FROM transactions WHERE uid=1").fetchone()[0]==0
 assert len(calls)==20
 print("08: All suggestions still unconfirmed; no automatic bookkeeping: PASS")
 # Per-user separation and refunds on external call failure.
 person["id"]=2
 assert cli.put("/api/finance-agent/consent",json=consent,headers=h).status_code==200
 assert cli.get("/api/finance-agent/limits").json()["used"]["text_ai"]==0
 agent.deepseek_text=lambda key,text: (_ for _ in ()).throw(HTTPException(503,"Simulated failure"))
 r=cli.post("/api/finance-agent/text",json={"text":"Gastei vinte reais na farmácia"},headers=h)
 assert r.status_code==503
 assert cli.get("/api/finance-agent/limits").json()["used"]["text_ai"]==0
 print("09: Provider failures refund reservation, other driver starts with own empty quota: PASS")
 tickets=[guard.reserve(2,"chart") for x in range(3)]
 for t in tickets:guard.complete(t)
 try:guard.reserve(2,"chart")
 except HTTPException as exc:assert exc.status_code==429
 else:raise AssertionError("Expected future PNG charts quota to cap at three")
 print("10: Future PNG chart generator has a 3-per-day reservation control, not yet a chart sender: PASS")
 agent.deepseek_text,agent.image_analyze,agent.speech_to_text,agent.interpret_transcribed_audio=model,img_model,audio_stt,audio_model
 with app.db() as c:assert c.execute("PRAGMA integrity_check").fetchone()[0]=="ok"
 app.app.dependency_overrides.clear()
print("10/10 isolated daily-limit + outside-scope tests PASSED; no real data or provider calls.")
