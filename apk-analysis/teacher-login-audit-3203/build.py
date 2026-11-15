"""Build a local teacher launcher patch without changing the vendor's server list."""
import hashlib
import json
import os
import re
import shutil
import subprocess
import zipfile
from pathlib import Path

B = Path(__file__).resolve().parent
R = B.parent.parent
T = R / 'tools/apk-patch'
JAVA = T / 'java21/zulu21.52.203-ca-jre21.0.12.1-win_x64/bin/java.exe'
ANDROID = R / 'tools/android-sdk/android-34-ext12/android.jar'
SOURCE = R / '星学伴教师端3.2.0.3.apk'
DEST = R / '星学伴教师端-3.2.0.3-本机入口修复-v2.apk'
EXPECTED = 'f2b9fd96a4d516dfae6f97970c5f081542d67c08061e83cf37b763b6d8bca871'
OWNER = 'com/hljzjx/launcher/teacher/launcher'
PATTERN = re.compile(r'^\.method ([^\n]+)\n.*?^\.end method', re.M | re.S)


def long(path):
    return Path('\\\\?\\' + str(path.resolve())) if os.name == 'nt' else path


def replace_method(relative, signature, rewrite):
    path = 'smali/' + OWNER + '/' + relative + '.smali'
    data = long(B / 'base3' / path).read_text('utf8')
    methods = [m for m in PATTERN.finditer(data) if m[1].split()[-1].startswith(signature)]
    assert len(methods) == 1, (relative, signature)
    method, = methods
    output = long(B / 'work3' / path)
    temp = output.with_suffix('.tmp')
    temp.write_text(data[:method.start()] + rewrite(method[0]) + data[method.end():], 'utf8')
    os.replace(temp, output)


def login_tabs(method):
    old = '    :cond_7\n    new-array p1, v4, [Ljava/lang/String;'
    assert method.count(old) == 1
    method = method.replace(old, '''    :cond_7
    const/4 v4, 0x3

    new-array p1, v4, [Ljava/lang/String;''')
    old = '    const-string v0, "VERIFICATION_CODE"\n\n    aput-object v0, p1, v2'
    assert method.count(old) == 1
    return method.replace(old, old + '''

    const/4 v4, 0x2

    const-string v0, "FACE_RECOGNITION"

    aput-object v0, p1, v4''')


def label_tab(method):
    # Three teacher tabs occupy approximately the same width as the original two.
    assert method.count('    const/16 p2, 0x9c') == 1
    method = method.replace('    const/16 p2, 0x9c', '    const/16 p2, 0x64')
    anchor = f'    invoke-virtual {{v6, v0}}, L{OWNER}/ui/login/custom/SelectButtonView;->setText(Ljava/lang/String;)V'
    assert method.count(anchor) == 1
    return method.replace(anchor, '''    const-string v1, "FACE_RECOGNITION"

    invoke-virtual {v1, p2}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v1

    if-eqz v1, :original_tab_title

    const-string/jumbo v0, "学生刷脸"

    :original_tab_title
''' + anchor)


def missing_app(method):
    anchor = '    if-nez v0, :cond_0\n'
    assert method.count(anchor) == 1
    method = method.replace(anchor, anchor + f'''
    iget-object v1, p0, L{OWNER}/ui/main/MainPresenter;->iView:Lcom/jchou/commonlibrary/mvp/view/IView;

    invoke-static {{v1, p1}}, Lcom/hljzjx/teachermod/InstalledApps;->offer(Ljava/lang/Object;Ljava/lang/String;)Z

    move-result v1

    if-eqz v1, :original_not_assigned

    return-void

    :original_not_assigned
''')
    start = method.index('    .line 435\n')
    end = method.index('    return-void', start)
    assert 'toast_app_not_assigned' in method[start:end]
    return method[:start] + '''    .line 435
    const-string/jumbo p0, "平台已下架此应用"

    invoke-static {p0}, Lcom/jchou/commonlibrary/utils/ToastUtils;->showShort(Ljava/lang/String;)V

''' + method[end:]


