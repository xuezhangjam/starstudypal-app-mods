"""Three-way classroom migration. Inputs are user-supplied APKs, never bundled.

Preserve 3.2.2.0 vendor code/resources; transfer only stock-3.2.1.0 -> v8 deltas.
No device or school service is accessed by this script.
"""
from pathlib import Path
from copy import deepcopy
import hashlib, json, os, re, shutil, subprocess, sys, zipfile
from lxml import etree as E
from filter_native import METHOD, methods, norm

B = Path(__file__).resolve().parent
ROOT = B.parent.parent
T = ROOT / 'tools/apk-patch'
JAVA = T / 'java21/zulu21.52.203-ca-jre21.0.12.1-win_x64/bin/java.exe'
STOCK = ROOT / '学生端课堂3.2.1.0.apk'
MOD = ROOT / '学生端课堂-3.2.1.0-网页打开方式选择-v8.apk'
NEW = ROOT / '学生端课堂3.2.2.0原版.apk'
DEST = ROOT / '学生端课堂-3.2.2.0-v8功能迁移.apk'
INPUT_HASHES = {
    STOCK: '2204879fd2c7e8046a966e7f91f3c315c73a2e3c48ee6485e6fa5e9593a790ac',
    MOD: '37c9f9836f2a99a5f8607c2e80ae33174c6485e7bd9b59955532c2b5cb1ec80f',
    NEW: '5cfc70699bb1ba7925b5d37260803884ec23970c3dcafdfa658f44d5fe69e7e5',
}
A = '{http://schemas.android.com/apk/res/android}'
PARSER = E.XMLParser(remove_blank_text=True)

def long(p):
    return Path('\\\\?\\' + str(p.resolve())) if os.name == 'nt' else p

def write(p, s):
    p.parent.mkdir(parents=True, exist_ok=True)
    q = p.with_name(p.name + '.tmp')
    q.write_text(s, encoding='utf-8')
    os.replace(q, p)

def xmlwrite(p, tree):
    write(p, E.tostring(tree, encoding='unicode', pretty_print=True,
                       xml_declaration=False))

def run(args):
    proc = subprocess.run(list(map(str, args)), capture_output=True, text=True,
                          encoding='utf-8', errors='replace')
    print(proc.stdout[-12000:], flush=True)
    if proc.stderr: print(proc.stderr[-12000:], flush=True)
    proc.check_returncode()

def decode(apk, out, resources=False):
    if not out.exists():
        run([JAVA, '-jar', T/'apktool.jar', 'd', '-s' if resources else '-r',
             '-o', out, apk])

def thin(apk, name, dex='classes4.dex'):
    out = B / (name + '.apk')
    with zipfile.ZipFile(apk) as z, zipfile.ZipFile(out, 'w') as w:
        w.writestr('classes.dex', z.read(dex))
        w.writestr('AndroidManifest.xml', z.read('AndroidManifest.xml'))
    decode(out, B/name)

def clone(src, dst, include=None):
    for p in long(src).rglob('*'):
        rel = p.relative_to(long(src))
        if rel.parts[0] in {'build', 'dist'} or (include and rel.parts[0] not in include):
            continue
        q = long(dst)/rel
        if p.is_dir(): q.mkdir(parents=True, exist_ok=True)
        elif not q.exists():
            q.parent.mkdir(parents=True, exist_ok=True)
            os.link(p, q)

def sem(el, unordered=False):
    children = [sem(c, unordered) for c in el]
    if unordered: children.sort(key=repr)
    return (el.tag, tuple(sorted(el.attrib.items())), (el.text or '').strip(), tuple(children))

def tree(folder, rel):
    return E.parse(str(B/folder/rel), PARSER)

def publics(folder):
    return {(x.get('type'), x.get('name')): int(x.get('id'),16)
            for x in tree(folder, 'res/values/public.xml').getroot()}

