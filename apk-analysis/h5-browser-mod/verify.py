"""Audit the final installed entry, package payloads and generated DEX links."""
from pathlib import Path
import hashlib, json, re, struct, sys, zipfile

B = Path(__file__).resolve().parent
ROOT = B.parent.parent
sys.path[:0] = [str(ROOT / 'apk-analysis/deps'), str(ROOT / 'apk-analysis')]
from loguru import logger
logger.remove()
from androguard.core.apk import APK
from androguard.core.dex import DEX
from launcher_dex_linkage import DexLinker

meta = json.loads((B / 'build.json').read_text('utf-8'))
source = ROOT / meta['input']; output = ROOT / meta['output']
def signature(name): return name.startswith('META-INF/') and name.upper().endswith(('.MF', '.SF', '.RSA', '.DSA', '.EC'))
with zipfile.ZipFile(source) as a, zipfile.ZipFile(output) as b:
    assert b.testzip() is None
    before = {n for n in a.namelist() if not signature(n)}
    after = {n for n in b.namelist() if not signature(n)}
    assert before | {'classes6.dex'} == after, (after - before, before - after)
    changed = {n for n in before if a.read(n) != b.read(n)}
    assert changed == {'AndroidManifest.xml'}, changed
    helper = DEX(b.read('classes6.dex'))
    classes = list(helper.get_classes())
    assert all(c.get_name().startswith('Lcom/hailiang/webbrowser/browser/') or c.get_name() == 'Lcom/android/tools/r8/annotations/LambdaMethod;' for c in classes)
    def class_names(data):
        _, strings = struct.unpack_from('<II', data, 56)
        _, types = struct.unpack_from('<II', data, 64)
        count, definitions = struct.unpack_from('<II', data, 96)
        names = set()
        for i in range(count):
            type_id = struct.unpack_from('<I', data, definitions + i * 32)[0]
            string_id = struct.unpack_from('<I', data, types + type_id * 4)[0]
            pos = struct.unpack_from('<I', data, strings + string_id * 4)[0]
            while data[pos] & 128: pos += 1
            pos += 1
            names.add(data[pos:data.index(b'\0', pos)].decode('utf-8', errors='replace'))
        return names
    original_classes = set()
    for name in before:
        if re.fullmatch(r'classes\d*\.dex', name): original_classes.update(class_names(a.read(name)))
    assert not original_classes.intersection(c.get_name() for c in classes), 'Duplicate DEX class definition'
    assert any(c.get_name() == 'Lcom/hailiang/webbrowser/browser/BrowserActivity;' and c.get_superclassname() == 'Landroid/app/Activity;' for c in classes)
    assert len(helper.get_methods()) < 65536
    refs, errors = DexLinker([helper]).check(classes)
    assert not errors, errors[:20]
    strings = set(helper.get_strings())
    assert not any(x in strings for x in ('/launch/app/v1/school_control_url/white_get_lists', 'otter-token'))
    assert not any(m.get_class_name().startswith(('Lcom/hailiang/opensdk/', 'Lcom/hailiang/xxb/mdm/', 'Lcom/hailiang/webbrowser/App;')) for m in helper.get_methods())