def bind_status_button(method):
    anchor = '->appCenterEmpty:Landroid/widget/LinearLayout;\n'
    assert method.count(anchor) == 1
    end = method.index(anchor) + len(anchor)
    return method[:end] + '''
    if-eqz v0, :native_empty_visibility

    invoke-static {p0, v2}, Lcom/hljzjx/teachermod/InstalledApps;->bindStatusButton(Landroid/app/Activity;Landroid/widget/LinearLayout;)V

    :native_empty_visibility
''' + method[end:]


def run(*args):
    subprocess.run(list(map(str, args)), check=True)


def signature(name):
    return name.startswith('META-INF/') and name.upper().endswith(('.SF', '.RSA', '.DSA', '.EC', '.MF'))


def main():
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == EXPECTED
    with zipfile.ZipFile(SOURCE) as apk, zipfile.ZipFile(B / 'teacher/login.apk') as cached:
        assert apk.read('classes3.dex') == cached.read('classes.dex')
    base = B / 'base3'
    if not (base / 'apktool.yml').is_file():
        run(JAVA, '-jar', T / 'apktool.jar', 'd', '-r', '-o', base, B / 'teacher/login.apk')
    work = B / 'work3'
    for path in long(base).rglob('*'):
        relative = path.relative_to(long(base))
        if relative.parts[0] in ('build', 'dist'):
            continue
        target = long(work) / relative
        if path.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        elif not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            os.link(path, target)

    replace_method('ui/login/viewmodel/LoginViewModel', 'handleLoginRole(', login_tabs)
    replace_method('ui/login/fragment/MainFragment', 'createButton(', label_tab)
    replace_method('ui/main/MainPresenter', 'checkApp(Ljava/lang/String;)', missing_app)
    replace_method('ui/main/MainActivity', 'syncAppCenterEmptyState(', bind_status_button)

    classes = B / 'classes'
    classes.mkdir(exist_ok=True)
    run(JAVA, '-jar', T / 'ecj.jar', '-proc:none', '-source', '8', '-target', '8', '-encoding', 'UTF-8',
        '-cp', ANDROID, '-d', classes, *sorted((B / 'src').rglob('*.java')))
    helper = B / 'helper.jar'
    with zipfile.ZipFile(helper, 'w') as jar:
        for path in classes.rglob('*.class'):
            jar.write(path, path.relative_to(classes).as_posix())
    dex = B / 'helper5'
    dex.mkdir(exist_ok=True)
    run(JAVA, '-cp', T / 'jadx/lib/jadx-gui-1.5.6-all.jar', 'com.android.tools.r8.D8',
        '--min-api', '29', '--lib', JAVA.parent.parent, '--lib', ANDROID, '--output', dex, helper)
    patched = B / 'classes3-patch.apk'
    run(JAVA, '-jar', T / 'apktool.jar', 'b', work, '-o', patched)
    unsigned = B / 'teacher-local-unsigned.apk'
    with zipfile.ZipFile(SOURCE) as apk, zipfile.ZipFile(patched) as patch, zipfile.ZipFile(unsigned, 'w') as out:
        for info in apk.infolist():
            if not signature(info.filename):
                out.writestr(info, patch.read('classes.dex') if info.filename == 'classes3.dex' else apk.read(info.filename))
        assert 'classes5.dex' not in apk.namelist()
        out.writestr('classes5.dex', (dex / 'classes.dex').read_bytes())
    stage = Path(os.environ['LOCALAPPDATA']) / 'CodexBuilds/teacher-local-3203-v2'
    signed = stage / 'signed'
    signed.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(unsigned, stage / unsigned.name)
    result = signed / 'teacher-local-aligned-signed.apk'
    result.unlink(missing_ok=True)
    run(JAVA, '-jar', T / 'uber-apk-signer.jar', '-a', stage / unsigned.name, '-o', signed,
        '--ks', T / 'signing/launcher-mod.jks', '--ksAlias', 'launchermod', '--ksPass', 'android', '--ksKeyPass', 'android')
    shutil.copyfile(result, DEST)
    metadata = {
        'input': SOURCE.name, 'input_sha256': EXPECTED, 'output': DEST.name,
        'sha256': hashlib.sha256(DEST.read_bytes()).hexdigest(), 'device_tested': False,
    }
    (B / 'build.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2), 'utf8')
    print(json.dumps(metadata, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
