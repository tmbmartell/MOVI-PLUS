"""Render compact financial summary as JPG locally, without LLM or network.

Uses built-in ffmpeg drawbox/drawtext, data from confirmed transactions only.
"""
import os,subprocess,tempfile
from pathlib import Path
from finance_agent_conversation_v2 import money

FONT="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
BOLD="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

def render_jpeg(data):
 if not data.get("has_data"):return None
 if not Path(FONT).is_file() or not Path(BOLD).is_file():
  raise RuntimeError("Local JPG font unavailable")
 with tempfile.TemporaryDirectory(prefix="ng-chart-") as folder:
  filters=[]
  def box(x,y,w,h,color):
   filters.append(f"drawbox=x={x}:y={y}:w={w}:h={h}:color={color}:t=fill")
  def label(text,x,y,size=20,color="0x173d30",bold=False):
   filepath=Path(folder)/f"label-{len(filters)}.txt"
   filepath.write_text(str(text).replace("\\n"," ")[:110],encoding="utf-8")
   filters.append(f"drawtext=fontfile={BOLD if bold else FONT}:textfile={filepath}:fontcolor={color}:fontsize={size}:x={x}:y={y}")
  box(0,0,900,705,"0xf5f8f2")
  box(0,0,900,105,"0x173b30")
  label("MOVI+",42,23,36,"white",True)
  label("SEU FLUXO FINANCEIRO  •  "+data["label"].upper(),42,66,16,"0xeac887",False)
  for x,title,val in ((38,"ENTRADAS",data["income"]),(330,"DESPESAS",data["expense"]),(621,"DIFERENÇA",data["balance"])):
   box(x,125,244,122,"white")
   label(title,x+14,144,17,"0x668574",True)
   label(money(val),x+14,181,23,"0x154f35",True)
  label("PARA ONDE FOI SEU DINHEIRO",39,273,24,"0x183d2f",True)
  categories=data.get("categories") or []
  if categories:
   maximum=max(v for _,v in categories)
   for i,(category,value) in enumerate(categories[:5]):
    yy=324+i*64
    label(category[:34],40,yy,17,"0x416a53")
    label(money(value),674,yy,18,"0x173d30",True)
    box(40,yy+30,610,14,"0xe1e9df")
    box(40,yy+30,max(8,round(610*value/maximum)),14,"0x31825b")
  else:
   label("Sem despesas confirmadas neste mês.",40,337,22,"0x657b6d")
  if "scheduled_total" in data:
   label("CONTAS FIXAS PREVISTAS (À PARTE): "+money(data.get("scheduled_total",0)),39,630,14,"0x507259",True)
  box(0,656,900,49,"0xe5efe3")
  label("SOMENTE REGISTROS CONFIRMADOS  •  NÃO É SALDO BANCÁRIO",38,672,15,"0x507259",True)
  outfile=str(Path(folder)/"movi-resumo-financeiro.jpg")
  argv=["/usr/bin/ffmpeg","-hide_banner","-loglevel","error","-nostdin","-y",
   "-f","lavfi","-i","color=c=0xf5f8f2:s=900x705:d=1",
   "-vf",",".join(filters),"-frames:v","1","-update","1","-q:v","3",outfile]
  proc=subprocess.run(argv,capture_output=True,timeout=16,check=False)
  if proc.returncode:
   raise RuntimeError("Local JPG generator failed")
  result=Path(outfile).read_bytes()
  if not result.startswith(b"\xff\xd8\xff") or len(result)>800000:
   raise RuntimeError("Local JPG file invalid")
  return result
