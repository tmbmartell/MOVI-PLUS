"""MOVI+ opt-in WhatsApp summaries: private pilot, at-most-once scheduling.

No network sends unless all of these are true:
  (1) explicit driver opt-in; (2) linked proven chat and agent opt-in;
  (3) admin gate armed; (4) single-contact pilot permitted;
  (5) MOVI_REPORT_DELIVERY_ENABLED=1 and valid HTTPS public base.
The CLI defaults to dry-run; no background timer is installed by this module.
"""
import argparse
import datetime as dt
import os
import re
import secrets
from urllib.parse import quote, urlparse
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse

from app import audit, db, dec, driver, admin, now, sha
from finance_agent_conversation_v2 import month_data, money
from finance_flow_v1 import build_flow

router = APIRouter()
TZ = ZoneInfo("America/Porto_Velho")
UTC = dt.timezone.utc
PERIOD_RE = re.compile(r"^\d{4}-(?:0[1-9]|1[0-2])$")
TOKEN_RE = re.compile(r"^[A-Za-z0-9_-]{30,100}$")
OUTBOUND_SWITCH = "MOVI_REPORT_DELIVERY_ENABLED"
BASE_URL_ENV = "MOVI_REPORT_PUBLIC_BASE_URL"

def init():
    with db() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS movi_report_preferences (
            uid INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
            enabled INTEGER NOT NULL DEFAULT 0 CHECK(enabled IN (0,1)),
            frequency TEXT NOT NULL DEFAULT 'weekly' CHECK(frequency IN ('weekly','monthly')),
            weekday INTEGER NOT NULL DEFAULT 1 CHECK(weekday BETWEEN 1 AND 7),
            hour INTEGER NOT NULL DEFAULT 9 CHECK(hour BETWEEN 8 AND 20),
            updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS movi_report_admin_gate (
            id INTEGER PRIMARY KEY CHECK(id=1),
            enabled INTEGER NOT NULL DEFAULT 0 CHECK(enabled IN (0,1)),
            updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS movi_report_deliveries (
            id INTEGER PRIMARY KEY,
            uid INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            frequency TEXT NOT NULL,
            period TEXT NOT NULL,
            month TEXT NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('reserved','sent','partial','failed')),
            created_at TEXT NOT NULL,
            completed_at TEXT,
            UNIQUE(uid,frequency,period)
        );
        CREATE TABLE IF NOT EXISTS movi_report_links (
            token_hash TEXT PRIMARY KEY,
            uid INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            month TEXT NOT NULL,
            expires_at INTEGER NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_movi_report_links_exp ON movi_report_links(expires_at);
        """)
        conn.commit()

init()

def _preference(conn, uid):
    r = conn.execute("SELECT enabled,frequency,weekday,hour,updated_at FROM movi_report_preferences WHERE uid=?", (uid,)).fetchone()
    return dict(r) if r else {"enabled":0,"frequency":"weekly","weekday":1,"hour":9,"updated_at":None}

def _gate(conn):
    r = conn.execute("SELECT enabled FROM movi_report_admin_gate WHERE id=1").fetchone()
    return bool(r and r["enabled"])

def _public_base():
    raw=os.getenv(BASE_URL_ENV,"").strip()
    if not raw:return None
    p=urlparse(raw)
    if (p.scheme!="https" or not p.hostname or p.username or p.password or p.query
        or p.fragment or p.path not in ("","/") or p.port not in (None,443)):
        return None
    # Avoid sending a localhost or internal development link.
    host=p.hostname.lower()
    if host in ("localhost","127.0.0.1") or host.endswith((".local",".internal",".test")):
        return None
    return "https://"+host

def _transport_enabled():
    return os.getenv(OUTBOUND_SWITCH,"0")=="1" and _public_base() is not None

@router.get("/api/finance/auto-report")
def preference_get(u=Depends(driver)):
    with db() as conn:
        prefs=_preference(conn,u["id"])
        linked=bool(conn.execute("SELECT 1 FROM finance_agent_wa_links WHERE uid=?", (u["id"],)).fetchone())
        from finance_agent_v1 import options
        opted=bool(options(conn,u["id"])["enabled"])
    return {"enabled":bool(prefs["enabled"]),"frequency":prefs["frequency"],
            "weekday":prefs["weekday"],"hour":prefs["hour"],"updated_at":prefs["updated_at"],
            "linked":linked,"financial_agent_authorized":opted,
            "note":"Resumo automático apenas com autorização específica. Sem Pix ou saldo bancário."}

@router.put("/api/finance/auto-report")
def preference_set(data:dict,u=Depends(driver)):
    if not isinstance(data,dict) or set(data)!={"enabled","frequency","weekday","hour"}:
        raise HTTPException(422,"Informe enabled, frequency, weekday e hour")
    enabled,frequency,weekday,hour=(data[k] for k in ("enabled","frequency","weekday","hour"))
    if (type(enabled) is not bool or frequency not in ("weekly","monthly")
        or type(weekday) is not int or not 1<=weekday<=7
        or type(hour) is not int or not 8<=hour<=20):
        raise HTTPException(422,"Preferências inválidas")
    with db() as conn:
        if enabled:
            from finance_agent_v1 import options
            if not options(conn,u["id"])["enabled"]:
                raise HTTPException(403,"Ative o agente financeiro primeiro")
            if not conn.execute("SELECT 1 FROM finance_agent_wa_links WHERE uid=?", (u["id"],)).fetchone():
                raise HTTPException(409,"Vincule o seu número de WhatsApp antes de autorizar envios")
        conn.execute(
            "INSERT INTO movi_report_preferences(uid,enabled,frequency,weekday,hour,updated_at) VALUES(?,?,?,?,?,?) "
            "ON CONFLICT(uid) DO UPDATE SET enabled=excluded.enabled,frequency=excluded.frequency,"
            "weekday=excluded.weekday,hour=excluded.hour,updated_at=excluded.updated_at",
            (u["id"],int(enabled),frequency,weekday,hour,now()))
        audit(conn,u["id"],"movi_report:consent", "enabled" if enabled else "revoked")
        conn.commit()
    return {"ok":True,"enabled":enabled,"frequency":frequency,"weekday":weekday,"hour":hour}

@router.get("/api/admin/finance/auto-report")
def admin_gate_get(u=Depends(admin)):
    with db() as conn:
        eligible=conn.execute("SELECT COUNT(*) FROM movi_report_preferences WHERE enabled=1").fetchone()[0]
        armed=_gate(conn)
        last=[dict(r) for r in conn.execute(
            "SELECT status,COUNT(*) AS total FROM movi_report_deliveries GROUP BY status")]
    return {"armed":armed,"transport_ready":_transport_enabled(),"consented_drivers":eligible,
            "delivery_counts":last,"restrict_to_single_pilot":True}

@router.put("/api/admin/finance/auto-report")
def admin_gate_set(data:dict,u=Depends(admin)):
    if not isinstance(data,dict) or set(data)!={"armed"} or type(data["armed"]) is not bool:
        raise HTTPException(422,"Informe armed verdadeiro ou falso")
    with db() as conn:
        conn.execute("INSERT INTO movi_report_admin_gate(id,enabled,updated_at) VALUES(1,?,?) "
            "ON CONFLICT(id) DO UPDATE SET enabled=excluded.enabled,updated_at=excluded.updated_at",
            (int(data["armed"]),now()))
        audit(conn,u["id"],"movi_report:admin_gate", "on" if data["armed"] else "off")
        conn.commit()
    return {"ok":True,"armed":data["armed"],"transport_ready":_transport_enabled()}

def _due(row,local_now):
    if not row["enabled"] or row["hour"]!=local_now.hour:return None
    if row["frequency"]=="weekly":
        if row["weekday"]!=local_now.isoweekday():return None
        start=(local_now.date()-dt.timedelta(days=local_now.weekday())).isoformat()
        # Weekly = month-to-date snapshot, not a rolling seven-day ledger.
        return start,local_now.strftime("%Y-%m")
    if row["frequency"]=="monthly":
        if local_now.day!=1:return None
        prev=local_now.date().replace(day=1)-dt.timedelta(days=1)
        month=prev.strftime("%Y-%m")
        return month,month
    return None

def _report_at(month):
    year,mon=map(int,month.split("-"))
    return dt.datetime(year,mon,1,tzinfo=TZ)

def _make_link(conn,uid,month,instant):
    base=_public_base()
    if not base:
        raise ValueError("domínio HTTPS público ausente")
    secret=secrets.token_urlsafe(36)
    expires=int(instant.timestamp())+3600
    conn.execute("DELETE FROM movi_report_links WHERE expires_at<?",(int(instant.timestamp()),))
    conn.execute("INSERT INTO movi_report_links(token_hash,uid,month,expires_at) VALUES(?,?,?,?)",
                 (sha(secret),uid,month,expires))
    return base+"/relatorio/"+quote(secret,safe="")

@router.get("/relatorio/{secret}")
def protected_link(secret:str,u=Depends(driver)):
    if not TOKEN_RE.fullmatch(secret):raise HTTPException(404,"Link não encontrado")
    with db() as conn:
        row=conn.execute(
            "SELECT month FROM movi_report_links WHERE token_hash=? AND uid=? AND expires_at>?",
            (sha(secret),u["id"],int(dt.datetime.now(UTC).timestamp()))
        ).fetchone()
    if not row:
        raise HTTPException(404,"Link expirou ou pertence a outra conta")
    return RedirectResponse("/meu-fluxo?month="+quote(row["month"],safe=""),status_code=303)

def _pilot_chat(conn,uid):
    from finance_agent_pilot_v1 import permitted
    from finance_agent_waha_v1 import private_settings,CHAT,link_hash
    from finance_agent_v1 import options
    from whatsapp_bridge_v5 import config_get
    if not permitted(conn,uid) or not options(conn,uid)["enabled"]:
        return None
    _,inbound_enabled=private_settings(conn)
    if not inbound_enabled:return None
    wa,cfg_at=config_get(conn)
    if not wa or wa.get("session")!="clube-motorista":return None
    link=conn.execute("SELECT encrypted_chat FROM finance_agent_wa_links WHERE uid=?", (uid,)).fetchone()
    if not link:return None
    try:
        chat=dec(link["encrypted_chat"])["chat"]
    except (KeyError,TypeError,ValueError):return None
    if not isinstance(chat,str) or not CHAT.fullmatch(chat):return None
    if not conn.execute("SELECT 1 FROM finance_agent_wa_links WHERE uid=? AND phone_hash=?",
                        (uid,link_hash(chat))).fetchone():return None
    return chat

def _message(flow,report,link,frequency):
    label="Fechamento do mês" if frequency=="monthly" else "Parcial do mês"
    return (
      "*MOVI+ · "+label+" ("+flow["label"]+")*\n"
      "Ganhos registrados: *"+money(report["income"])+"*\n"
      "Despesas registradas: *"+money(report["expense"])+"*\n"
      "Diferença dos registros: *"+money(report["balance"])+"*\n"
      "Contas fixas previstas: *"+money(flow["scheduled_expenses_total_cents"])+"*"
      " (não somadas novamente).\n\n"
      "Seu relatório visual, com acesso pela sua conta MOVI+ (link válido por 1h):\n"+link+"\n\n"
      "Não é saldo bancário. Para parar: desative em Meu Fluxo > Relatórios."
    )

def run_due(instant=None, dry_run=True):
    """Single bounded batch. To send, admin+user+env gates must all be active.
    Reserve one slot per uid/frequency/period before the network operation;
    failures are audited, never auto retried (avoids uncertain duplicate sends).
    """
    instant=instant or dt.datetime.now(UTC)
    if instant.tzinfo is None:
        raise ValueError("instant requires timezone")
    local_now=instant.astimezone(TZ)
    with db() as conn:
        gate=_gate(conn)
        rows=[dict(x) for x in conn.execute(
            "SELECT p.uid,p.enabled,p.frequency,p.weekday,p.hour FROM movi_report_preferences p "
            "JOIN users u ON u.id=p.uid WHERE u.role='driver' AND u.status='active' "
            "AND p.enabled=1 ORDER BY p.uid LIMIT 200")]
    due=[(row,*period) for row in rows if (period:=_due(row,local_now)) is not None]
    if dry_run:
        return {"dry_run":True,"due":len(due),"would_send":sum(
            1 for row,period,month in due if _ready(row["uid"],gate)), "sent":0}
    if not gate or not _transport_enabled():
        return {"dry_run":False,"due":len(due),"sent":0,"blocked":"delivery gate or HTTPS transport not ready"}
    delivered,partial,failed=0,0,0
    for row,period,month in due:
        uid=row["uid"]
        with db() as conn:
            pref=_preference(conn,uid)
            if not pref["enabled"] or not _gate(conn):continue
            if not _pilot_chat(conn,uid):continue
            report=month_data(conn,uid,_report_at(month))
            if not report["has_data"]:continue
            # BEGIN IMMEDIATE enforces uniqueness for concurrent scheduler workers.
            conn.execute("BEGIN IMMEDIATE")
            existing=conn.execute("SELECT id FROM movi_report_deliveries WHERE uid=? AND frequency=? AND period=?",
                                  (uid,row["frequency"],period)).fetchone()
            if existing:
                conn.rollback()
                continue
            conn.execute("INSERT INTO movi_report_deliveries(uid,frequency,period,month,status,created_at) "
                         "VALUES(?,?,?,?, 'reserved',?)",(uid,row["frequency"],period,month,now()))
            link=_make_link(conn,uid,month,instant)
            flow=build_flow(conn,uid,month)
            chat=_pilot_chat(conn,uid)
            if not chat or not _preference(conn,uid)["enabled"] or not _gate(conn):
                conn.rollback()
                continue
            conn.commit()
        event_id=f"movi-report-{uid}-{row['frequency']}-{period}"
        from finance_agent_pilot_v1 import send_once,send_chart_once
        # Recheck consent immediately before contacting WAHA.
        with db() as conn:
            allowed=bool(_preference(conn,uid)["enabled"] and _gate(conn) and _pilot_chat(conn,uid))
        ok=bool(allowed and _transport_enabled() and send_once(
            uid,chat,event_id,_message(flow,report,link,row["frequency"])))
        image_ok=bool(ok and send_chart_once(uid,chat,event_id,report))
        status=("sent" if image_ok else "partial" if ok else "failed")
        with db() as conn:
            conn.execute("UPDATE movi_report_deliveries SET status=?,completed_at=? "
                         "WHERE uid=? AND frequency=? AND period=?",
                         (status,now(),uid,row["frequency"],period))
            audit(conn,uid,"movi_report:delivery",status)
            conn.commit()
        if image_ok:delivered+=1
        elif ok:partial+=1
        else:failed+=1
    return {"dry_run":False,"due":len(due),"sent":delivered,"partial":partial,"failed":failed}

def _ready(uid,gate):
    if not gate or not _transport_enabled():return False
    with db() as conn:
        return _pilot_chat(conn,uid) is not None

if __name__=="__main__":
    parser=argparse.ArgumentParser(description="MOVI+ pilot report scheduler; dry-run by default")
    parser.add_argument("--send",action="store_true",help="Allow actual sending if every opt-in and gate passes")
    args=parser.parse_args()
    print(run_due(dry_run=not args.send))
