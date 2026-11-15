"""Verify the final APK and that the original submit and result flows remain intact."""
import hashlib
import json
import re
import sys
import zipfile

from build import B, R, SOURCE, DEST, EXPECTED
from patch_native import ANSWER, RESULT, REQUEST, PPT

sys.path[:0] = [str(R / 'apk-analysis/deps'), str(R / 'apk-analysis'),
               str(R / 'apk-analysis/precision-md3e-4.0.1.0')]
from loguru import logger
from androguard.core.apk import APK
from androguard.core.dex import DEX
from canonical_notice_methods import methods
from dex_symbols import Symbols

logger.remove()
HOOKS = {
    (REQUEST, 'invokeSuspend'),
    (RESULT, 'onViewCreated$lambda$2'),
    (ANSWER, 'observeData'),
    (ANSWER, 'onFragmentFirstVisible'),
    (PPT, 'visibility'),
}


def signing(name):
    return name.startswith('META-INF/') and name.upper().endswith(('.MF', '.SF', '.RSA', '.DSA', '.EC'))


def canonical(value):
    flags, registers, code = value
    indexes, active = {}, []
    for i, (op, args) in enumerate(code):
        indexes[i] = len(active)
        if op != 'nop':
            active.append((op.removesuffix('/jumbo'), args))
    return flags, registers, [
        (op, [(k, indexes.get(v, v) if k == 3 else [indexes.get(t, t) for t in v] if k == 'targets' else v)
              for k, v in args])
        for op, args in active
    ]


def verify():
    build = json.loads((B / 'build.json').read_text('utf8'))
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == EXPECTED
    assert hashlib.sha256(DEST.read_bytes()).hexdigest() == build['sha256']
    for name, digest in build['own_source_sha256'].items():
        assert hashlib.sha256((B / name).read_bytes()).hexdigest() == digest
    symbols = Symbols()
    with zipfile.ZipFile(SOURCE) as source, zipfile.ZipFile(DEST) as final:
        assert final.testzip() is None and len(final.namelist()) == len(set(final.namelist()))
        names = {n for n in source.namelist() if not signing(n)}
        assert {n for n in final.namelist() if not signing(n)} == names | {'classes16.dex'}
        assert {n for n in names if source.read(n) != final.read(n)} == {'classes4.dex', 'classes10.dex'}
        for name in final.namelist():
            if re.fullmatch(r'classes\d*\.dex', name):
                symbols.add(final.read(name), name)
        old = [DEX(source.read(f'classes{i}.dex')) for i in (4, 10)]
        new = [DEX(final.read(f'classes{i}.dex')) for i in (4, 10)]
        helper_bytes = final.read('classes16.dex')
    assert helper_bytes == (B / 'helper16/classes.dex').read_bytes()
    helper = DEX(helper_bytes)
    assert all(c.get_name().startswith('Lcom/hljzjx/classroom/reentry/')
               or c.get_name() == 'Lcom/android/tools/r8/annotations/LambdaMethod;'
               for c in helper.get_classes())
    assert all(count <= 65536 for count in symbols.method_counts.values())
    baseline = {k: canonical(v) for d in old for k, v in methods(d).items()}
    patched = {k: canonical(v) for d in new for k, v in methods(d).items()}
    assert baseline.keys() == patched.keys()
    differences = [k for k in baseline if baseline[k] != patched[k]]
    assert len(differences) == len(HOOKS) and {(k[0], k[1]) for k in differences} == HOOKS, differences
    for before, after in zip(old, new):
        for c in before.get_classes():
            current = after.get_class(c.get_name())
            fields = lambda cls: {(f.get_name(), f.get_descriptor()) for f in cls.get_fields()}
            expected = fields(c) | ({('modRequestUser', 'J')} if c.get_name() == REQUEST else set())
            assert fields(current) == expected
    classes = [new[0].get_class(owner) for owner in (ANSWER, REQUEST, RESULT)]
    classes.append(new[1].get_class(PPT))
    refs, errors = symbols.check(classes + helper.get_classes())
    assert not errors, errors[:25]
    apk, original = APK(str(DEST)), APK(str(SOURCE))
    assert apk.get_package() == original.get_package() == 'com.hljzjx.edu.student.classroom'
    assert apk.get_androidversion_name() == original.get_androidversion_name() == '3.2.2.0'
    assert apk.get_androidversion_code() == original.get_androidversion_code() == '322000'
    assert apk.is_signed_v2() and apk.is_signed_v3()
    assert apk.get_certificates_der_v3()[0] == original.get_certificates_der_v3()[0]
    report = {
        'passed': True, 'sha256': build['sha256'], 'changed_native_methods': len(differences),
        'unchanged_native_methods': len(baseline) - len(differences), 'checked_member_references': refs,
        'unchanged_payloads': len(names) - 2, 'pixel_tested': False, 'server_tested': False,
    }
    (B / 'verification.json').write_text(json.dumps(report, indent=2), 'utf8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    verify()
