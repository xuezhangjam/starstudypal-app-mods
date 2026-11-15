"""Execute final DEX warning/confirmation paths with modeled Android services."""
from pathlib import Path
import importlib.util
import itertools

B = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('previous_launcher_flows', B.parent / 'launcher-apps-todo/test_flows.py')
previous = importlib.util.module_from_spec(spec)
spec.loader.exec_module(previous)
O, Failure, ref, regs = previous.O, previous.Failure, previous.ref, previous.regs
F, P, A, C = previous.F, previous.P, previous.A, previous.C
CAT = 'Lcom/hljzjx/md3/LocalAppCatalog;'
DIALOG = 'Lcom/hailiang/launcher/control/dialog/ControlDialog;'
ACTION = 'Lcom/hljzjx/md3/ForceLaunchAction;'
CONFIRM = 'Lcom/hljzjx/md3/ConfirmLaunchAction;'
APP = 'Lcom/hailiang/launcher/common/app/AppLauncher;'
BUILDER = 'Lcom/hailiang/ui/designsystem/dialog/DialogProvider$Builder;'

class Machine(previous.Machine):
    def __init__(self, ms, encoded):
        super().__init__(ms, encoded)
        self.statics = {}
        self.controlled = True
        self.dialogs = []
        self.rule_reads = 0
        self.refreshes = 0
        self.fail_launch = False
        self.fail_refresh = False
        self.fail_classroom = False
        self.events = []
        self.route_presenter = False

    def execute(self, key, values, stop=None):
        info = self.ms[key]
        rr = {info[1]-len(values)+i: value for i, value in enumerate(values)}
        seq = info[2]
        pc, result, exception = 0, None, None
        raw = self.encoded[key]
        pcs = [p//2 for p, _ in raw.get_instructions_idx()]
        index = {p: i for i, p in enumerate(pcs)}
        for steps in range(5000):
            op, args = seq[pc]
            r, target, nextpc = regs(args), ref(args), pc+1
            if stop and stop(pc, op, args): return 'ORIGINAL'
            try:
                if op in ['nop', 'check-cast']: pass
                elif op.startswith('const'): rr[r[0]] = args[1][1]
                elif op == 'move-exception': rr[r[0]] = exception
                elif op.startswith('move-result'): rr[r[0]] = result
                elif op.startswith('move'): rr[r[0]] = rr[r[1]]
                elif op.startswith('iget'):
                    rr[r[0]] = rr[r[1]].fields[target.split('->')[1].split()[0]]
                    if op == 'iget-wide': rr[r[0]+1] = 0
                elif op.startswith('iput'): rr[r[1]].fields[target.split('->')[1].split()[0]] = rr[r[0]]
                elif op.startswith('sget'):
                    rr[r[0]] = self.allowed if 'allowedPackage' in target else self.statics.get(target, None if '->disposable ' in target else O(target))
                elif op.startswith('sput'):
                    if 'allowedPackage' in target:
                        self.allowed = rr[r[0]] or None
                        self.events.append(('allowed', self.allowed))
                    else: self.statics[target] = rr[r[0]]
                elif op == 'instance-of':
                    cls, v = args[-1][1], rr[r[1]]
                    rr[r[0]] = bool(isinstance(v, O) and cls == 'Landroid/content/Context;' and v.fields.get('context'))
                elif op == 'new-instance': rr[r[0]] = O(args[-1][1])
                elif op == 'cmp-long': rr[r[0]] = (rr[r[1]] > rr[r[2]]) - (rr[r[1]] < rr[r[2]])
                elif op.startswith('goto'): nextpc = args[0][1]
                elif op.startswith('if-'):
                    x, y = rr[r[0]], rr[r[1]] if len(r) > 1 else 0
                    if x is None: x = 0
                    if y is None: y = 0
                    mode = op[3:].rstrip('z')
                    if {'eq': lambda: x == y, 'ne': lambda: x != y, 'lt': lambda: x < y,
                        'ge': lambda: x >= y, 'gt': lambda: x > y, 'le': lambda: x <= y}[mode]():
                        nextpc = args[-1][1]
                elif op.startswith('invoke-'): result = self.invoke(target, [rr.get(x) for x in r])
                elif op.startswith('return'): return None if op == 'return-void' else rr[r[0]]
                else: raise AssertionError((key, pc, op, args))
            except Failure as failure:
                exception, hit = failure, False
                handlers = raw.get_code().get_handlers()
                for item in raw.get_code().get_tries():
                    if item.get_start_addr() <= pcs[pc] < item.get_start_addr()+item.get_insn_count():
                        handler = next(h for h in handlers.get_list() if h.get_off()-handlers.get_off() == item.get_handler_off())
                        if handler.get_handlers(): destination = handler.get_handlers()[0].get_addr()
                        else: destination = handler.get_catch_all_addr()
                        nextpc, hit = index[destination], True
                        break
                if not hit: raise
            pc = nextpc
        raise AssertionError(('nonterminating DEX', key))

    def invoke(self, target, v):
        owner, name = target.split('->')
        name = name.split('(')[0]
        if owner == A and name == 'requestAppListAndControl':
            self.events.append(('request', bool(v[1])))
            return None
        if owner.endswith('/MainView;') and name == 'startApp' and self.route_presenter:
            return self.execute(self.key(A, name), v)
        if owner == C:
            if name in ['showControlDialog', 'needControlDialog']: return self.call(C, name, v)
            if name == 'request':
                self.rule_reads += 1
                self.events.append(('rule', v[1], self.allowed, len(self.enabled)))
                return O(appPeriod=O(packageName=v[1], appName='Fixture app') if self.controlled else None,
                         preTipAppPeriod=None)
            if name == 'refresh':
                self.refreshes += 1
                if self.fail_refresh: raise Failure('refresh failed')
                return None
            if name == 'getDayType': return 'school'
        if owner == DIALOG: return self.call(DIALOG, name, v)
        if owner.startswith(DIALOG[:-1]+'$$ExternalSyntheticLambda') and name in ['<init>', 'invoke']:
            return self.call(owner, name, v)
        if owner == CAT and name == 'isLocal': return self.call(CAT, name, v)
        if owner in [ACTION, CONFIRM] and name in ['<init>', 'invoke']: return self.call(owner, name, v)
        if owner == BUILDER:
            builder = v[0]
            if name == '<init>': builder.fields.update(negative=None, positive=None); return None
            if name in ['title', 'message', 'dialogHolder', 'negative', 'positive', 'cancelable']:
                builder.fields[name] = v[1:] if name in ['negative', 'positive'] else v[1]
                return builder
            if name == 'buildAndShow':
                self.dialogs.append(builder)
                self.events.append(('dialog', builder.fields.get('title', 'original-control'), self.allowed, len(self.enabled)))
                return O('MessageBoxDisposable')
        if owner == APP and name == 'safeOpenApp':
            if self.fail_launch: raise Failure('launch failed')
            self.launched.append((v[1], v[2] or None))
            self.events.append(('launch', v[1], v[2], self.allowed))
            return None
        if name == 'setClassRoomEnabled':
            if self.fail_classroom: raise Failure('classroom policy unavailable')
        if name == 'getInstance' and 'BaseLauncherApplication' in owner: return O(context=True)
        if name == 'getApplicationContext': return v[0]
        if owner == 'Ljava/lang/System;' and name == 'currentTimeMillis': return 1700000000000
        if name == 'getContext': return v[0].fields['context']
        if name in ['getPackageName', 'getAppName', 'getLogoUrl', 'getControlEnable', 'getAppPeriod', 'getPreTipAppPeriod']:
            field = name[3].lower()+name[4:]
            return v[0].fields[field]
        if name == 'contains': return v[1] in v[0]
        if name in ['checkNotNullParameter', 'dismiss', 'show', 'i']: return None
        if name == 'inControl': return self.controlled
        if name == 'makeText': return O('Toast', text=v[1])
        return super().invoke(target, v)

    def click(self, dialog, side):
        button = dialog.fields[side]
        if button and button[1]:
            return self.call(button[1].kind, 'invoke', [button[1], O(context=O(context=True))])

def run(ms, encoded):
    report = previous.run(ms, encoded)
    checks, cases = 0, 0
    def ok(value, message):
        nonlocal checks
        checks += 1
        assert value, message

    # The lookup itself must never allow/enable a package or clear another
    # active launch while the caller is only deciding whether an app exists.
    for pkg, installed in itertools.product(['app.test', '', None], [False, True]):
        vm = Machine(ms, encoded)
        vm.allowed = 'earlier.selected'
        vm.installed = {pkg} if installed and pkg else set()
        found = vm.call(F, 'isInstalled', [O(context=True), pkg])
        ok(bool(found) == bool(pkg and installed), 'pure installed lookup result')
        ok(vm.allowed == 'earlier.selected' and not vm.enabled, 'checking install does not grant an exception')
        cases += 1

    packages = ['com.tencent.mm', 'com.ss.android.ugc.aweme', 'com.netease.cloudmusic',
                'com.hljzjx.edu.student.classroom', 'com.nice.recordclass', 'app.test']
    packages += ['new.unissued.app'+str(i) for i in range(8)]
    for route, pkg, controlled in itertools.product(['home', 'catalog', 'presenter'], packages, [False, True]):
        vm = Machine(ms, encoded)
        vm.installed = {pkg}
        vm.controlled = controlled
        vm.allowed = pkg  # stale exceptions cannot suppress a new manual warning
        activity = O(context=True)
        if route == 'home': vm.call(A, 'startApp', [activity, pkg, None])
        elif route == 'catalog':
            vm.call(CAT, 'openIfLocal', [activity, O(packageName=pkg, logoUrl='local-app://')])
        else:
            vm.route_presenter = True
            key = next(k for k in ms if k[0] == P and k[1] == 'checkApp' and k[2] == '(Ljava/lang/String;)V')
            vm.execute(key, [O(iView=activity, cachedAppMap=O(map={})), pkg])
        ok(vm.rule_reads == 1, 'every manual route checks real cached control rules')
        ok(any(e[0] == 'rule' and e[2] is None and e[3] == 0 for e in vm.events), 'warning checked before enable/allow')
        target = 'com.hljzjx.student.classroom.review.MainActivity' if pkg.endswith('.classroom') else None
        if controlled:
            ok(not vm.launched and not vm.enabled and vm.allowed is None, 'control dialog alone never launches/enables')
            ok(len(vm.dialogs) == 1 and vm.dialogs[0].fields['negative'][0] == '仍然打开'
               and vm.dialogs[0].fields['positive'][0] == '我知道了', 'original warning retains both choices')
            vm.click(vm.dialogs[0], 'negative')
            ok(len(vm.dialogs) == 2 and vm.dialogs[1].fields['title'] == '确认仍然打开', 'still-open keeps existing confirmation')
            ok(not vm.enabled and not vm.launched and vm.allowed is None, 'secondary dialog can still be canceled without enabling')
            vm.click(vm.dialogs[1], 'positive')
            ok(vm.launched == [(pkg, target)] and vm.allowed == pkg, 'confirmed app opens through original launcher with correct target')
            ok(vm.enabled and all(item[0] == pkg for item in vm.enabled), 'only selected package enabled')
            reads = vm.rule_reads
            ok(vm.call(C, 'needControlDialog', [activity, pkg, True]) in [None, 0]
               and vm.rule_reads == reads, 'foreground monitor respects confirmed temporary exception')
            vm.call(F, 'clear', [])
            ok(vm.allowed is None, 'return-to-home cleanup removes temporary exception')
        else:
            ok(not vm.dialogs and vm.launched == [(pkg, target)], 'uncontrolled installed apps open directly')
            ok(vm.allowed == pkg and vm.refreshes == 1, 'normal open sets scoped exception then refreshes original control')
        cases += 1

    # Acknowledging or canceling an existing warning must not run its force path.
    vm = Machine(ms, encoded)
    vm.call(A, 'startApp', [O(context=True), 'app.test', None])
    vm.click(vm.dialogs[0], 'positive')
    ok(not vm.launched and vm.allowed is None and ('app.test', True) not in vm.enabled, 'acknowledge is not open')
    vm = Machine(ms, encoded)
    vm.call(A, 'startApp', [O(context=True), 'app.test', None])
    vm.click(vm.dialogs[0], 'negative')
    vm.click(vm.dialogs[1], 'negative')
    ok(not vm.launched and not vm.enabled and vm.allowed is None, 'canceling confirmation never enables or opens')

    # Unsupported OEM policy/refresh errors cannot crash a manual confirmed open.
    for policy, refresh, classroom in itertools.product([False, True], repeat=3):
        vm = Machine(ms, encoded)
        vm.policy, vm.fail_refresh, vm.fail_classroom = policy, refresh, classroom
        pkg = 'com.hljzjx.edu.student.classroom'
        vm.call(F, 'open', [O(context=True), pkg])
        ok(vm.launched == [(pkg, 'com.hljzjx.student.classroom.review.MainActivity')], 'policy failures leave original safe-open attempt available')
        ok(vm.allowed == pkg, 'only current package allowed after policy failure')
        cases += 1
    for missing, failure in itertools.product([False, True], repeat=2):
        vm = Machine(ms, encoded)
        vm.installed = set() if missing else {'app.test'}
        vm.fail_launch = failure
        vm.call(F, 'open', [O(context=True), 'app.test'])
        if missing or failure:
            ok(not vm.launched and vm.allowed is None, 'failed launch does not retain temporary exception')
        cases += 1
    vm = Machine(ms, encoded)
    result = vm.call(CAT, 'openIfLocal', [O(context=True), O(logoUrl='https://original/icon')])
    ok(not result and not vm.dialogs and not vm.launched, 'issued and H5 beans stay on original presenter path')
    for enabled, in_set in itertools.product([False, True], repeat=2):
        vm = Machine(ms, encoded)
        result = vm.call(A, 'isAppControlled', [O(controlApps={'app.test'} if in_set else set()),
                                               O(packageName='app.test', controlEnable=enabled)])
        ok(bool(result) == (enabled and in_set), 'control indicator reflects original metadata and current set')
        cases += 1
    return {**report, 'warning_flow_scenarios': cases, 'warning_flow_assertions': checks,
            'warning_test_scope': 'final DEX for warning, actions and confirmation; modeled Android UI, policy and cached control responses; no device/MDM activity'}
