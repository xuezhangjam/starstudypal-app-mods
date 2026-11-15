"""Replace only APK update orchestration, keeping original version requests."""
from pathlib import Path
import json,sys
B=Path(__file__).resolve().parent;R=B.parent.parent
from smali_tools import methods
U='Lcom/hljzjx/md3/updates/ManualUpdates;'
def apply(root,replace,write):
 changes=[]
 def edit(file,key,fn):
  p=root/file;s=p.read_text('utf8');new=fn(methods(s)[key]);write(p,replace(s,key,new));changes.append({'file':file,'method':key,'action':'changed','merge':'download-only updates'})
 def body(sig,code,locals=1):return '.method '+sig+'\n    .locals '+str(locals)+'\n'+code+'\n    return-void\n.end method'
 global_context='    invoke-static {}, Lcom/hailiang/hlutil/AppUtilKt;->getApplication()Landroid/app/Application;\n    move-result-object v0\n'
 f='com/hljzjx/launch/MyApplication.smali'
 def init(s):
  needle='    invoke-static {p0}, Lcom/hljzjx/md3/ThemeController;->apply(Landroid/content/Context;)V';assert s.count(needle)==1
  return s.replace(needle,needle+'\n    invoke-static {p0}, '+U+'->init(Landroid/app/Application;)V')
 edit(f,'onCreate()V',init)
 f='com/hljzjx/launch/ui/personcenter/PersonCenterActivity.smali'
 def settings(s):
  needle='    invoke-static {p0}, Lcom/hljzjx/schedule/ProfileSettings;->bind(Landroid/app/Activity;)V';assert s.count(needle)==1
  return s.replace(needle,needle+'\n    invoke-static {p0}, '+U+'->bindSettings(Landroid/app/Activity;)V')
 edit(f,'onCreate(Landroid/os/Bundle;)V',settings)
 f='com/hljzjx/launch/ui/main/MainPresenter.smali';sig='silentDownloadApks(Ljava/util/List;)V'
 edit(f,sig,lambda _:body('private '+sig,global_context+'    invoke-static {v0, p1}, '+U+'->detectBeans(Landroid/content/Context;Ljava/util/List;)V'))
 # Observe the complete successful response before stock force-update filtering;
 # optional updates must still be detected when forceUpdate() is false.
 f='com/hljzjx/launch/ui/main/MainPresenter$5.smali'
 sig='apply(Lcom/jchou/commonlibrary/model/BaseHttpResult;)Lcom/jchou/commonlibrary/model/BaseHttpResult;'
 def all_updates(s):
  needle='    :cond_0\n';assert s.count(needle)==1
  code='''    invoke-static {}, Lcom/hailiang/hlutil/AppUtilKt;->getApplication()Landroid/app/Application;
    move-result-object v2
    invoke-static {v2, v1}, Lcom/hljzjx/md3/updates/ManualUpdates;->detectBeans(Landroid/content/Context;Ljava/util/List;)V
'''
  return s.replace(needle,needle+'\n'+code+'\n',1)
 edit(f,sig,all_updates)
 f='com/hailiang/launcher/common/download/app/AppUpdateManager.smali'
 sig='updateApp(Ljava/util/List;)V'
 edit(f,sig,lambda _:body('public final '+sig,global_context+'    invoke-static {v0, p1}, '+U+'->detectTasks(Landroid/content/Context;Ljava/util/List;)V'))
 sig='retryUpdate(Lcom/hailiang/launcher/common/download/app/AppUpdateTask;)V'
 edit(f,sig,lambda _:body('public final '+sig,global_context+'    invoke-static {p1}, Ljava/util/Collections;->singletonList(Ljava/lang/Object;)Ljava/util/List;\n    move-result-object v1\n    invoke-static {v0, v1}, '+U+'->detectTasks(Landroid/content/Context;Ljava/util/List;)V',2))
 sig='installApp(Lcom/hailiang/launcher/common/download/app/AppUpdateTask;Ljava/io/File;)V'
 edit(f,sig,lambda _:body('private final '+sig,'',0))
 sig='installApp$lambda$3(Lcom/hailiang/launcher/common/download/app/AppUpdateTask;Ljava/io/File;)V'
 edit(f,sig,lambda _:body('private static final '+sig,'',0))
 f='com/hailiang/launcher/data/bean/response/AppHtmlListBean.smali';sig='forceUpdate()Z'
 edit(f,sig,lambda _:'.method public final '+sig+'\n    .locals 1\n    const/4 v0, 0x0\n    return v0\n.end method')
 f='com/hailiang/launcher/update/LauncherUpdateManager.smali'
 sig='showAppUpdateDialog(Landroid/content/Context;Lcom/hailiang/launcher/data/bean/response/AppHtmlListBean;)V'
 edit(f,sig,lambda _:body('public static final '+sig,'    const/4 v0, 0x0\n    invoke-static {p0, p1, v0}, '+U+'->offerBean(Landroid/content/Context;Lcom/hailiang/launcher/data/bean/response/AppHtmlListBean;Z)V'))
 for name in ['showCheckUpdateDialog','showDownloadDialog']:
  sig=name+'(Landroid/content/Context;Lcom/hailiang/launcher/data/bean/response/AppHtmlListBean;)V'
  edit(f,sig,lambda _,sig=sig:body('private final '+sig,'    const/4 v0, 0x1\n    invoke-static {p1, p2, v0}, '+U+'->offerBean(Landroid/content/Context;Lcom/hailiang/launcher/data/bean/response/AppHtmlListBean;Z)V'))
 write(B/'update-changes.json',json.dumps(changes,ensure_ascii=False,indent=2));return changes
