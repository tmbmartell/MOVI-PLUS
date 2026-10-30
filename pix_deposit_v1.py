"""MOVI+ P1: fixed CNPJ Pix key, monthly installment planning and declared deposits.

IMPORTANT: this app does not initiate Pix or read bank balances. Its only outbound
mechanism is a gated WAHA reminder to a linked pilot driver; disabled by default.
Recipient name must first be checked on the banking app by the responsible admin.
"""
import datetime as dt
import os
import re
from zoneinfo import ZoneInfo
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from app import ROOT, db, admin, driver, enc, dec, audit, now, cents
from finance_deposit_planner_v1 import month_plan, SLOTS

router=APIRouter()
TZ=ZoneInfo("America/Porto_Velho")
DAY_RE=re.compile(r"^20\d{2}-(0[1-9]|1[0-2])-([0-3]\d)$")
DEFAULT_SLOT_HOURS={"manha":9,"tarde":14,"noite":19}
NOTICE_ENV="MOVI_PIX_REMINDERS_ENABLED"

def pix_cnpj(key):
    """Strictly validate numeric CNPJ Pix keys, no registration inference."""
    if not isinstance(key,str):raise HTTPException(422,"Chave Pix CNPJ inválida")
    digits=re.sub(r"[.\-/]","",key.strip())
    if not re.fullmatch(r"\d{14}",digits) or digits==digits[0]*14:
        raise HTTPException(422,"Informe um CNPJ Pix válido")
    a=list(map(int,digits))
    def check(count,weights):
        rem=sum(a[i]*w for i,w in enumerate(weights))%11
        return 0 if rem<2 else 11-rem
    if a[12]!=check(12,(5,4,3,2,9,8,7,6,5,4,3,2)) or a[13]!=check(13,(6,5,4,3,2,9,8,7,6,5,4,3,2)):
        raise HTTPException(422,"Dígitos verificadores do CNPJ inválidos")
    return digits

