from pathlib import Path
import hashlib,json,zipfile
B=Path(__file__).resolve().parent;R=B.parent.parent
DEST=R/'学生端课堂-3.2.2.0-讨论结束换组-源码与脚本.zip'
files=[B/f for f in ['README.md','build.py','verify.py','test_flow.py','package_source.py','build.json','verification.json','changes.json','controls-regression.json']]
files += [R/'apk-analysis/canonical_notice_methods.py',R/'apk-analysis/precision-md3e-4.0.1.0/dex_symbols.py']
with zipfile.ZipFile(DEST,'w',compression=zipfile.ZIP_DEFLATED) as z:
 for p in files:assert p.is_file();z.write(p,p.relative_to(R).as_posix())
 z.write(R/'github-release/repository/LICENSE','LICENSE')
with zipfile.ZipFile(DEST) as z:assert z.testzip() is None
report={'file':DEST.name,'files':len(files)+1,'bytes':DEST.stat().st_size,'sha256':hashlib.sha256(DEST.read_bytes()).hexdigest()}
(B/'source-archive.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf8');print(json.dumps(report,ensure_ascii=False,indent=2))
