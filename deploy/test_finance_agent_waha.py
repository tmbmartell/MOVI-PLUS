"""Isolated, signed WAHA event and driver pairing QA; sends zero real messages."""
import os,sys,tempfile,time,json,hmac,hashlib
from fastapi.testclient import TestClient
with tempfile.TemporaryDirectory(prefix="novagente_waha_fin_") as tmp:
 os.environ["CLUBE_DATA"]=tmp
 sys.path.insert(0,os.path.dirname(os.path.dirname(__file__)))
 import app,finance_agent_waha_v1 as wa,finance_agent_pilot_v1 as pilot
 from whatsapp_bridge_v5 import ensure_table
 outbound=[]
 pilot.waha=lambda cfg,method,path,body=None: (
  outbound.append({"method":method,"path":path,"chatId":(body or {}).get("chatId"),"text":(body or {}).get("text")}),
  200)
 with app.db() as c:
  for uid,role in ((1,"admin"),(2,"driver"),(3,"driver")):
   c.execute("INSERT INTO users(id,username,phash,role,status,name,created_at,must_change) VALUES(?,?,?,?,?,?,?,0)",
    (uid,"qa"+str(uid),"notused",role,"active","Fake user",app.now()))
  ensure_table(c)
  c.execute("INSERT INTO whatsapp_bridge_config(id,encrypted,updated_at,actor) VALUES(1,?,?,?)",
    (app.enc({"base_url":"http://127.0.0.1:18182","session":"clube-motorista","api_key":"test-only-key"}),app.now(),1))
  c.execute("INSERT INTO finance_agent_wa_pilot(id,uid,enabled,updated_at) VALUES(1,2,1,?)",(app.now(),))
  c.commit()
 who={"id":1,"role":"admin","name":"Test","status":"active","must_change":0}
 app.app.dependency_overrides[app.auth]=lambda:who
 client=TestClient(app.app,base_url="https://qa.local")
 H={"X-Requested-With":"NOVAGENTE-V5"}
 def post(path,d={}):return client.post(path,json=d,headers=H)
 def good(r):assert r.status_code==200,(r.status_code,r.text[:150]);return r.json()
 status=good(client.get("/api/admin/finance-agent/whatsapp"))
 assert not status["enabled"]
 assert post("/api/finance-agent/whatsapp/events",{"event":"message"}).status_code==401
 print("01 - webhook starts OFF; unsigned events rejected: PASS")
 prepared=good(post("/api/admin/finance-agent/whatsapp/prepare"))
 key=prepared["hmac_key"]
 assert len(key)>50 and prepared["not_enabled"]
 assert "hmac_key" not in str(good(client.get("/api/admin/finance-agent/whatsapp")))
 print("02 - HMAC secret generated encrypted and not returned by status: PASS")
 good(client.put("/api/admin/finance-agent/whatsapp/enabled",json={"enabled":True},headers=H))
 def signed(payload,secret=key,stamp=None):
  body=json.dumps(payload,separators=(",",":")).encode()
  sig=hmac.new(secret.encode(),body,hashlib.sha512).hexdigest()
  headers={**H,"X-Webhook-Hmac":sig,"X-Webhook-Hmac-Algorithm":"sha512",
      "X-Webhook-Timestamp":str(stamp or int(time.time()*1000))}
  return client.post("/api/finance-agent/whatsapp/events",content=body,headers=headers)
 fake_chat="5511998877665@c.us"
 msg=lambda val,mid="false_testid_12345678",chat=fake_chat:{"session":"clube-motorista","event":"message",
  "payload":{"id":mid,"from":chat,"fromMe":False,"body":val,"hasMedia":False}}
 assert signed(msg("Gastei R$ 50 no posto"),"incorrect").status_code==401
 assert signed(msg("Gastei R$ 50 no posto"),stamp=int(time.time()*1000)-720000).status_code==401
 assert signed(msg("Gastei R$ 50 no posto")).json()["ignored"]
 print("03 - HMAC, timestamp and link checks enforced: PASS")
 who.update({"id":2,"role":"driver"})
 cons={"enabled":True,"media_ai":False,"trends":False,"offers":False}
 good(client.put("/api/finance-agent/consent",json=cons,headers=H))
 token=good(post("/api/finance-agent/whatsapp/link-code"))["code"]
 linked=signed(msg("VINCULAR "+token,"false_link_123456789"))
 assert linked.status_code==200 and linked.json()["linked"]
 assert linked.json()["reply_sent"] is True
 assert good(client.get("/api/finance-agent/whatsapp/link-status"))["linked"]
 from finance_agent_pilot_v1 import MAX_REPLY_LENGTH
 assert outbound[-1]["text"]==wa.ONBOARDING_MESSAGE
 assert len(wa.ONBOARDING_MESSAGE)<=MAX_REPLY_LENGTH
 assert "Boas-vindas" in wa.ONBOARDING_MESSAGE
 assert "responde naturalmente" in wa.ONBOARDING_MESSAGE
 assert "*ok*" in wa.ONBOARDING_MESSAGE
 from finance_agent_conversation_v2 import command,is_uncertain,propose_text
 for reply in ("ok","blza","sim","isso","confirma","falow","top","tá bom!",
               "legal","s","👍","beleza","fechou","perfeito","pode",
               "isso mesmo","pode registrar","certinho"):
  assert command(reply)==("CONFIRMAR",None),reply
 for reply in ("talvez","marca","não sei","acho que sim","não","errado"):
  assert command(reply) is None and is_uncertain(reply),reply
 for reply in ("ok, gastei 100 reais","sim recebi 30","top! o jogo foi bom",
               "ok 90 de gasolina","mais ou menos gostei"):
  assert command(reply) is None,reply
 assert command("CONFIRMAR 7")==("CONFIRMAR",7)
 assert command("descartar 8")==("DESCARTAR",8)
 assert "Está tudo certinho?" in propose_text(
  {"kind":"expense","status":"ready","amount":30,"category":"Combustível"},7,"qa")
 assert "Gastei R$ 120" in wa.ONBOARDING_MESSAGE
 assert "piloto exclusivo" not in wa.ONBOARDING_MESSAGE.lower()
 print("04 - linking requires driver login + one-time code and sends friendly onboarding: PASS")
 previous_count=len(outbound)
 help_message=signed(msg("AJUDA","false_help_123456789"))
 assert help_message.status_code==200 and help_message.json()["reason"]=="onboarding_help"
 assert help_message.json()["reply_sent"] is True and help_message.json()["model_called"] is False
 assert len(outbound)==previous_count+1 and outbound[-1]["text"]==wa.ONBOARDING_MESSAGE
 again=signed(msg("AJUDA","false_help_123456789"))
 assert again.status_code==200 and again.json()["duplicate"]
 assert len(outbound)==previous_count+1
 with app.db() as c:assert c.execute("SELECT COUNT(*) FROM finance_agent_proposals").fetchone()[0]==0
 print("04a - existing linked driver requests AJUDA and gets onboarding once, with no LLM cost or financial record: PASS")
 # Off-topic replies are prepared for a future approved sender but never transmitted.
 unrelated=signed(msg("Me conta uma piada sobre gasolina","false_outscope_123456"))
 assert unrelated.status_code==200
 assert unrelated.json()["reason"]=="out_of_scope"
 assert "copiloto financeiro" in unrelated.json()["reply_text"]
 assert unrelated.json()["reply_sent"] is True and unrelated.json()["model_called"] is False
 assert outbound and outbound[-1]["chatId"]==fake_chat
 with app.db() as c:assert c.execute("SELECT COUNT(*) FROM finance_agent_proposals").fetchone()[0]==0
 print("04b - out-of-scope WhatsApp event uses canned response and mocked single-contact outbound: PASS")
 assert signed(msg("VINCULAR "+token,"false_link_again_123456")).json()["link"]=="invalid"
 reply=signed(msg("Gastei R$ 10 no supermercado","false_expense_123456"))
 assert reply.status_code==200 and reply.json()["reply_sent"] is True
 assert signed(msg("Gastei R$ 10 no supermercado","false_expense_123456")).json()["duplicate"]
 found=good(client.get("/api/finance-agent/proposals"))["items"]
 assert len(found)==1 and found[0]["status"]=="pending" and found[0]["proposal"]["category"]=="Supermercado"
 print("05 - signed WhatsApp text becomes pending entry, retries deduplicated; mocked sender used: PASS")
 with app.db() as c:assert c.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]==0
 proposed=reply.json()["proposal_id"]
 assert outbound[-1]["chatId"]==fake_chat
 assert "Está tudo certinho?" in outbound[-1]["text"]
 assert "R$ 10,00" in outbound[-1]["text"]
 assert "responder do seu jeito" in outbound[-1]["text"]
 confirmed=signed(msg(f"CONFIRMAR {proposed}","false_confirm_12345678"))
 assert confirmed.status_code==200,confirmed.text
 assert confirmed.json()["reply_sent"] is True
 assert signed(msg(f"CONFIRMAR {proposed}","false_confirm_12345678")).json()["duplicate"]
 with app.db() as c:
  assert c.execute("SELECT COUNT(*) FROM transactions WHERE uid=2").fetchone()[0]==1
  assert c.execute("SELECT COUNT(*) FROM transactions WHERE uid=3").fetchone()[0]==0
 print("06 - WhatsApp command confirms exactly once only for linked pilot user; no cross-user posting: PASS")
 fuel=signed(msg("90,00 de gasolina","false_fuel_example_123456"))
 assert fuel.status_code==200 and fuel.json().get("proposal_id") and fuel.json().get("reply_sent"),fuel.text
 assert "Combustível" in outbound[-1]["text"]
 short=signed(msg("confimar","false_confimar_1234567"))
 assert short.status_code==200 and short.json().get("result")=="confirm",short.text
 with app.db() as c:
  assert c.execute("SELECT COUNT(*) FROM transactions WHERE uid=2").fetchone()[0]==2
 print("06a - shorthand 90,00 gasoline and misspelled 'confimar' confirm the last delivered entry: PASS")
 again=signed(msg("confirmar","false_confirma_again_12345"))
 assert again.status_code==200 and again.json().get("result")=="no_recent_offer"
 with app.db() as c:assert c.execute("SELECT COUNT(*) FROM transactions WHERE uid=2").fetchone()[0]==2
 print("06b - bare confirmation cannot double-post a resolved entry: PASS")
 with app.db() as c:
  assert not wa.options(c,2)["trends"]
 before=len(outbound)
 report=signed(msg("me manda onde gastei","false_actual_report_123456"))
 assert report.status_code==200 and report.json().get("reason")=="financial_report",report.text
 assert report.json().get("reply_sent") is True and report.json().get("chart_sent") is True
 assert report.json()["consent_scope"]=="request_only_no_preference_changes"
 assert len(outbound)==before+2
 assert outbound[-2]["path"]=="/api/sendText" and outbound[-1]["path"]=="/api/sendImage"
 assert "Combustível" in outbound[-2]["text"] and "Supermercado" in outbound[-2]["text"]
 assert "não é" in outbound[-2]["text"].lower() or "não são" in outbound[-2]["text"].lower()
 assert signed(msg("me manda onde gastei","false_actual_report_123456")).json()["duplicate"]
 with app.db() as c:
  from finance_agent_limits_v1 import usage
  u=usage(c,2)
  assert u["used"]["text_ai"]==0 and u["used"]["chart"]==1
  assert c.execute("SELECT COUNT(*) FROM transactions WHERE uid=2").fetchone()[0]==2
  assert not wa.options(c,2)["trends"]
  assert not wa.options(c,2)["offers"]
  rows=c.execute("SELECT action,target FROM audit WHERE action='finance_agent:whatsapp_report_requested'").fetchall()
  assert any("driver_direct_request:confirmed_only:one_time"==r["target"] for r in rows)
 print("06c - Direct WhatsApp report + JPEG works with trends OFF, without changing preferences or using AI: PASS")
 # The website's independent permission remains off; no access to proactive trends is granted.
 web_insights=client.get("/api/finance-agent/insights")
 assert web_insights.status_code==403
 print("06d - One-time WhatsApp report does not silently enable future trend analysis or offers: PASS")
 # Keep the mock below the anti-flood threshold while simulating a new day.
 with app.db() as c:
  c.execute("UPDATE finance_agent_wa_pilot_outbox SET created_at='2025-01-01T00:00:00+00:00' WHERE uid=?",(2,))
  c.commit()
 easy=signed(msg("Gastei R$ 18 no mercado","natural_offer_ok_00123"))
 assert easy.status_code==200 and easy.json().get("reply_sent")
 natural=signed(msg("ok!","natural_confirm_ok_001234"))
 assert natural.status_code==200 and natural.json().get("result")=="confirm",natural.text
 with app.db() as c:
  assert c.execute("SELECT COUNT(*) FROM transactions WHERE uid=2").fetchone()[0]==3
 print("06e - Short natural 'ok!' confirms last delivered suggestion and posts only once: PASS")

 # Uncertainty never records a proposal; same chat may clarify with another casual yes.
 fuel2=signed(msg("Gastei R$ 22 de gasolina","natural_offer_uncertain_0123"))
 assert fuel2.json().get("reply_sent")
 unclear=signed(msg("marca","natural_mark_review_01234"))
 assert unclear.json().get("reason")=="uncertain_confirmation",unclear.text
 with app.db() as c:
  assert c.execute("SELECT COUNT(*) FROM transactions WHERE uid=2").fetchone()[0]==3
  assert c.execute("SELECT COUNT(*) FROM audit WHERE action='finance_agent:uncertain_confirmation'").fetchone()[0]==1
 approved=signed(msg("blza","natural_confirm_blza_0123"))
 assert approved.json().get("result")=="confirm",approved.text
 print("06f - 'marca' flags doubt and asks clarification; 'blza' then confirms same recent offer: PASS")

 # An explicit negative means do not register. A later 's' must not approve the rejected offer.
 pending=signed(msg("Gastei R$ 29 de gasolina","natural_offer_no_0123456"))
 assert pending.json().get("reply_sent")
 stopped=signed(msg("não","natural_denial_01234567"))
 assert stopped.json().get("reason")=="uncertain_confirmation"
 later=signed(msg("s","natural_after_no_0123456"))
 assert later.json().get("result")=="no_recent_offer",later.text
 with app.db() as c:assert c.execute("SELECT COUNT(*) FROM transactions WHERE uid=2").fetchone()[0]==4
 print("06g - 'não' leaves entry unposted and prevents subsequent casual 's' from posting it: PASS")

 # A report moves the topic away from previous proposal; bare 'top' cannot approve it.
 with app.db() as c:
  c.execute("UPDATE finance_agent_wa_pilot_outbox SET created_at='2025-01-01T00:00:00+00:00' WHERE uid=?",(2,))
  c.commit()
 pending2=signed(msg("Gastei R$ 11 no mercado","natural_offer_topic_0123"))
 assert pending2.json().get("reply_sent")
 report2=signed(msg("me manda meu relatório","natural_topic_report_01234"))
 assert report2.json().get("reason")=="financial_report"
 stray=signed(msg("top","natural_after_report_01234"))
 assert stray.json().get("result")=="no_recent_offer"
 with app.db() as c:assert c.execute("SELECT COUNT(*) FROM transactions WHERE uid=2").fetchone()[0]==4
 print("06h - Casual positive after switching to report cannot confirm stale financial offer: PASS")

 # Even without a topic switch, a 15-minute-old short reply is not a valid approval.
 stale=signed(msg("Gastei R$ 12 no mercado","natural_offer_expiry_0123"))
 assert stale.json().get("reply_sent")
 with app.db() as c:
  c.execute("UPDATE finance_agent_wa_last_offer SET offered_at='2025-01-01T00:00:00+00:00' WHERE uid=?",(2,))
  c.commit()
 delayed=signed(msg("legal","natural_expired_yes_01234"))
 assert delayed.json().get("result")=="no_recent_offer"
 with app.db() as c:assert c.execute("SELECT COUNT(*) FROM transactions WHERE uid=2").fetchone()[0]==4
 print("06i - Delayed ambiguous affirmations expire after 15 minutes, explicit ID remains available: PASS")
 with app.db() as c:
  c.execute("UPDATE finance_agent_wa_pilot_outbox SET created_at='2025-01-01T00:00:00+00:00' WHERE uid=?",(2,))
  c.commit()
 for label,expected,origin,affirmation,event in [
   ("Recebi R$ 180 da Uber","APLICATIVO","Uber","ok","income_uber"),
   ("Recebi R$ 75 da 99","APLICATIVO","99","blza","income_99"),
   ("Peguei um cliente de 40 reais","APLICATIVO",None,"top","income_passenger"),
   ("Recebi R$ 20 a mais","OUTROS","Extra","sim","income_extra")]:
  sent_event=signed(msg(label,event+"_offer_123456"))
  assert sent_event.status_code==200 and sent_event.json().get("reply_sent"),(event,sent_event.text)
  assert "Etiqueta: *"+expected+"*" in outbound[-1]["text"]
  if origin:assert "Origem: *"+origin+"*" in outbound[-1]["text"]
  checked=signed(msg(affirmation,event+"_accepted_1234"))
  assert checked.status_code==200 and checked.json().get("result")=="confirm",(event,checked.text)
  with app.db() as c:
   current=c.execute("SELECT category,note FROM transactions WHERE uid=2 ORDER BY id DESC LIMIT 1").fetchone()
   assert current and current["category"]==expected,(event,dict(current))
   if origin:assert "Origem: "+origin in current["note"],(event,dict(current))
 print("06j - Uber, 99, passenger ride -> APLICATIVO; extra -> OUTROS; origin retained after natural WhatsApp confirmation: PASS")
 with app.db() as c:
  c.execute("UPDATE finance_agent_wa_pilot_outbox SET created_at='2025-01-01T00:00:00+00:00' WHERE uid=?",(2,))
  c.commit()
 income_report=signed(msg("me manda meu relatório","income_summary_report_0123"))
 assert income_report.status_code==200 and income_report.json().get("reason")=="financial_report",income_report.text
 assert income_report.json().get("reply_sent") is True
 report_text_only=outbound[-2]["text"] if income_report.json().get("chart_sent") else outbound[-1]["text"]
 assert "Aplicativo:" in report_text_only and "Outros:" in report_text_only
 assert "Uber R$" in report_text_only and "99 R$" in report_text_only
 with app.db() as c:
  from finance_agent_conversation_v2 import month_data
  totals=month_data(c,2)
  assert totals["income_labels"]["APLICATIVO"]==29500
  assert totals["income_labels"]["OUTROS"]==2000
  assert totals["app_sources"]["Uber"]==18000 and totals["app_sources"]["99"]==7500
 print("06k - Confirmed income report separates app/other and named Uber/99 without changing older categories: PASS")
 # Media is authorized/revoked inside the already-linked WhatsApp, never implicitly
 # via a mere file upload, and never by turning on offers or ongoing trends.
 with app.db() as c:
  c.execute("UPDATE finance_agent_wa_pilot_outbox SET created_at='2025-01-01T00:00:00+00:00' WHERE uid=?",(2,))
  c.commit()
 media_event={"session":"clube-motorista","event":"message","payload":{
  "id":"false_media_0123456789","from":fake_chat,"fromMe":False,"body":"",
  "hasMedia":True,"media":{"url":"http://localhost:3000/api/files/abc.png","mimetype":"image/png"}}}
 media_wait=signed(media_event)
 assert media_wait.status_code==200 and media_wait.json()["reason"]=="media_consent_required"
 assert media_wait.json()["reply_sent"] and "AUTORIZAR MIDIA" in outbound[-1]["text"]
 with app.db() as c:
  assert not wa.options(c,2)["media_ai"] and not wa.options(c,2)["offers"]
 print("07a - unsolicited picture gets on-chat purpose-specific consent prompt, no external AI: PASS")
 granted=signed(msg("AUTORIZAR MÍDIA","false_media_grant_123456"))
 assert granted.status_code==200 and granted.json()["reason"]=="media_permission_updated"
 assert granted.json()["media_ai"] is True and granted.json()["reply_sent"]
 assert signed(msg("AUTORIZAR MÍDIA","false_media_grant_123456")).json()["duplicate"]
 with app.db() as c:
  assert wa.options(c,2)["media_ai"]
  assert not wa.options(c,2)["offers"] and not wa.options(c,2)["trends"] and not wa.options(c,2)["text_ai"]
 print("07b - explicit WhatsApp media opt-in updates only media_ai, without activating other permissions: PASS")
 revoked=signed(msg("REVOGAR MIDIA","false_media_revoke_123456"))
 assert revoked.status_code==200 and revoked.json()["media_ai"] is False
 with app.db() as c:
  assert not wa.options(c,2)["media_ai"]
  assert not wa.options(c,2)["offers"] and not wa.options(c,2)["trends"]
 print("07c - WhatsApp revokes media permission without website or auto-sharing: PASS")
 who.update({"id":3,"role":"driver"})
 assert not good(client.get("/api/finance-agent/whatsapp/link-status"))["linked"]
 who.update({"id":2,"role":"driver"})
 good(client.put("/api/finance-agent/consent",json={**cons,"enabled":False},headers=H))
 assert signed(msg("Gastei R$ 80 na farmácia","false_receipt_123456")).json()["reason"]=="no_consent"
 print("07 - media and revocation consents independent of text: PASS")
 assert signed(msg("Gastei R$ 100 no mercado","false_group_12345","120363429156569266@g.us")).json()["ignored"]
 assert signed({"session":"clube-motorista","event":"message","payload":{
  "id":"true_fromme_123456","from":fake_chat,"fromMe":True,"body":"Gastei R$ 20"}}).json()["ignored"]
 assert signed({"session":"clube-motorista","event":"message","payload":{
  "id":"true_outgoing_link_12345","from":fake_chat,"fromMe":True,"body":"VINCULAR ABCDEFGHIJKL"}}).json()["ignored"]
 print("08 - group and outbound self-messages ignored, including link attempts: PASS")
 # WAHA WEBJS can identify valid incoming private chats with a LID rather than c.us.
 # The code is the proof of control; never infer a telephone number from the LID digits.
 good(client.put("/api/finance-agent/consent",json={**cons,"enabled":True},headers=H))
 lid_code=good(post("/api/finance-agent/whatsapp/link-code"))["code"]
 lid_chat="245896994390182@lid"
 lid_result=signed(msg("VINCULAR "+lid_code,"false_lid_link_12345678",lid_chat))
 assert lid_result.status_code==200 and lid_result.json()["linked"]
 assert outbound[-1]["chatId"]==lid_chat
 print("08b - incoming private @lid address accepts proof-based linking and mocks reply to same chat: PASS")
 assert good(client.delete("/api/finance-agent/whatsapp/link",headers=H))["ok"]
 assert not good(client.get("/api/finance-agent/whatsapp/link-status"))["linked"]
 who.update({"id":1,"role":"admin"})
 good(client.put("/api/admin/finance-agent/whatsapp/enabled",json={"enabled":False},headers=H))
 with app.db() as c:
  assert c.execute('PRAGMA integrity_check').fetchone()[0]=="ok"
 print("09 - driver unlink, admin disable and DB integrity: PASS")
 app.app.dependency_overrides.clear()
print("9/9 signed WAHA adapter tests passed; no remote WhatsApp used.")
