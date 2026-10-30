"""Headless Chrome rendering QA for the MOVI+ monthly dashboard.

Fixtures are synthetic and served over a temporary localhost-only HTTP server.
No MOVI+ app, database, WhatsApp provider or public port is contacted.
"""
import json
import re
import subprocess
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT=Path(__file__).resolve().parent.parent
STATIC=ROOT/"static"
MONTH={
  "month":"2026-10","label":"Outubro/2026","has_data":True,
  "income_cents":580000,"expense_cents":425000,"result_cents":155000,"positive":True,
  "expense_categories":[{"label":"Combustível","amount_cents":145000},{"label":"Moradia","amount_cents":120000}],
  "recurring_commitments_declared":[],"recurring_commitments_total_cents":0,
  "other_monthly_estimates":[],"scheduled_expenses":[{"label":"Seguro do carro","amount_cents":12000}],
  "scheduled_expenses_total_cents":12000,"pending_suggestions":0,
  "notice":"Dados fictícios; somente registros confirmados, não saldo bancário."
}
CONSENT={"enabled":False,"frequency":"weekly","weekday":1,"hour":9,"linked":False,"financial_agent_authorized":False}
RECURRING={"items":[{"id":1,"title":"Seguro do carro","category":"Seguro","amount_cents":12000,
    "due_day":10,"starts":"2026-01","ends":None,"active":True}]}

class Fake(BaseHTTPRequestHandler):
    def log_message(self,*args): pass
    def do_GET(self):
        url=urlparse(self.path).path
        if url in ("/","/meu-fluxo"):
            body=(STATIC/"movi-fluxo-v1.html").read_text(encoding="utf-8")
            probe="""<script>
            window.addEventListener('load',function(){
              setTimeout(function(){
                var root=document.documentElement;
                root.setAttribute('data-movi-loaded',String(!document.querySelector('#content').hidden));
                root.setAttribute('data-movi-width',String(window.innerWidth));
                root.setAttribute('data-movi-overflow',String(root.scrollWidth>window.innerWidth+1));
                root.setAttribute('data-movi-income',document.querySelector('#income').textContent);
              },1000);
            });
            </script>"""
            body=body.replace("</body>",probe+"</body>")
            content=body.encode("utf-8");type_="text/html;charset=utf-8"
        elif url.startswith("/assets/"):
            file=STATIC/url[len("/assets/"):]
            if file.is_file() and file.name in ("movi-fluxo-v1.js","movi-auto-report-v1.js"):
                content=file.read_bytes();type_="text/javascript"
            else:
                self.send_error(404);return
        elif url=="/api/finance/flow":
            content=json.dumps(MONTH,ensure_ascii=False).encode();type_="application/json"
        elif url=="/api/finance/recurring":
            content=json.dumps(RECURRING).encode();type_="application/json"
        elif url=="/api/finance/auto-report":
            content=json.dumps(CONSENT).encode();type_="application/json"
        else:
            self.send_error(404);return
        self.send_response(200)
        self.send_header("Content-Type",type_)
        self.send_header("Content-Length",str(len(content)))
        self.send_header("Cache-Control","no-store")
        self.end_headers();self.wfile.write(content)

def smoke(width,port):
    with tempfile.TemporaryDirectory(prefix="movi-chrome-qa-") as folder:
        cmd=["/usr/local/bin/google-chrome","--headless=new","--no-sandbox",
             "--disable-dev-shm-usage","--disable-gpu","--disable-background-networking",
             "--no-first-run","--no-default-browser-check", "--user-data-dir="+folder,
             "--window-size="+str(width)+",900","--virtual-time-budget=3300",
             "--dump-dom",f"http://127.0.0.1:{port}/meu-fluxo?month=2026-10"]
        r=subprocess.run(cmd,capture_output=True,text=True,timeout=30,check=False)
    if r.returncode:
        raise AssertionError("Headless Chrome did not finish: "+str(r.returncode))
    text=r.stdout
    attrs={name:re.search(r'data-movi-'+name+r'="([^"]*)"',text)
           for name in ("loaded","width","overflow","income")}
    assert all(attrs.values()),"Missing browser rendering probe"
    attrs={k:v.group(1) for k,v in attrs.items()}
    assert attrs["loaded"]=="true", "Financial content failed to render"
    assert attrs["overflow"]=="false", "Horizontal overflow detected"
    assert "5.800" in attrs["income"],"Financial figure not populated"
    assert "Seguro do carro" in text,"Recurring expenses list failed"
    assert "Quero receber o relatório" in text,"Auto report options missing"
    print(f"Chrome viewport requested {width}px, actual {attrs['width']}px: PASS. "
          "Loaded all widgets, no overflow, correct fake value.")

def main():
    server=ThreadingHTTPServer(("127.0.0.1",0),Fake)
    th=threading.Thread(target=server.serve_forever,daemon=True);th.start()
    try:
        for width in (390,768,1366):
            smoke(width,server.server_address[1])
    finally:
        server.shutdown();server.server_close()
    print("3/3 headless Chrome web-dashboard rendering tests PASS; only fake data.")

if __name__=="__main__":
    main()
