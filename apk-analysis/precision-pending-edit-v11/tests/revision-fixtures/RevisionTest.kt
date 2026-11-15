
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
