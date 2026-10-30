#!/usr/bin/env python3
"""MOVI+ release preflight; read-only, no secrets, no HTTP calls or deployments.

Result is deliberately conservative: unknown/manual evidence blocks public release.
The checklist percentage is tracked separately in GitHub issue #3.
"""
import argparse
import ast
import datetime as dt
import json
import os
import re
import sqlite3
from pathlib import Path
from urllib.parse import urlparse

REQUIRED_CODE = (
    "app.py", "legal_v8.py", "finance_flow_v1.py",
    "finance_recurring_v1.py", "finance_auto_report_v1.py",
    "static/driver-v8.js", "static/gestor-v8.js",
    "static/movi-fluxo-v1.html", "static/movi-auto-report-v1.js",
    "deploy/novagente-movi-report.service", "deploy/novagente-movi-report.timer",
)

def legal_info(source):
    try:
        body = ast.parse(source)
    except (SyntaxError, UnicodeError):
        return None, None
    fields={}
    for stmt in body.body:
        if isinstance(stmt,ast.Assign) and len(stmt.targets)==1:
            target=stmt.targets[0]
            if isinstance(target,ast.Name) and target.id in ("CONTROLLER","PARTNERS"):
                try: fields[target.id]=ast.literal_eval(stmt.value)
                except (ValueError,TypeError,SyntaxError):pass
    return fields.get("CONTROLLER"),fields.get("PARTNERS")

def has_placeholder(value):
    if not isinstance(value,str) or not value.strip():
        return True
    return bool(re.search(r"\[[^\]]+\]|TODO|PREENCHER|SUBSTITUIR",value,re.I))

def public_https(value):
    try:
        parsed=urlparse(value or "")
        port=parsed.port
        if (parsed.scheme!="https" or not parsed.hostname or port not in (None,443)
            or parsed.username or parsed.password or parsed.path not in ("","/")
            or parsed.query or parsed.fragment):
            return False
        host=parsed.hostname.lower()
        if host in ("localhost","127.0.0.1") or host.endswith(
                (".local",".test",".internal",".example",".invalid")):
            return False
        return True
    except ValueError:
        return False

def check_db(data):
    path=data/"v5.sqlite3"
    if not path.is_file():
        return {"status":"verify","detail":"Banco de produção não foi fornecido ao preflight."}
    # Read-only SQLite; never import app or initialize tables.
    try:
        uri=path.resolve().as_uri()+"?mode=ro"
        con=sqlite3.connect(uri,uri=True,timeout=3)
        try:
            integrity=con.execute("PRAGMA quick_check(1)").fetchone()[0]
        finally:con.close()
        if integrity!="ok":
            return {"status":"block","detail":"Integridade SQLite não confirmada."}
        return {"status":"pass","detail":"SQLite quick_check: ok."}
    except (sqlite3.Error,OSError,ValueError):
        return {"status":"block","detail":"Leitura/checagem SQLite falhou."}

def run(root,data,environ=None):
    env=environ if environ is not None else os.environ
    root=Path(root).resolve();data=Path(data).resolve()
    checks={}
    def add(key,status,detail):
        checks[key]={"status":status,"detail":detail}
    missing=[p for p in REQUIRED_CODE if not (root/p).is_file()]
    add("release_code","pass" if not missing else "block",
        "Todos os módulos de release existem." if not missing
        else "Arquivos não encontrados: "+", ".join(missing))
    try:
        content=(root/"legal_v8.py").read_text(encoding="utf-8")
        controller,partners=legal_info(content)
        invalid=(not isinstance(controller,dict) or not controller or
                 any(has_placeholder(v) for v in controller.values()) or
                 has_placeholder(partners))
        add("controller_and_partners","block" if invalid else "pass",
            "Controlador, encarregado, prazos e parceiros exigem dados reais e revisão."
            if invalid else "Campos preenchidos; revisão jurídica independente ainda exigida.")
    except OSError:
        add("controller_and_partners","block","Termos V8 ausentes.")
    add("legal_review","verify","Aprovação jurídica documentada precisa ser fornecida pelo responsável.")
    base=env.get("MOVI_REPORT_PUBLIC_BASE_URL","")
    add("https_public_base","pass" if public_https(base) else "block",
        "URL HTTPS configurada, mas DNS, certificado e acesso externo ainda exigem prova."
        if public_https(base) else "Endereço HTTPS público válido não configurado.")
    add("domain_external_test","verify","DNS, certificado TLS e login em rede externa não foram testados.")
    add("driver_real_phone","verify","Homologação de uso no aparelho físico ainda não comprovada.")
    add("waha_roundtrip","verify","Vínculo, ida/volta e imagem WhatsApp real requerem piloto autorizado.")
    add("admin_mfa","verify","Ativação de MFA para contas administrativas reais requer verificação sem expor códigos.")
    add("offsite_backup_restore","verify","Backup criptografado fora da VPS e restauração de teste não comprovados.")
    add("pix_conciliation","block","Pag.me/Pix real ainda requer contrato, credenciais, webhook e homologação financeira.")
    add("security_load_test","verify","Pentest, teste de carga e auditoria de segredos do GitHub pendentes.")
    add("repository_private_status","verify","Visibilidade pública/privada e histórico de segredos exigem revisão.")
    add("sqlite_integrity",**check_db(data))
    # Even a perfect local scan cannot prove manual controls were completed.
    blocked=[k for k,v in checks.items() if v["status"]=="block"]
    needs_evidence=[k for k,v in checks.items() if v["status"]=="verify"]
    return {"product":"MOVI+","mode":"read_only_preflight","public_release_authorized":False,
            "check_count":len(checks),"blocked":blocked,"requires_external_evidence":needs_evidence,
            "checks":checks,"note":"Relatório informativo; nunca ativa serviços nem substitui aprovação humana."}

def main():
    parser=argparse.ArgumentParser(description="MOVI+ conservador: apenas leitura")
    parser.add_argument("--root",default=str(Path(__file__).resolve().parent.parent))
    parser.add_argument("--data",default=os.environ.get("CLUBE_DATA","data"))
    args=parser.parse_args()
    print(json.dumps(run(args.root,args.data),ensure_ascii=False,indent=2))

if __name__=="__main__":
    main()
