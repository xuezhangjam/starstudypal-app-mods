# Executed by build.py with the immutable v7 base and an isolated work tree.
FILE='com/nice/room/ui/roomlive/interaction/impl/ThirdAppInteraction.smali'
THIRD='Lcom/nice/room/ui/roomlive/interaction/impl/ThirdAppInteraction;'
INFO='Lcom/nice/room/ui/roomlive/interaction/impl/ThirdAppInteraction$ExternalLinkInfo;'
original=(base/'smali'/FILE).read_text('utf-8')
write(work/'smali'/FILE,original)
def prefix(body,extra):
 marker=re.search(r'    \.locals \d+\n',body);assert marker
 return body[:marker.end()]+'\n'+extra+body[marker.end():]
def offer(old):
 extra='    iget-boolean v0, p0, '+THIRD+'->modWebChoiceBypass:Z\n    if-nez v0, :mod_web_original\n    invoke-static {p0}, '+HELPER+'->offer('+THIRD+')Z\n    move-result v0\n    if-eqz v0, :mod_web_original\n    return-void\n    :mod_web_original\n'
 return prefix(old,extra)
edit(FILE,'openApp()V',offer)
edit(FILE,'openApp$lambda$1('+THIRD+INFO+'Ljava/util/Set;)Lkotlin/Unit;',lambda old:prefix(old,'    invoke-static {p0, p1}, '+HELPER+'->allowNative('+THIRD+INFO+')Z\n    move-result v0\n    if-nez v0, :mod_web_current\n    sget-object v0, Lkotlin/Unit;->INSTANCE:Lkotlin/Unit;\n    return-object v0\n    :mod_web_current\n'))
edit(FILE,'end(Lkotlin/jvm/functions/Function0;)V',lambda old:prefix(old,'    invoke-static {p0}, '+HELPER+'->close('+THIRD+')V\n'))
def ended(old):
 needle='    iput-boolean p1, p0, '+THIRD+'->classroomEnded:Z\n';assert old.count(needle)==1
 return old.replace(needle,needle+'\n    invoke-static {p0}, '+HELPER+'->close('+THIRD+')V\n',1)
edit(FILE,'handleMessage(Lcom/hailiang/mqtt/classroom/RoomMqttMessageType;Ljava/lang/String;)V',ended)
path=work/'smali'/FILE;s=path.read_text('utf-8');needle='.field private modLocalOnly:Z';assert s.count(needle)==1
s=s.replace(needle,needle+'\n\n.field private modWebChoiceBypass:Z',1)
s+='''
.method public final modCanOpenWeb('''+INFO+''')Z
    .locals 2
    if-eqz p1, :mod_not_current
    iget-boolean v0, p0, '''+THIRD+'''->classroomEnded:Z
    if-nez v0, :mod_not_current
    iget-object v0, p0, '''+THIRD+'''->appInfo:'''+INFO+'''
    if-ne v0, p1, :mod_not_current
    const/4 v0, 0x1
    return v0
    :mod_not_current
    const/4 v0, 0x0
    return v0
.end method

.method public final modKeepWebShortcut()V
    .locals 0
    invoke-direct {p0}, '''+THIRD+'''->addShutcut()V
    return-void
.end method

.method public final modOpenWebInClass('''+INFO+''')V
    .locals 2
    invoke-virtual {p0, p1}, '''+THIRD+'''->modCanOpenWeb('''+INFO+''')Z
    move-result v0
    if-eqz v0, :mod_open_done
    const/4 v0, 0x1
    iput-boolean v0, p0, '''+THIRD+'''->modWebChoiceBypass:Z
    :mod_try_start
    invoke-direct {p0}, '''+THIRD+'''->openApp()V
    :mod_try_end
    .catchall {:mod_try_start .. :mod_try_end} :mod_open_failed
    const/4 v0, 0x0
    iput-boolean v0, p0, '''+THIRD+'''->modWebChoiceBypass:Z
    :mod_open_done
    return-void
    :mod_open_failed
    move-exception v1
    const/4 v0, 0x0
    iput-boolean v0, p0, '''+THIRD+'''->modWebChoiceBypass:Z
    throw v1
.end method
'''
write(path,s)