def migrate_resources():
    work = B/'resources-work'
    clone(B/'resources-new', work, {'res', 'AndroidManifest.xml', 'apktool.yml'})
    for f in ['AndroidManifest.xml', 'res/values/public.xml', 'res/values/ids.xml']:
        write(work/f,(B/'resources-new'/f).read_text('utf-8'))
    plan = json.loads((B/'resource-plan.json').read_text('utf-8'))
    assert not plan['removed'] and not plan['value_removed'] and not plan['value_conflicts']
    for x in plan['value_changed']:
        # apktool sorts enum/flag/style declarations; these are not modifications.
        assert sem(E.fromstring(x['old']['xml']), True) == sem(E.fromstring(x['mod']['xml']), True), x['key']
    for f in plan['changed']:
        o,m,n = [tree(k,f) for k in ('resources-old-stock','resources-old-mod','resources-new')]
        if f == 'res/layout/item_course_history.xml':
            # Keep the newly visible vendor classroom-report button, add download only.
            assert sum(x.get(A+'id')=='@id/mod_course_download' for x in m.getroot()) == 1
            new = n.getroot()
            new.append(deepcopy(next(x for x in m.getroot() if x.get(A+'id')=='@id/mod_course_download')))
            xmlwrite(work/f, n)
        else:
            assert sem(o.getroot()) == sem(n.getroot()), f
            write(work/f, (B/'resources-old-mod'/f).read_text('utf-8'))
    for f in plan['added']:
        assert not (B/'resources-new'/f).exists()
        write(work/f, (B/'resources-old-mod'/f).read_text('utf-8'))
    for x in plan['value_added']:
        f=x['mod']['file']; doc=E.parse(str(work/f),PARSER)
        el=E.fromstring(x['mod']['xml'])
        assert not any(y.tag==el.tag and y.get('name')==el.get('name') for y in doc.getroot())
        doc.getroot().append(el); xmlwrite(work/f,doc)
    oldpub=publics('resources-old-mod'); newpub=publics('resources-new')
    pubdoc=E.parse(str(work/'res/values/public.xml'),PARSER)
    added=[]
    for key in sorted(oldpub.keys()-newpub.keys()):
        typ,name=key; id_=max(v for (t,_),v in newpub.items() if t==typ)+1
        assert id_>>16 == oldpub[key]>>16
        E.SubElement(pubdoc.getroot(),'public',type=typ,name=name,id=hex(id_))
        newpub[key]=id_; added.append({'type':typ,'name':name,'id':hex(id_)})
    xmlwrite(work/'res/values/public.xml',pubdoc)
    remap={v:newpub[k] for k,v in oldpub.items() if v!=newpub[k]}
    # The manifest contains no newly added vendor components. Preserve vendor removals.
    o,m,n=[tree(k,'AndroidManifest.xml') for k in ('resources-old-stock','resources-old-mod','resources-new')]
    changes=[]
    for activity in m.findall('application/activity'):
        name=activity.get(A+'name')
        before=next(x for x in o.findall('application/activity') if x.get(A+'name')==name)
        after=next(x for x in n.findall('application/activity') if x.get(A+'name')==name)
        for attr in set(before.attrib)|set(activity.attrib):
            if before.get(attr)==activity.get(attr): continue
            assert after.get(attr)==before.get(attr), (name,attr)
            if activity.get(attr) is None: after.attrib.pop(attr,None)
            else: after.set(attr,activity.get(attr))
            changes.append((name,attr,before.get(attr),activity.get(attr)))
        for child in activity:
            if not any(sem(child)==sem(c) for c in before):
                assert not any(sem(child)==sem(c) for c in after)
                after.append(deepcopy(child))
    xmlwrite(work/'AndroidManifest.xml',n)
    write(B/'resource-remap.json',json.dumps({hex(k):hex(v) for k,v in remap.items()},indent=2))
    write(B/'resource-merge.json',json.dumps({'added_resources':added,'remapped_ids':len(remap),
          'changed_layouts':plan['changed'],'added_files':plan['added'],
          'manifest_attributes':changes,'vendor_report_visibility_preserved':True,
          'vendor_removed_route_filter_preserved':True},ensure_ascii=False,indent=2))
    return remap

