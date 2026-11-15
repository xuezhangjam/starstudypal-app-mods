"""Exact-baseline, narrow client fixes. Does not alter school services or identity."""
import re,json
from build import B,write,PAT
FRAG='com/nice/room/ui/roomlive/fragment/discussion/DiscussionFragment'
MANAGER='com/nice/room/ui/roomlive/RoomLiveDocumentManager'
CORE='com/hailiang/handwrite/widget/HandwriteCoreView'
P='Lcom/hljzjx/classroom/repairs/'

def patch(base):
 changes=[];texts={}
 def edit(rel,selector,change):
  s=texts.get(rel,(base/'smali'/(rel+'.smali')).read_text('utf8'))
  found=[m for m in PAT.finditer(s) if selector(m[1].split()[-1])];assert len(found)==1,(rel,len(found))
  m=found[0];new=change(m[0]);assert new!=m[0]
  texts[rel]=s[:m.start()]+new+s[m.end():]
  changes.append({'file':rel+'.smali','method':m[1].split()[-1]})
 def start(body,call):
  marker=re.search(r'    \.locals \d+\n',body);assert marker
  return body[:marker.end()]+'\n'+call+'\n'+body[marker.end():]
 edit(FRAG,lambda n:n=='takePhoto()V',lambda body:start(body,'    invoke-static {p0}, '+P+'DiscussionPhotos;->begin(L'+FRAG+';)V'))
 def photo_result(body):
  marker='    if-gtz v2, :cond_1';assert body.count(marker)==1
  return body.replace(marker,'''    move/from16 v3, p2
    invoke-static {v0, v2, v3}, '''+P+'''DiscussionPhotos;->result(L'''+FRAG+''';II)I
    move-result v2
    if-ltz v2, :cond_5
'''+marker,1)
 edit(FRAG,lambda n:n.startswith('onActivityResult('),photo_result)
 def preserve_upload(body):
  marker='    invoke-virtual {v0}, Lcom/nice/room/ui/roomlive/fragment/discussion/DiscussionViewModel;->cancelSaveImage()V'
  assert body.count(marker)==1
  # In endDiscussion p0 is preserved and v1 is not live across this void call.
  assert '.locals 2' in body
  return body.replace(marker,'''    invoke-static {p0}, '''+P+'''DiscussionPhotos;->keepUpload(L'''+FRAG+''';)Z
    move-result v1
    if-nez v1, :mod_keep_photo_upload
'''+marker+'''
    :mod_keep_photo_upload''',1)
 edit(FRAG,lambda n:n=='endDiscussion()V',preserve_upload)
 texts[FRAG]+='''
.method public final modCanImportAfterEnd()Z
    .locals 1
    invoke-direct {p0}, L'''+FRAG+''';->modEndedWriteAllowed()Z
    move-result v0
    return v0
.end method
'''
 def layout(body):
  marker='    invoke-static {p0, p1}, Lcom/hljzjx/classroom/mod/LiveBrowse;->layout(L'+MANAGER+';Lcom/alibaba/fastjson/JSONObject;)V'
  assert body.count(marker)==1
  return body.replace(marker,marker+'''
    invoke-static {p0, p1}, '''+P+'''DocumentViewport;->adjust(L'''+MANAGER+''';Lcom/alibaba/fastjson/JSONObject;)Lcom/alibaba/fastjson/JSONObject;
    move-result-object p1
''',1)
 edit(MANAGER,lambda n:n.startswith('setPptLayout('),layout)
 def scroll_message(body):
  marker='    invoke-static {p0, p1}, Lcom/hljzjx/classroom/mod/LiveBrowse;->message(L'+MANAGER+';Lcom/alibaba/fastjson/JSONObject;)V'
  assert body.count(marker)==1
  return body.replace(marker,marker+'\n    invoke-static {p0, p1}, '+P+'DocumentViewport;->message(L'+MANAGER+';Lcom/alibaba/fastjson/JSONObject;)Lcom/alibaba/fastjson/JSONObject;\n    move-result-object p1\n',1)
 edit(MANAGER,lambda n:n.startswith('handleMqttPPTMessage('),scroll_message)
 def loaded(body):
  assert body.count('    return-void')==1
  return body.replace('    return-void','    invoke-static {p0}, '+P+'DocumentViewport;->loaded(L'+MANAGER+';)V\n\n    return-void')
 edit(MANAGER,lambda n:n.startswith('onDocumentLoaded('),loaded)
 texts[MANAGER]+='''
.method public final modDocumentType()Lcom/hailiang/document/DocumentType;
    .locals 1
    iget-object v0, p0, L'''+MANAGER+''';->documentManager:Lcom/hailiang/document/DocumentManager;
    invoke-virtual {v0}, Lcom/hailiang/document/DocumentManager;->getDocumentType()Lcom/hailiang/document/DocumentType;
    move-result-object v0
    return-object v0
.end method
'''
 # Observe unmodified sender dimensions before the SDK converts the received points.
 for name in ['path','point','paths']:
  def observer(body,name=name):
   pattern=r'    invoke-static \{p0, p1\}, Lcom/hljzjx/classroom/mod/TeacherViewport;->'+name+r'(\([^\n]+)'
   matches=list(re.finditer(pattern,body));assert len(matches)==1
   m=matches[0]
   return body[:m.end()]+'\n    invoke-static {p0, p1}, '+P+'DocumentViewport;->'+name+m[1]+'\n'+body[m.end():]
  edit(CORE,lambda n,name=name:n.startswith({'path':'restorePath(','point':'restorePathPoint(','paths':'setPathInfoList(Ljava/util/List;Z)'}[name]),observer)
 def pdf_origin(body):
  marker='    :cond_0\n';assert body.count(marker)==1
  return body.replace(marker,'''    :cond_0
    invoke-static {p0}, '''+P+'''DocumentViewport;->isPdfFrame(Landroid/view/View;)Z
    move-result v0
    if-eqz v0, :mod_legacy_teacher_offset
    return p1
    :mod_legacy_teacher_offset
''',1)
 edit(CORE,lambda n:n=='modTeacherDisplayY(F)F',pdf_origin)
 for rel,text in texts.items():write(B/'work4/smali'/(rel+'.smali'),text)
 write(B/'changes.json',json.dumps(changes,indent=2))
