"""Patch only manifest version attributes without rebuilding any resources."""
import struct
def version(data,oldcode,newcode,oldname,newname):
 d=bytearray(data);p=struct.unpack_from('<H',d,2)[0];pool=None;edits=[]
 while p<len(d):
  typ,header,size=struct.unpack_from('<HHI',d,p)
  assert size>=header and size>0
  if typ==1:
   count,_,flags,start,_=struct.unpack_from('<IIIII',d,p+8)
   offsets=struct.unpack_from('<'+'I'*count,d,p+header);strings=[];locations=[]
   for offset in offsets:
    q=p+start+offset
    if flags&0x100:
     if d[q]&128:q+=2
     else:q+=1
     length=d[q];q+=1
     if length&128:length=((length&127)<<8)|d[q];q+=1
     raw=bytes(d[q:q+length]);strings.append(raw.decode('utf8'));locations.append((q,length,'utf8'))
    else:
     length=struct.unpack_from('<H',d,q)[0];q+=2
     if length&0x8000:length=((length&0x7fff)<<16)|struct.unpack_from('<H',d,q)[0];q+=2
     raw=bytes(d[q:q+length*2]);strings.append(raw.decode('utf-16le'));locations.append((q,length*2,'utf-16le'))
   pool=(strings,locations)
  if typ==0x102:
   assert pool;strings,locations=pool
   if strings[struct.unpack_from('<I',d,p+20)[0]]=='manifest':
    start,attrs,count=struct.unpack_from('<HHH',d,p+24)
    for i in range(count):
     q=p+16+start+i*attrs;name=strings[struct.unpack_from('<I',d,q+4)[0]]
     if name=='versionCode':
      assert d[q+15]==0x10 and struct.unpack_from('<I',d,q+16)[0]==oldcode
      struct.pack_into('<I',d,q+16,newcode);edits.append(name)
     elif name=='versionName':
      assert d[q+15]==3
      index=struct.unpack_from('<I',d,q+16)[0];at,length,encoding=locations[index]
      assert strings[index]==oldname
      encoded=newname.encode(encoding);assert len(encoded)==length
      d[at:at+length]=encoded;edits.append(name)
  p+=size
 assert sorted(edits)==['versionCode','versionName']
 assert len(d)==len(data)
 return bytes(d)
