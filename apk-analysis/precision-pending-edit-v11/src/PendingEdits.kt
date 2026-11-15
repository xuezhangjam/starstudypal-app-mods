package com.hailiang.workcloud.student.md3e.v3

import android.content.Context
import android.os.SystemClock
import android.widget.Toast
import androidx.lifecycle.ViewModelKt
import com.hailiang.workcloud.student.auth.AuthSession
import com.hailiang.workcloud.student.auth.AuthSessionProvider
import com.hailiang.workcloud.student.data.enums.CheckMark
import com.hailiang.workcloud.student.data.enums.ReviewCorrectionStatus
import com.hailiang.workcloud.student.data.enums.WorkType
import com.hailiang.workcloud.student.data.model.*
import com.hailiang.workcloud.student.data.repository.*
import com.hailiang.workcloud.student.shareui.home.HomeworkUiModel
import com.hailiang.workcloud.student.shareui.home.HomeworkStatus
import com.hailiang.workcloud.student.shareui.work.WorkAnswerViewModel
import com.hailiang.workcloud.student.shareui.work.WorkAnswerUiState
import com.hailiang.workcloud.student.shareui.work.select.AnswerQuestionWorkHandler
import com.hailiang.workcloud.student.shareui.work.photofile.PhotoFileWorkHandler
import java.lang.ref.WeakReference
import java.util.WeakHashMap
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.first

/** Current authenticated user's pending work only; the native request and response stay intact. */
object PendingEdits {
    private data class Request(val group: Long, val at: Long, val context: WeakReference<Context>)
    private data class Lease(val vm: WeakReference<WorkAnswerViewModel>, val auth: AuthSessionProvider,
        val account: AuthSession, val group: Long, val task: Long, val state: Long, val snapshot: String)
    private var requested: Request? = null
    private var opening: Request? = null
    private val leases = WeakHashMap<WorkAnswerRepository, MutableMap<Long, Lease>>()
    private val leaseLock = Any()

    fun request(work: HomeworkUiModel, context: Context) {
        if (work.getStatus() == HomeworkStatus.GRADING && work.getSchoolworkGroupId() > 0)
            requested = Request(work.getSchoolworkGroupId(), SystemClock.elapsedRealtime(), WeakReference(context.applicationContext))
    }
    @JvmStatic fun openRequested(group: Long): Boolean {
        val r = requested ?: return false
        requested = null
        if (r.group != group || SystemClock.elapsedRealtime() - r.at !in 0..45000) return false
        opening = r
        return true
    }
    private fun notice(r: Request, text: String) { r.context.get()?.let { Toast.makeText(it, text, Toast.LENGTH_LONG).show() } }
    private suspend fun review(repo: WorkAnswerRepository, group: Long): ReviewWork = repo.getReviewWorkDetail(group)
    private suspend fun original(repo: KtorWorkAnswerRepository, request: WorkGroupSubmitRequest): Unit = repo.modSubmitWorkGroupOriginal(request)

    private fun blankText(text: String?): Boolean = text.isNullOrBlank() || text.trim() in listOf("null", "[]", "{}")
    private fun slots(task: ReviewTask): List<Triple<Long, Long, ReviewBlank>> = task.getQuestions().flatMap { q ->
        q.getBlanks().map { Triple(q.getSource().getBigQuestionId(), q.getSource().getSubQuestionId(), it) } +
            q.getSubQuestions().flatMap { sub -> sub.getBlanks().map {
                Triple(sub.getSource().getBigQuestionId(), sub.getSource().getSubQuestionId(), it)
            } }
    }
    private fun aiPending(q: ReviewAiQuestion): Boolean = q.getCheckMark() == CheckMark.PENDING && q.getSubQuestions().all { aiPending(it) }
    internal fun eligible(task: ReviewTask): Boolean {
        if (task.getWorkType() == WorkType.COMPOSITION || task.getTeacherReviewFinished() || task.getAiGrading() || task.getHasTeacherMark()) return false
        if (task.getMaterialGroupChecks().any { it.getHasTeacherCorrection() } || !task.getAiQuestions().all { aiPending(it) }) return false
        val blanks = slots(task)
        if (task.getWorkType() == WorkType.SELECT_QUESTION && blanks.isEmpty()) return false
        return blanks.all { (_, _, b) -> b.getCheckMark() == CheckMark.PENDING && b.getOriginalCheckMark() == CheckMark.PENDING &&
            b.getTeacherCorrectMark() == CheckMark.PENDING && b.getCorrection() == ReviewCorrectionStatus.NONE &&
            blankText(b.getTeacherAnswerCheckDetail()) && blankText(b.getTeacherCorrectionStrokes()) }
    }
    /** Preserve exact native cached ink/photos, and never reopen a missing/foreign/stale answer set. */
    internal fun hasOriginals(task: ReviewTask, local: List<QuestionAnswer>, group: Long): Boolean {
        return slots(task).all { (question, sub, b) ->
            val saved = local.firstOrNull { it.getQuestionId() == question && it.getSubQuestionId() == sub && it.getIdx() == b.getIndex() }
            val answered = !blankText(b.getMyAnswer()) || !b.getStudentAnswerPicList().isNullOrEmpty() || b.getStudentAnswerJson() != null
            if (!answered) true else saved != null && saved.getWorkGroupId() == group && saved.getWorkId() == task.getSchoolworkId() &&
                (!blankText(saved.getAnswer()) || !blankText(saved.getStrokes()) || !blankText(saved.getStrokesImg()) || !saved.getImagePaths().isNullOrEmpty()) &&
                (blankText(b.getMyAnswer()) || b.getMyAnswer()?.trim() == saved.getAnswer()?.trim()) &&
                (b.getStudentAnswerPicList().isNullOrEmpty() || !saved.getImagePaths().isNullOrEmpty() || !blankText(saved.getStrokes()) || !blankText(saved.getStrokesImg()))
        }
    }
    internal fun snapshot(task: ReviewTask): String = task.toString()

