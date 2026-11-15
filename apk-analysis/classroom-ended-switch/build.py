"""Keep native group switching available after a live discussion ends."""
from pathlib import Path
import hashlib,json,os,re,shutil,subprocess,zipfile
B=Path(__file__).resolve().parent;R=B.parent.parent;T=R/'tools/apk-patch'
JAVA=T/'java21/zulu21.52.203-ca-jre21.0.12.1-win_x64/bin/java.exe'
SOURCE=R/'学生端课堂-3.2.2.0-v8功能迁移.apk'
DEST=R/'学生端课堂-3.2.2.0-讨论结束后换组.apk'
EXPECTED='1a14c14cebfbd1a1e882c36d293a29e115ce6ef3550af4cceeda0b9947430850'
FILE='com/nice/room/ui/roomlive/fragment/discussion/DiscussionFragment.smali'
OWNER='L'+FILE[:-6]+';'
PAT=re.compile(r'^\.method ([^\n]+)\n.*?^\.end method',re.M|re.S)
def long(p):return Path('\\\\?\\'+str(p.resolve()))
def write(p,s):
 p=long(p);p.parent.mkdir(parents=True,exist_ok=True);q=p.with_name(p.name+'.tmp');q.write_text(s,'utf8');os.replace(q,p)
def run(args):
 p=subprocess.run(list(map(str,args)),capture_output=True,text=True,encoding='utf8',errors='replace')
 if p.stdout:print(p.stdout[-3500:],flush=True)
 if p.stderr:print(p.stderr[-2500:],flush=True)
 p.check_returncode()
def clone(a,b):
 for p in long(a).rglob('*'):
  f=p.relative_to(long(a))
  if f.parts[0] in ['build','dist']:continue
  q=long(b)/f
  if p.is_dir():q.mkdir(parents=True,exist_ok=True)
  elif not q.exists():q.parent.mkdir(parents=True,exist_ok=True);os.link(p,q)
def methods(s):return {m[1].split()[-1]:m[0] for m in PAT.finditer(s)}
def main():
 assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==EXPECTED
 cache=R/'apk-analysis/classroom-migration-3.2.2.0';use_cache=False
 if (cache/'classes4-patch.apk').exists():
  with zipfile.ZipFile(SOURCE) as z,zipfile.ZipFile(cache/'classes4-patch.apk') as c:use_cache=z.read('classes4.dex')==c.read('classes.dex')
 if use_cache:base=cache/'work4'
 else:
  base=B/'base4'
  if not base.exists():
   with zipfile.ZipFile(SOURCE) as z,zipfile.ZipFile(B/'base4.apk','w') as w:w.writestr('classes.dex',z.read('classes4.dex'));w.writestr('AndroidManifest.xml',z.read('AndroidManifest.xml'))
   run([JAVA,'-jar',T/'apktool.jar','d','-r','-o',base,B/'base4.apk'])
 clone(base,B/'work4');s=(long(base/'smali')/FILE).read_text('utf8');original=methods(s);changes=[]
 def edit(key,fn):
  nonlocal s
  m=next(m for m in PAT.finditer(s) if m[1].split()[-1]==key);new=fn(m[0]);assert new!=m[0];s=s[:m.start()]+new+s[m.end():];changes.append(key)
 def refresh(body):
  needle='    check-cast v0, Lcom/nice/room/databinding/FragmentDiscussionBinding;';assert body.count(needle)==1
  code='''
    iget-object v1, v0, Lcom/nice/room/databinding/FragmentDiscussionBinding;->tvSwitchGroup:Lcom/hailiang/component/shape/GradientTextView;
    const/4 v2, 0x0
    invoke-virtual {v1, v2}, Lcom/hailiang/component/shape/GradientTextView;->setVisibility(I)V
'''
  return body.replace(needle,needle+'\n'+code,1)
 edit('modRefreshEndedTools()V',refresh)
 def chooser(body):
  # Teacher-assigned groups retain their active-discussion guard. Once this
  # attached live discussion is ENDED, use the same original group list/route.
  needle='    if-ne v0, v1, :cond_0\n';assert body.count(needle)==1
  code='''
    invoke-direct {p0}, OWNER->modEndedWriteAllowed()Z
    move-result v0
    if-nez v0, :cond_0
'''.replace('OWNER',OWNER)
  return body.replace(needle,needle+code,1)
 edit('changeGroup()V',chooser)
 def success(body):
  needle='    sget-object p0, Lkotlin/Unit;->INSTANCE:Lkotlin/Unit;'
  # There are separate failure and success returns. Only restore ended tools
  # after the native successful callback updated groupId and subscriptions.
  last=body.rfind(needle);assert last>=0 and body[:last].count('->publishJoinGroup(JJ)V')==1
  return body[:last]+'    invoke-direct {p0}, '+OWNER+'->modRefreshEndedTools()V\n\n'+body[last:]
 key='changeGroup$lambda$31$lambda$30(Lcom/nice/room/ui/roomlive/fragment/discussion/DiscussionFragment;Ljava/util/List;ILcom/hailiang/xxb/room/server/entity/discussion/DiscussionGroupInfo;Z)Lkotlin/Unit;'
 edit(key,success)
 write(B/'work4/smali'/FILE,s);write(B/'changes.json',json.dumps(changes,indent=2))
 out=B/'classes4-patch.apk';run([JAVA,'-jar',T/'apktool.jar','b',B/'work4','-o',out])
 unsigned=B/'classroom-ended-switch-unsigned.apk'
 def signature(k):return k.startswith('META-INF/') and k.upper().endswith(('.MF','.SF','.RSA','.DSA','.EC'))
 with zipfile.ZipFile(SOURCE) as z,zipfile.ZipFile(out) as c,zipfile.ZipFile(unsigned,'w') as w:
  for info in z.infolist():
   if not signature(info.filename):w.writestr(info,c.read('classes.dex') if info.filename=='classes4.dex' else z.read(info.filename))
 stage=Path(os.environ['LOCALAPPDATA'])/'CodexBuilds/classroom-ended-switch';stage.mkdir(parents=True,exist_ok=True);shutil.copyfile(unsigned,stage/unsigned.name)
 signed=stage/'signed';signed.mkdir(exist_ok=True);result=signed/'classroom-ended-switch-aligned-signed.apk';result.unlink(missing_ok=True)
 run([JAVA,'-jar',T/'uber-apk-signer.jar','-a',stage/unsigned.name,'-o',signed,'--ks',T/'signing/classroom-mod.jks','--ksAlias','classroommod','--ksPass','android','--ksKeyPass','android'])
 shutil.copyfile(result,DEST)
 report={'input':SOURCE.name,'input_sha256':EXPECTED,'output':DEST.name,'sha256':hashlib.sha256(DEST.read_bytes()).hexdigest(),'bytes':DEST.stat().st_size,'changed_payloads':['classes4.dex'],'changed_methods':changes,'android_device_tested':False,'server_tested':False}
 write(B/'build.json',json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