def remap_smali(s, ids):
    # ID constants in instructions/field values, not arbitrary user-visible strings.
    def line(l):
        if l.lstrip().startswith(('const-string','#','.source')): return l
        return re.sub(r'(?<![\w])0x7f[0-9a-fA-F]{6}\b',
                      lambda m:hex(ids.get(int(m[0],16),int(m[0],16))),l)
    return '\n'.join(line(l) for l in s.split('\n'))

def prefix(body, code):
    return re.sub(r'(    \.locals \d+\n)',lambda m:m[0]+'\n'+code+'\n',body,count=1)

def conflict(file, sig, native):
    if file=='com/hljzjx/student/classroom/review/MainActivity.smali':
        assert native is None; return None
    if file=='com/nice/room/ui/RoomLiveActivity.smali':
        return prefix(native,'    invoke-static {p0}, Lcom/hljzjx/classroom/mod/LocalApps;->install(Landroid/app/Activity;)V')
    if file.endswith('answer/QuestionAskAnswerBaseFragment.smali'):
        return prefix(native,'''    invoke-static {p0}, Lcom/hljzjx/classroom/mod/HandwriteContinuation;->consumeSubmit(Lcom/nice/room/ui/roomlive/fragment/ask/answer/QuestionAskAnswerBaseFragment;)Z
    move-result v0
    if-eqz v0, :mod_original_submit_322
    return-void
    :mod_original_submit_322''')
    if file.endswith('view/QuestionAskHandwriteAnswerView.smali'):
        needle='    move-object v5, p0'
        assert native.count(needle)==1
        return native.replace(needle,'''    invoke-static {p3, v6}, Lcom/hljzjx/classroom/mod/ContinuationResults;->guardImages(Landroid/view/View;Lkotlin/jvm/functions/Function1;)Lkotlin/jvm/functions/Function1;
    move-result-object v6

'''+needle)
    if file.endswith('discussion/DiscussionFragment.smali'):
        needle='invoke-virtual {p2, v2}, Lcom/hailiang/handwrite/widget/HandwriteView;->setPenColor(I)V'
        assert native.count(needle)==1
        return native.replace(needle,'invoke-static {p2, v2}, Lcom/hljzjx/classroom/mod/DiscussionTools;->memberColor(Lcom/hailiang/handwrite/widget/HandwriteView;I)V')
    raise AssertionError((file,sig))

def migrate_native(ids):
    work=B/'work4'; clone(B/'new-original4',work)
    old=long(B/'old-stock4/smali'); mod=long(B/'old-mod4/smali'); new=long(B/'new-original4/smali')
    plan=json.loads((B/'native-plan.json').read_text('utf-8'))
    conflicts={(x['file'],x['method']) for x in plan['conflicts']}
    report=[]
    for x in plan['native']:
        file=x['file']; src=(new/file).read_text('utf-8'); om=methods((old/file).read_text('utf-8')); mm=methods((mod/file).read_text('utf-8')); nm=methods(src)
        expected={}
        for sig in x['changed']:
            if (file,sig) in conflicts:
                result=conflict(file,sig,nm.get(sig))
                if result is None:
                    report.append({'file':file,'method':sig,'action':'satisfied_by_official_removal'});continue
            else:
                assert norm(nm[sig])==norm(om[sig]),(file,sig)
                result=remap_smali(mm[sig],ids)
            assert result!=nm[sig],(file,sig)
            expected[sig]=result
            report.append({'file':file,'method':sig,'action':'adapted' if (file,sig) in conflicts else 'ported'})
        src=METHOD.sub(lambda m:expected.get(m[1].split()[-1],m[0]),src)
        for sig in x['added']:
            assert sig not in nm,(file,sig)
            src+='\n\n'+remap_smali(mm[sig],ids)+'\n'
            report.append({'file':file,'method':sig,'action':'added'})
        # Preserve official field initializers/annotations; add only actual new fields.
        a_fields={line.split(' = ')[0].split()[-1] for line in (old/file).read_text('utf-8').splitlines() if line.startswith('.field ')}
        b_fields=[line for line in (mod/file).read_text('utf-8').splitlines() if line.startswith('.field ') and line.split(' = ')[0].split()[-1] not in a_fields]
        for field in b_fields:
            assert field.split(' = ')[0].split()[-1] not in {line.split(' = ')[0].split()[-1] for line in src.splitlines() if line.startswith('.field ')}
            idx=src.index('.method ')
            src=src[:idx]+remap_smali(field,ids)+'\n\n'+src[idx:]
        if src!=(new/file).read_text('utf-8'):write(work/'smali'/file,src)
    for file in plan['added_mod_classes']:
        assert not (new/file).exists()
        write(work/'smali'/file,remap_smali((mod/file).read_text('utf-8'),ids))
    write(B/'native-merge.json',json.dumps(report,ensure_ascii=False,indent=2))

