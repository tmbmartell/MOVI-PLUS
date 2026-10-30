"""MOVI+ manual Pix bank-statement review: end-to-end synthetic security tests.

No real account, financial institution API, user record or WhatsApp messages.
"""
import datetime as dt
import os
import sys
import tempfile
from zoneinfo import ZoneInfo
from fastapi.testclient import TestClient

with tempfile.TemporaryDirectory(prefix="movi_pix_statement_qa_") as folder:
    os.environ["CLUBE_DATA"]=folder
    sys.path.insert(0,os.path.dirname(os.path.dirname(__file__)))
    import app
    import legal_v8
    import pix_reconciliation_v1 as review

    h={"X-Requested-With":"NOVAGENTE-V5"}
    credential="SyntheticPassword2026!"
    api="/api/admin/pix"
    now_day=dt.datetime.now(ZoneInfo("America/Porto_Velho")).date().isoformat()

    with app.db() as c:
        for uid,role in ((1,"admin"),(2,"driver"),(3,"driver")):
            c.execute("INSERT INTO users(id,username,phash,role,status,name,created_at,must_change) "
                      "VALUES(?,?,?,?,?,?,?,0)",
                      (uid,"statement"+str(uid),app.password_hash(credential),role,"active","Pessoa fictícia",app.now()))
        for uid in (2,3):
            legal_v8.record(c,uid,{k:True for k,_ in legal_v8.REQUIRED},
                            {k:False for k,_ in legal_v8.OPTIONAL},"qa")
        c.commit()

    def login(uid):
        client=TestClient(app.app,base_url="https://statement-test.invalid")
        result=client.post("/api/login",json={"username":"statement"+str(uid),"password":credential},headers=h)
        assert result.status_code==200,result.text
        return client

    anonymous=TestClient(app.app,base_url="https://statement-test.invalid")
    assert anonymous.get(api+"/reviews").status_code==401
    assert anonymous.post(api+"/review/1",json={},headers=h).status_code==401
    adm=login(1);motor2=login(2);motor3=login(3)
    assert motor2.get(api+"/reviews").status_code==403
    assert motor2.post(api+"/review/1",json={},headers=h).status_code==403
    print("01 - real sessions enforce admin-only bank statement reviews: PASS")

    form={"key":"12.345.678/0001-95","recipient_name":"Titular Fictício",
          "bank_verified":False,"enabled":False}
    assert adm.put(api,json=form,headers=h).status_code==200
    assert adm.put(api,json={**form,"bank_verified":True,"enabled":True},headers=h).status_code==200
    for uid in (2,3):
        r=adm.put(api+"/driver/"+str(uid),json={"monthly_amount":"1500.00","active":True},headers=h)
        assert r.status_code==200,r.text
    d2=motor2.get("/api/driver/pix/day?date="+now_day).json()
    expected=next(slot["amount_cents"] for slot in d2["slots"] if slot["slot"]=="manha")
    assert motor2.post("/api/driver/pix/declare",json={"date":now_day,"slot":"manha"},headers=h).status_code==200
    assert motor3.post("/api/driver/pix/declare",json={"date":now_day,"slot":"manha"},headers=h).status_code==200
    listing=adm.get(api+"/reviews")
    assert listing.status_code==200,listing.text
    items=listing.json()["items"]
    assert len(items)==2 and listing.json()["pending_count"]==2
    assert listing.json()["confirmed_manually_cents"]==0
    ids={x["uid"]:x["id"] for x in items}
    print("02 - two drivers declare deposits; all remain unconfirmed: PASS")

    good={"decision":"confirmed_manual","statement_checked":True,
          "bank_amount":str(expected/100),"reference":"E1234567890SYNTHETIC0001",
          "statement_day":now_day,"note":"Extrato fictício conferido em QA"}
    assert adm.post(api+"/review/"+str(ids[2]),json={**good,"statement_checked":False},headers=h).status_code==422
    assert adm.post(api+"/review/"+str(ids[2]),json={**good,"reference":""},headers=h).status_code==422
    assert adm.post(api+"/review/"+str(ids[2]),json={**good,"bank_amount":"1"},headers=h).status_code==409
    assert adm.post(api+"/review/"+str(ids[2]),json={**good,"statement_day":"2023-01-01"},headers=h).status_code==422
    assert adm.post(api+"/review/999999",json=good,headers=h).status_code==404
    assert adm.post(api+"/review/"+str(ids[2]),json=good).status_code==403
    print("03 - bank confirmation requires explicit check, matching amount, unique reference, valid date and CSRF: PASS")

    confirmed=adm.post(api+"/review/"+str(ids[2]),json=good,headers=h)
    assert confirmed.status_code==200,confirmed.text
    assert confirmed.json()["state"]=="confirmed_manual" and confirmed.json()["bank_api_verified"] is False
    assert adm.post(api+"/review/"+str(ids[2]),json=good,headers=h).status_code==409
    assert adm.post(api+"/review/"+str(ids[3]),json=good,headers=h).status_code==409
    with app.db() as c:
        row=c.execute("SELECT reference_sha256,state FROM movi_pix_manual_reviews WHERE declaration_id=?",
                      (ids[2],)).fetchone()
        assert row["state"]=="confirmed_manual" and len(row["reference_sha256"])==64
        assert "E1234567890" not in row["reference_sha256"]
        assert c.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]==0
    print("04 - manual confirmation stored as immutable audited review, reference hashed, no financial ledger posting: PASS")

    m2=motor2.get("/api/driver/pix/reviews?date="+now_day)
    m3=motor3.get("/api/driver/pix/reviews?date="+now_day)
    assert m2.status_code==m3.status_code==200
    assert m2.json()["items"]==[{"slot":"manha","amount_cents":expected,"review_state":"confirmed_manual"}]
    assert m3.json()["items"][0]["review_state"]=="pending"
    assert "E1234567890" not in str(m2.json()) and "reference_sha256" not in str(m2.json())
    print("05 - each driver sees only their own reconciliation state, never bank reference: PASS")

    bad={"decision":"unmatched","statement_checked":True,"bank_amount":"0",
         "reference":"","statement_day":"","note":"Não apareceu no extrato, revisar"}
    assert adm.post(api+"/review/"+str(ids[3]),json={**bad,"note":""},headers=h).status_code==422
    disagreed=adm.post(api+"/review/"+str(ids[3]),json=bad,headers=h)
    assert disagreed.status_code==200,disagreed.text
    assert motor3.get("/api/driver/pix/reviews?date="+now_day).json()["items"][0]["review_state"]=="unmatched"
    print("06 - unmatched deposits remain disputed, not silently marked paid: PASS")

    fixed={**good,"reference":"E1234567890SYNTHETIC0002"}
    assert adm.post(api+"/review/"+str(ids[3]),json=fixed,headers=h).status_code==200
    assert adm.get(api+"/reviews").json()["confirmed_manually_cents"]==2*expected
    assert adm.get(api+"/reviews?month=2026-99").status_code==422
    assert adm.get(api+"/reviews?month="+now_day[:7]).status_code==200
    with app.db() as c:
        assert c.execute("SELECT COUNT(*) FROM movi_pix_manual_reviews WHERE state='confirmed_manual'").fetchone()[0]==2
        assert c.execute("SELECT COUNT(*) FROM audit WHERE action='pix:bank_statement_review'").fetchone()[0]==3
    print("07 - disputed can be reconciled later with a different unique reference; audit retained: PASS")

    # More than 300 historical claims cannot silently disappear from manager view.
    with app.db() as c:
        for i in range(321):
            day=(dt.date(2026,1,1)+dt.timedelta(days=i)).isoformat()
            c.execute("INSERT INTO movi_pix_declarations(uid,entry_day,slot,expected_cents,created_at) "
                      "VALUES(2,?,'tarde',100,?)",(day,app.now()))
        c.commit()
    first=adm.get(api+"/reviews?page=1&page_size=50")
    older=adm.get(api+"/reviews?page=2&page_size=50")
    assert first.status_code==older.status_code==200
    a=first.json();b=older.json()
    assert a["count"]==323 and b["count"]==323
    assert len(a["items"])==50 and len(b["items"])==50
    assert a["has_next"] is True and a["page"]==1 and b["page"]==2
    assert {x["id"] for x in a["items"]}.isdisjoint({x["id"] for x in b["items"]})
    assert a["pending_count"]==321 and a["confirmed_manually_cents"]==2*expected
    assert a["declared_cents"]==32100+2*expected
    pending=adm.get(api+"/reviews?state=pending&page=1&page_size=75").json()
    confirmed_filter=adm.get(api+"/reviews?state=confirmed_manual").json()
    feb=adm.get(api+"/reviews?month=2026-02&page=2&page_size=10").json()
    assert pending["count"]==321 and len(pending["items"])==75
    assert confirmed_filter["count"]==2 and all(x["review_state"]=="confirmed_manual" for x in confirmed_filter["items"])
    assert feb["count"]==28 and len(feb["items"])==10
    assert adm.get(api+"/reviews?state=invalid").status_code==422
    assert adm.get(api+"/reviews?page=0").status_code==422
    assert adm.get(api+"/reviews?page_size=101").status_code==422
    assert adm.get(api+"/reviews?month=2026-99").status_code==422
    print("08 - 323 deposits: page/filter/count accurate, no overlaps, old items accessible: PASS")

print("8/8 manual Pix statement review tests PASS. All synthetic, no bank/WhatsApp integration.")
