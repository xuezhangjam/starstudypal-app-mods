from pathlib import Path
import hashlib,json,re,struct,sys,zipfile
B=Path(__file__).resolve().parent; R=B.parent.parent
sys.path[:0]=[str(R/'apk-analysis/deps')]
from loguru import logger
logger.remove()
from androguard.core.apk import APK
FILES=['3.2.1.4原版.apk','星学伴mod-3.2.1.4-全部未下发应用-保留管控提醒.apk','星学伴学生端3.2.1.5原版.apk']
report=[]
for name in FILES:
 p=R/name; a=APK(str(p))
 with zipfile.ZipFile(p) as z:
  dex={n:{'sha256':hashlib.sha256(z.read(n)).hexdigest(),'methods':struct.unpack_from('<I',z.read(n),88)[0]} for n in z.namelist() if re.fullmatch(r'classes\d*\.dex',n)}
 report.append(dict(file=name,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),size=p.stat().st_size,package=a.get_package(),version=a.get_androidversion_name(),code=a.get_androidversion_code(),min=a.get_min_sdk_version(),target=a.get_target_sdk_version(),dex=dex))
with zipfile.ZipFile(R/FILES[0]) as o,zipfile.ZipFile(R/FILES[2]) as n:
 old=set(o.namelist());new=set(n.namelist())
 delta={'added':sorted(new-old),'removed':sorted(old-new),'changed':sorted(k for k in old&new if o.read(k)!=n.read(k))}
(B/'inputs.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf8')
(B/'stock-payload-delta.json').write_text(json.dumps(delta,ensure_ascii=False,indent=2),'utf8')
print(json.dumps(report,ensure_ascii=False,indent=2))
print('Stock delta',json.dumps(delta,ensure_ascii=False))
