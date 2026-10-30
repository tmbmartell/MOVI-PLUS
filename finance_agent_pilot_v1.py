"""One-contact WAHA pilot gate. Never sends unless registered opt-in pilot UID
has proved ownership of chat by a single-use link code sent from that chat.
No unlinked or other-user outgoing messages, and no message fan-out.
"""
import datetime,re
from fastapi import APIRouter,Depends,HTTPException
from app import db,admin,auth,now,audit,sha
from finance_agent_core import plain as normalize
from whatsapp_bridge_v5 import waha,config_get

router=APIRouter()
MAX_REPLY_LENGTH=850

def init(c):
 c.execute("""CREATE TABLE IF NOT EXISTS finance_agent_wa_pilot(
 id INTEGER PRIMARY KEY CHECK(id=1),uid INTEGER REFERENCES users(id),
 enabled INTEGER NOT NULL DEFAULT 0,
 updated_at TEXT NOT NULL)""")
 c.execute("""CREATE TABLE IF NOT EXISTS finance_agent_wa_pilot_outbox(
 event_hash TEXT PRIMARY KEY,uid INTEGER NOT NULL,
 status TEXT NOT NULL CHECK(status IN ('reserved','sent','failed')),
 created_at TEXT NOT NULL,completed_at TEXT)""")
 c.execute("""CREATE TABLE IF NOT EXISTS finance_agent_wa_last_offer(
 uid INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
 chat_hash TEXT NOT NULL,pid INTEGER NOT NULL,offered_at TEXT NOT NULL)""")
 c.commit()
with db() as _c:init(_c)

def state(c):
 r=c.execute("SELECT uid,enabled FROM finance_agent_wa_pilot WHERE id=1").fetchone()
 return (int(r["uid"]) if r and r["uid"] is not None else None,bool(r and r["enabled"]))

def permitted(c,uid):
 target,enabled=state(c)
 return bool(enabled and target==uid)

def linked(c,uid,chat):
 from finance_agent_waha_v1 import link_hash
 match=c.execute("SELECT 1 FROM finance_agent_wa_links WHERE uid=? AND phone_hash=?",
   (uid,link_hash(chat))).fetchone()
 return bool(match)

def send_once(uid,chat,event_id,text):
 """At-most-once attempt, intentionally no automatic retries; failed responses audited."""
 from finance_agent_waha_v1 import CHAT
 if not isinstance(text,str) or not 1<=len(text)<=MAX_REPLY_LENGTH:return False
 if not isinstance(chat,str) or not CHAT.fullmatch(chat):return False
 if not isinstance(event_id,str) or not 8<=len(event_id)<=300:return False
 receipt=sha("ng-pilot-outbound:"+event_id)
 with db() as c:
  if not permitted(c,uid) or not linked(c,uid,chat):return False
  cfg,_=config_get(c)
  if not cfg or cfg.get("session")!="clube-motorista":return False
  exist=c.execute("SELECT 1 FROM finance_agent_wa_pilot_outbox WHERE event_hash=?",(receipt,)).fetchone()
  if exist:return False
  # Avoid unlimited replies during an unusual message storm; 60/day and 12/10 minutes.
  day=datetime.date.today().isoformat()
  daily=c.execute("SELECT COUNT(*) FROM finance_agent_wa_pilot_outbox WHERE uid=? AND created_at>=?",
    (uid,day)).fetchone()[0]
  last_ten=(datetime.datetime.now(datetime.timezone.utc)-datetime.timedelta(minutes=10)).isoformat(timespec="seconds")
  recent=c.execute("SELECT COUNT(*) FROM finance_agent_wa_pilot_outbox WHERE uid=? AND created_at>=?",
    (uid,last_ten)).fetchone()[0]
  if daily>=60 or recent>=12:return False
  c.execute("INSERT INTO finance_agent_wa_pilot_outbox(event_hash,uid,status,created_at) VALUES(?,?,'reserved',?)",
   (receipt,uid,now()))
  c.commit()
 # Explicit send to the proven chat ONLY. No contact searches, broadcasts or media sends.
 ok=False
 try:
  _,status=waha(cfg,"POST","/api/sendText",
    {"session":"clube-motorista","chatId":chat,"text":text,"linkPreview":False})
  ok=status in (200,201,202)
 except Exception:
  ok=False
 with db() as c:
  c.execute("UPDATE finance_agent_wa_pilot_outbox SET status=?,completed_at=? WHERE event_hash=?",
    ("sent" if ok else "failed",now(),receipt))
  audit(c,uid,"finance_agent:pilot_outbound","delivery="+("sent" if ok else "failed"))
  c.commit()
 return ok

