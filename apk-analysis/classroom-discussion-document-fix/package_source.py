from pathlib import Path
import hashlib,json,zipfile
B=Path(__file__).resolve().parent;R=B.parent.parent
DEST=R/'学生端课堂-3.2.2.0-图片上传与文档偏移修补-源码与脚本.zip'
files=[B/n for n in ['README.md','statistics-audit.md','build.py','patch_native.py','verify.py','test_behavior.py','package_source.py','build.json','changes.json','verification.json','behavior-tests.json']]
for folder in ['src','compile-api']:
 files.extend(p for p in (B/folder).rglob('*.java'))
files.extend([R/'apk-analysis/canonical_notice_methods.py',R/'apk-analysis/precision-md3e-4.0.1.0/dex_symbols.py',R/'apk-analysis/classroom-review-entry-fix/check_flow.py'])
with zipfile.ZipFile(DEST,'w',compression=zipfile.ZIP_DEFLATED) as z:
 for p in files:assert p.is_file();z.write(p,p.relative_to(R).as_posix())
 z.write(R/'github-release/repository/LICENSE','LICENSE')
with zipfile.ZipFile(DEST) as z:
 assert z.testzip() is None and len(z.namelist())==len(set(z.namelist()))
 assert all(not n.endswith(('.apk','.dex','.class','.jar','.jks','.keystore')) and '/work4/' not in n and '/audit/' not in n for n in z.namelist())
report={'file':DEST.name,'files':len(files)+1,'bytes':DEST.stat().st_size,'sha256':hashlib.sha256(DEST.read_bytes()).hexdigest()}
(B/'source-archive.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf8');print(json.dumps(report,ensure_ascii=False,indent=2))
