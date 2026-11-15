"""Build the standalone browser without rewriting any original DEX/resources."""
from pathlib import Path
import hashlib, json, os, re, shutil, subprocess, zipfile
import xml.etree.ElementTree as E

B = Path(__file__).resolve().parent
ROOT = B.parent.parent
TOOLS = ROOT / 'tools/apk-patch'
JAVA = TOOLS / 'java21/zulu21.52.203-ca-jre21.0.12.1-win_x64/bin/java.exe'
ANDROID = ROOT / 'tools/android-sdk/android-34-ext12/android.jar'
SOURCE = ROOT / 'H5应用.apk'
EXPECTED = '9f1d5b696befd7cde78d430cbcc4e5cdea63e389f12f51e5eaf76abbdb11e3c4'
DEST = ROOT / 'H5浏览器-1.0.13-首页应用直达修复.apk'
PACKAGE = 'com.hailiang.xxb.web.app'
ACTIVITY = 'com.hailiang.webbrowser.browser.BrowserActivity'
A = '{http://schemas.android.com/apk/res/android}'
E.register_namespace('android', A[1:-1])
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == EXPECTED
assert ANDROID.is_file(), 'Use the verified Android platform download recorded in tools/android-sdk/download.json'

def run(args):
    result = subprocess.run(list(map(str, args)), capture_output=True, text=True, encoding='utf-8', errors='replace')
    if result.stdout: print(result.stdout, flush=True)
    if result.stderr: print(result.stderr, flush=True)
    result.check_returncode()
    return result

# Only the generated binary manifest is used from this resource build. All
# original resource IDs/files, icon bytes, native libraries and DEX stay intact.
decoded = ROOT / 'apk-analysis/h5-browser-whitelist/resources'
stage = Path(os.environ['LOCALAPPDATA']) / 'CodexBuilds/h5-browser-mod'
stage.mkdir(parents=True, exist_ok=True)
# The Windows native aapt2/zipalign helpers require an ASCII build path.
work = stage / 'manifest-work'
work.mkdir(exist_ok=True)
shutil.copytree(decoded / 'res', work / 'res', dirs_exist_ok=True)
shutil.copyfile(decoded / 'apktool.yml', work / 'apktool.yml')
yml = (work / 'apktool.yml').read_text('utf-8')
yml = re.sub(r'(?m)^  versionCode:.*$', '  versionCode: 1015', yml)
yml = re.sub(r'(?m)^  versionName:.*$', '  versionName: 1.0.13-browser.2', yml)
(work / 'apktool.yml').write_text(yml, 'utf-8')

manifest = E.Element('manifest', {'package': PACKAGE})
for permission in ('INTERNET', 'ACCESS_NETWORK_STATE', 'CAMERA', 'RECORD_AUDIO', 'ACCESS_COARSE_LOCATION', 'ACCESS_FINE_LOCATION'):
    E.SubElement(manifest, 'uses-permission', {A + 'name': 'android.permission.' + permission})
for feature in ('camera', 'camera.autofocus', 'microphone'):
    E.SubElement(manifest, 'uses-feature', {A + 'name': 'android.hardware.' + feature, A + 'required': 'false'})
app = E.SubElement(manifest, 'application', {
    A + 'name': 'android.app.Application', A + 'icon': '@mipmap/ic_logo', A + 'roundIcon': '@mipmap/ic_logo',
    A + 'label': 'H5 浏览器', A + 'theme': '@android:style/Theme.Material.Light.NoActionBar',
    A + 'hardwareAccelerated': 'true', A + 'usesCleartextTraffic': 'true',
    A + 'networkSecurityConfig': '@xml/network_security_config', A + 'allowBackup': 'false',
    A + 'supportsRtl': 'true', A + 'extractNativeLibs': 'false',
})
activity = E.SubElement(app, 'activity', {
    A + 'name': ACTIVITY, A + 'exported': 'true', A + 'launchMode': 'singleTask',
    A + 'resizeableActivity': 'true', A + 'windowSoftInputMode': 'adjustResize',
})

def intent_filter(parent, actions, categories, schemes=(), mime=None):
    f = E.SubElement(parent, 'intent-filter')
    for value in actions: E.SubElement(f, 'action', {A + 'name': 'android.intent.action.' + value})
    for value in categories: E.SubElement(f, 'category', {A + 'name': 'android.intent.category.' + value})
    for scheme in schemes: E.SubElement(f, 'data', {A + 'scheme': scheme})
    if mime: E.SubElement(f, 'data', {A + 'mimeType': mime})