def send_chart_once(uid,chat,event_id,report):
 """Send only a per-driver report derived from confirmed records.

 No automatic re-send on uncertain API failure. One contact, one signed WAHA session,
 same limited pilot outbox, plus the preconfigured chart quota (3/day).
 """
 import base64
 from finance_agent_waha_v1 import CHAT
 from finance_agent_limits_v1 import reserve,complete,refund
 from finance_agent_chart_v1 import render_jpeg
 if not report.get("has_data") or not CHAT.fullmatch(str(chat)) or not 8<=len(str(event_id))<=300:
  return False
 receipt=sha("ng-pilot-outbound:"+str(event_id)+":chart")
 with db() as c:
  if not permitted(c,uid) or not linked(c,uid,chat):return False
  cfg,_=config_get(c)
  if not cfg or cfg.get("session")!="clube-motorista":return False
  if c.execute("SELECT 1 FROM finance_agent_wa_pilot_outbox WHERE event_hash=?",(receipt,)).fetchone():
   return False
  today=datetime.datetime.now(datetime.timezone.utc).date().isoformat()
  cutoff=(datetime.datetime.now(datetime.timezone.utc)-datetime.timedelta(minutes=10)).isoformat(timespec="seconds")
  daily=c.execute("SELECT COUNT(*) FROM finance_agent_wa_pilot_outbox WHERE uid=? AND created_at>=?",(uid,today)).fetchone()[0]
  recent=c.execute("SELECT COUNT(*) FROM finance_agent_wa_pilot_outbox WHERE uid=? AND created_at>=?",(uid,cutoff)).fetchone()[0]
  if daily>=60 or recent>=12:return False
 try:ticket=reserve(uid,"chart")
 except HTTPException:return False
 try:
  jpeg=render_jpeg(report)
  if not jpeg:refund(ticket);return False
  with db() as c:
   if not permitted(c,uid) or not linked(c,uid,chat):
    refund(ticket)
    return False
   if c.execute("SELECT 1 FROM finance_agent_wa_pilot_outbox WHERE event_hash=?",(receipt,)).fetchone():
    refund(ticket)
    return False
   c.execute("INSERT INTO finance_agent_wa_pilot_outbox(event_hash,uid,status,created_at) "
    "VALUES(?,?,'reserved',?)",(receipt,uid,now()))
   c.commit()
  body={"session":"clube-motorista","chatId":chat,
        "file":{"mimetype":"image/jpeg","data":base64.b64encode(jpeg).decode("ascii"),
                "filename":"movi-resumo-financeiro.jpg"},
        "caption":"📊 Seu minigráfico do mês. Somente lançamentos confirmados; não é saldo bancário."}
  ok=False
  try:
   _,status=waha(cfg,"POST","/api/sendImage",body)
   ok=status in (200,201,202)
  except Exception:
   ok=False
  with db() as c:
   c.execute("UPDATE finance_agent_wa_pilot_outbox SET status=?,completed_at=? WHERE event_hash=?",
      ("sent" if ok else "failed",now(),receipt))
   audit(c,uid,"finance_agent:pilot_chart","delivery="+("sent" if ok else "failed"))
   c.commit()
  if ok:complete(ticket)
  else:refund(ticket)
  return ok
 except Exception:
  refund(ticket)
  return False

def currency(amount):
 return "R$ "+f"{float(amount):,.2f}".replace(",","_").replace(".",",").replace("_",".")

def proposed_message(proposal,pid,event_id="default"):
 from finance_agent_conversation_v2 import propose_text
 return propose_text(proposal,pid,event_id)

def remember_last(uid,chat,pid):
 """Only remember proposals actually delivered to this verified chat."""
 from finance_agent_waha_v1 import link_hash
 with db() as c:
  if not permitted(c,uid) or not linked(c,uid,chat):return False
  c.execute("INSERT INTO finance_agent_wa_last_offer(uid,chat_hash,pid,offered_at) "
   "VALUES(?,?,?,?) ON CONFLICT(uid) DO UPDATE SET "
   "chat_hash=excluded.chat_hash,pid=excluded.pid,offered_at=excluded.offered_at",
   (uid,link_hash(chat),pid,now()))
  c.commit()
  return True

