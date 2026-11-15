"""Verify the signed v12 archive, its linkage, and the changed native entry points."""
import hashlib
import json
import re
import sys
import zipfile

from build import B, R, SOURCE, DEST, EXPECTED, OWN
from patch_native import QUESTION, PEN_HELPER, SPAN

sys.path[:0] = [
    str(R / 'apk-analysis/deps'), str(R / 'apk-analysis'),
    str(R / 'apk-analysis/precision-md3e-4.0.1.0'),
    str(R / 'apk-analysis/classroom-review-entry-fix'),
]
from loguru import logger
from androguard.core.apk import APK
from androguard.core.dex import DEX
from canonical_notice_methods import methods
from dex_symbols import Symbols
from check_flow import check

logger.remove()
SELECT = 'Lcom/hailiang/workcloud/student/shareui/work/select/'
FILL = 'Lcom/hailiang/xxb/question/ui/v3/plugins/FillInsertRenderPluginV3;'
CHANGES = {
    QUESTION: {'dispatchTouchEvent', 'reset', 'onDetachedFromWindow'},
    PEN_HELPER: {'isPenEvent'},
    SELECT + 'SelectQuestionPanel_androidKt;': {'SelectQuestionPanelAnswering'},
    SELECT + 'QuestionAnswerBoardAreaKt;': {'QuestionAnswerBoardArea-pglpRAY'},
    SPAN: {'updateState'},
    FILL: {'render-NjoSL3Q'},
}


def signature(name):
    return name.startswith('META-INF/') and name.upper().endswith(('.MF', '.SF', '.RSA', '.DSA', '.EC'))


def own(name):
    return name.startswith(OWN) or name == 'Lcom/android/tools/r8/annotations/LambdaMethod;'


def sequence(method):
    flags, registers, instructions = method
    # The assembler may add nop padding and upgrade string loads as indices move.
    positions = {}
    filtered = []
    for i, (op, args) in enumerate(instructions):
        positions[i] = len(filtered)
        if op != 'nop':
            filtered.append((op.removesuffix('/jumbo'), args))
    return flags, registers, [
        (op, [(kind, positions.get(v, v) if kind == 3 else
               [positions.get(t, t) for t in v] if kind == 'targets' else v)
              for kind, v in args])
        for op, args in filtered
    ]


def main():
    meta = json.loads((B / 'build.json').read_text('utf8'))
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == EXPECTED
    assert hashlib.sha256(DEST.read_bytes()).hexdigest() == meta['sha256']
    assert meta['own_source_sha256'] == {
        p.relative_to(B).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in (B / 'src').glob('*.kt')
    }
    symbols = Symbols()
    with zipfile.ZipFile(SOURCE) as base, zipfile.ZipFile(DEST) as output:
        assert output.testzip() is None and len(output.namelist()) == len(set(output.namelist()))
        names = {n for n in base.namelist() if not signature(n)}
        assert names == {n for n in output.namelist() if not signature(n)}
        assert {n for n in names if base.read(n) != output.read(n)} == {'classes5.dex', 'classes11.dex'}
        for name in names:
            if re.fullmatch(r'classes\d*\.dex', name):
                symbols.add(output.read(name), name)
        before = [DEX(base.read(f'classes{i}.dex')) for i in (5, 11)]
        after = [DEX(output.read(f'classes{i}.dex')) for i in (5, 11)]

    native = lambda dexes: {k: sequence(v) for d in dexes for k, v in methods(d).items() if not own(k[0])}
    original, current = native(before), native(after)
    assert original.keys() <= current.keys()
    assert {(k[0], k[1]) for k in current.keys() - original.keys()} == {(QUESTION, 'modDispatchWritingEvent')}
    delta = [k for k in original if original[k] != current[k]]
    assert len(delta) == sum(map(len, CHANGES.values())), delta
    assert {(k[0], k[1]) for k in delta} == {(c, m) for c, names in CHANGES.items() for m in names}, delta

    bundled = DEX((B / 'helper11/classes.dex').read_bytes())
    helpers = lambda dex: {k: sequence(v) for k, v in methods(dex).items() if k[0].startswith(OWN)}
    final_helpers = helpers(after[1])
    assert final_helpers == helpers(bundled)
    assert all(final_helpers.get(k) == v for k, v in helpers(before[1]).items())
    classes = [after[0].get_class(c) for c in CHANGES]
    classes += [c for c in after[1].get_classes() if c.get_name().startswith(OWN)]
    refs, errors = symbols.check(classes)
    assert not errors, errors[:30]
    assert all(count <= 65536 for count in symbols.method_counts.values())

    def changed(owner, name):
        return next(m for m in after[0].get_class(owner).get_methods() if m.get_name() == name)

    bridge = changed(QUESTION, 'modDispatchWritingEvent')
    bridge_code = [i.get_output() for i in bridge.get_instructions()]
    offset = lambda needle: next(i for i, text in enumerate(bridge_code) if needle in text)
    assert offset('cancelAutoSave(') < offset('HandwriteView;->dispatchTouchEvent(') < offset('executeAutoSave(')
    flow = [check(bridge), check(changed(QUESTION, 'dispatchTouchEvent')), check(changed(PEN_HELPER, 'isPenEvent'))]
    assert all(not result['uninitialized_reads'] for result in flow)

    apk, base = APK(str(DEST)), APK(str(SOURCE))
    assert apk.get_package() == base.get_package() == 'com.hailiang.workcloud.student'
    assert apk.get_androidversion_name() == base.get_androidversion_name() == '4.0.1.0'
    assert apk.get_androidversion_code() == base.get_androidversion_code() == '400100'
    assert apk.is_signed_v2() and apk.is_signed_v3()
    cert = apk.get_certificates_der_v3()[0]
    assert cert == base.get_certificates_der_v3()[0]
    report = {
        'passed': True, 'sha256': meta['sha256'], 'bytes': meta['bytes'],
        'native_methods_changed': len(delta), 'other_native_methods_identical': len(original) - len(delta),
        'other_apk_payloads_identical': len(names) - 2, 'checked_member_references': refs,
        'dex5_method_ids': symbols.method_counts['classes5.dex'],
        'certificate_sha256': hashlib.sha256(cert).hexdigest(), 'android_device_tested': False,
    }
    (B / 'verification.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), 'utf8')
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
