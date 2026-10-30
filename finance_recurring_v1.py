"""Compromissos mensais declarados pelo motorista; nenhum lançamento ou cobrança automática."""
import calendar
import datetime
import re
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException
from app import audit, cents, db, driver, now

router = APIRouter()
MONTH_RE = re.compile(r"^\d{4}-(?:0[1-9]|1[0-2])$")
TZ = ZoneInfo("America/Porto_Velho")

def month_value(value, required=False):
    if value in ("", None) and not required:
        return datetime.datetime.now(TZ).strftime("%Y-%m")
    if not isinstance(value, str) or not MONTH_RE.fullmatch(value):
        raise HTTPException(422, "Mês inválido; use AAAA-MM")
    if not (2000 <= int(value[:4]) <= 2100):
        raise HTTPException(422, "Ano fora do intervalo permitido")
    return value

def init_recurring():
    with db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS finance_recurring (
              id INTEGER PRIMARY KEY,
              uid INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
              title TEXT NOT NULL,
              category TEXT NOT NULL,
              amount_cents INTEGER NOT NULL CHECK(amount_cents > 0),
              due_day INTEGER NOT NULL CHECK(due_day BETWEEN 1 AND 31),
              starts TEXT NOT NULL,
              ends TEXT,
              active INTEGER NOT NULL DEFAULT 1,
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_recurring_user ON finance_recurring(uid,active,starts,ends)")
        conn.commit()

init_recurring()

def normalize(data):
    if not isinstance(data, dict):
        raise HTTPException(422, "Estrutura inválida")
    allowed = {"title", "category", "amount", "due_day", "starts", "ends", "active"}
    if set(data) - allowed:
        raise HTTPException(422, "Campo desconhecido")
    title = str(data.get("title", "")).strip()
    category = str(data.get("category", "")).strip()
    if not 2 <= len(title) <= 65 or not 2 <= len(category) <= 50:
        raise HTTPException(422, "Informe uma descrição e categoria válidas")
    amount_cents = cents(data.get("amount"))
    if amount_cents <= 0:
        raise HTTPException(422, "Informe um valor maior que zero")
    try:
        due_day = int(data["due_day"])
        if isinstance(data["due_day"], bool) or not 1 <= due_day <= 31:
            raise ValueError()
    except (KeyError, ValueError, TypeError):
        raise HTTPException(422, "Informe o dia do vencimento de 1 a 31")
    starts = month_value(data.get("starts"), required=False)
    ends = data.get("ends") or None
    if ends is not None:
        ends = month_value(ends, required=True)
        if ends < starts:
            raise HTTPException(422, "Fim não pode ser anterior ao início")
    active = data.get("active", True)
    if not isinstance(active, bool):
        raise HTTPException(422, "Estado ativo inválido")
    return title, category, amount_cents, due_day, starts, ends, int(active)

def _row(row, month=None):
    info = dict(row)
    info["active"] = bool(info["active"])
    if month:
        y, m = map(int, month.split("-"))
        day = min(int(info["due_day"]), calendar.monthrange(y, m)[1])
        info["due_date"] = f"{month}-{day:02d}"
    return info

def list_for_month(conn, uid, month):
    """Somente compromissos programados para o mês; não prova pagamento."""
    month = month_value(month, required=True)
    rows = conn.execute(
        "SELECT id,title,category,amount_cents,due_day,starts,ends,active "
        "FROM finance_recurring WHERE uid=? AND active=1 AND starts<=? "
        "AND (ends IS NULL OR ends>=?) ORDER BY due_day,id LIMIT 100",
        (uid, month, month)
    )
    return [_row(row, month) for row in rows]

@router.get("/api/finance/recurring")
def get_recurring(month: str = "", u=Depends(driver)):
    with db() as conn:
        if month:
            period = month_value(month, required=True)
            items = list_for_month(conn, u["id"], period)
        else:
            rows = conn.execute(
                "SELECT id,title,category,amount_cents,due_day,starts,ends,active "
                "FROM finance_recurring WHERE uid=? ORDER BY active DESC,id DESC LIMIT 100", (u["id"],)
            )
            items = [_row(row) for row in rows]
        return {"items": items, "total_cents": sum(i["amount_cents"] for i in items),
                "notice": "Valores planejados e declarados; não representam pagamentos efetivados."}

@router.post("/api/finance/recurring")
def create_recurring(data: dict, u=Depends(driver)):
    item = normalize(data)
    with db() as conn:
        if conn.execute("SELECT COUNT(*) FROM finance_recurring WHERE uid=?", (u["id"],)).fetchone()[0] >= 100:
            raise HTTPException(422, "Limite de 100 compromissos por motorista")
        cursor = conn.execute(
            "INSERT INTO finance_recurring(uid,title,category,amount_cents,due_day,starts,ends,active,created_at,updated_at) "
            "VALUES(?,?,?,?,?,?,?,?,?,?)", (u["id"], *item, now(), now())
        )
        audit(conn, u["id"], "recurring:created", cursor.lastrowid)
        conn.commit()
        return {"ok": True, "id": cursor.lastrowid}

@router.put("/api/finance/recurring/{rid}")
def edit_recurring(rid: int, data: dict, u=Depends(driver)):
    item = normalize(data)
    with db() as conn:
        result = conn.execute(
            "UPDATE finance_recurring SET title=?,category=?,amount_cents=?,due_day=?,"
            "starts=?,ends=?,active=?,updated_at=? WHERE id=? AND uid=?",
            (*item, now(), rid, u["id"])
        )
        if result.rowcount != 1:
            raise HTTPException(404, "Compromisso não encontrado")
        audit(conn, u["id"], "recurring:updated", rid)
        conn.commit()
        return {"ok": True}

@router.delete("/api/finance/recurring/{rid}")
def delete_recurring(rid: int, u=Depends(driver)):
    with db() as conn:
        result = conn.execute("DELETE FROM finance_recurring WHERE id=? AND uid=?", (rid, u["id"]))
        if result.rowcount != 1:
            raise HTTPException(404, "Compromisso não encontrado")
        audit(conn, u["id"], "recurring:deleted", rid)
        conn.commit()
        return {"ok": True}