def forget_last(uid,chat):
 """A nonconfirmation interaction ends the context for a casual 'ok' or 'sim'."""
 from finance_agent_waha_v1 import link_hash
 with db() as c:
  c.execute("DELETE FROM finance_agent_wa_last_offer WHERE uid=? AND chat_hash=?",
    (uid,link_hash(chat)))
  c.commit()

def last_offer_for_clarification(uid,chat,minutes=15):
 """Read the last actually delivered pending suggestion in a short reply window."""
 from finance_agent_waha_v1 import link_hash
 from app import dec
 with db() as c:
  if not permitted(c,uid) or not linked(c,uid,chat):return None
  last=c.execute("SELECT pid,offered_at FROM finance_agent_wa_last_offer "
    "WHERE uid=? AND chat_hash=?",(uid,link_hash(chat))).fetchone()
  if not last:return None
  delta=datetime.datetime.now(datetime.timezone.utc)-datetime.datetime.fromisoformat(last["offered_at"])
  if not 0<=delta.total_seconds()<=minutes*60:return None
  row=c.execute("SELECT status,encrypted FROM finance_agent_proposals WHERE id=? AND uid=?",
    (last["pid"],uid)).fetchone()
  if not row or row["status"]!="pending":return None
  return {"id":last["pid"],"proposal":dec(row["encrypted"])}

def is_pilot_command(text):
 from finance_agent_conversation_v2 import command
 return command(text)

def handle_command(uid,chat,event_id,command):
 """Confirm only a recent delivered offer for natural replies; explicit IDs remain supported."""
 from finance_agent_waha_v1 import link_hash
 from finance_agent_v1 import confirm,discard
 from finance_agent_conversation_v2 import confirmed_text,discarded_text
 from app import dec
 verb,pid=command
 fingerprint=sha("finance_agent_event:"+event_id)
 result=None
 proposal=None
 with db() as c:
  if not permitted(c,uid) or not linked(c,uid,chat):
   return {"ignored":True,"reason":"pilot_not_authorized"}
  if c.execute("SELECT 1 FROM finance_agent_wa_events WHERE event_hash=?",(fingerprint,)).fetchone():
   return {"duplicate":True,"reply_sent":False}
  if pid is None:
   last=c.execute("SELECT pid,offered_at FROM finance_agent_wa_last_offer "
     "WHERE uid=? AND chat_hash=?",(uid,link_hash(chat))).fetchone()
   if last:
    delta=datetime.datetime.now(datetime.timezone.utc)-datetime.datetime.fromisoformat(last["offered_at"])
    if 0<=delta.total_seconds()<=900:pid=last["pid"]
   if pid is None:
    older=c.execute("SELECT id,encrypted FROM finance_agent_proposals "
       "WHERE uid=? AND origin='whatsapp' AND status='pending' ORDER BY id DESC LIMIT 4",
       (uid,)).fetchall()
    if older:
     choices=[]
     for item in older[:3]:
      item_data=dec(item["encrypted"])
      val=item_data.get("amount")
      label=str(item_data.get("category") or "a revisar")[:45]
      choices.append(f"• *{item['id']}* — {currency(val) if val else 'valor a conferir'} em {label}")
     message=("Você tem sugestão(ões) aguardando confirmação. 😊\n"+
       "\n".join(choices)+
       "\nPara evitar enganos, responda *CONFIRMAR + número* ou *DESCARTAR + número*.")
    else:
     message=("Ainda não tenho uma sugestão recente para confirmar. "
       "Me mande seu gasto ou ganho, ou responda *CONFIRMAR + número* de uma sugestão anterior.")
    result="no_recent_offer"
  if pid is not None:
   row=c.execute("SELECT uid,status,encrypted FROM finance_agent_proposals WHERE id=?",(pid,)).fetchone()
   if not row or row["uid"]!=uid:
    message="Não encontrei esse lançamento na sua conta. Confira o número e tente novamente."
    result="missing"
   elif row["status"]!="pending":
    message="Essa sugestão já foi resolvida. Não registrei novamente."
    result="already_decided"
   else:
    proposal=dec(row["encrypted"])
    if verb=="CONFIRMAR" and (proposal.get("status")!="ready" or
        proposal.get("kind") not in ("expense","income") or not proposal.get("amount")):
     message=("Ainda falta confirmar o valor ou a categoria desse lançamento. 🙂 "
      "Me mande a informação mais completa, como *Gastei R$ 50 de gasolina*, "
      "e eu preparo outra sugestão por aqui. Não salvei esse valor.")
     result="review_required"
    else:
     result="confirm" if verb=="CONFIRMAR" else "discard"
     message=None
  c.execute("INSERT INTO finance_agent_wa_events(event_hash,uid,handled_at) VALUES(?,?,?)",
   (fingerprint,uid,now()))
  c.commit()
 if result=="confirm":
  try:
   from finance_agent_core import CATEGORIES
   cat=proposal["category"]
   if cat not in [c[0] for c in CATEGORIES]+["Outros","Outros / a confirmar","Corridas","Outras receitas","APLICATIVO","OUTROS"]:
    message="Ainda preciso que você revise a categoria no Clube."
   else:
    note=str(proposal.get("summary") or "")[:150]
    if proposal.get("kind")=="income":
     origin=proposal.get("merchant")
     if origin in ("Uber","99","inDrive","Urbano Norte","iFood","Rappi","Loggi","Extra","Particular"):
      note=("Origem: "+origin+" | "+note)[:200]
    confirm(pid,{"kind":proposal["kind"],"amount":proposal["amount"],"category":cat,
      "note":note,"date":proposal.get("date") or ""},
      u={"id":uid})
    message=confirmed_text(proposal,event_id)
  except HTTPException:
   message="Não consegui confirmar esse lançamento. Confira a sugestão pelo Clube."
 elif result=="discard":
  try:
   discard(pid,u={"id":uid})
   message=discarded_text(event_id)
  except HTTPException:
   message="Não consegui descartar a sugestão. Confira pelo Clube."
 # Stale follow-up bare confirmation must never confirm the prior decision again.
 if result in ("confirm","discard","already_decided","missing"):
  with db() as c:
   c.execute("DELETE FROM finance_agent_wa_last_offer WHERE uid=? AND chat_hash=? AND pid=?",
     (uid,link_hash(chat),pid))
   c.commit()
 sent=send_once(uid,chat,event_id,message)
 return {"ok":True,"command":verb.lower(),"reply_sent":sent,"result":result,"proposal_id":pid}

