import androidx.compose.ui.layout.Measurable
import androidx.compose.ui.layout.MeasurePolicy
import androidx.compose.ui.layout.MeasureScope
import androidx.compose.ui.layout.Placeable
import androidx.compose.ui.unit.Constraints
import androidx.compose.ui.unit.IntOffset
import androidx.compose.ui.unit.IntSize
import androidx.compose.ui.unit.LayoutDirection
import androidx.compose.ui.unit.constrainWidth
import com.hailiang.workcloud.student.md3e.v3.AnsweringPanes

private object Scope : MeasureScope {
    override val density = 1f
    override val fontScale = 1f
    override val layoutDirection = LayoutDirection.Ltr
}

private class Pane(var preferredWidth: Int) : Measurable {
    override val parentData: Any? = null
    var measuredWidth = -1
    var x = -1
    override fun measure(constraints: Constraints): Placeable {
        measuredWidth = constraints.constrainWidth(preferredWidth)
        return object : Placeable() {
            init {
                measurementConstraints = constraints
                measuredSize = IntSize(this@Pane.measuredWidth, 450)
            }
            override fun get(alignmentLine: androidx.compose.ui.layout.AlignmentLine): Int =
                androidx.compose.ui.layout.AlignmentLine.Unspecified
            override fun placeAt(
                position: IntOffset,
                zIndex: Float,
                layerBlock: (androidx.compose.ui.graphics.GraphicsLayerScope.() -> Unit)?,
            ) {
                x = position.x
            }
        }
    }
    override fun minIntrinsicWidth(height: Int) = preferredWidth
    override fun maxIntrinsicWidth(height: Int) = preferredWidth
    override fun minIntrinsicHeight(width: Int) = 450
    override fun maxIntrinsicHeight(width: Int) = 450
}

fun main() {
    var fallbackCount = 0
    val fallback = MeasurePolicy { _, _ ->
        fallbackCount++
        layout(0, 0) {}
    }
    val policy = AnsweringPanes.withAnswerWidth(fallback)
    val question = Pane(820)
    val answer = Pane(430)
    fun layout(width: Int, expectedQuestion: Int, expectedAnswer: Int) {
        val result = with(policy) { Scope.measure(listOf(question, answer), Constraints(maxWidth = width, maxHeight = 600)) }
        result.placeChildren()
        check(question.measuredWidth == expectedQuestion && answer.measuredWidth == expectedAnswer) {
            "Window $width allocated ${question.measuredWidth} + ${answer.measuredWidth}"
        }
        check(question.x == 0 && question.x + question.measuredWidth + 12 == answer.x)
        check(answer.x + answer.measuredWidth == width)
    }
    layout(1260, 818, 430)
    answer.preferredWidth = 740
    layout(1260, 508, 740)
    layout(600, 212, 376)
    answer.preferredWidth = 430
    layout(1260, 818, 430)
    with(policy) { Scope.measure(listOf(question), Constraints(maxWidth = 1260, maxHeight = 600)) }
    check(fallbackCount == 1)
    println("Passed expanded, collapsed, narrow, restored and single-pane layout checks.")
}
