package com.hailiang.workcloud.student.md3e.v3

import androidx.compose.ui.layout.Measurable
import androidx.compose.ui.layout.MeasurePolicy
import androidx.compose.ui.layout.MeasureResult
import androidx.compose.ui.layout.MeasureScope
import androidx.compose.ui.unit.Constraints
import androidx.compose.ui.unit.constrainHeight
import androidx.compose.ui.unit.dp
import java.util.WeakHashMap

object AnsweringPanes {
    private val policies = WeakHashMap<MeasurePolicy, MeasurePolicy>()

    @JvmStatic
    fun withAnswerWidth(box: MeasurePolicy): MeasurePolicy =
        policies.getOrPut(box) { SideBySide(box) }

    private class SideBySide(private val box: MeasurePolicy) : MeasurePolicy {
        override fun MeasureScope.measure(
            measurables: List<Measurable>,
            constraints: Constraints,
        ): MeasureResult {
            if (measurables.size != 2 || !constraints.hasBoundedWidth) {
                val scope = this
                return with(box) { scope.measure(measurables, constraints) }
            }

            val width = constraints.maxWidth
            val gap = minOf(12.dp.roundToPx(), width / 12)
            val answer = measurables[1].measure(
                constraints.copy(minWidth = 0, maxWidth = (width - gap) * 64 / 100, minHeight = 0),
            )
            val questionWidth = width - answer.width - gap
            val question = measurables[0].measure(
                constraints.copy(minWidth = questionWidth, maxWidth = questionWidth, minHeight = 0),
            )
            return layout(width, constraints.constrainHeight(maxOf(question.height, answer.height))) {
                question.placeRelative(0, 0)
                answer.placeRelative(width - answer.width, 0)
            }
        }
    }
}