@router.get("/api/finance-agent/whatsapp/pilot")
def pilot_driver_info(u=Depends(auth)):
 with db() as c:
  owner,enabled=state(c)
  linked_to_pilot=c.execute("SELECT 1 FROM finance_agent_wa_links WHERE uid=?",(u["id"],)).fetchone() is not None
 return {"pilot_enabled":enabled,"eligible":u["role"]=="driver" and u["id"]==owner,
  "linked":bool(linked_to_pilot) if u["id"]==owner else False,
  "automatic_replies":bool(enabled and u["id"]==owner and linked_to_pilot),
  "instructions":"Use seu cadastro de motorista, autorize o agente e vincule o WhatsApp com o código temporário."}

@router.get("/api/admin/finance-agent/whatsapp/pilot")
def pilot_admin_info(u=Depends(admin)):
 with db() as c:
  owner,enabled=state(c)
  linked_to_pilot=bool(owner and c.execute("SELECT 1 FROM finance_agent_wa_links WHERE uid=?",(owner,)).fetchone())
  sent=c.execute("SELECT COUNT(*) FROM finance_agent_wa_pilot_outbox WHERE status='sent'").fetchone()[0]
 return {"pilot_enabled":enabled,"pilot_uid_set":bool(owner),"pilot_linked":linked_to_pilot,
  "replies_sent":sent,"restrict_to_one_contact":True}

@router.put("/api/admin/finance-agent/whatsapp/pilot")
def pilot_admin_toggle(data:dict,u=Depends(admin)):
 if set(data)!={"enabled"} or type(data["enabled"]) is not bool:
  raise HTTPException(422,"Informe enabled verdadeiro ou falso.")
 with db() as c:
  owner,old=state(c)
  if not owner:raise HTTPException(409,"Configure o motorista piloto antes de ativar.")
  c.execute("UPDATE finance_agent_wa_pilot SET enabled=?,updated_at=? WHERE id=1",
    (int(data["enabled"]),now()))
  audit(c,u["id"],"finance_agent:pilot_enabled",str(data["enabled"]))
  c.commit()
 return {"ok":True,"pilot_enabled":data["enabled"],"restrict_to_one_contact":True}
