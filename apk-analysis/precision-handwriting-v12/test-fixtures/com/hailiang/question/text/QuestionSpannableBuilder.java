
package com.hailiang.question.text;
public class QuestionSpannableBuilder {
    public String text = "";
    public QuestionSpannableBuilder append(CharSequence value) { text += value; return this; }
}
