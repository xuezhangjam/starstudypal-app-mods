package com.hailiang.workcloud.student.md3e.v3

import android.graphics.Rect
import android.view.MotionEvent
import android.view.View
import com.hailiang.handwrite.bean.PathInfo
import com.hailiang.handwrite.bean.PointInfo
import com.hailiang.question.widget.view.QuestionHandwriteView
import java.lang.ref.WeakReference
import java.util.WeakHashMap

data class HistoryStatus(val undo: Boolean = false, val redo: Boolean = false,
    val visible: Boolean = true, val available: Boolean = false)

/** UI-thread only. No network calls, global drawing modes, or native listener replacement. */
object InkHistory {
    private data class CanvasKey(val user: Long, val question: Long, val sub: Long, val state: Long,
        val answer: Long, val idx: Int, val answerType: Int, val solveType: Int, val width: Int, val height: Int)
    private class State(val key: CanvasKey) {
        val journal = InkJournal()
        var before: List<InkPath>? = null
        var pending = false
        var ticket = 0
        var hidden = false
        var oldVisibility = View.VISIBLE
        var touched = 0L
    }
    private val states = WeakHashMap<QuestionHandwriteView, State>()
    private var active = WeakReference<QuestionHandwriteView>(null)
    private var clock = 0L
    private fun key(v: QuestionHandwriteView) = CanvasKey(v.getUserId(), v.getQuestionId(),
        v.getSubQuestionId(), v.getQuestionStateId(), v.getAnswerId(), v.getIdx(),
        v.getAnswerType(), v.getSolveType(), v.width, v.height)

    private fun eligible(v: QuestionHandwriteView, hidden: Boolean = false): Boolean =
        v.isAttachedToWindow && v.width > 0 && v.height > 0 && v.getCanDraw() &&
        !v.isInGeometryEditMode() && (if (hidden) v.parent is View && (v.parent as View).isShown
            else v.isShown && v.getGlobalVisibleRect(Rect()))

    fun capture(v: QuestionHandwriteView): List<InkPath>? {
        var points = 0
        val paths = v.getPathInfoList()
        if (paths.size > 4000) return null
        return paths.map { p ->
            val list = p.pointsList.orEmpty()
            points += list.size
            if (points > 60000) return null
            InkPath(p.alpha, p.bottom, p.color, p.drawType, p.left, p.right, p.top,
                p.pathID, p.userMark, p.strokeWidth, list.map { q ->
                    InkPoint(q.color, q.index, q.phoneHeight, q.phoneWidth, q.type,
                        q.x, q.y, q.drawTime, q.pathId, q.pressure)
                })
        }
    }
    fun nativePaths(paths: List<InkPath>): List<PathInfo> = paths.map { p -> PathInfo().apply {
        alpha=p.alpha; bottom=p.bottom; color=p.color; drawType=p.drawType; left=p.left
        right=p.right; top=p.top; pathID=p.pathID; userMark=p.userMark; strokeWidth=p.strokeWidth
        pointsList=p.points.map { q -> PointInfo().apply {
            color=q.color; index=q.index; phoneHeight=q.phoneHeight; phoneWidth=q.phoneWidth
            type=q.type; x=q.x; y=q.y; drawTime=q.drawTime; pathId=q.pathId; pressure=q.pressure
        } }
    } }

    @JvmStatic fun beforeTouch(v: QuestionHandwriteView, event: MotionEvent?) {
        if (event?.actionMasked != MotionEvent.ACTION_DOWN) return
        try {
            if (!eligible(v)) return
            reveal()
            val identity = key(v)
            var s = states[v]
            if (s == null || s.key != identity) {
                forget(v)
                while (states.size >= 4) states.entries.minByOrNull { it.value.touched }?.key?.let { forget(it) }
                s = State(identity); states[v] = s
            }
            // Finish a posted UP before a very fast following DOWN.
            finish(v, s)
            active = WeakReference(v); s.touched = ++clock
            s.before = capture(v)
            if (s.before == null) s.journal.reset()
            else s.journal.synchronize(s.before!!)
            s.pending = s.before != null; s.ticket++
        } catch (_: Exception) { forget(v) } // A history fault cannot consume the native touch.
    }

    @JvmStatic fun afterTouch(v: QuestionHandwriteView, event: MotionEvent?) {
        val action = event?.actionMasked
        if (action != MotionEvent.ACTION_UP && action != MotionEvent.ACTION_CANCEL) return
        try {
            val s = states[v] ?: return
            if (!s.pending) return
            val ticket = s.ticket
            val weak = WeakReference(v)
            // Native stroke finalization runs first; do not retain/recycle MotionEvent objects.
            v.post { weak.get()?.let { current ->
                if (states[current] === s && ticket == s.ticket) {
                    try { finish(current, s) } catch (_: Exception) { forget(current) }
                }
            } }
        } catch (_: Exception) { forget(v) }
    }

    private fun finish(v: QuestionHandwriteView, s: State) {
        if (!s.pending) return
        val before = s.before
        s.before = null; s.pending = false
        if (s.key != key(v) || !eligible(v)) { s.journal.reset(); return }
        val after = capture(v)
        if (before == null || after == null) s.journal.reset()
        else s.journal.record(before, after)
    }

    private fun current(): Pair<QuestionHandwriteView, State>? {
        val v = active.get() ?: return null
        val s = states[v] ?: return null
        if (s.key != key(v) || !eligible(v, s.hidden)) return null
        return v to s
    }

    fun status(): HistoryStatus { return try {
        val (v, s) = current() ?: return HistoryStatus()
        HistoryStatus(!s.pending && !s.hidden && s.journal.canUndo,
            !s.pending && !s.hidden && s.journal.canRedo, !s.hidden, true)
    } catch (_: Exception) { HistoryStatus() } }

    fun undo(): Boolean = move(false)
    fun redo(): Boolean = move(true)
    private fun move(forward: Boolean): Boolean {
        var restore: List<InkPath>? = null
        var targetView: QuestionHandwriteView? = null
        return try {
            val (v, s) = current() ?: return false
            if (s.pending || s.hidden) return false
            val before = capture(v) ?: return false
            val target = if (forward) s.journal.redoTarget(before) else s.journal.undoTarget(before)
            if (target == null) return false
            restore = before; targetView = v
            // False means current canvas coordinates: no second scaling on zoomed pages.
            v.setPathInfoList(nativePaths(target), false)
            val actual = capture(v) ?: throw IllegalStateException("无法读取笔迹")
            if (forward) s.journal.didRedo(actual) else s.journal.didUndo(actual)
            v.modSaveHistory() // Original QuestionEvent / draft / submission pipeline, even empty ink.
            true
        } catch (_: Exception) {
            try {
                if (targetView != null && restore != null) {
                    targetView.setPathInfoList(nativePaths(restore), false)
                    targetView.modSaveHistory()
                    forget(targetView)
                }
            } catch (_: Exception) { }
            false
        }
    }

    fun toggleVisibility() {
        try {
            val (v, s) = current() ?: return
            if (s.pending) return
            if (s.hidden) { v.visibility = s.oldVisibility; s.hidden = false }
            else { s.oldVisibility = v.visibility; v.visibility = View.INVISIBLE; s.hidden = true }
        } catch (_: Exception) { }
    }
    fun reveal() {
        states.forEach { (v, s) -> if (s.hidden) { v.visibility = s.oldVisibility; s.hidden = false } }
    }
    @JvmStatic fun forget(v: QuestionHandwriteView) {
        val s = states.remove(v)
        if (s?.hidden == true) v.visibility = s.oldVisibility
        if (active.get() === v) active.clear()
    }
}
