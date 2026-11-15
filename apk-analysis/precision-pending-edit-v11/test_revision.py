"""Compiled Kotlin revision workflow using explicit model/API fixtures; no school requests."""
from pathlib import Path
import hashlib,json,os,subprocess
from build import B,R,JAVA,T,write
D=R/'tools/precision-compose'
def run(args):
 p=subprocess.run(list(map(str,args)),capture_output=True,text=True,encoding='utf8',errors='replace');assert p.returncode==0,p.stdout+p.stderr;return p.stdout
sources={
'android/content/Context.java':'package android.content;public class Context {public Context getApplicationContext(){return this;}}',
'android/os/SystemClock.java':'package android.os;public class SystemClock {public static long time=100;public static long elapsedRealtime(){return time;}}',
'android/widget/Toast.java':'package android.widget;public class Toast {public static final int LENGTH_LONG=1;public static String last;public static Toast makeText(android.content.Context c,CharSequence s,int n){last=s.toString();return new Toast();}public void show(){}}',
'androidx/lifecycle/ViewModelKt.java':'package androidx.lifecycle;public class ViewModelKt {public static kotlinx.coroutines.CoroutineScope scope;public static kotlinx.coroutines.CoroutineScope getViewModelScope(ViewModel vm){return scope;}}',
'Fixture.java':r'''
import java.util.*;
import com.hailiang.workcloud.student.data.enums.*;
import com.hailiang.workcloud.student.data.model.*;
import com.hailiang.workcloud.student.data.repository.*;
import com.hailiang.workcloud.student.shareui.work.*;
import com.hailiang.workcloud.student.shareui.work.select.*;
import com.hailiang.workcloud.student.shareui.work.photofile.*;
import com.hailiang.workcloud.student.shareui.home.*;
import com.hailiang.workcloud.student.auth.*;
import kotlinx.coroutines.flow.*;
import kotlin.coroutines.Continuation;
public class Fixture {
 public static class B extends ReviewBlank {
  public String answer="A",teacher="",teacherInk="";public CheckMark mark=CheckMark.PENDING,original=CheckMark.PENDING,teacherMark=CheckMark.PENDING;public ReviewCorrectionStatus correction=ReviewCorrectionStatus.NONE;
  public CheckMark getCheckMark(){return mark;}public CheckMark getOriginalCheckMark(){return original;}public CheckMark getTeacherCorrectMark(){return teacherMark;}public ReviewCorrectionStatus getCorrection(){return correction;}
  public String getTeacherAnswerCheckDetail(){return teacher;}public String getTeacherCorrectionStrokes(){return teacherInk;}public int getIndex(){return 1;}public String getMyAnswer(){return answer;}public List<String> getStudentAnswerPicList(){return Collections.emptyList();}
 }
 public static class WQ extends WorkQuestion {public long getBigQuestionId(){return 42;}public long getSubQuestionId(){return 0;}}
 public static class Q extends ReviewQuestion {
  public B blank=new B();public boolean empty;public WorkQuestion getSource(){return new WQ();}public List<ReviewBlank> getBlanks(){return empty?Collections.emptyList():Collections.singletonList(blank);}public List<ReviewSubQuestion> getSubQuestions(){return Collections.emptyList();}
 }
 public static class WT extends WorkTask {public long getId(){return 7;}public long getSchoolworkId(){return 7;}}
 public static class RT extends ReviewTask {
  public Q q=new Q();public WorkType type=WorkType.SELECT_QUESTION;public boolean finished,ai,teacher;public long state=70;
  public WorkType getWorkType(){return type;}public boolean getTeacherReviewFinished(){return finished;}public boolean getAiGrading(){return ai;}public boolean getHasTeacherMark(){return teacher;}
  public List<MaterialGroupCheck> getMaterialGroupChecks(){return Collections.emptyList();}public List<ReviewAiQuestion> getAiQuestions(){return Collections.emptyList();}public List<ReviewQuestion> getQuestions(){return Collections.singletonList(q);}public WorkTask getWorkTask(){return new WT();}public long getSchoolworkId(){return 7;}public long getSchoolworkStateId(){return state;}
  public String toString(){return "task="+state+";"+q.blank.answer+";"+q.blank.mark+";"+finished+";"+type;}
 }
 public static class WG extends WorkGroup {public long id=1;public long getId(){return id;}public List<WorkTask> getTasks(){return Collections.singletonList(new WT());}}
 public static class RW extends ReviewWork {public WG group=new WG();public RT task=new RT();public WorkGroup getWorkGroup(){return group;}public List<ReviewTask> getTasks(){return Collections.singletonList(task);}}
 public static class QA extends QuestionAnswer {
  public long group=1,work=7;public String answer="A";public long getQuestionId(){return 42;}public long getSubQuestionId(){return 0;}public int getIdx(){return 1;}public long getWorkGroupId(){return group;}public long getWorkId(){return work;}public String getAnswer(){return answer;}public String getStrokes(){return "";}public String getStrokesImg(){return "";}public List<String> getImagePaths(){return Collections.emptyList();}
 }
 public static class WS extends WorkStatus {public List<QuestionAnswer> answers=new ArrayList<QuestionAnswer>();public List<QuestionAnswer> getQuestionAnswers(){return answers;}}
 public static class H extends AnswerQuestionWorkHandler {public boolean submitted=true;public WS status=new WS();public H(){status.answers.add(new QA());}public WorkStatus getStatus(){return status;}public void modBeginRevision(){submitted=false;}}
 public static class PH extends PhotoFileWorkHandler {public boolean submitted=true,photos=true;public boolean getHasPhotoItems(){return photos;}public boolean getHasWritingAnswers(){return false;}public void modBeginRevision(){submitted=false;}}
 public static class Repo extends KtorWorkAnswerRepository {
  public RW work=new RW();public int reads,posts;public boolean fail,pauseReview,pauseOriginal;public WorkGroupSubmitRequest received;public Runnable onRead;public Continuation reviewContinuation,originalContinuation;
  public Object getReviewWorkDetail(long group,Continuation<? super ReviewWork> c){reads++;if(onRead!=null)onRead.run();if(pauseReview){reviewContinuation=c;return kotlin.coroutines.intrinsics.IntrinsicsKt.getCOROUTINE_SUSPENDED();}return work;}
  public Object modSubmitWorkGroupOriginal(WorkGroupSubmitRequest r,Continuation<? super kotlin.Unit> c){posts++;received=r;if(fail)throw new IllegalStateException("native server failure");if(pauseOriginal){originalContinuation=c;return kotlin.coroutines.intrinsics.IntrinsicsKt.getCOROUTINE_SUSPENDED();}return kotlin.Unit.INSTANCE;}
 }
 public static class Auth implements AuthSessionProvider {public AuthSession account=new AuthSession();public AuthSession current(){return account;}}
 public static class Success extends WorkAnswerUiState.Success {public WG group=new WG();public WorkGroup getWorkGroup(){return group;}}
 public static class VM extends WorkAnswerViewModel {
  public Repo repo=new Repo();public H handler=new H();public Map<Long,WorkHandler> handlers=new HashMap<Long,WorkHandler>();public MutableStateFlow<WorkAnswerUiState> flow=StateFlowKt.MutableStateFlow(new Success());public int refreshed,selected=-1;
  public VM(){handlers.put(7L,handler);}public long modRevisionGroupId(){return 1;}public WorkAnswerRepository modRevisionRepository(){return repo;}public Map<Long,WorkHandler> modRevisionHandlers(){return handlers;}public void modRevisionRefresh(){refreshed++;}public void selectTask(int i){selected=i;}public StateFlow<WorkAnswerUiState> getUiState(){return flow;}
 }
 public static class Home extends HomeworkUiModel {public long getSchoolworkGroupId(){return 1;}public HomeworkStatus getStatus(){return HomeworkStatus.GRADING;}}
 public static class Sub extends SubSchoolworkSubmit {public long state=70;public long getSchoolworkId(){return 7;}public long getSchoolworkStateId(){return state;}}
 public static class Request extends WorkGroupSubmitRequest {public Sub sub=new Sub();public long getSchoolworkGroupId(){return 1;}public List<SubSchoolworkSubmit> getSubSchoolworkList(){return Collections.singletonList(sub);}}
}
''',
'RevisionTest.kt':r'''
import com.hailiang.workcloud.student.md3e.v3.PendingEdits
import com.hailiang.workcloud.student.data.enums.*
import com.hailiang.workcloud.student.auth.AuthSession
import kotlinx.coroutines.*
import kotlin.coroutines.*
import androidx.lifecycle.ViewModelKt
var checks=0
fun ok(value:Boolean,why:String){checks++;check(value){why}}
val context=android.content.Context()
fun open(vm:Fixture.VM,auth:Fixture.Auth=Fixture.Auth()):Fixture.Auth {
 PendingEdits.request(Fixture.Home(),context);check(PendingEdits.openRequested(1));PendingEdits.attach(vm,auth);return auth
}
fun denied(change:(Fixture.VM)->Unit,reason:String){val vm=Fixture.VM();change(vm);open(vm);ok(vm.handler.submitted,reason);ok(vm.repo.posts==0,"no request during eligibility check");}
fun main()=runBlocking {
 ViewModelKt.scope=CoroutineScope(SupervisorJob()+Dispatchers.Unconfined)
 val normal=Fixture.Repo();val unchanged=Fixture.Request();PendingEdits.submit(normal,unchanged);ok(normal.posts==1&&normal.reads==0&&normal.received===unchanged,"ordinary submission delegates unchanged");
 val vm=Fixture.VM();val auth=open(vm);ok(!vm.handler.submitted&&vm.refreshed==1&&vm.selected==0,"pending task reopened in native handler");ok(vm.repo.reads==1&&vm.repo.posts==0,"opening only reads status");ok(PendingEdits.isRevising(vm,7),"refresh keeps active native revision editable");ok(!PendingEdits.isRevising(Fixture.VM(),7),"another VM cannot reuse lease");
 val req=Fixture.Request();PendingEdits.submit(vm.repo,req);ok(vm.repo.posts==1&&vm.repo.received===req,"same original request goes to native method");ok(!PendingEdits.isRevising(vm,7),"lease consumed after successful native response");ok(vm.repo.work.task.q.blank.mark==CheckMark.PENDING,"client never changes grading data");
 denied({it.repo.work.task.finished=true},"finished teacher review blocked")
 denied({it.repo.work.task.ai=true},"active AI grading blocked")
 denied({it.repo.work.task.teacher=true},"teacher annotations block revision")
 denied({it.repo.work.task.q.blank.mark=CheckMark.CORRECT},"already marked answer blocked")
 denied({it.repo.work.task.q.blank.original=CheckMark.HALF_WRONG},"original partial grade blocked")
 denied({it.repo.work.task.q.blank.teacherMark=CheckMark.WRONG},"teacher correction mark blocked")
 denied({it.repo.work.task.q.blank.correction=ReviewCorrectionStatus.SAVED},"existing correction flow preserved")
 denied({it.repo.work.task.q.blank.teacher="{teacher:1}"},"teacher detail blocked")
 denied({it.handler.status.answers.clear()},"missing original cache cannot become blank submission")
 denied({(it.handler.status.answers[0] as Fixture.QA).group=2},"foreign local answer blocked")
 denied({(it.handler.status.answers[0] as Fixture.QA).answer="B"},"stale cached objective answer blocked")
 denied({it.repo.work.task.type=WorkType.COMPOSITION},"external composition is not reopened")
 denied({it.repo.work.task.q.empty=true},"missing question records rejected")
 val photo=Fixture.VM();val ph=Fixture.PH();photo.handlers[7]=ph;photo.repo.work.task.type=WorkType.FILE_UPLOAD;photo.repo.work.task.q.empty=true;open(photo);ok(!ph.submitted,"pending photo/file handler retains original content and becomes editable")
 val graded=Fixture.VM();open(graded);graded.repo.work.task.q.blank.mark=CheckMark.CORRECT;val blocked=runCatching{PendingEdits.submit(graded.repo,Fixture.Request())};ok(blocked.isFailure&&graded.repo.posts==0,"fresh grade blocks submission before native HTTP")
 val changed=Fixture.VM();open(changed);changed.repo.work.task.q.blank.answer="B";ok(runCatching{PendingEdits.submit(changed.repo,Fixture.Request())}.isFailure&&changed.repo.posts==0,"changed server answer cannot be overwritten")
 val account=Fixture.VM();val provider=open(account);provider.account=AuthSession();ok(runCatching{PendingEdits.submit(account.repo,Fixture.Request())}.isFailure&&account.repo.posts==0,"account change invalidates revision")
 val retry=Fixture.VM();open(retry);retry.repo.fail=true;ok(runCatching{PendingEdits.submit(retry.repo,Fixture.Request())}.isFailure&&PendingEdits.isRevising(retry,7),"native failure propagates and keeps editable draft");retry.repo.fail=false;PendingEdits.submit(retry.repo,Fixture.Request());ok(retry.repo.posts==2&&!PendingEdits.isRevising(retry,7),"retry validates and only successful response consumes lease")
 val suspended=Fixture.VM();open(suspended);suspended.repo.pauseReview=true;suspended.repo.pauseOriginal=true
 val deferred=async(Dispatchers.Unconfined){PendingEdits.submit(suspended.repo,Fixture.Request())}
 ok(!deferred.isCompleted&&suspended.repo.posts==0,"suspended status read cannot submit early")
 @Suppress("UNCHECKED_CAST") (suspended.repo.reviewContinuation as Continuation<com.hailiang.workcloud.student.data.model.ReviewWork>).resume(suspended.repo.work)
 ok(!deferred.isCompleted&&suspended.repo.posts==1&&PendingEdits.isRevising(suspended,7),"suspended native response keeps lease until completion")
 @Suppress("UNCHECKED_CAST") (suspended.repo.originalContinuation as Continuation<Unit>).resume(Unit);deferred.await();ok(!PendingEdits.isRevising(suspended,7),"coroutine resumption completes once")
 val expired=Fixture.Home();PendingEdits.request(expired,context);android.os.SystemClock.time+=46000;ok(!PendingEdits.openRequested(1),"expired navigation intent ignored")
 val moved=Fixture.VM();val movedAuth=Fixture.Auth();moved.repo.onRead=Runnable{movedAuth.account=AuthSession()};open(moved,movedAuth);ok(moved.handler.submitted,"account changed during opening read leaves task locked")
 println("PASS $checks compiled Kotlin revision assertions, native API fixtures only")
}
'''
}
root=B/'tests/revision-fixtures';classes=B/'revision-test-classes';classes.mkdir(exist_ok=True)
for name,source in sources.items():write(root/name,source)
jars=[p for p in D.glob('*.jar') if not any(x in p.name for x in ['compiler','daemon','reflect','sources','script-runtime'])]
cp=os.pathsep.join(map(str,[classes,B/'ui.jar',B/'api.jar',R/'tools/android-sdk/android-34-ext12/android.jar',*jars]))
run([JAVA,'-jar',T/'ecj.jar','-proc:none','-source','8','-target','8','-warn:none','-encoding','UTF-8','-cp',cp,'-d',classes,*list(root.rglob('*.java'))])
compiler=os.pathsep.join(str(D/n) for n in ['kotlin-compiler-embeddable-2.3.0.jar','kotlin-stdlib-2.3.0.jar','kotlin-script-runtime-2.3.0.jar','kotlin-reflect-1.6.10.jar','kotlin-daemon-embeddable-2.3.0.jar','kotlinx-coroutines-core-jvm-1.8.0.jar','annotations-13.0.jar'])
run([JAVA,'-cp',compiler,'org.jetbrains.kotlin.cli.jvm.K2JVMCompiler','-no-stdlib','-no-reflect','-jvm-target','1.8','-classpath',cp,'-d',classes,root/'RevisionTest.kt'])
result=run([JAVA,'-cp',cp,'RevisionTestKt']);write(B/'revision-test-results.txt',result)
write(B/'revision-tests.json',json.dumps({'passed':True,'result':result.strip(),'ui_jar_sha256':hashlib.sha256((B/'ui.jar').read_bytes()).hexdigest(),'scope':__doc__},ensure_ascii=False,indent=2));print(result)
