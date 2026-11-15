"""Archive only the migration implementation/plans and verification evidence."""
from pathlib import Path
import hashlib,json,zipfile
B=Path(__file__).resolve().parent;ROOT=B.parent.parent
DEST=ROOT/'学生端课堂-3.2.2.0-v8迁移脚本与校验.zip'
names=['README.md','migrate.py','filter_native.py','verify.py','package_source.py',
       'native-plan.json','build.json','verification.json','regressions.json',
       'resource-merge.json','resource-remap.json','helper-remap.json',
       'native-merge.json','dex-split.json']
report=json.loads((B/'verification.json').read_text('utf-8'));assert report['passed']
assert hashlib.sha256((ROOT/report['output']).read_bytes()).hexdigest()==report['sha256']
plan=json.loads((B/'resource-plan.json').read_text('utf-8'))
# Omit third-party enum declaration snippets introduced solely by apktool order.
plan['value_changed']=[]
prefix=B.relative_to(ROOT).as_posix()
with zipfile.ZipFile(DEST,'w',zipfile.ZIP_DEFLATED) as z:
    for name in names:z.write(B/name,prefix+'/'+name)
    z.writestr(prefix+'/resource-plan.json',json.dumps(plan,ensure_ascii=False,indent=2))
    for name in ['canonical_notice_methods.py','launcher_dex_linkage.py']:
        z.write(ROOT/'apk-analysis'/name,'apk-analysis/'+name)
    z.write(ROOT/'github-release/repository/LICENSE','LICENSE')
with zipfile.ZipFile(DEST) as z:
    assert z.testzip() is None
    assert all(Path(n).suffix not in {'.apk','.jks','.keystore','.dex','.class','.jar','.smali'} for n in z.namelist())
    summary={'archive':DEST.name,'files':len(z.namelist()),'size':DEST.stat().st_size,
             'sha256':hashlib.sha256(DEST.read_bytes()).hexdigest()}
(B/'source-archive.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),'utf-8')
print(json.dumps(summary,ensure_ascii=False,indent=2))
