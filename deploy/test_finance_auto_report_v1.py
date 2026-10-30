"""No-network QA of opt-in scheduled WhatsApp financial reports."""
import datetime as dt
import os
import re
import sys
import tempfile
from zoneinfo import ZoneInfo
from fastapi.testclient import TestClient

with tempfile.TemporaryDirectory(prefix="movi_auto_report_") as tmp:
    os.environ["CLUBE_DATA"]=tmp
    os.environ.pop("MOVI_REPORT_DELIVERY_ENABLED",None)
    os.environ.pop("MOVI_REPORT_PUBLIC_BASE_URL",None)
    sys.path.insert(0,os.path.dirname(os.path.dirname(__file__)))
    import app
    import finance_auto_report_v1 as ar
    import finance_agent_pilot_v1 as pilot
    import finance_agent_chart_v1 as chart
    from finance_agent_waha_v1 import link_hash

    client=TestClient(app.app,base_url="https://movi-qa.local")
    H={"X-Requested-With":"NOVAGENTE-V5"}
    pref="/api/finance/auto-report"
    settings={"enabled":True,"frequency":"weekly","weekday":1,"hour":9}
    fake_chat="5511998877665@c.us"
    sent=[]
    pilot.waha=lambda cfg,method,path,body=None: (
        sent.append({"path":path,"body":body}),200)
    chart.render_jpeg=lambda data:b"\xff\xd8\xfftest-image\xff\xd9"

    with app.db() as c:
        for uid,role in ((1,"admin"),(2,"driver"),(3,"driver")):
            c.execute("INSERT INTO users(id,username,phash,role,status,name,created_at,must_change) VALUES(?,?,?,?,?,?,?,0)",
                (uid,f"autotest{uid}","test",role,"active",f"Fake {uid}",app.now()))
        # Pilot transport stays limited to user 2, whose phone link has been proven separately.
        c.execute("INSERT INTO finance_agent_wa_pilot(id,uid,enabled,updated_at) VALUES(1,2,1,?)",(app.now(),))
        c.execute("INSERT INTO finance_agent_consent(uid,enabled,media_ai,trends,offers,text_ai,changed_at) "
                  "VALUES(2,1,0,0,0,0,?)",(app.now(),))
        c.execute("INSERT INTO finance_agent_wa_config(id,key_blob,enabled,updated_at) VALUES(1,?,1,?)",
                  (app.enc({"key":"fake-hmac-secret"}),app.now()))
        c.execute("INSERT INTO whatsapp_bridge_config(id,encrypted,updated_at,actor) VALUES(1,?,?,?)",
                  (app.enc({"base_url":"http://127.0.0.1:18182","session":"clube-motorista",
                            "api_key":"test-only-key"}),app.now(),1))
        c.execute("INSERT INTO finance_agent_wa_links(phone_hash,uid,encrypted_chat,linked_at) VALUES(?,?,?,?)",
                  (link_hash(fake_chat),2,app.enc({"chat":fake_chat}),app.now()))
        for kind,category,cents,date in (
          ("income","APLICATIVO",200000,"2026-11-02"),
          ("expense","Combustível",30000,"2026-11-02"),
          ("income","APLICATIVO",180000,"2026-10-19"),
          ("expense","Alimentação",20000,"2026-10-20")
        ):
            c.execute("INSERT INTO transactions(uid,kind,category,amount_cents,entry_date,note,at) "
                      "VALUES(2,?,?,?,?,?,?)",(kind,category,cents,date,"",app.now()))
        c.commit()

    assert client.get(pref).status_code==401
    assert client.put(pref,json=settings,headers=H).status_code==401
    assert client.get("/api/admin/finance/auto-report").status_code==401
    print("01 - reports and admin controls require login: PASS")

    driver={"id":2,"role":"driver","name":"Fake 2","status":"active","must_change":0}
    app.app.dependency_overrides[app.driver]=lambda:driver
    assert client.get(pref).json()["enabled"] is False
    assert client.get(pref).json()["linked"] is True
    for payload in (
        {**settings,"weekday":8},
        {**settings,"weekday":True},
        {**settings,"hour":22},
        {**settings,"frequency":"daily"},
        {**settings,"enabled":"true"},
        {**settings,"unexpected":True},
    ):
        assert client.put(pref,json=payload,headers=H).status_code==422
    assert client.put(pref,json=settings).status_code==403
    good=client.put(pref,json=settings,headers=H)
    assert good.status_code==200,good.text
    assert client.get(pref).json()["enabled"] is True
    print("02 - separate driver opt-in, validation and CSRF protection: PASS")

    instant=dt.datetime(2026,11,2,13,0,tzinfo=dt.timezone.utc) # 9 AM Porto Velho Monday
    assert ar.run_due(instant)["due"]==1
    assert ar.run_due(instant,dry_run=False)["sent"]==0
    assert sent==[]
    admin={"id":1,"role":"admin","name":"Fake Admin","status":"active","must_change":0}
    app.app.dependency_overrides[app.admin]=lambda:admin
    assert client.get("/api/admin/finance/auto-report").json()["armed"] is False
    assert client.put("/api/admin/finance/auto-report",json={"armed":True}).status_code==403
    assert client.put("/api/admin/finance/auto-report",json={"armed":True},headers=H).status_code==200
    assert ar.run_due(instant,dry_run=False)["sent"]==0
    print("03 - admin switch and environment prevent accidental sends: PASS")

    os.environ["MOVI_REPORT_DELIVERY_ENABLED"]="1"
    os.environ["MOVI_REPORT_PUBLIC_BASE_URL"]="http://unsecured.example"
    assert ar.run_due(instant,dry_run=False)["sent"]==0
    os.environ["MOVI_REPORT_PUBLIC_BASE_URL"]="https://movi.example"
    assert ar.run_due(instant,dry_run=True)["would_send"]==1
    assert sent==[]
    print("04 - HTTPS domain validated and dry run never sends: PASS")

    result=ar.run_due(instant,dry_run=False)
    assert result["sent"]==1,result
    assert len(sent)==2,sent
    assert sent[0]["path"]=="/api/sendText"
    assert sent[1]["path"]=="/api/sendImage"
    assert sent[0]["body"]["chatId"]==sent[1]["body"]["chatId"]==fake_chat
    text=sent[0]["body"]["text"]
    assert "2.000,00" in text and "300,00" in text
    assert "https://movi.example/relatorio/" in text
    assert "não" in text.lower()
    assert ar.run_due(instant,dry_run=False)["sent"]==0
    assert len(sent)==2
    with app.db() as c:
        assert c.execute("SELECT COUNT(*) FROM movi_report_deliveries").fetchone()[0]==1
    print("05 - signed pilot chat receives one text and chart, no duplicates: PASS")

    link=re.search(r"https://movi\.example(/relatorio/[A-Za-z0-9_-]+)",text).group(1)
    assert client.get(link).status_code==401
    app.app.dependency_overrides.clear()
    client.cookies.set("clube_session","driver2-token")
    with app.db() as c:
        c.execute("INSERT INTO sessions(hash,uid,expires) VALUES(?,?,?)",
                  (app.sha("driver2-token"),2,app.stamp()+3600))
        c.commit()
    linked=client.get(link,follow_redirects=False)
    assert linked.status_code==303 and linked.headers["location"]=="/meu-fluxo?month=2026-11"
    client.cookies.set("clube_session","driver3-token")
    with app.db() as c:
        c.execute("INSERT INTO sessions(hash,uid,expires) VALUES(?,?,?)",
                  (app.sha("driver3-token"),3,app.stamp()+3600))
        c.commit()
    assert client.get(link).status_code==404
    with app.db() as c:
        c.execute("UPDATE movi_report_links SET expires_at=1")
        c.commit()
    client.cookies.set("clube_session","driver2-token")
    assert client.get(link).status_code==404
    print("06 - 1h private link requires original logged-in driver and expires: PASS")

    app.app.dependency_overrides[app.driver]=lambda:driver
    changed=client.put(pref,json={**settings,"enabled":False},headers=H)
    assert changed.status_code==200 and not changed.json()["enabled"]
    next_week=instant+dt.timedelta(days=7)
    assert ar.run_due(next_week,dry_run=False)["sent"]==0
    assert len(sent)==2
    print("07 - explicit opt-out blocks future report delivery: PASS")

    # Separate on-demand consent from financial-agent consent: disabled agent blocks enabling.
    with app.db() as c:
        c.execute("UPDATE finance_agent_consent SET enabled=0 WHERE uid=2")
        c.commit()
    assert client.put(pref,json=settings,headers=H).status_code==403
    with app.db() as c:
        c.execute("UPDATE finance_agent_consent SET enabled=1 WHERE uid=2")
        c.execute("DELETE FROM finance_agent_wa_links WHERE uid=2")
        c.commit()
    assert client.put(pref,json=settings,headers=H).status_code==409
    assert ar.run_due(next_week,dry_run=False)["sent"]==0
    print("08 - revoked agent permission and lost phone link prevent sends: PASS")

    with app.db() as c:
        c.execute("INSERT INTO finance_agent_wa_links(phone_hash,uid,encrypted_chat,linked_at) VALUES(?,?,?,?)",
                  (link_hash(fake_chat),2,app.enc({"chat":fake_chat}),app.now()))
        c.commit()
    monthly={"enabled":True,"frequency":"monthly","weekday":1,"hour":9}
    assert client.put(pref,json=monthly,headers=H).status_code==200
    month_day=dt.datetime(2026,11,1,13,0,tzinfo=dt.timezone.utc)
    assert ar.run_due(month_day,dry_run=True)["due"]==1
    assert ar.run_due(month_day+dt.timedelta(days=1),dry_run=True)["due"]==0
    assert ar.run_due(month_day,dry_run=False)["sent"]==1
    assert "Outubro/2026" in sent[-2]["body"]["text"]
    assert len(sent)==4
    assert ar.run_due(month_day,dry_run=False)["sent"]==0
    print("09 - monthly sends previous month only on day 1, at most once: PASS")

    # Reset to stop all real-user traffic; no network was used in these tests.
    assert all(x["body"]["chatId"]==fake_chat for x in sent)
    with app.db() as c:
        assert c.execute("SELECT COUNT(*) FROM finance_agent_wa_pilot_outbox").fetchone()[0]==4
    print("10 - synthetic transport only, no other contacts and traceable outbox: PASS")
    os.environ.pop("MOVI_REPORT_DELIVERY_ENABLED",None)
    os.environ.pop("MOVI_REPORT_PUBLIC_BASE_URL",None)

print("10/10 auto-report tests passed. Synthetic driver, fake WhatsApp sender; no live messages.")
