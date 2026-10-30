"""CNPJ Pix deposit requests: synthetic data; no actual transfer or WhatsApp network."""
import datetime as dt
import os
import sys
import tempfile
from zoneinfo import ZoneInfo
from fastapi.testclient import TestClient

with tempfile.TemporaryDirectory(prefix="movi_pix_qa_") as folder:
    os.environ["CLUBE_DATA"]=folder
    os.environ.pop("MOVI_PIX_REMINDERS_ENABLED",None)
    sys.path.insert(0,os.path.dirname(os.path.dirname(__file__)))
    import app
    import pix_deposit_v1 as pix
    import finance_agent_pilot_v1 as pilot
    import legal_v8
    from finance_agent_waha_v1 import link_hash
    from whatsapp_bridge_v5 import ensure_table

    client=TestClient(app.app,base_url="https://pix-test.invalid")
    h={"X-Requested-With":"NOVAGENTE-V5"}
    key="12.345.678/0001-95" # synthetic CNPJ checksum fixture, no live send
    form={"key":key,"recipient_name":"","bank_verified":False,"enabled":False}
    assert pix.pix_cnpj(key)=="12345678000195"
    for invalid in ("00.000.000/0000-00","12.345.678/0001-96","123","a"*14):
        try:pix.pix_cnpj(invalid)
        except Exception as e:assert e.status_code==422
        else:raise AssertionError("CNPJ erroneously valid")
    print("01 - synthetic Pix CNPJ checksum valid, invalid numbers rejected: PASS")

    assert client.get("/api/admin/pix").status_code==401
    assert client.get("/api/driver/pix/day").status_code==401
    assert client.put("/api/admin/pix",json=form,headers=h).status_code==401
    print("02 - anonymous Pix key/setup requests denied: PASS")

    with app.db() as c:
        for uid,role in ((1,"admin"),(2,"driver"),(3,"driver")):
            c.execute("INSERT INTO users(id,username,phash,role,status,name,created_at,must_change)"
                      "VALUES(?,?,?,?,?,?,?,0)",(uid,"pixqa"+str(uid),app.password_hash("QaPassword2026!"),role,"active","Teste",app.now()))
        ensure_table(c)
        c.commit()
    admin={"id":1,"role":"admin","name":"Gestor"}
    driver={"id":2,"role":"driver","name":"Teste"}
    app.app.dependency_overrides[app.admin]=lambda:admin

    res=client.put("/api/admin/pix",json=form,headers=h)
    assert res.status_code==200,res.text
    assert res.json()["enabled"] is False
    assert client.get("/api/admin/pix").json()["key"]=="12345678000195"
    assert client.put("/api/admin/pix",json={**form,"enabled":True},headers=h).status_code in (409,422)
    assert client.put("/api/admin/pix",json={**form,"recipient_name":"Recebedor Teste","enabled":True},headers=h).status_code==409
    # Any change in recipient or key requires a separate saved-but-disabled step.
    assert client.put("/api/admin/pix",json={**form,"recipient_name":"Recebedor Teste","bank_verified":True,"enabled":True},headers=h).status_code==409
    assert client.put("/api/admin/pix",json={**form,"recipient_name":"Recebedor Teste"},headers=h).status_code==200
    assert client.put("/api/admin/pix",json={**form,"recipient_name":"Recebedor Teste","bank_verified":True,"enabled":True},headers=h).status_code==200
    assert client.put("/api/admin/pix/driver/2",json={"monthly_amount":"1500.00","active":True},headers=h).status_code==200
    default_schedule=client.get("/api/admin/pix/schedule")
    assert default_schedule.status_code==200
    assert default_schedule.json()["hours"]=={"manha":9,"tarde":14,"noite":19}
    assert client.put("/api/admin/pix/schedule",json={"manha":5,"tarde":14,"noite":19},headers=h).status_code==422
    assert client.put("/api/admin/pix/schedule",json={"manha":True,"tarde":14,"noite":19},headers=h).status_code==422
    changed=client.put("/api/admin/pix/schedule",json={"manha":8,"tarde":15,"noite":20},headers=h)
    assert changed.status_code==200,changed.text
    assert changed.json()["delivery_activated"] is False
    assert client.get("/api/admin/pix/schedule").json()["hours"]=={"manha":8,"tarde":15,"noite":20}
    restored=client.put("/api/admin/pix/schedule",json={"manha":9,"tarde":14,"noite":19},headers=h)
    assert restored.status_code==200
    assert client.get("/gestao/pix").status_code==200
    assert "Depósitos via Pix" in client.get("/gestao/pix").text
    print("03 - admin stores key encrypted, enables only with bank-attestation + recipient name: PASS")

    app.app.dependency_overrides[app.driver]=lambda:driver
    today=dt.datetime.now(ZoneInfo("America/Porto_Velho")).date()
    oct_result=client.get("/api/driver/pix/day?date=2026-10-30")
    assert oct_result.status_code==200,oct_result.text
    j=oct_result.json()
    assert j["pix_key"]=="12345678000195"
    assert j["recipient_name_configured"]=="Recebedor Teste"
    assert len(j["slots"])==3
    assert sum(s["amount_cents"] for s in j["slots"])==j["slots"][0]["amount_cents"]+j["slots"][1]["amount_cents"]+j["slots"][2]["amount_cents"]
    assert all(key.replace(".","").replace("/","").replace("-","") in s["message"] for s in j["slots"])
    assert all("confirma" in s["message"].lower() or "banco" in s["message"].lower() for s in j["slots"])
    assert all("Favorecido informado pelo Clube: Recebedor Teste" in s["message"] for s in j["slots"])
    assert client.get("/meu-pix").status_code==200
    print("04 - three daily requests include validated Pix key and exact planned values: PASS")

    assert client.get("/api/driver/pix/day?date=2026-02-30").status_code==422
    assert client.post("/api/driver/pix/declare",json={"date":"2027-02-01","slot":"manha"},headers=h).status_code==422
    if today.isoformat()=="2026-10-30":
        declaring=client.post("/api/driver/pix/declare",json={"date":"2026-10-30","slot":"manha"},headers=h)
    else:
        declaring=client.post("/api/driver/pix/declare",json={"date":today.isoformat(),"slot":"manha"},headers=h)
    assert declaring.status_code==200,declaring.text
    assert declaring.json()["status"]=="declared" and declaring.json()["verified_by_bank"] is False
    duplicate=client.post("/api/driver/pix/declare",json={"date":today.isoformat(),"slot":"manha"},headers=h)
    assert duplicate.status_code==200 and duplicate.json()["duplicate"] is True
    with app.db() as c:
        assert c.execute("SELECT COUNT(*) FROM movi_pix_declarations").fetchone()[0]==1
        assert c.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]==0
    print("05 - driver declaration idempotent, never books actual bank receipt or ledger transaction: PASS")

    driver["id"]=3
    assert client.get("/api/driver/pix/day").status_code==409
    assert client.get("/api/admin/pix/declarations").status_code==200 # admin override is separate
    driver["id"]=2
    print("06 - driver 3 cannot inherit driver 2 installment or Pix instructions: PASS")

    out=[]
    pilot.send_once=lambda uid,chat,event_id,text:(out.append((uid,chat,event_id,text)) or True)
    current_month=today.strftime("%Y-%m")
    sample=dt.datetime(today.year,today.month,today.day,18,0,tzinfo=dt.timezone.utc) # 14h Porto Velho, tarde
    due=pix.run_notice(instant=sample,dry_run=True)
    assert due["due"]==0 and not out
    assert client.put("/api/driver/pix/notice-consent",json={"enabled":True},headers=h).status_code==409
    print("07 - reminders OFF without opt-in and proven WhatsApp link: PASS")

    from finance_agent_waha_v1 import link_hash
    whatsapp="5511998765432@c.us"
    with app.db() as c:
        c.execute("INSERT INTO finance_agent_consent(uid,enabled,media_ai,trends,offers,text_ai,changed_at) "
                  "VALUES(2,1,0,0,0,0,?)",(app.now(),))
        c.execute("INSERT INTO finance_agent_wa_pilot(id,uid,enabled,updated_at) VALUES(1,2,1,?)",(app.now(),))
        c.execute("INSERT INTO finance_agent_wa_links(phone_hash,uid,encrypted_chat,linked_at) VALUES(?,?,?,?)",
                  (link_hash(whatsapp),2,app.enc({"chat":whatsapp}),app.now()))
        c.execute("INSERT INTO finance_agent_wa_config(id,key_blob,enabled,updated_at) VALUES(1,?,1,?)",
                  (app.enc({"key":"synthetic_hmac_secret"}),app.now()))
        c.execute("INSERT INTO whatsapp_bridge_config(id,encrypted,updated_at,actor) VALUES(1,?,?,?)",
                  (app.enc({"base_url":"http://127.0.0.1:18182","session":"clube-motorista","api_key":"synthetic"}),app.now(),1))
        legal_v8.record(c,2,{k:True for k,_ in legal_v8.REQUIRED},{k:False for k,_ in legal_v8.OPTIONAL},"qa")
        c.commit()
    enabled=client.put("/api/driver/pix/notice-consent",json={"enabled":True},headers=h)
    assert enabled.status_code==200,enabled.text
    assert pix.run_notice(instant=sample,dry_run=False)["sent"]==0
    assert not out
    print("08 - explicit driver consent still cannot bypass server's OFF delivery flag: PASS")

    os.environ["MOVI_PIX_REMINDERS_ENABLED"]="1"
    sent=pix.run_notice(instant=sample,dry_run=False)
    assert sent["sent"]==1,sent
    assert len(out)==1 and out[0][1]==whatsapp and "12345678000195" in out[0][3]
    # Morning was declared paid already: never remind again on that slot.
    morning=pix.run_notice(instant=sample-dt.timedelta(hours=5),dry_run=False)
    assert morning["sent"]==0 and len(out)==1
    assert pix.run_notice(instant=sample,dry_run=False)["sent"]==0 and len(out)==1
    print("09 - synthetic send one eligible turn only, skips declared morning and prevents retries: PASS")

    assert client.put("/api/driver/pix/notice-consent",json={"enabled":False},headers=h).status_code==200
    next_day=sample+dt.timedelta(days=1)
    assert pix.run_notice(instant=next_day,dry_run=False)["sent"]==0
    assert len(out)==1
    print("10 - driver can revoke reminder consent before next day: PASS")

    admin_set=client.put("/api/admin/pix",json={"key":"00.000.000/0001-91","recipient_name":"Outro Teste",
      "bank_verified":False,"enabled":False},headers=h)
    assert admin_set.status_code==200,admin_set.text
    assert client.get("/api/driver/pix/day").status_code==409
    assert client.get("/api/driver/pix/notice-consent").json()["enabled"] is False
    print("11 - recipient key change revokes approval and blocks driver access: PASS")

    os.environ.pop("MOVI_PIX_REMINDERS_ENABLED",None)
print("11/11 PIX key and manual-deposit tests PASS; no external messages or bank calls.")
