package com.hailiang.workcloud.student.md3e.v3

/** Immutable copies. The SDK mutates its own point objects while drawing. */
data class InkPoint(val color: Int, val index: Int, val phoneHeight: Int, val phoneWidth: Int,
    val type: Int, val x: Int, val y: Int, val drawTime: Long, val pathId: Long, val pressure: Float)

data class InkPath(val alpha: Float, val bottom: Int, val color: Int, val drawType: Int,
    val left: Int, val right: Int, val top: Int, val pathID: Long, val userMark: Long,
    val strokeWidth: Float, val points: List<InkPoint>)

/** Bounded, per-canvas history, including whole-line erasures and original z-order. */
class InkJournal(private val maxEntries: Int = 32, private val maxChangedPoints: Int = 60000) {
    private data class Edit(val before: List<InkPath>, val after: List<InkPath>, val cost: Int)
    private val undo = ArrayDeque<Edit>()
    private val redo = ArrayDeque<Edit>()
    private var expected: List<InkPath>? = null
    val canUndo get() = undo.isNotEmpty()
    val canRedo get() = redo.isNotEmpty()
    val retainedEdits get() = undo.size + redo.size

    fun reset(current: List<InkPath>? = null) {
        undo.clear(); redo.clear(); expected = current
    }

    /** A new server/model load must never be overwritten by stale history. */
    fun synchronize(current: List<InkPath>): Boolean {
        if (expected != current) { reset(current); return false }
        return true
    }

    fun record(before: List<InkPath>, after: List<InkPath>): Boolean {
        synchronize(before)
        if (before == after) return false // Touch, pan or zoom without ink is not an edit.
        // Share unchanged immutable paths across snapshots; no SDK objects are retained.
        val stableBefore = expected ?: before
        val previous = stableBefore.associateBy { it.pathID }
        val shared = after.map { p -> previous[p.pathID]?.takeIf { it == p } ?: p }
        val old = before.associateBy { it.pathID }
        val next = shared.associateBy { it.pathID }
        val cost = before.filter { next[it.pathID] != it }.sumOf { it.points.size + 1 } +
            shared.filter { old[it.pathID] != it }.sumOf { it.points.size + 1 }
        redo.clear()
        if (cost > maxChangedPoints) { reset(shared); return false }
        undo.addLast(Edit(stableBefore, shared, cost)); expected = shared
        while (undo.size > maxEntries || undo.sumOf { it.cost } > maxChangedPoints) undo.removeFirst()
        return true
    }

    fun undoTarget(current: List<InkPath>): List<InkPath>? {
        if (!synchronize(current)) return null
        return undo.lastOrNull()?.before
    }
    fun redoTarget(current: List<InkPath>): List<InkPath>? {
        if (!synchronize(current)) return null
        return redo.lastOrNull()?.after
    }
    // Called only after the native setter succeeded. SDK-normalized bounds are accepted.
    fun didUndo(actual: List<InkPath>) { redo.addLast(undo.removeLast()); expected = actual }
    fun didRedo(actual: List<InkPath>) { undo.addLast(redo.removeLast()); expected = actual }
}

/** Use actual window width; keep 48+ dp targets, scroll rather than shrink icons. */
fun toolbarWidth(windowWidthDp: Float): Float = (windowWidthDp - 420f).coerceIn(112f, 328f)

fun boundedTitleWidth(windowWidthDp: Float): Float =
    (windowWidthDp - toolbarWidth(windowWidthDp) - 340f).coerceIn(24f, 300f)
