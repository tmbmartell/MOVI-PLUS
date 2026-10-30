"""Search for any driver among thousands without 1000-row hard limit."""
import os
import sys
import tempfile
from pathlib import Path
from fastapi.testclient import TestClient
with tempfile.TemporaryDirectory(prefix="movi_driver_search_") as tmp:
    os.environ["CLUBE_DATA"]=tmp
    sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
    import app
    import pix_deposit_v1
    client=TestClient(app.app,base_url="https://pix-search.invalid")
    assert client.get("/api/admin/pix/drivers").status_code==401
    with app.db() as db:
        phash=app.password_hash("SyntheticPassForSearch2026!")
        db.execute("INSERT INTO users(id,username,phash,role,status,name,created_at,must_change) "
                   "VALUES(1,'synthetic_admin',?,'admin','active','Gestor Teste',?,0)",(phash,app.now()))
        for uid in range(2,4002):
            db.execute("INSERT INTO users(id,username,phash,role,status,name,created_at,must_change) "
                       "VALUES(?, ?, ?,'driver','active',?, ?,0)",
                       (uid,"motorista"+str(uid),phash,"Motorista Teste "+str(uid),app.now()))
        db.commit()
    app.app.dependency_overrides[app.admin]=lambda:{"id":1,"role":"admin"}
    try:
        first=client.get("/api/admin/pix/drivers")
        assert first.status_code==200,first.text
        result=first.json()
        assert result["count"]==4000 and result["more"] is True and len(result["items"])==25
        assert result["items"][0]["id"]==4001
        print("01 - initial driver list bounded to 25 even with 4000 users: PASS")

        for q,identifier in (("motorista3601",3601),("3601",3601),("Motorista Teste 3601",3601)):
            r=client.get("/api/admin/pix/drivers",params={"q":q})
            assert r.status_code==200,r.text
            assert any(x["id"]==identifier for x in r.json()["items"])
        print("02 - driver beyond 1000 accessible by login, display name and exact ID: PASS")

        assert client.get("/api/admin/pix/drivers",params={"q":"%"}).json()["count"]==0
        assert client.get("/api/admin/pix/drivers",params={"q":"_"}).json()["count"]==0
        assert client.get("/api/admin/pix/drivers",params={"q":"a"*61}).status_code==422
        assert client.get("/api/admin/pix/drivers",params={"q":"not-in-list"}).json()["count"]==0
        print("03 - literal wildcard escape, empty search and validation: PASS")

        upd=client.put("/api/admin/pix/driver/3601",json={"monthly_amount":"1550.25","active":True},
                       headers={"X-Requested-With":"NOVAGENTE-V5"})
        assert upd.status_code==200,upd.text
        one=client.get("/api/admin/pix/drivers",params={"q":"3601"}).json()["items"]
        assert len(one)==1 and one[0]["monthly_cents"]==155025
        print("04 - full installment lifecycle for driver beyond initial list: PASS")
    finally:
        app.app.dependency_overrides.clear()
print("4/4 scalable driver search tests PASS. All synthetic.")
