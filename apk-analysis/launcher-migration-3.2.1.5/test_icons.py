"""Final DEX icon routing with observable PackageManager and Glide fixtures."""
def run(ms,encoded,flows):
 O,Failure=flows.O,flows.Failure
 S='Lcom/hljzjx/md3/SystemAppIcons;';L='Lcom/hljzjx/md3/LocalAppCatalog;'
 class Machine(flows.Machine):
  def __init__(self):
   super().__init__(ms,encoded);self.icons={};self.events=[];self.generic=O('system-default');self.reads=[]
  def invoke(self,target,v):
   owner,name=target.split('->');name=name.split('(')[0]
   if owner==S or owner==L and name=='bindIcon':return self.call(owner,name,v)
   if name=='isWeb':return v[0].fields['web']
   if name=='getApplicationIcon':
    self.reads.append(v[1])
    if v[1] not in self.icons:raise Failure('not installed / unavailable')
    return self.icons[v[1]]
   if name=='getDefaultActivityIcon':return self.generic
   if name=='with':return O('Glide')
   if name=='clear':self.events.append(('clear',v[1]));v[1].fields['pending_remote']=False;return None
   if name=='setImageDrawable':self.events.append(('drawable',v[1]));v[0].fields['drawable']=v[1];return None
   return super().invoke(target,v)
 checks=0;cases=0
 def ok(value,message):
  nonlocal checks;checks+=1;assert value,message
 for web in [False,True]:
  for installed in [False,True]:
   for local in [False,True]:
    vm=Machine();icon=O('adaptive-system-icon');pkg='installed.app';view=O(drawable='old',pending_remote=True);ctx=O(context=True)
    if installed:vm.icons[pkg]=icon
    got=vm.call(L,'bindIcon',[ctx,O(web=web,packageName=pkg,logoUrl='local-app://' if local else 'https://server/icon'),view])
    ok(bool(got)==(not web),'every native app bound; H5 remains on original loader')
    if web:ok(not vm.events and not vm.reads,'H5 never reads container icon or clears web artwork')
    else:
     ok(view.fields['drawable'] is (icon if installed else vm.generic),'installed adaptive drawable or system default')
     ok(vm.events[0][0]=='clear' and vm.events[1][0]=='drawable' and not view.fields['pending_remote'],'cancel old network request before binding')
     ok(vm.reads==[pkg],'use application package icon, even issued server-logo entries')
    cases+=1
 for installed in [False,True]:
  vm=Machine();ctx=O(context=True);view=O(drawable='fixed-original',pending_remote=True);pkg='shortcut.app';icon=O('shortcut-system')
  if installed:vm.icons[pkg]=icon
  result=vm.call(S,'bindInstalled',[ctx,pkg,view]);ok(bool(result)==installed,'fixed native shortcuts prefer system icon')
  ok(view.fields['drawable'] is icon if installed else view.fields['drawable']=='fixed-original','missing fixed web key retains original artwork');cases+=1
 for ctx,bean,view in [(None,O(web=False,packageName='x'),O()),(O(context=True),None,O()),(O(context=True),O(web=False,packageName='x'),None)]:
  vm=Machine();ok(not vm.call(L,'bindIcon',[ctx,bean,view]) and not vm.events,'invalid/recycled input does not crash or mutate');cases+=1
 # Negative control: the shipped previous implementation only bound synthetic
 # local-app:// items. The issued native case above would return false there.
 return {'icon_scenarios':cases,'icon_dex_assertions':checks,'icon_scope':'actual helper DEX with PackageManager/Glide fixtures; no Android rendering'}