def split_dex():
    # Stock DEX4 already contains 65,525 method IDs (limit 65,536). Relocate
    # unchanged Guava hash classes and our early helpers into a new DEX. Android
    # 29+ loads all DEX files with the same application classloader, preserving
    # package-private access. No original class/method is removed from the APK.
    work=B/'work4'; out=B/'work13'
    for f in ['apktool.yml','AndroidManifest.xml']:
        dest=out/f;dest.parent.mkdir(parents=True,exist_ok=True)
        if f.endswith('.xml'):
            q=dest.with_suffix('.tmp');q.write_bytes((work/f).read_bytes());os.replace(q,dest)
        else:write(dest,(work/f).read_text('utf-8'))
    files=list(long(work/'smali/com/google/common/hash').rglob('*.smali'))
    plan=json.loads((B/'native-plan.json').read_text('utf-8'))
    files += [long(work/'smali')/f for f in plan['added_mod_classes']]
    moved=[]
    for p in files:
        rel=p.relative_to(long(work/'smali'));dst=long(out/'smali')/rel
        write(dst,p.read_text('utf-8'))
        # Both paths have been verified under the isolated build work directory.
        assert p.is_relative_to(long(B/'work4/smali'))
        p.unlink();moved.append(rel.as_posix())
    write(B/'dex-split.json',json.dumps({'moved_to_classes13':moved,
           'reason':'Official DEX4 has 65525 method IDs. Preserve every class and method across DEX4/13.'},indent=2))

def migrate_helpers(ids):
    helper=B/'helpers-original'
    if not helper.exists():
        with zipfile.ZipFile(MOD) as z,zipfile.ZipFile(B/'helpers.apk','w') as w:
            w.writestr('AndroidManifest.xml',z.read('AndroidManifest.xml'))
            for i in range(6,13):w.writestr('classes'+(str(i-5) if i>6 else '')+'.dex',z.read(f'classes{i}.dex'))
        decode(B/'helpers.apk',helper)
    clone(helper,B/'helpers-work')
    changed=[]
    for p in long(helper).rglob('*.smali'):
        src=p.read_text('utf-8'); dst=remap_smali(src,ids)
        if dst!=src:write(long(B/'helpers-work')/p.relative_to(long(helper)),dst);changed.append(str(p.relative_to(long(helper))))
    write(B/'helper-remap.json',json.dumps(changed,ensure_ascii=False,indent=2))
    return changed

def sig(name):
    return name.startswith('META-INF/') and name.upper().endswith(('.MF','.SF','.RSA','.DSA','.EC'))

