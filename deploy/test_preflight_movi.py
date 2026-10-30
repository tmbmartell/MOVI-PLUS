"""Preflight must be read-only and fail closed on unknown real-world controls."""
import json
import os
import sys
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/"deploy"))
from preflight_movi import run,public_https,legal_info

with tempfile.TemporaryDirectory(prefix="movi_preflight_") as temp:
    root=Path(temp)
    # Source assets, not a real deployment.
    for relative in (
        "app.py","legal_v8.py","finance_flow_v1.py","finance_recurring_v1.py",
        "finance_auto_report_v1.py","pix_deposit_v1.py","static/driver-v8.js","static/gestor-v8.js",
        "static/movi-fluxo-v1.html","static/movi-auto-report-v1.js",
        "static/movi-pix-v1.html","static/movi-pix-admin-v1.html",
        "deploy/novagente-movi-report.service","deploy/novagente-movi-report.timer",
    ):
        path=root/relative;path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text("test",encoding="utf-8")
    (root/"legal_v8.py").write_text(
        'CONTROLLER={"name":"[CONTROLADOR]","cnpj":"[CNPJ]"}\nPARTNERS="[LISTA]"',
        encoding="utf-8")
    before={str(p.relative_to(root)):p.read_bytes() for p in root.rglob("*") if p.is_file()}
    status=run(root,root/"missing-data",{"MOVI_REPORT_PUBLIC_BASE_URL":""})
    assert status["public_release_authorized"] is False
    assert status["checks"]["controller_and_partners"]["status"]=="block"
    assert status["checks"]["https_public_base"]["status"]=="block"
    assert status["checks"]["pix_conciliation"]["status"]=="block"
    assert status["checks"]["offsite_backup_restore"]["status"]=="verify"
    after={str(p.relative_to(root)):p.read_bytes() for p in root.rglob("*") if p.is_file()}
    assert before==after
    print("01 - placeholders fail closed and scan leaves all source files untouched: PASS")

    (root/"legal_v8.py").write_text(
      'CONTROLLER={"name":"Empresa","cnpj":"123","address":"Rua teste",'
      '"contact":"a@b.invalid","dpo_name":"Equipe","dpo_email":"a@b.invalid",'
      '"hosting":"Host","backup_days":"30"}\nPARTNERS="Parceiro autorizado"',
      encoding="utf-8")
    status=run(root,root/"missing-data",{"MOVI_REPORT_PUBLIC_BASE_URL":"https://movi.novagente.com.br"})
    assert status["checks"]["controller_and_partners"]["status"]=="pass"
    assert status["checks"]["https_public_base"]["status"]=="pass"
    assert status["checks"]["legal_review"]["status"]=="verify"
    assert status["public_release_authorized"] is False
    print("02 - locally filled fields never imply legal or HTTPS go-live approval: PASS")

    for bad in ("http://movi.novagente.com.br","https://localhost","https://movi.example",
                "https://movi.test","https://user:pass@movi.example.org","https://movi.example.org/path",
                "https://movi.novagente.com.br:8443","https://movi.novagente.com.br:abc"):
        assert not public_https(bad),bad
    assert public_https("https://movi.novagente.com.br")
    print("03 - rejects obvious bad/placeholder/internal HTTPS domains: PASS")

    assert legal_info("CONTROLLER = {}\nPARTNERS='x'")==({}, "x")
    assert legal_info("CONTROLLER = __import__('os').environ\nPARTNERS='x'")[0] is None
    print("04 - AST legal parsing does not evaluate arbitrary code: PASS")
print("4/4 read-only preflight tests PASS.")
