from pathlib import Path
import hashlib,json,zipfile
B=Path(__file__).resolve().parent;R=B.parent.parent
DEST=R/'星学伴mod-3.2.1.5-系统图标与更新仅下载-源码与脚本.zip'
files=['README.md','官方更新对比.md','inspect_inputs.py','prepare.py','plan.py','smali_tools.py','manifest_version.py','SystemAppIcons.smali','build.py','build_helper.py','patch_updates.py','verify.py','test_icons.py','test_updates.py','tests/UpdatesTest.java','package_source.py','inputs.json','stock-payload-delta.json','moved-classes.json','plan.json','vendor-changes.json','changes.json','update-changes.json','api-sources.json','build.json','verification.json','update-tests.json']
items=[B/f for f in files]+list((B/'src').rglob('*.java'))
items += [R/'apk-analysis'/f for f in ['canonical_notice_methods.py','launcher_ai_android_stubs.py','precision-md3e-4.0.1.0/dex_symbols.py','launcher-controlled-open/test_flows.py','launcher-apps-todo/test_flows.py']]
license=R/'github-release/repository/LICENSE'
assert 'GNU GENERAL PUBLIC LICENSE' in license.read_text('utf8')
with zipfile.ZipFile(DEST,'w',compression=zipfile.ZIP_DEFLATED) as z:
 for p in items:
  assert p.is_file() and p.suffix not in ['.apk','.jks','.keystore']
  z.write(p,p.relative_to(R).as_posix())
 z.write(license,'LICENSE')
with zipfile.ZipFile(DEST) as z:assert z.testzip() is None and len(z.namelist())==len(set(z.namelist()))
report={'file':DEST.name,'files':len(items)+1,'bytes':DEST.stat().st_size,'sha256':hashlib.sha256(DEST.read_bytes()).hexdigest(),'excluded':['APK','vendor source','decoded trees','third-party tools','private keys']}
(B/'source-archive.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf8');print(json.dumps(report,ensure_ascii=False,indent=2))