old, apk = APK(str(source)), APK(str(output))
assert apk.get_package() == old.get_package() == meta['package']
assert apk.get_androidversion_code() == '1015'
assert apk.get_androidversion_name() == '1.0.13-browser.2'
assert apk.get_min_sdk_version() == old.get_min_sdk_version() == '29'
assert apk.get_target_sdk_version() == old.get_target_sdk_version() == '29'
assert apk.get_main_activity() == meta['launcher_activity']
ns = '{http://schemas.android.com/apk/res/android}'
manifest = apk.get_android_manifest_xml(); app = manifest.find('application')
old_app = old.get_android_manifest_xml().find('application')
assert app.get(ns + 'name') == 'android.app.Application'
assert app.get(ns + 'label') == 'H5 浏览器'
assert app.get(ns + 'icon') == old_app.get(ns + 'icon')
assert app.get(ns + 'roundIcon') == old_app.get(ns + 'roundIcon')
assert app.get(ns + 'networkSecurityConfig') == old_app.get(ns + 'networkSecurityConfig')
assert len(app.findall('activity')) == 1
assert not app.findall('provider') and not app.findall('service') and not app.findall('receiver')
activity = app.find('activity'); filters = activity.findall('intent-filter')
assert activity.get(ns + 'name') == meta['launcher_activity']
assert activity.get(ns + 'exported') == 'true' and activity.get(ns + 'resizeableActivity') == 'true'
assert any(any(a.get(ns + 'name') == 'android.intent.action.MAIN' for a in f.findall('action')) and any(c.get(ns + 'name') == 'android.intent.category.LAUNCHER' for c in f.findall('category')) for f in filters)
assert {d.get(ns + 'scheme') for f in filters for d in f.findall('data') if d.get(ns + 'scheme')} == {'http', 'https'}
assert any(d.get(ns + 'mimeType') == 'text/plain' for f in filters for d in f.findall('data'))
aliases = app.findall('activity-alias')
assert len(aliases) == 5 and all(a.get(ns + 'targetActivity') == meta['launcher_activity'] for a in aliases)
assert len(apk.get_permissions()) == 6
assert apk.is_signed_v2() and apk.is_signed_v3()
cert = (apk.get_certificates_der_v3() or apk.get_certificates_der_v2())[0]
old_cert = (old.get_certificates_der_v3() or old.get_certificates_der_v2() or old.get_certificates_der_v1())[0]
report = {
    **meta, 'sha256': hashlib.sha256(output.read_bytes()).hexdigest(),
    'changed_original_payloads': sorted(changed), 'preserved_original_payloads': len(before) - 1,
    'all_five_original_dex_and_all_icon_resources_identical': True,
    'new_browser_classes': len(classes), 'checked_new_dex_member_references': refs,
    'new_dex_has_no_direct_school_sdk_references': True, 'legacy_aliases_verified': len(aliases),
    'launcher_http_https_and_text_share_filters_verified': True,
    'school_providers_and_services_not_registered': True,
    'certificate_sha256': hashlib.sha256(cert).hexdigest(),
    'official_certificate_sha256': hashlib.sha256(old_cert).hexdigest(),
    'can_cover_official_signature': cert == old_cert,
    'signed_v2': apk.is_signed_v2(), 'signed_v3': apk.is_signed_v3(),
    'url_parser_test_cases': 44,
    'external_link_regression_cases': 55,
    'android_device_tested': False,
}
previous_path = ROOT / 'H5浏览器-1.0.13-自由浏览-桌面图标.apk'
previous = APK(str(previous_path))
previous_cert = (previous.get_certificates_der_v3() or previous.get_certificates_der_v2())[0]
assert previous_cert == cert
with zipfile.ZipFile(previous_path) as a, zipfile.ZipFile(output) as b:
    old_files = {n for n in a.namelist() if not signature(n)}
    new_files = {n for n in b.namelist() if not signature(n)}
    assert old_files == new_files
    delta = {n for n in old_files if a.read(n) != b.read(n)}
    assert delta == {'AndroidManifest.xml', 'classes6.dex'}, delta
report['same_signature_as_previous_browser'] = True
report['changed_payloads_vs_previous_browser'] = sorted(delta)
# School launch requests must use directUrl/finishAppLink, never the search
# routing method. Shared text is intentionally separate from app URL launches.
activity_class = helper.get_class('Lcom/hailiang/webbrowser/browser/BrowserActivity;')
open_link = next(m for m in activity_class.get_methods() if m.get_name() == 'openAppLink')
calls = [i.get_output() for i in open_link.get_instructions() if i.get_name().startswith('invoke-')]
assert any('BrowserInput;->directUrl' in s for s in calls)
assert not any('->navigate(' in s or 'BrowserInput;->resolve' in s for s in calls)
report['external_app_link_has_no_search_fallback'] = True
(B / 'verification.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), 'utf-8')
print(json.dumps(report, ensure_ascii=False, indent=2))
