from pathlib import Path
import hashlib,json,os,subprocess,sys,zipfile
B=Path(__file__).resolve().parent;R=B.parent.parent;T=R/'tools/apk-patch'
JAVA=T/'java21/zulu21.52.203-ca-jre21.0.12.1-win_x64/bin/java.exe'
sys.path[:0]=[str(R/'apk-analysis/deps'),str(R/'apk-analysis/precision-md3e-4.0.1.0')]
from loguru import logger
logger.remove()
from androguard.core.apk import APK
from dex_symbols import Symbols
def run(args):
 p=subprocess.run(list(map(str,args)),capture_output=True,text=True,encoding='utf8',errors='replace');print(p.stdout[-2400:],flush=True)
 if p.stderr:print(p.stderr[-2400:],flush=True)
 p.check_returncode()
def main():
 files=json.loads((B/'inputs.json').read_text('utf8'))
 for label,meta in zip(['old','mod','new'],files):
  apk=R/meta['file'];assert hashlib.sha256(apk.read_bytes()).hexdigest()==meta['sha256']
  index=Symbols()
  with zipfile.ZipFile(apk) as z:
   for name in meta['dex']:index.add(z.read(name),name)
   if not (B/label).exists():
    thin=B/(label+'.apk')
    with zipfile.ZipFile(thin,'w') as w:w.writestr('classes.dex',z.read('classes3.dex'));w.writestr('AndroidManifest.xml',z.read('AndroidManifest.xml'))
    run([JAVA,'-jar',T/'apktool.jar','d','-r','-o',B/label,thin])
  data={k:{**v,'methods':sorted(v['methods']),'fields':sorted(v['fields'])} for k,v in index.classes.items()}
  (B/(label+'-classes.json')).write_text(json.dumps(data,indent=1),'utf8')
  a=APK(str(apk));(B/(label+'-manifest.xml')).write_bytes(a.get_android_manifest_axml().get_xml())
 old=json.loads((B/'old-classes.json').read_text());new=json.loads((B/'new-classes.json').read_text())
 print('Class additions',[x for x in new if x not in old])
 print('Class removals',[x for x in old if x not in new])
 moved=[(k,old[k]['dex'],new[k]['dex']) for k in old.keys()&new.keys() if old[k]['dex']!=new[k]['dex']]
 (B/'moved-classes.json').write_text(json.dumps(moved,indent=2),'utf8');print('Moved classes',len(moved),moved[:10])
if __name__=='__main__':main()
