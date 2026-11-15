"""Verify the signed APK delta, unchanged payloads, references, and auth boundaries."""
import copy,hashlib,json,re,sys,zipfile
from build import B,R,SOURCE,DEST,EXPECTED,signature
sys.path[:0]=[str(R/'apk-analysis/deps'),str(R/'apk-analysis'),str(R/'apk-analysis/precision-md3e-4.0.1.0')]
from loguru import logger
logger.remove()
from androguard.core.apk import APK
from androguard.core.dex import DEX
from canonical_notice_methods import methods
from dex_symbols import Symbols

def normal(value):
    access,regs,seq=value
    keep=[i for i,x in enumerate(seq) if x[0]!='nop'];mapping={i:j for j,i in enumerate(keep)}
    for i in range(len(seq)-1,-1,-1):
        if i not in mapping and i+1 in mapping:mapping[i]=mapping[i+1]
    result=copy.deepcopy([seq[i] for i in keep])
    for op,args in result:
        for j,(kind,v) in enumerate(args):
            if kind==3:args[j]=(kind,mapping.get(v,v))
            elif kind=='targets':args[j]=(kind,[mapping.get(t,t) for t in v])
    return access,regs,result

def key(row):
    name,desc=row['method'].split('(',1)
    return 'L'+row['file'][:-6]+';',name,'('+desc

def mapping(d):return {(a,b,c.replace(' ','')):v for (a,b,c),v in methods(d).items()}

def saved_bundle_protected(dex):
    cls=dex.get_class('Lcom/hljzjx/launch/ui/login/CommonLoginActivity;')
    method=next(m for m in cls.get_methods() if m.get_name()=='onCreate')
    regs=method.get_code().get_registers_size()
    instructions=list(method.get_instructions())
    def registers(i):return [arg[1] for arg in i.get_operands() if int(arg[0])==0]
    # The original two input words are this, Bundle. Dedicated local v2 must
    # receive the Bundle before the vendor overwrites its parameter register.
    assert regs==5 and instructions[0].get_name().startswith('move-object')
    assert registers(instructions[0])==[2,4]
    writes=('move','const','new-','iget','sget','aget','array-length','instance-of','check-cast','cmp','add','sub','mul','div','rem','and','or-','xor','shl','shr','ushr','neg','not-','int-to','long-to','float-to','double-to')
    for i in instructions[1:]:
        if i.get_name().startswith(writes):
            operands=registers(i)
            assert not operands or operands[0]!=2,('saved Bundle clobbered',i.get_name(),i.get_output())
    recovery=[i for i in instructions if 'LoginRecovery;->resumeSavedLogin' in str(i.get_operands())]
    clear=[i for i in instructions if 'LoginRecovery;->shouldClearOnCreate' in str(i.get_operands())]
    assert len(recovery)==len(clear)==1
    assert registers(recovery[0])==[3,2] and registers(clear[0])==[2]
    return True