def main():
    for p,h in INPUT_HASHES.items(): assert hashlib.sha256(p.read_bytes()).hexdigest()==h,p
    for apk,name in [(STOCK,'old-stock4'),(MOD,'old-mod4'),(NEW,'new-original4')]:
        if not (B/name).exists():thin(apk,name)
    for apk,name in [(STOCK,'resources-old-stock'),(MOD,'resources-old-mod'),(NEW,'resources-new')]:decode(apk,B/name,True)
    if '--build-only' not in sys.argv:
        ids=migrate_resources();migrate_native(ids);changed=migrate_helpers(ids);split_dex()
    else:changed=json.loads((B/'helper-remap.json').read_text('utf-8'))
    run([JAVA,'-jar',T/'apktool.jar','b',B/'work4','-o',B/'classes4-patch.apk'])
    run([JAVA,'-jar',T/'apktool.jar','b',B/'work13','-o',B/'classes13-patch.apk'])
    if changed:run([JAVA,'-jar',T/'apktool.jar','b',B/'helpers-work','-o',B/'helpers-remapped.apk'])
    # Bundled Windows aapt2 cannot consume this workspace's Chinese path.
    # Mirror only resource inputs to an ASCII build directory; never rewrite
    # hardlinked source files in place.
    stage=Path(os.environ['LOCALAPPDATA'])/'CodexBuilds/classroom-migration-322'
    stage.mkdir(parents=True,exist_ok=True); resource_stage=stage/'resources-work'
    for p in (B/'resources-work').rglob('*'):
        rel=p.relative_to(B/'resources-work')
        if rel.parts[0] not in {'res','AndroidManifest.xml','apktool.yml'}:continue
        q=resource_stage/rel
        if p.is_dir():q.mkdir(parents=True,exist_ok=True)
        else:
            q.parent.mkdir(parents=True,exist_ok=True);temp=q.with_name(q.name+'.linktmp')
            temp.unlink(missing_ok=True);os.link(p,temp);os.replace(temp,q)
    run([JAVA,'-jar',T/'apktool.jar','b',resource_stage,'-o',B/'resources-patch.apk'])
    with zipfile.ZipFile(B/'classes4-patch.apk') as z:patch={'classes4.dex':z.read('classes.dex')}
    with zipfile.ZipFile(B/'classes13-patch.apk') as z:patch['classes13.dex']=z.read('classes.dex')
    with zipfile.ZipFile(B/'resources-patch.apk') as z:
        patch.update({n:z.read(n) for n in z.namelist() if n in ('AndroidManifest.xml','resources.arsc') or n.startswith('res/')})
    with zipfile.ZipFile(MOD) as z:
        for i in range(6,13):patch[f'classes{i}.dex']=z.read(f'classes{i}.dex')
        for n in ['assets/mod_toolbar/onion.png','assets/mod_toolbar/pip.png']:patch[n]=z.read(n)
    if changed:
        with zipfile.ZipFile(B/'helpers-remapped.apk') as z:
            for i in range(6,13):patch[f'classes{i}.dex']=z.read('classes'+(str(i-5) if i>6 else '')+'.dex')
    unsigned=B/'classroom-322-unsigned.apk'
    with zipfile.ZipFile(NEW) as z,zipfile.ZipFile(unsigned,'w') as w:
        for info in z.infolist():
            n=info.filename
            if sig(n) or n in patch or n.startswith('res/'):continue
            w.writestr(info,z.read(n))
        for n,data in patch.items():w.writestr(n,data,compress_type=zipfile.ZIP_STORED if n.endswith(('.dex','.arsc','.png','.jpg','.webp')) else zipfile.ZIP_DEFLATED)
    stage.mkdir(parents=True,exist_ok=True);shutil.copyfile(unsigned,stage/unsigned.name)
    signed=stage/'signed';signed.mkdir(exist_ok=True)
    result=signed/'classroom-322-aligned-signed.apk';result.unlink(missing_ok=True)
    run([JAVA,'-jar',T/'uber-apk-signer.jar','-a',stage/unsigned.name,'-o',signed,
         '--ks',T/'signing/classroom-mod.jks','--ksAlias','classroommod','--ksPass','android','--ksKeyPass','android'])
    shutil.copyfile(result,DEST)
    meta={'inputs':{p.name:h for p,h in INPUT_HASHES.items()},'output':DEST.name,
          'sha256':hashlib.sha256(DEST.read_bytes()).hexdigest(),'size':DEST.stat().st_size,
          'version_name':'3.2.2.0','version_code':322000,'package':'com.hljzjx.edu.student.classroom',
          'helper_classes_resource_remapped':changed,'device_tested':False,'school_service_tested':False}
    write(B/'build.json',json.dumps(meta,ensure_ascii=False,indent=2));print(json.dumps(meta,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
