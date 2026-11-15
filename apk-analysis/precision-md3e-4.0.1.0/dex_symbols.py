"""Small DEX declaration index for cross-DEX ABI checking without decoding code."""
import struct

PLATFORM=('Landroid/','Ljava/','Ljavax/','Ldalvik/','Lorg/json/','Lorg/xmlpull/','Lorg/w3c/dom/','[')

class Symbols:
    def __init__(self):self.classes={};self.method_counts={}
    def add(self,data,label):
        d=data
        def u32(p):return struct.unpack_from('<I',d,p)[0]
        def uleb(p):
            result=0;shift=0
            while True:
                b=d[p];p+=1;result|=(b&127)<<shift
                if b<128:return result,p
                shift+=7
        sc,so=struct.unpack_from('<II',d,56);tc,to=struct.unpack_from('<II',d,64)
        pc,po=struct.unpack_from('<II',d,72);fc,fo=struct.unpack_from('<II',d,80)
        mc,mo=struct.unpack_from('<II',d,88);cc,co=struct.unpack_from('<II',d,96)
        string_ids=struct.unpack_from('<'+'I'*sc,d,so);type_ids=struct.unpack_from('<'+'I'*tc,d,to);cache={}
        self.method_counts[label]=mc
        def string(i):
            if i not in cache:
                _,p=uleb(string_ids[i]);cache[i]=d[p:d.find(b'\0',p)].decode('utf8',errors='replace')
            return cache[i]
        def typ(i):return string(type_ids[i])
        def proto(i):
            _,ret,off=struct.unpack_from('<III',d,po+i*12)
            pars=[] if not off else [typ(x) for x in struct.unpack_from('<'+'H'*u32(off),d,off+4)]
            return '('+''.join(pars)+')'+typ(ret)
        def method(i):
            owner,p,n=struct.unpack_from('<HHI',d,mo+i*8)
            return string(n),proto(p)
        def field(i):
            owner,t,n=struct.unpack_from('<HHI',d,fo+i*8)
            return string(n),typ(t)
        for i in range(cc):
            cls,flags,parent,interfaces,_,annotations,body,static=struct.unpack_from('<IIIIIIII',d,co+i*32)
            name=typ(cls)
            assert name not in self.classes,('duplicate class',name,label)
            info={'parent':None if parent==0xffffffff else typ(parent),
                  'interfaces':[] if not interfaces else [typ(x) for x in struct.unpack_from('<'+'H'*u32(interfaces),d,interfaces+4)],
                  'methods':set(),'fields':set(),'flags':flags,'dex':label}
            if body:
                counts=[];p=body
                for k in range(4):v,p=uleb(p);counts.append(v)
                for k,count in enumerate(counts):
                    idx=0
                    for _ in range(count):
                        delta,p=uleb(p);access,p=uleb(p);idx+=delta
                        if k>=2:
                            offset,p=uleb(p);info['methods'].add(method(idx))
                        else:info['fields'].add(field(idx))
            self.classes[name]=info
    def resolve(self,owner,name,desc,field=False,seen=None):
        seen=set() if seen is None else seen
        if owner in seen:return False
        seen.add(owner)
        if owner not in self.classes:return owner.startswith(PLATFORM)
        c=self.classes[owner]
        if (name,desc) in c['fields' if field else 'methods']:return True
        if not field and name in ('<init>','<clinit>'):return False
        parents=[p for p in [c['parent'],*c['interfaces']] if p]
        return any(self.resolve(p,name,desc,field,seen) for p in parents)
    def check(self,classes):
        refs=0;errors=[]
        for c in classes:
            for m in c.get_methods():
                for i in m.get_instructions():
                    for op in i.get_operands():
                        if len(op)<3 or int(op[0]) not in (256,258):continue
                        owner,target=op[2].split('->',1)
                        if int(op[0])==256:name,desc=target.split('(',1);desc='('+desc.replace(' ','');field=False
                        else:name,desc=target.split(' ',1);desc=desc.replace(' ','');field=True
                        if not self.resolve(owner,name,desc,field):errors.append((c.get_name(),m.get_name(),op[2]))
                        refs+=1
        return refs,errors