def main():
    meta=json.loads((B/'build.json').read_text('utf8'))
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==EXPECTED
    assert hashlib.sha256(DEST.read_bytes()).hexdigest()==meta['sha256']
    symbols=Symbols();deltas=[];checked=[];untouched_methods=0
    with zipfile.ZipFile(SOURCE) as base,zipfile.ZipFile(DEST) as out:
        assert out.testzip() is None and len(out.namelist())==len(set(out.namelist()))
        original={n for n in base.namelist() if not signature(n)}
        assert {n for n in out.namelist() if not signature(n)}==original|{'classes11.dex'}
        assert {n for n in original if base.read(n)!=out.read(n)}=={'classes3.dex','classes5.dex'}
        for n in out.namelist():
            if re.fullmatch(r'classes\d*\.dex',n):symbols.add(out.read(n),n)
        for n in ('classes3.dex','classes5.dex'):
            old,new=DEX(base.read(n)),DEX(out.read(n))
            om,nm=mapping(old),mapping(new)
            assert om.keys()==nm.keys()
            delta={k for k in om if normal(om[k])!=normal(nm[k])}
            expected={key(row) for row in meta['changed_methods'] if row['dex']==n}
            assert delta==expected,{'dex':n,'unexpected':list(delta-expected),'missing':list(expected-delta)}
            changed_owners={k[0] for k in delta}
            checked.extend(c for c in new.get_classes() if c.get_name() in changed_owners)
            deltas.extend(delta);untouched_methods+=len(om)-len(delta)
            for c in old.get_classes():
                other=new.get_class(c.get_name())
                assert (c.get_access_flags(),c.get_superclassname(),c.get_interfaces())==(other.get_access_flags(),other.get_superclassname(),other.get_interfaces())
                assert {(f.get_name(),f.get_descriptor(),f.get_access_flags()) for f in c.get_fields()}=={(f.get_name(),f.get_descriptor(),f.get_access_flags()) for f in other.get_fields()}
            if n=='classes3.dex':
                native=nm
                assert saved_bundle_protected(new)
                # Regression negative control: the first Samsung APK must fail
                # this exact final-DEX register check.
                bad=R/'星学伴mod-3.2.1.5-三星登录与提示崩溃修复.apk'
                with zipfile.ZipFile(bad) as z:bad_dex=DEX(z.read('classes3.dex'))
                rejected=False
                try:saved_bundle_protected(bad_dex)
                except AssertionError:rejected=True
                assert rejected,'broken v1 incorrectly passed register regression'
        helper=DEX(out.read('classes11.dex'))
        assert out.read('classes11.dex')==(B/'helper-dex/classes.dex').read_bytes()
        assert all(c.get_name().startswith('Lcom/hljzjx/samsung/') for c in helper.get_classes()),'API declarations leaked'
        checked.extend(helper.get_classes())
        refs,errors=symbols.check(checked)
        assert not errors,errors[:30]
        assert all(n<65536 for n in symbols.method_counts.values())
        # No authentication failure handling, credential mutation or token
        # interceptors were changed by this Samsung patch.
        assert not any(k[0] in {
            'Lcom/hljzjx/launch/ui/login/LoginActivity;',
            'Lcom/hljzjx/launch/ui/login/base/LoginBaseActivity;',
            'Lcom/jchou/commonlibrary/utils/LoginUtil;',
            'Lcom/hailiang/opensdk/LauncherData;',
            'Lcom/hailiang/opensdk/SaasData;',
            'Lcom/hailiang/libhttp/utils/RequestErrorUtil;',
            'Lcom/hailiang/core/util/RequestErrorUtil;',
            'Lcom/hailiang/libhttp/interceptors/TokenInterceptor;',
            'Lcom/hailiang/libhttp/interceptors/Auth401Interceptor;',
        } for k in deltas)
        hm=mapping(helper)
        for k,v in hm.items():
            if k[0]=='Lcom/hljzjx/samsung/LoginRecovery;':
                assert not any(s in str(v) for s in ('updateToken','setToken','clearToken','clearLoginInfo','clearSaasInfo','http','System;->exit'))
        actual=next(v for k,v in native.items() if k[0]=='Lcom/hailiang/ui/designsystem/toast/ToastManager;' and k[1]=='actualToast')
        calls=[str(args) for op,args in actual[2] if op.startswith('invoke-')]
        assert next(i for i,v in enumerate(calls) if 'PageHints;->show' in v)<next(i for i,v in enumerate(calls) if 'ToastProvider;->create' in v)
        create=next(v for k,v in native.items() if k[0]=='Lcom/hljzjx/launch/ui/login/CommonLoginActivity;' and k[1]=='onCreate')
        assert 'LoginRecovery;->shouldClearOnCreate' in str(create) and 'LoginRecovery;->resumeSavedLogin' in str(create)
        # No remaining unpatched framework show sites in our changed code trees.
        for cls in checked:
            if cls.get_name().startswith('Lcom/hljzjx/samsung/'):continue
            assert not any('Landroid/widget/Toast;->show()V' in str(i.get_operands()) for m in cls.get_methods() for i in m.get_instructions())
    apk,base_apk=APK(str(DEST)),APK(str(SOURCE))
    assert apk.get_package()==base_apk.get_package()=='com.hljzjx.edu.student.launch'
    assert apk.get_androidversion_name()==base_apk.get_androidversion_name()=='3.2.1.5'
    assert apk.get_androidversion_code()==base_apk.get_androidversion_code()=='32015'
    assert apk.is_signed_v2() and apk.is_signed_v3()
    cert=hashlib.sha256(apk.get_certificates_der_v3()[0]).hexdigest()
    assert cert==hashlib.sha256(base_apk.get_certificates_der_v3()[0]).hexdigest()=='0262266e6908148d5411f0d6f190818d95cdb4f859556b6d5f53ab7109e244ca'
    report={k:v for k,v in meta.items() if k!='changed_methods'}
    report.update({'changed_methods':len(deltas),'unchanged_methods_in_rebuilt_dex':untouched_methods,'unchanged_payloads':len(original)-2,'checked_member_references':refs,'dex_method_id_counts':symbols.method_counts,'certificate_sha256':cert,'login_recovery_tests':json.loads((B/'login-tests.json').read_text('utf8')),'saved_bundle_register_regression':{'v2_passed':True,'broken_v1_rejected':True}})
    (B/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
