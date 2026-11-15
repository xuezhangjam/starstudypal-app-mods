package com.hailiang.workcloud.student.md3e.v3

import com.hailiang.question.data.QuestionBean
import com.hailiang.question.enums.EnumQuestionType
import com.hailiang.question.listener.InsertEventListener
import com.hailiang.question.text.QuestionSpannableBuilder
import com.hailiang.question.text.SpanFactory
import com.hailiang.question.text.span.SpanClickListener
import com.hailiang.question.widget.compose.theme.QuestionColors
import com.hailiang.workcloud.student.shareui.uicore.question.QuestionComponentDisplay

object BlankLabels {
    @JvmStatic
    fun label(question: QuestionBean?, index: Int): String? =
        if (isBlank(question, index)) "（$index）" else null

    private fun isBlank(question: QuestionBean?, index: Int): Boolean =
        index > 0 && question?.getQuestionTypeEnum() == EnumQuestionType.QUESTION_TYPE_FILL

    @JvmStatic
    fun boardTitle(
        title: String,
        question: QuestionBean?,
        index: Int,
        display: QuestionComponentDisplay,
    ): String = buildString {
        append(title)
        val number = display.getData().getQuestionNum()
        if (number > 0) append(" · 第${number}题")
        if (isBlank(question, index)) append(" · 第${index}空")
    }

    @JvmStatic
    fun renderInline(
        builder: QuestionSpannableBuilder,
        question: QuestionBean,
        index: Int,
        listener: InsertEventListener?,
        width: Int,
    ): Boolean {
        val text = label(question, index) ?: return false
        val factory = SpanFactory.INSTANCE
        val span = factory.createHandwriteIdxSpan(
            text, QuestionColors.getNormalTextColorInt(), width, 39,
        )
        val click = listener?.let {
            SpanClickListener { _, _, _, location, _ ->
                it.onClick(question, index, "", emptyList(), location)
            }
        }
        builder.setReplaceClickSpan(span, click != null, false, click)
        return true
    }
}
