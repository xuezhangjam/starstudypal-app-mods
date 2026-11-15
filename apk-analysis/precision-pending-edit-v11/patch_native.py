"""Narrow display/revision hooks; native HTTP request contents are preserved."""
import json,re
from build import B,write,PAT,OWN
VM='com/hailiang/workcloud/student/shareui/work/WorkAnswerViewModel'
HOME='com/hailiang/workcloud/student/app/StudentAppNavigation$HomeFeatureNavigation'
REPO='com/hailiang/workcloud/student/data/repository/KtorWorkAnswerRepository'
REQ='Lcom/hailiang/workcloud/student/data/model/WorkGroupSubmitRequest;'
CONT='Lkotlin/coroutines/Continuation;'
SUBMIT='('+REQ+CONT+')Ljava/lang/Object;'
SELECT='com/hailiang/workcloud/student/shareui/work/select/AnswerQuestionWorkHandler'
PHOTO='com/hailiang/workcloud/student/shareui/work/photofile/PhotoFileWorkHandler'
CARD='com/hailiang/workcloud/student/shareui/work/review/components/detail/BlankReviewCardKt'
def patch(base):
 texts={};changes=[]
 def edit(rel,name,change):
  src=texts.get(rel,(base/'smali'/(rel+'.smali')).read_text('utf8'))
  matches=[m for m in PAT.finditer(src) if m[1].split('(')[0].split()[-1]==name];assert len(matches)==1,(rel,name)
  m=matches[0];body=change(m[0]);assert body!=m[0];texts[rel]=src[:m.start()]+body+src[m.end():]
  changes.append({'file':rel+'.smali','method':m[1].split()[-1]})
 def navigation(body):
  marker='    .locals 3\n';assert marker in body
  return body.replace(marker,marker+'''\n    invoke-virtual {p1}, Lcom/hailiang/workcloud/student/shareui/home/HomeworkUiModel;->getSchoolworkGroupId()J
    move-result-wide v0
    invoke-static {v0, v1}, '''+OWN+'''PendingEdits;->openRequested(J)Z
    move-result v0
    if-nez v0, :cond_0
''',1)
 edit(HOME,'registerEntries$lambda$0$0$0$0',navigation)
 def constructor(body):
  assert body.count('    return-void')==1
  # v0 remains the initialized VM; p14 is the original authenticated session provider.
  return body.replace('    return-void','    move-object/from16 v1, p14\n    invoke-static {v0, v1}, '+OWN+'PendingEdits;->attach(L'+VM+';Lcom/hailiang/workcloud/student/auth/AuthSessionProvider;)V\n\n    return-void')
 edit(VM,'<init>',constructor)
 def submitted(body):
  marker=re.search(r'    \.locals (\d+)\n',body);assert marker and int(marker[1])>=2
  return body[:marker.end()]+'''
    invoke-virtual {p1}, Lcom/hailiang/workcloud/student/data/model/WorkTask;->getId()J
    move-result-wide v0
    invoke-static {p0, v0, v1}, '''+OWN+'''PendingEdits;->isRevising(L'''+VM+''';J)Z
    move-result v0
    if-eqz v0, :mod_stock_submission_state
    const/4 v0, 0x0
    return v0
    :mod_stock_submission_state
'''+body[marker.end():]
 edit(VM,'isSubmittedByApi',submitted)
 texts[VM]+='''
.method public final modRevisionGroupId()J
    .locals 2
    iget-object v0, p0, L'''+VM+''';->route:Lcom/hailiang/workcloud/student/shareui/work/WorkAnswerRoute;
    invoke-virtual {v0}, Lcom/hailiang/workcloud/student/shareui/work/WorkAnswerRoute;->getWorkGroupId()J
    move-result-wide v0
    return-wide v0
.end method

.method public final modRevisionRepository()Lcom/hailiang/workcloud/student/data/repository/WorkAnswerRepository;
    .locals 1
    iget-object v0, p0, L'''+VM+''';->workAnswerRepository:Lcom/hailiang/workcloud/student/data/repository/WorkAnswerRepository;
    return-object v0
.end method

.method public final modRevisionHandlers()Ljava/util/Map;
    .locals 1
    iget-object v0, p0, L'''+VM+''';->handlers:Ljava/util/Map;
    return-object v0
.end method

.method public final modRevisionRefresh()V
    .locals 0
    invoke-direct {p0}, L'''+VM+''';->refreshUiState()V
    return-void
.end method
'''
 for handler in [SELECT,PHOTO]:
  texts[handler]=(base/'smali'/(handler+'.smali')).read_text('utf8')+'''
.method public final modBeginRevision()V
    .locals 1
    const/4 v0, 0x0
    iput-boolean v0, p0, L'''+handler+''';->submitted:Z
    return-void
.end method
'''
 def original(body):return body.replace(' submitWorkGroup(', ' modSubmitWorkGroupOriginal(',1)
 edit(REPO,'submitWorkGroup',original)
 texts[REPO]+='''
.method public submitWorkGroup'''+SUBMIT+'''
    .locals 1
    invoke-static {p0, p1, p2}, '''+OWN+'''PendingEdits;->submit(L'''+REPO+''';'''+REQ+CONT+''')Ljava/lang/Object;
    move-result-object v0
    return-object v0
.end method
'''
 def resume(body):
  old='L'+REPO+';->submitWorkGroup'+SUBMIT
  assert body.count(old)==1
  return body.replace(old,'L'+REPO+';->modSubmitWorkGroupOriginal'+SUBMIT)
 edit(REPO+'$submitWorkGroup$1','invokeSuspend',resume)
 def mark(body):
  signature=body.splitlines()[0]
  return signature+'''\n    .locals 0
    invoke-static/range {p0 .. p2}, '''+OWN+'''PrecisionDetailKt;->ReviewMark(Lcom/hailiang/workcloud/student/data/enums/CheckMark;Landroidx/compose/runtime/Composer;I)V
    return-void
.end method'''
 edit(CARD,'MarkIcon',mark)
 for rel,src in texts.items():write(B/'work5/smali'/(rel+'.smali'),src)
 write(B/'changes.json',json.dumps(changes,indent=2))
