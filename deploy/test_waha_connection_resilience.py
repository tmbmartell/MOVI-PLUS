"""WAHA connection resiliency without sending messages or reading secrets."""
import os,sys,tempfile
from unittest.mock import patch
from fastapi import HTTPException
import httpx
with tempfile.TemporaryDirectory(prefix="ng-waha-connection-qa-") as work:
 os.environ["CLUBE_DATA"]=work
 sys.path.insert(0,os.path.dirname(os.path.dirname(__file__)))
 import app
 from whatsapp_bridge_v5 import waha
 cfg={"base_url":"http://127.0.0.1:18182","api_key":"FAKE_TEST_KEY","session":"clube-motorista"}
 actions=[]
 class MockClient:
  def __init__(self,**kwargs):self.settings=kwargs
  def __enter__(self):return self
  def __exit__(self,*args):return False
  def request(self,method,url,**kwargs):
   actions.append(method)
   if len(actions)==1:raise httpx.ConnectError("transient",request=httpx.Request(method,url))
   return httpx.Response(200,request=httpx.Request(method,url),json={"status":"WORKING"})
 with patch("whatsapp_bridge_v5.httpx.Client",MockClient):
  with patch("whatsapp_bridge_v5.time.sleep",lambda s:None):
   reply,status=waha(cfg,"GET","/api/sessions/clube-motorista")
 assert actions==["GET","GET"] and status==200 and reply.json()["status"]=="WORKING"
 print("01: GET retries once and recovers from brief WAHA disconnect: PASS")
 actions.clear()
 with patch("whatsapp_bridge_v5.httpx.Client",MockClient):
  try:waha(cfg,"POST","/api/sessions",{"name":"clube-motorista"})
  except HTTPException as e:
   assert e.status_code==503
  else:raise AssertionError("Expected HTTP 503")
 assert actions==["POST"],actions
 print("02: POST actions never retried, preventing duplicate session or message operations: PASS")
 class AlwaysOffline(MockClient):
  def request(self,method,url,**kwargs):
   actions.append(method)
   raise httpx.ConnectError("transient",request=httpx.Request(method,url))
 actions.clear()
 with patch("whatsapp_bridge_v5.httpx.Client",AlwaysOffline):
  with patch("whatsapp_bridge_v5.time.sleep",lambda s:None):
   try:waha(cfg,"GET","/api/sessions/clube-motorista")
   except HTTPException as e:
    assert e.status_code==503 and "Aguarde alguns segundos" in e.detail
   else:raise AssertionError("Expected HTTP 503")
 assert actions==["GET","GET"]
 print("03: Persistent failure uses actionable error message after bounded GET retries: PASS")
print("3/3 WAHA connect resilience tests PASS.")
