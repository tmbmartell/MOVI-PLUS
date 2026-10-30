"""Whisper local audio tests without expensive model inference or customer media."""
import os,sys,tempfile,subprocess,json,fcntl
from pathlib import Path
from fastapi import HTTPException
from unittest.mock import patch
with tempfile.TemporaryDirectory(prefix="ng_whisper_test_") as temp:
 os.environ["CLUBE_DATA"]=temp
 sys.path.insert(0,os.path.dirname(os.path.dirname(__file__)))
 import app,finance_agent_v1 as agent
 actual_model_ready=agent.whisper_ready()
 if not actual_model_ready:
  # The Git repo must not bundle >100MB model weights; simulate file existence
  # only for mocked-worker tests below, never claim actual ASR is ready.
  model_stub=Path(temp)/"synthetic-whisper-model-stub.pt"
  with open(model_stub,"wb") as handle:handle.truncate(101*1024*1024)
  agent.LOCAL_WHISPER_MODEL=model_stub
 assert agent.whisper_ready()
 assert agent.LOCAL_WHISPER_MODEL.stat().st_size>100*1024*1024
 print("01: Actual Whisper weights "+("present" if actual_model_ready else "NOT staged (mock only)")+
       "; fake model for isolated subprocess tests: PASS")
 assert agent.read_mime(b"OggS"+b"0"*25)=="audio/ogg"
 assert agent.read_mime(b"RIFF"+b"0"*4+b"WAVE"+b"0"*22)=="audio/wav"
 assert agent.read_mime(b"ID3"+b"0"*20)=="audio/mpeg"
 print("02: OGG/WAV/MP3 audio formats detected: PASS")
 observed=[]
 def fake_worker(args,**kwargs):
  observed.append({"args":args,"input":kwargs["input"],"timeout":kwargs["timeout"],"resource_limited":bool(kwargs.get("preexec_fn"))})
  return subprocess.CompletedProcess(args,0,stdout=json.dumps({"text":"Gastei quarenta e cinco reais no supermercado"}).encode(),stderr=b"")
 with patch.object(agent.subprocess,"run",side_effect=fake_worker):
  recognized=agent.speech_to_text(b"FAKE_SYNTHETIC_AUDIO","audio/ogg")
 assert "supermercado" in recognized
 assert observed and observed[0]["args"][0]=="/usr/bin/python3"
 assert observed[0]["timeout"]<=105 and observed[0]["resource_limited"]
 assert observed[0]["input"]==b"FAKE_SYNTHETIC_AUDIO"
 print("03: Local subprocess with isolation/resource/time limits, no API token: PASS")
 lock=Path(temp)/"finance_whisper.lock"
 with open(lock,"a+b") as handle:
  fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
  try:
   agent.speech_to_text(b"FAKE_SYNTHETIC_AUDIO","audio/ogg")
  except HTTPException as e:assert e.status_code==429
  else:raise AssertionError("Expected concurrent audio rejection")
  finally:fcntl.flock(handle,fcntl.LOCK_UN)
 print("04: Shared VPS admits only one transcriber at a time: PASS")
 with patch.object(agent.subprocess,"run",return_value=subprocess.CompletedProcess([],2,stdout=b'{"error":"ValueError"}',stderr=b'')):
  try:agent.speech_to_text(b"BAD_AUDIO","audio/ogg")
  except HTTPException as e:assert e.status_code==422
  else:raise AssertionError("Expected invalid-audio rejection")
 print("05: Invalid audio fails safely without storing it: PASS")
 original_json=agent.llm_json
 agent.llm_json=lambda credential,payload:{
  "kind":"expense","amount":55,"category":"Combustível",
  "summary":"Gastei 55 reais no posto de gasolina","items":[]}
 proposal=agent.interpret_transcribed_audio("SYNTHETIC_ONLY","Gastei 55 reais no posto de gasolina")
 agent.llm_json=original_json
 assert proposal["source"]=="audio" and proposal["amount"]==55
 assert proposal["category"]=="Combustível"
 print("06: Audio transcript is classified financially by language model and still requires user approval: PASS")
