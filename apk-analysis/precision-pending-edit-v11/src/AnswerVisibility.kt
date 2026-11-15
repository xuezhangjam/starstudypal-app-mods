package com.hailiang.workcloud.student.md3e.v3

import android.view.View
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import com.hailiang.question.parser.html.raw.Raw
import com.hailiang.workcloud.student.shareui.work.review.components.detail.AnswerRichText_androidKt
import kotlinx.serialization.json.JsonElement
import java.util.WeakHashMap

/** Session display preference for whole reference/analysis panels; keeps their child state. */
object AnswerVisibility {
    var visible by mutableStateOf(true)
        private set
    private val rows = WeakHashMap<View, Int>()

    @JvmStatic fun bind(view: View) {
        if (!rows.containsKey(view)) rows[view] = view.visibility
        view.visibility = if (visible) rows[view] ?: View.VISIBLE else View.GONE
    }
    fun showAnswers(value: Boolean) {
        visible = value
        rows.forEach { (view, original) -> view.visibility = if (value) original else View.GONE }
    }
    fun toggle() = showAnswers(!visible)
}

/** Used only for the native reference-answer tab, never the student's answer. */
@OptIn(InternalComposeApi::class)
@Composable
fun ReferenceAnswerContent(element: JsonElement?, fallback: String?, emptyLabel: String?,
    fontSize: Long, color: Long, modifier: Modifier?, raw: Raw?, questionType: Int, nativeDefaults: Int) {
    if (AnswerVisibility.visible) {
        AnswerRichText_androidKt.modRenderAnswer(element, fallback, emptyLabel, fontSize, color,
            modifier, raw, questionType, currentComposer, 0, nativeDefaults)
    } else Text("参考答案和解析已隐藏", color = MaterialTheme.colorScheme.onSurfaceVariant,
        style = MaterialTheme.typography.bodyMedium)
}
