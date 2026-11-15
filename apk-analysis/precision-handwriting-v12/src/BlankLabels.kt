package com.hailiang.workcloud.student.md3e.v3

import com.hailiang.question.data.QuestionBean
import com.hailiang.question.enums.EnumQuestionType
import com.hailiang.question.text.QuestionSpannableBuilder

object BlankLabels {
    @JvmStatic
    fun label(question: QuestionBean?, index: Int): String? =
        if (index > 0 && question?.getQuestionTypeEnum() == EnumQuestionType.QUESTION_TYPE_FILL) {
            "第${index}空"
        } else {
            null
        }

    @JvmStatic
    fun boardTitle(title: String, question: QuestionBean?, index: Int): String =
        label(question, index)?.let { "$title · $it" } ?: title

    @JvmStatic
    fun appendStemLabel(builder: QuestionSpannableBuilder, question: QuestionBean?, index: Int) {
        label(question, index)?.let { builder.append("$it ") }
    }
}
