from pathlib import Path
import hashlib,json,zipfile
from build import B,R,DEST
v=json.loads((B/'verification.json').read_text('utf8'));t=json.loads((B/'revision-tests.json').read_text('utf8'))
assert v['passed'] and t['passed'] and hashlib.sha256(DEST.read_bytes()).hexdigest()==v['sha256']
assert t['ui_jar_sha256']==json.loads((B/'compile.json').read_text('utf8'))['ui_jar_sha256']
files={B/n for n in ['README.md','build.py','compile.py','make_api.py','patch_native.py','verify.py','test_revision.py','package_source.py','build.json','compile.json','changes.json','retained-native11.json','verification.json','revision-tests.json','revision-test-results.txt']}
for folder,pattern in [('src','*.kt'),('tests','*.kt'),('tests','*.java'),('compile-api','*.java')]:files.update((B/folder).rglob(pattern))
files.update([R/'apk-analysis/canonical_notice_methods.py',R/'apk-analysis/precision-md3e-4.0.1.0/dex_symbols.py',R/'apk-analysis/classroom-review-entry-fix/check_flow.py'])
archive=R/'精准作业-4.0.1.0-半对图标-未批改答案修改-v11-源码与脚本.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
 for p in sorted(files):assert p.is_file();z.write(p,p.relative_to(R).as_posix())
 z.write(R/'github-release/repository/LICENSE','LICENSE')
 z.write(R/'apk-analysis/precision-google-tools-v7/assets/google-material-symbols/LICENSE','LICENSE.google-material-symbols')
with zipfile.ZipFile(archive) as z:
 assert z.testzip() is None and all(Path(n).suffix not in {'.apk','.dex','.class','.jar','.smali','.jks','.keystore','.aar'} for n in z.namelist())
 assert not any('/audit/' in n or '/work5/' in n or '/work11/' in n for n in z.namelist())
 report={'archive':archive.name,'files':len(z.namelist()),'bytes':archive.stat().st_size,'sha256':hashlib.sha256(archive.read_bytes()).hexdigest()}
(B/'source-archive.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf8');print(json.dumps(report,ensure_ascii=False,indent=2))
