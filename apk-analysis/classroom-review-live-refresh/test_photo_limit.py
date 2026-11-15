"""Execute the actual native photo-entry DEX against modeled image counts."""
def run(method,own_count,peer_count):
 code=list(method.get_instructions_idx());indices={pc:i for i,(pc,_) in enumerate(code)}
 owner={'fragment':True};images=[{'userId':7} for _ in range(own_count)]+[{'userId':8} for _ in range(peer_count)]
 regs={method.get_code().get_registers_size()-1:owner};result=None;index=0;opened=0;limited=0;listener=None
 for _ in range(100000):
  pc,ins=code[index];op=ins.get_name();args=ins.get_operands();r=[a[1] for a in args if int(a[0])==0];ref=next((a[2] for a in args if len(a)>2),None);nextpc=index+1
  if op.startswith('invoke'):
   obj,target=ref.split('->',1);name=target.split('(',1)[0];v=[regs[x] for x in r]
   if name in ['getViewModel','getImageRecordFlow']:result=owner
   elif name=='getValue':result=images
   elif name=='iterator':result={'list':v[0],'at':0}
   elif name=='hasNext':result=v[0]['at']<len(v[0]['list'])
   elif name=='next':result=v[0]['list'][v[0]['at']];v[0]['at']+=1
   elif name=='add':v[0].append(v[1]);result=True
   elif name=='size':result=len(v[0])
   elif name=='getUserId':result=7
   elif name=='getString':result='最多上传2张照片'
   elif name=='checkNotNullExpressionValue':assert v[0] is not None and isinstance(v[1],str)
   elif name=='getParentFragmentManager':assert v[0] is owner;result={'manager':owner}
   elif name=='<init>':
    if 'DiscussionFragment$takePhoto$1;' in obj:assert v[1] is owner;v[0]['owner']=owner
   elif name=='setOnTakePhotoListener':listener=v[1];assert listener['owner'] is owner
   elif name=='show$default':
    if 'AppToast;' in obj:limited+=1
    else:assert listener is not None and v[1]['manager'] is owner;opened+=1
   else:raise AssertionError(('unexpected invocation',name))
  elif op.startswith('move-result'):
   regs[r[0]]=result
   if 'wide' in op:regs[r[0]+1]=0
  elif op.startswith('move'):regs[r[0]]=regs[r[1]]
  elif op.startswith('const-string'):regs[r[0]]=ref
  elif op.startswith('const'):regs[r[0]]=args[-1][1]
  elif op=='new-instance':regs[r[0]]=[] if ref=='Ljava/util/ArrayList;' else {'type':ref}
  elif op.startswith('iget'):
   regs[r[0]]=regs[r[1]][ref.split('->')[1].split(' ')[0]]
   if 'wide' in op:regs[r[0]+1]=0
  elif op.startswith('sget'):regs[r[0]]=ref
  elif op=='cmp-long':regs[r[0]]=(regs[r[1]]>regs[r[2]])-(regs[r[1]]<regs[r[2]])
  elif op.startswith('if-'):
   a=regs[r[0]];b=regs[r[1]] if len(r)>1 else 0;mode=op[3:].rstrip('z')
   if {'eq':lambda:a==b,'ne':lambda:a!=b,'lt':lambda:a<b,'gt':lambda:a>b,'le':lambda:a<=b,'ge':lambda:a>=b}[mode]():nextpc=indices[pc+args[-1][1]*2]
  elif op.startswith('goto'):nextpc=indices[pc+args[-1][1]*2]
  elif op.startswith('return'):return opened,limited
  elif op in ['check-cast','nop']:pass
  else:raise AssertionError(('unexpected opcode',op))
  index=nextpc
 raise AssertionError('nonterminating modeled native photo flow')
def test(old,new):
 assertions=0;cases=0
 for own in [0,1,2,3,10,50,500]:
  for peers in [0,1,2,7,20]:
   cases+=1;before=run(old,own,peers);after=run(new,own,peers)
   assert before==((1,0) if own<2 else (0,1)),(own,peers,before);assertions+=1
   assert after==(1,0),(own,peers,after);assertions+=1
 return {'actual_dex_scenarios':cases,'assertions':assertions,'scope':'actual native photo-entry instructions with modeled views/image counts; no camera/gallery/HTTP execution'}
