"""Manual review of driver-declared Pix deposits; never claims bank API integration.

Only an authenticated administrator can record independent evidence from an actual
bank statement. A declaration is NOT a verified receipt until explicitly checked.
No bank credentials, full references, or statements are stored.
"""
import datetime as dt
import hashlib
import hmac
import re
import sqlite3
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException

from app import admin, driver, db, audit, now, cents, KEY
from pix_deposit_v1 import _date

router = APIRouter()
TZ = ZoneInfo("America/Porto_Velho")
REF = re.compile(r"^[A-Za-z0-9_.\-/]{8,90}$")
MONTH = re.compile(r"^20\d{2}-(0[1-9]|1[0-2])$")

def init():
    with db() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS movi_pix_manual_reviews (
            declaration_id INTEGER PRIMARY KEY REFERENCES movi_pix_declarations(id) ON DELETE CASCADE,
            state TEXT NOT NULL CHECK(state IN ('confirmed_manual','unmatched')),
            bank_amount_cents INTEGER NOT NULL CHECK(bank_amount_cents >= 0),
            reference_sha256 TEXT UNIQUE,
            statement_day TEXT,
            reviewer_uid INTEGER NOT NULL REFERENCES users(id),
            note TEXT NOT NULL DEFAULT '',
            reviewed_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_pix_reviews_state ON movi_pix_manual_reviews(state);
        """)
        conn.commit()
init()

def _ref_hash(reference):
    # Keyed digest prevents offline guessing of short bank reference values if DB leaks.
    return hmac.new(KEY.read_bytes(),("movi_pix_manual_ref_v1|"+reference.upper()).encode(),hashlib.sha256).hexdigest()

def _safe_amount(value):
    try: amount=cents(value)
    except (TypeError,ValueError):
        raise HTTPException(422,"Informe um valor de extrato válido")
    if amount>100000000000:
        raise HTTPException(422,"Valor de extrato fora do limite")
    return amount

@router.get("/api/admin/pix/reviews")
def admin_reviews(month:str="",u=Depends(admin)):
    if month and not MONTH.fullmatch(month):
        raise HTTPException(422,"Mês inválido")
    with db() as conn:
        rows=[dict(x) for x in conn.execute(
          "SELECT d.id,d.uid,u.name,d.entry_day,d.slot,d.expected_cents,d.created_at, "
          "r.state AS review_state,r.bank_amount_cents,r.statement_day,r.reviewed_at,r.note, "
          "rv.name AS reviewer_name "
          "FROM movi_pix_declarations d "
          "JOIN users u ON u.id=d.uid "
          "LEFT JOIN movi_pix_manual_reviews r ON r.declaration_id=d.id "
          "LEFT JOIN users rv ON rv.id=r.reviewer_uid "
          "WHERE (?='' OR substr(d.entry_day,1,7)=?) "
          "ORDER BY d.entry_day DESC,d.id DESC LIMIT 300",(month,month))]
    declared=sum(row["expected_cents"] for row in rows)
    confirmed=sum(row["bank_amount_cents"] for row in rows if row["review_state"]=="confirmed_manual")
    return {"items":rows,"count":len(rows),
      "declared_cents":declared,"confirmed_manually_cents":confirmed,
      "unmatched_count":sum(r["review_state"]=="unmatched" for r in rows),
      "pending_count":sum(r["review_state"] is None for r in rows),
      "external_bank_api_connected":False,
      "notice":"Conferência humana do extrato, sem conexão bancária automática. Totais limitados às linhas retornadas."}

@router.get("/api/driver/pix/reviews")
def driver_reviews(date:str="",u=Depends(driver)):
    target=_date(date) if date else dt.datetime.now(TZ).date()
    with db() as conn:
        rows=[dict(x) for x in conn.execute(
         "SELECT d.slot,d.expected_cents,r.state FROM movi_pix_declarations d "
         "LEFT JOIN movi_pix_manual_reviews r ON r.declaration_id=d.id "
         "WHERE d.uid=? AND d.entry_day=? ORDER BY d.id",
         (u["id"],target.isoformat()))]
    return {"day":target.isoformat(),
      "items":[{"slot":x["slot"],"amount_cents":x["expected_cents"],
                "review_state":x["state"] or "pending"} for x in rows],
      "notice":"Confirmado manualmente significa que um gestor declarou ter conferido o extrato do recebedor."}

@router.post("/api/admin/pix/review/{declaration_id}")
def review(declaration_id:int,data:dict,u=Depends(admin)):
    if not isinstance(data,dict) or set(data)!={"decision","statement_checked","bank_amount","reference","statement_day","note"}:
        raise HTTPException(422,"Informe decisão, confirmação do extrato, valor, referência, data e observação")
    decision=data["decision"]
    if decision not in ("confirmed_manual","unmatched") or type(data["statement_checked"]) is not bool or not data["statement_checked"]:
        raise HTTPException(422,"Conferência explícita do extrato exigida")
    amount=_safe_amount(data["bank_amount"])
    reference=data["reference"]
    note=data["note"]
    if not isinstance(reference,str) or not isinstance(note,str) or len(note)>240:
        raise HTTPException(422,"Referência ou observação inválida")
    reference=reference.strip()
    note=note.strip()
    day=_date(data["statement_day"]) if data["statement_day"] else None
    if decision=="confirmed_manual":
        if not REF.fullmatch(reference) or day is None or day>dt.datetime.now(TZ).date():
            raise HTTPException(422,"Para confirmar, informe referência única e data válida do crédito no extrato")
        if amount<=0:raise HTTPException(422,"Crédito precisa ser maior que zero")
    else:
        if reference or amount!=0 or len(note)<8:
            raise HTTPException(422,"Divergência sem crédito: use valor zero, referência vazia e explique o motivo")
        day=None
    with db() as conn:
        conn.execute("BEGIN IMMEDIATE")
        declaration=conn.execute(
           "SELECT id,uid,entry_day,slot,expected_cents FROM movi_pix_declarations WHERE id=?",
           (declaration_id,)).fetchone()
        if not declaration:
            raise HTTPException(404,"Declaração não encontrada")
        existing=conn.execute("SELECT state FROM movi_pix_manual_reviews WHERE declaration_id=?",
                             (declaration_id,)).fetchone()
        if existing and existing["state"]=="confirmed_manual":
            raise HTTPException(409,"Conferência já confirmada. Não é possível sobrescrever sem procedimento de estorno")
        if decision=="confirmed_manual" and amount!=declaration["expected_cents"]:
            raise HTTPException(409,"Valor bancário difere do previsto: marque como divergência para análise")
        if day and day<dt.date.fromisoformat(declaration["entry_day"]):
            raise HTTPException(422,"Data do crédito anterior à declaração exige revisão")
        hash_ref=_ref_hash(reference) if decision=="confirmed_manual" else None
        try:
            conn.execute(
                "INSERT INTO movi_pix_manual_reviews(declaration_id,state,bank_amount_cents,"
                "reference_sha256,statement_day,reviewer_uid,note,reviewed_at)"
                "VALUES(?,?,?,?,?,?,?,?) "
                "ON CONFLICT(declaration_id) DO UPDATE SET state=excluded.state,"
                "bank_amount_cents=excluded.bank_amount_cents,reference_sha256=excluded.reference_sha256,"
                "statement_day=excluded.statement_day,reviewer_uid=excluded.reviewer_uid,"
                "note=excluded.note,reviewed_at=excluded.reviewed_at",
                (declaration_id,decision,amount,hash_ref,day.isoformat() if day else None,u["id"],note,now()))
        except sqlite3.IntegrityError:
            raise HTTPException(409,"Essa referência bancária já foi usada para outra declaração")
        audit(conn,u["id"],"pix:bank_statement_review",
              str(declaration_id)+":"+decision)
        conn.commit()
    return {"ok":True,"declaration_id":declaration_id,"state":decision,
      "confirmed_manually":decision=="confirmed_manual",
      "bank_api_verified":False,
      "notice":"Conferência humana registrada; não há comunicação automática com o banco."}
