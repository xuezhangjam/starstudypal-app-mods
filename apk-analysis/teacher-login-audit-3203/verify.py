import hashlib
import json
import re
import sys
import zipfile

from build import B, R, SOURCE, DEST, EXPECTED, OWNER, signature

sys.path[:0] = [str(R / 'apk-analysis/deps'), str(R / 'apk-analysis'),
               str(R / 'apk-analysis/precision-md3e-4.0.1.0')]
from loguru import logger
from androguard.core.apk import APK
from androguard.core.dex import DEX
from canonical_notice_methods import methods
from dex_symbols import Symbols

logger.remove()
TARGETS = {
    (f'L{OWNER}/ui/login/viewmodel/LoginViewModel;', 'handleLoginRole'),
    (f'L{OWNER}/ui/login/fragment/MainFragment;', 'createButton'),
    (f'L{OWNER}/ui/main/MainPresenter;', 'checkApp'),
    (f'L{OWNER}/ui/main/MainActivity;', 'syncAppCenterEmptyState'),
}


def normalize(value):
    flags, registers, instructions = value
    filtered, remap = [], {}
    for i, (op, args) in enumerate(instructions):
        remap[i] = len(filtered)
        if op != 'nop':
            filtered.append((op.removesuffix('/jumbo'), args))
    return flags, registers, [
        (op, [(kind, remap.get(v, v) if kind == 3 else
               [remap.get(i, i) for i in v] if kind == 'targets' else v)
              for kind, v in args])
        for op, args in filtered
    ]


def main():
    meta = json.loads((B / 'build.json').read_text('utf8'))
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == EXPECTED
    assert hashlib.sha256(DEST.read_bytes()).hexdigest() == meta['sha256']
    symbols = Symbols()
    with zipfile.ZipFile(SOURCE) as original, zipfile.ZipFile(DEST) as output:
        assert output.testzip() is None and len(output.namelist()) == len(set(output.namelist()))
        files = {n for n in original.namelist() if not signature(n)}
        assert {n for n in output.namelist() if not signature(n)} == files | {'classes5.dex'}
        assert {n for n in files if original.read(n) != output.read(n)} == {'classes3.dex'}
        for n in output.namelist():
            if re.fullmatch(r'classes\d*\.dex', n):
                symbols.add(output.read(n), n)
        old, new = DEX(original.read('classes3.dex')), DEX(output.read('classes3.dex'))
        helper_dex = output.read('classes5.dex')
    assert helper_dex == (B / 'helper5/classes.dex').read_bytes()
    helper = DEX(helper_dex)
    assert all(c.get_name().startswith('Lcom/hljzjx/teachermod/')
               or c.get_name() == 'Lcom/android/tools/r8/annotations/LambdaMethod;'
               for c in helper.get_classes())
    baseline, patched = methods(old), methods(new)
    assert baseline.keys() == patched.keys()
    delta = [key for key, value in baseline.items() if normalize(value) != normalize(patched[key])]
    assert len(delta) == len(TARGETS) and {(k[0], k[1]) for k in delta} == TARGETS, delta
    assert any(k[1] == 'checkApp' and k[2] == '(Ljava/lang/String;)V' for k in delta)
    changed = [new.get_class(owner) for owner, name in TARGETS]
    refs, errors = symbols.check(changed + helper.get_classes())
    assert not errors, errors[:20]
    assert all(c <= 65536 for c in symbols.method_counts.values())
    apk, original = APK(str(DEST)), APK(str(SOURCE))
    assert apk.get_package() == original.get_package() == 'com.hljzjx.edu.teacher.launch'
    assert apk.get_androidversion_name() == original.get_androidversion_name() == '3.2.0.3'
    assert apk.get_androidversion_code() == original.get_androidversion_code() == '32003'
    assert apk.is_signed_v2() and apk.is_signed_v3()
    certificate = apk.get_certificates_der_v3()[0]
    assert certificate not in original.get_certificates_der_v2() + original.get_certificates_der_v3()
    report = {
        **meta, 'changed_native_methods': len(delta), 'unchanged_native_methods': len(baseline) - len(delta),
        'unchanged_original_payloads': len(files) - 1, 'checked_member_references': refs,
        'certificate_sha256': hashlib.sha256(certificate).hexdigest(),
    }
    (B / 'verification.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), 'utf8')
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