intent_filter(activity, ['MAIN'], ['LAUNCHER'])
intent_filter(activity, ['VIEW'], ['DEFAULT', 'BROWSABLE'], ['http', 'https'])
intent_filter(activity, ['SEND'], ['DEFAULT'], mime='text/plain')
# Existing explicit component names and school URL extras enter the browser as
# well. They no longer instantiate the old school-login WebView activities.
for name, exported in [('LaunchDispatcherActivity', True), ('WebViewActivity', True), ('MainActivity', False), ('HomeScreen', False), ('UrlRequiredScreen', False)]:
    alias = E.SubElement(app, 'activity-alias', {A + 'name': 'com.hailiang.webbrowser.' + name, A + 'targetActivity': ACTIVITY, A + 'exported': str(exported).lower()})
    if name == 'LaunchDispatcherActivity': intent_filter(alias, ['VIEW'], ['DEFAULT', 'BROWSABLE'], ['hlxxb'])
E.indent(manifest)
E.ElementTree(manifest).write(work / 'AndroidManifest.xml', encoding='utf-8', xml_declaration=True)

classes = B / 'classes'; classes.mkdir(exist_ok=True)
sources = list((B / 'src').rglob('*.java'))
run([JAVA, '-jar', TOOLS / 'ecj.jar', '-proc:none', '-source', '8', '-target', '8', '-encoding', 'UTF-8', '-warn:none', '-cp', ANDROID, '-d', classes, *sources])
jar = B / 'browser.jar'
with zipfile.ZipFile(jar, 'w') as z:
    for path in classes.rglob('*.class'): z.write(path, path.relative_to(classes).as_posix())
dex = B / 'dex'; dex.mkdir(exist_ok=True)
run([JAVA, '-cp', TOOLS / 'jadx/lib/jadx-gui-1.5.6-all.jar', 'com.android.tools.r8.D8', '--min-api', '29', '--lib', JAVA.parent.parent, '--lib', ANDROID, '--output', dex, jar])
rebuilt = stage / 'manifest-resources.apk'
run([JAVA, '-jar', TOOLS / 'apktool.jar', 'b', work, '-o', rebuilt])
shutil.copyfile(rebuilt, B / 'manifest-resources.apk')
unsigned = B / 'h5-browser-unsigned.apk'
def signature(name): return name.startswith('META-INF/') and name.upper().endswith(('.MF', '.SF', '.RSA', '.DSA', '.EC'))
with zipfile.ZipFile(SOURCE) as original, zipfile.ZipFile(rebuilt) as compiled, zipfile.ZipFile(unsigned, 'w') as out:
    assert 'classes6.dex' not in original.namelist()
    for info in original.infolist():
        if not signature(info.filename): out.writestr(info, compiled.read('AndroidManifest.xml') if info.filename == 'AndroidManifest.xml' else original.read(info.filename))
    out.writestr('classes6.dex', (dex / 'classes.dex').read_bytes(), compress_type=zipfile.ZIP_STORED)

key = TOOLS / 'signing/h5-browser-mod.jks'
if not key.exists():
    run([JAVA.parent / 'keytool.exe', '-genkeypair', '-keystore', key, '-storetype', 'JKS', '-storepass', 'android', '-keypass', 'android', '-alias', 'h5browsermod', '-keyalg', 'RSA', '-keysize', '2048', '-validity', '10000', '-dname', 'CN=H5 Browser Mod, OU=Personal Mod, O=xuezhangjam, C=CN', '-noprompt'])
signed = stage / 'signed'; signed.mkdir(exist_ok=True)
sign_input = stage / unsigned.name
shutil.copyfile(unsigned, sign_input)
result = signed / 'h5-browser-aligned-signed.apk'
result.unlink(missing_ok=True)
run([JAVA, '-jar', TOOLS / 'uber-apk-signer.jar', '-a', sign_input, '-o', signed, '--ks', key, '--ksAlias', 'h5browsermod', '--ksPass', 'android', '--ksKeyPass', 'android'])
assert result.is_file()
shutil.copyfile(result, DEST)
metadata = {
    'input': SOURCE.name, 'input_sha256': EXPECTED, 'output': DEST.name,
    'sha256': hashlib.sha256(DEST.read_bytes()).hexdigest(), 'size': DEST.stat().st_size,
    'package': PACKAGE, 'version_name': '1.0.13-browser.2', 'version_code': 1015,
    'launcher_activity': ACTIVITY, 'original_dex': 'all five preserved byte-for-byte',
    'original_resources_and_icon': 'preserved byte-for-byte',
    'application': 'android.app.Application; no school SDK initializers or providers',
    'legacy_components': 'activity aliases to standalone BrowserActivity',
    'android_device_tested': False,
}
(B / 'build.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2), 'utf-8')
print(json.dumps(metadata, ensure_ascii=False, indent=2))