    @JvmStatic fun isRevising(vm: WorkAnswerViewModel, task: Long): Boolean = synchronized(leaseLock) {
        val l = leases[vm.modRevisionRepository()]?.get(task)
        l != null && l.vm.get() === vm && l.auth.current() == l.account
    }

    @JvmStatic fun attach(vm: WorkAnswerViewModel, auth: AuthSessionProvider) {
        val r = opening ?: return
        if (vm.modRevisionGroupId() != r.group) return
        opening = null
        val account = auth.current() ?: return
        ViewModelKt.getViewModelScope(vm).launch {
            try {
                val loaded = withTimeout(20000) { vm.getUiState().first { it is WorkAnswerUiState.Success } } as WorkAnswerUiState.Success
                if (loaded.getWorkGroup().getId() != r.group || auth.current() != account) return@launch
                notice(r, "正在检查最新批阅状态…")
                val repo = vm.modRevisionRepository()
                val fresh = review(repo, r.group)
                ensureActive()
                val current = vm.getUiState().value as? WorkAnswerUiState.Success
                if (auth.current() != account || fresh.getWorkGroup().getId() != r.group || current?.getWorkGroup()?.getId() != r.group) return@launch
                val enabled = mutableListOf<Long>()
                for (task in fresh.getTasks()) {
                    if (!eligible(task)) continue
                    val handler = vm.modRevisionHandlers()[task.getWorkTask().getId()]
                    val canRestore = when (handler) {
                        is AnswerQuestionWorkHandler -> hasOriginals(task, handler.getStatus().getQuestionAnswers().orEmpty(), r.group)
                        is PhotoFileWorkHandler -> handler.getHasPhotoItems() || handler.getHasWritingAnswers()
                        else -> false
                    }
                    if (!canRestore) continue
                    val lease = Lease(WeakReference(vm), auth, account, r.group, task.getSchoolworkId(), task.getSchoolworkStateId(), snapshot(task))
                    synchronized(leaseLock) { leases.getOrPut(repo) { mutableMapOf() }[lease.task] = lease }
                    when (handler) {
                        is AnswerQuestionWorkHandler -> handler.modBeginRevision()
                        is PhotoFileWorkHandler -> handler.modBeginRevision()
                    }
                    enabled += task.getWorkTask().getId()
                }
                vm.modRevisionRefresh()
                if (enabled.isEmpty()) notice(r, "没有可修改的任务：已批改、批改中或原作答未完整加载")
                else {
                    val index = loaded.getWorkGroup().getTasks().indexOfFirst { it.getId() in enabled }
                    if (index >= 0) vm.selectTask(index)
                    notice(r, "已开放 ${enabled.size} 个未批改任务，修改后点击提交作业")
                }
            } catch (e: CancellationException) { throw e }
              catch (e: Exception) { notice(r, "暂未开放修改：${e.message ?: "无法核对批阅状态"}") }
        }
    }
    /** Runs immediately before the unchanged native HTTP submission, after native image upload. */
    @JvmStatic suspend fun submit(repo: KtorWorkAnswerRepository, request: WorkGroupSubmitRequest) {
        val touched = synchronized(leaseLock) { request.getSubSchoolworkList().mapNotNull { leases[repo]?.get(it.getSchoolworkId()) } }
        if (touched.isNotEmpty()) {
            for (l in touched) check(l.group == request.getSchoolworkGroupId() && l.vm.get() != null && l.auth.current() == l.account) { "修改会话已失效，请重新打开作业" }
            val fresh = review(repo, request.getSchoolworkGroupId())
            check(fresh.getWorkGroup().getId() == request.getSchoolworkGroupId()) { "作业记录已变化" }
            for (l in touched) {
                check(l.auth.current() == l.account) { "账号已变化，请重新打开作业" }
                val task = fresh.getTasks().singleOrNull { it.getSchoolworkId() == l.task }
                check(task != null && eligible(task) && task.getSchoolworkStateId() == l.state && snapshot(task) == l.snapshot) { "作答或批阅状态已更新，请重新打开作业" }
                check(request.getSubSchoolworkList().single { it.getSchoolworkId() == l.task }.getSchoolworkStateId() == l.state) { "作答记录已更新" }
            }
        }
        original(repo, request)
        // Native request must succeed before a revision lease is consumed.
        synchronized(leaseLock) { touched.forEach { leases[repo]?.remove(it.task) } }
    }
}