def init():
    with db() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS movi_pix_receiver(
            id INTEGER PRIMARY KEY CHECK(id=1), encrypted BLOB NOT NULL,
            enabled INTEGER NOT NULL DEFAULT 0,bank_verified INTEGER NOT NULL DEFAULT 0,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS movi_pix_installment(
            uid INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
            monthly_cents INTEGER NOT NULL CHECK(monthly_cents>0),
            active INTEGER NOT NULL DEFAULT 1,updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS movi_pix_installment_month(
            uid INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            month TEXT NOT NULL,
            monthly_cents INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            PRIMARY KEY(uid,month)
        );
        CREATE TABLE IF NOT EXISTS movi_pix_notice_schedule(
            id INTEGER PRIMARY KEY CHECK(id=1),
            morning_hour INTEGER NOT NULL DEFAULT 9,
            afternoon_hour INTEGER NOT NULL DEFAULT 14,
            evening_hour INTEGER NOT NULL DEFAULT 19,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS movi_pix_notice_consent(
            uid INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
            enabled INTEGER NOT NULL DEFAULT 0,updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS movi_pix_declarations(
            id INTEGER PRIMARY KEY,
            uid INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            entry_day TEXT NOT NULL, slot TEXT NOT NULL,
            expected_cents INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'declared' CHECK(status='declared'),
            created_at TEXT NOT NULL,
            UNIQUE(uid,entry_day,slot)
        );
        CREATE TABLE IF NOT EXISTS movi_pix_notice_outbox(
            uid INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            entry_day TEXT NOT NULL,slot TEXT NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('attempted','sent','failed')),
            created_at TEXT NOT NULL,
            PRIMARY KEY(uid,entry_day,slot)
        );
        """)
        c.commit()
init()

def _receiver(c):
    r=c.execute("SELECT encrypted,enabled,bank_verified,updated_at FROM movi_pix_receiver WHERE id=1").fetchone()
    if not r:return {"key":"","recipient_name":"","enabled":False,"bank_verified":False}
    obj=dec(r["encrypted"])
    return {"key":obj["key"],"recipient_name":obj.get("recipient_name",""),
            "enabled":bool(r["enabled"]),"bank_verified":bool(r["bank_verified"]),
            "updated_at":r["updated_at"]}

def _notice_hours(c):
    row=c.execute("SELECT morning_hour,afternoon_hour,evening_hour FROM movi_pix_notice_schedule WHERE id=1").fetchone()
    return dict(zip(SLOTS,(row["morning_hour"],row["afternoon_hour"],row["evening_hour"]))) if row else dict(DEFAULT_SLOT_HOURS)

@router.get("/api/admin/pix/schedule")
def get_notice_schedule(u=Depends(admin)):
    with db() as c:
        hours=_notice_hours(c)
    return {"hours":hours,"timezone":"America/Porto_Velho",
            "delivery_active":os.environ.get(NOTICE_ENV)=="1",
            "notice":"Os horários programam lembretes; não ativam o WhatsApp."}

@router.put("/api/admin/pix/schedule")
def set_notice_schedule(data:dict,u=Depends(admin)):
    if not isinstance(data,dict) or set(data)!=set(SLOTS):
        raise HTTPException(422,"Informe manhã, tarde e noite")
    if any(type(data[slot]) is not int for slot in SLOTS):
        raise HTTPException(422,"Horários devem ser horas inteiras")
    morning,afternoon,evening=(data[s] for s in SLOTS)
    if not (6<=morning<=11 and 12<=afternoon<=17 and 18<=evening<=22):
        raise HTTPException(422,"Manhã 6–11h, tarde 12–17h e noite 18–22h")
    with db() as c:
        c.execute("INSERT INTO movi_pix_notice_schedule(id,morning_hour,afternoon_hour,evening_hour,updated_at)"
                  "VALUES(1,?,?,?,?) ON CONFLICT(id) DO UPDATE SET "
                  "morning_hour=excluded.morning_hour,afternoon_hour=excluded.afternoon_hour,"
                  "evening_hour=excluded.evening_hour,updated_at=excluded.updated_at",
                  (morning,afternoon,evening,now()))
        audit(c,u["id"],"pix:notice_schedule","updated")
        c.commit()
    return {"ok":True,"hours":{s:data[s] for s in SLOTS},
            "delivery_activated":False}

def _money(raw):
    amount=cents(raw)
    if amount<1 or amount>1000000000:
        raise HTTPException(422,"Informe parcela entre R$ 0,01 e R$ 10.000.000")
    return amount

def _date(date):
    if not isinstance(date,str) or not DAY_RE.fullmatch(date):
        raise HTTPException(422,"Informe uma data AAAA-MM-DD")
    try:return dt.date.fromisoformat(date)
    except ValueError:raise HTTPException(422,"Data inválida")

def _money_text(amount):
    return "R$ "+f"{amount/100:,.2f}".replace(",","_").replace(".",",").replace("_",".")

def _item(c,uid,day):
    receiver=_receiver(c)
    if not receiver["enabled"] or not receiver["bank_verified"]:
        raise HTTPException(409,"Pix ainda não foi verificado e liberado pelo gestor")
    driver_row=c.execute("SELECT status FROM users WHERE id=? AND role='driver'",(uid,)).fetchone()
    if not driver_row or driver_row["status"]!="active":
        raise HTTPException(403,"Motorista não está ativo")
    rec=c.execute("SELECT monthly_cents FROM movi_pix_installment WHERE uid=? AND active=1",(uid,)).fetchone()
    if not rec:raise HTTPException(409,"Parcela deste motorista ainda não configurada")
    month=day.strftime("%Y-%m")
    # Freeze the installment for the first month request: later plan changes do
    # not silently rewrite a previously delivered daily Pix amount.
    c.execute("INSERT OR IGNORE INTO movi_pix_installment_month(uid,month,monthly_cents,created_at) "
              "VALUES(?,?,?,?)",(uid,month,rec["monthly_cents"],now()))
    locked=c.execute("SELECT monthly_cents FROM movi_pix_installment_month WHERE uid=? AND month=?",
                     (uid,month)).fetchone()
    c.commit()
    plan=month_plan(month,locked["monthly_cents"])
    return receiver,plan["days"][day.day-1]

def message_for_slot(key,day,slot,amount,recipient_name=""):
    """Explicit copyable key, not QR or an assertion that any bank transfer succeeded."""
    label={"manha":"manhã","tarde":"tarde","noite":"noite"}[slot]
    return (
      "MOVI+ · Lembrete de depósito ("+label+")\n"
      "Data: "+day+"\n"
      "Valor programado: "+_money_text(amount)+"\n"
      "Chave Pix CNPJ do recebedor: "+key+"\n"
      "Favorecido informado pelo Clube: "+(recipient_name or "consulte o gestor")+"\n"
      "Antes de pagar, confira no seu banco o nome do titular da conta.\n"
      "Depois, informe o pagamento pelo MOVI+. A declaração não confirma recebimento bancário."
    )

@router.get("/api/admin/pix")
def admin_get(u=Depends(admin)):
    with db() as c:
        info=_receiver(c)
        users=c.execute(
            "SELECT COUNT(*) FROM movi_pix_installment WHERE active=1").fetchone()[0]
        declared=c.execute("SELECT COUNT(*) FROM movi_pix_declarations").fetchone()[0]
    return {**info,"configured_drivers":users,"declared_count":declared,
            "bank_integration":False,"automatic_reminders":False}

@router.put("/api/admin/pix")
def admin_set(data:dict,u=Depends(admin)):
    if not isinstance(data,dict) or set(data)!={"key","recipient_name","bank_verified","enabled"}:
        raise HTTPException(422,"Campos esperados: key, recipient_name, bank_verified, enabled")
    key=pix_cnpj(data["key"])
    name=data["recipient_name"]
    if not isinstance(name,str) or len(name.strip())>120:
        raise HTTPException(422,"Nome do recebedor inválido")
    name=name.strip()
    verified=data["bank_verified"]
    enabled=data["enabled"]
    if type(verified) is not bool or type(enabled) is not bool:
        raise HTTPException(422,"Estados inválidos")
    if (enabled or verified) and len(name)<3:
        raise HTTPException(422,"Confirme o nome do titular que aparece no banco")
    if enabled and not verified:
        raise HTTPException(409,"Confira a chave Pix e o titular no banco antes de ativar")
    with db() as c:
        previous=_receiver(c)
        # Changing a key or recipient always revokes previous bank verification.
        if previous["key"] and (key!=previous["key"] or name!=previous["recipient_name"]):
            if enabled or verified:
                raise HTTPException(409,"Nova chave ou titular: salve desligado e confira no banco antes de verificar")
            c.execute("UPDATE movi_pix_notice_consent SET enabled=0")
        c.execute("INSERT INTO movi_pix_receiver(id,encrypted,enabled,bank_verified,updated_at) "
                  "VALUES(1,?,?,?,?) ON CONFLICT(id) DO UPDATE SET encrypted=excluded.encrypted,"
                  "enabled=excluded.enabled,bank_verified=excluded.bank_verified,"
                  "updated_at=excluded.updated_at",
                  (enc({"key":key,"recipient_name":name}),int(enabled),int(verified),now()))
        audit(c,u["id"],"pix:recipient_config","activated" if enabled else "disabled")
        c.commit()
    return {"ok":True,"key":key,"enabled":enabled,"bank_verified":verified,
            "notice":"Chave guardada; validar dados exibidos no aplicativo bancário."}

@router.put("/api/admin/pix/driver/{uid}")
def set_installment(uid:int,data:dict,u=Depends(admin)):
    if not isinstance(data,dict) or set(data)!={"monthly_amount","active"} or type(data["active"]) is not bool:
        raise HTTPException(422,"Valor mensal e situação necessários")
    monthly=_money(data["monthly_amount"])
    with db() as c:
        who=c.execute("SELECT id FROM users WHERE id=? AND role='driver'",(uid,)).fetchone()
        if not who:raise HTTPException(404,"Motorista não encontrado")
        c.execute("INSERT INTO movi_pix_installment(uid,monthly_cents,active,updated_at)"
                  "VALUES(?,?,?,?) ON CONFLICT(uid) DO UPDATE SET monthly_cents=excluded.monthly_cents,"
                  "active=excluded.active,updated_at=excluded.updated_at",
                  (uid,monthly,int(data["active"]),now()))
        audit(c,u["id"],"pix:installment_config",uid);c.commit()
    return {"ok":True,"uid":uid,"monthly_cents":monthly,"active":data["active"]}

@router.get("/api/admin/pix/drivers")
def driver_list(u=Depends(admin)):
    with db() as c:
        rows=c.execute("SELECT u.id,u.name,u.status,p.monthly_cents,p.active FROM users u "
             "LEFT JOIN movi_pix_installment p ON p.uid=u.id WHERE u.role='driver' "
             "ORDER BY u.id LIMIT 1000")
        return {"items":[dict(x) for x in rows]}

@router.get("/api/driver/pix/day")
def driver_day(date:str="",u=Depends(driver)):
    target=_date(date) if date else dt.datetime.now(TZ).date()
    with db() as c:
        receiver,day=_item(c,u["id"],target)
        declared={r["slot"] for r in c.execute(
            "SELECT slot FROM movi_pix_declarations WHERE uid=? AND entry_day=?",
            (u["id"],target.isoformat()))}
    return {"day":target.isoformat(),"monthly_installment_configured":True,
      "pix_key":receiver["key"],"pix_key_type":"CNPJ",
      "recipient_name_configured":receiver["recipient_name"],
      "slots":[{**slot,"declared_by_driver":slot["slot"] in declared,
                "message":message_for_slot(receiver["key"],target.isoformat(),slot["slot"],slot["amount_cents"],receiver["recipient_name"])}
               for slot in day["slots"]],
      "notice":"Motorista declara depósito; apenas comprovante do banco confirma recebimento."}

@router.get("/api/driver/pix/notice-consent")
def notice_get(u=Depends(driver)):
    with db() as c:
        r=c.execute("SELECT enabled FROM movi_pix_notice_consent WHERE uid=?",(u["id"],)).fetchone()
    return {"enabled":bool(r and r["enabled"]),"message":"Avisos automáticos exigem consentimento e WhatsApp vinculado."}

@router.put("/api/driver/pix/notice-consent")
def notice_set(data:dict,u=Depends(driver)):
    if not isinstance(data,dict) or set(data)!={"enabled"} or type(data["enabled"]) is not bool:
        raise HTTPException(422,"Informe enabled verdadeiro ou falso")
    with db() as c:
        if data["enabled"]:
            _item(c,u["id"],dt.datetime.now(TZ).date())
            from finance_auto_report_v1 import _pilot_chat
            if not _pilot_chat(c,u["id"]):
                raise HTTPException(409,"Vincule o WhatsApp e autorize o agente financeiro antes dos avisos")
        c.execute("INSERT INTO movi_pix_notice_consent(uid,enabled,updated_at) VALUES(?,?,?) "
                  "ON CONFLICT(uid) DO UPDATE SET enabled=excluded.enabled,updated_at=excluded.updated_at",
                  (u["id"],int(data["enabled"]),now()))
        audit(c,u["id"],"pix:notice_consent","enabled" if data["enabled"] else "revoked")
        c.commit()
    return {"ok":True,"enabled":data["enabled"]}

@router.post("/api/driver/pix/declare")
def declare(data:dict,u=Depends(driver)):
    if not isinstance(data,dict) or set(data)!={"date","slot"}:
        raise HTTPException(422,"Informe data e turno")
    day=_date(data["date"]);slot=data["slot"]
    if slot not in SLOTS:raise HTTPException(422,"Turno inválido")
    if day>dt.datetime.now(TZ).date():
        raise HTTPException(422,"Não declare um pagamento futuro")
    with db() as c:
        _,item=_item(c,u["id"],day)
        amount=next(x["amount_cents"] for x in item["slots"] if x["slot"]==slot)
        existing=c.execute("SELECT id FROM movi_pix_declarations WHERE uid=? AND entry_day=? AND slot=?",
                           (u["id"],day.isoformat(),slot)).fetchone()
        if existing:return {"ok":True,"id":existing["id"],"status":"declared","duplicate":True}
        cursor=c.execute("INSERT INTO movi_pix_declarations(uid,entry_day,slot,expected_cents,created_at) "
              "VALUES(?,?,?,?,?)",(u["id"],day.isoformat(),slot,amount,now()))
        audit(c,u["id"],"pix:driver_declared",str(cursor.lastrowid));c.commit()
    return {"ok":True,"id":cursor.lastrowid,"status":"declared","duplicate":False,
            "verified_by_bank":False}

@router.get("/api/admin/pix/declarations")
def declarations(u=Depends(admin)):
    with db() as c:
        rows=[dict(r) for r in c.execute(
            "SELECT d.id,d.uid,u.name,d.entry_day,d.slot,d.expected_cents,d.status,d.created_at "
            "FROM movi_pix_declarations d JOIN users u ON u.id=d.uid ORDER BY d.id DESC LIMIT 200")]
        return {"items":rows,"note":"Declarações de motoristas, NÃO conciliação bancária."}

@router.get("/meu-pix")
def driver_page(u=Depends(driver)):
    return FileResponse(ROOT/"static"/"movi-pix-v1.html",media_type="text/html")

@router.get("/gestao/pix")
def admin_page(u=Depends(admin)):
    return FileResponse(ROOT/"static"/"movi-pix-admin-v1.html",media_type="text/html")

def run_notice(instant=None,dry_run=True):
    instant=instant or dt.datetime.now(dt.timezone.utc)
    local=instant.astimezone(TZ)
    day=local.date()
    with db() as c:
        slot=next((s for s,h in _notice_hours(c).items() if h==local.hour),None)
        if not slot:return {"due":0,"sent":0,"dry_run":dry_run}
        ready=_receiver(c)
        eligible=[r["uid"] for r in c.execute(
            "SELECT i.uid FROM movi_pix_installment i "
            "JOIN movi_pix_notice_consent n ON n.uid=i.uid AND n.enabled=1 "
            "WHERE i.active=1 ORDER BY i.uid LIMIT 200")]
    if not ready["enabled"] or not ready["bank_verified"]:
        return {"due":0,"sent":0,"blocked":"Pix não verificado"}
    if dry_run:return {"due":len(eligible),"sent":0,"dry_run":True}
    if os.getenv(NOTICE_ENV)!="1":
        return {"due":len(eligible),"sent":0,"blocked":"Envio automático desligado"}
    count=0
    for uid in eligible:
        with db() as c:
            if not c.execute("SELECT enabled FROM movi_pix_notice_consent WHERE uid=? AND enabled=1",(uid,)).fetchone():
                continue
            from finance_auto_report_v1 import _pilot_chat
            chat=_pilot_chat(c,uid)
            if not chat:continue
            # Do not remind a driver who has already declared this turn paid,
            # even while the manager is verifying the bank statement.
            if c.execute("SELECT 1 FROM movi_pix_declarations WHERE uid=? AND entry_day=? AND slot=?",
                         (uid,day.isoformat(),slot)).fetchone():
                continue
            receiver,item=_item(c,uid,day)
            amount=next(x["amount_cents"] for x in item["slots"] if x["slot"]==slot)
            # No duplicate attempts, including when WAHA response is ambiguous.
            inserted=c.execute("INSERT OR IGNORE INTO movi_pix_notice_outbox(uid,entry_day,slot,status,created_at)"
                      "VALUES(?,?,?,'attempted',?)",(uid,day.isoformat(),slot,now()))
            if inserted.rowcount!=1:continue
            c.commit()
        from finance_agent_pilot_v1 import send_once
        sent=send_once(uid,chat,"movi-pix-"+str(uid)+"-"+day.isoformat()+"-"+slot,
           message_for_slot(receiver["key"],day.isoformat(),slot,amount,receiver["recipient_name"]))
        with db() as c:
            c.execute("UPDATE movi_pix_notice_outbox SET status=? WHERE uid=? AND entry_day=? AND slot=?",
                ("sent" if sent else "failed",uid,day.isoformat(),slot))
            audit(c,uid,"pix:notice","sent" if sent else "failed");c.commit()
        count+=int(bool(sent))
    return {"due":len(eligible),"sent":count,"dry_run":False}


if __name__=="__main__":
    import argparse
    parser=argparse.ArgumentParser(description="MOVI+ Pix reminder pilot (dry-run by default)")
    parser.add_argument("--send",action="store_true",help="Send only if opt-in, verified key, single-pilot and environment gate allow")
    args=parser.parse_args()
    print(run_notice(dry_run=not args.send))
