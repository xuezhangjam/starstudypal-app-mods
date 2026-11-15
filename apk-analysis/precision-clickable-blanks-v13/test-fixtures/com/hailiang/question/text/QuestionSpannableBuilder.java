
package com.hailiang.question.text;
import com.hailiang.question.text.span.*;
public class QuestionSpannableBuilder {
    public ReplacementClickableSpan span;
    public SpanClickListener click;
    public boolean clickable;
    public QuestionSpannableBuilder setReplaceClickSpan(ReplacementClickableSpan span, boolean clickable,
            boolean selected, SpanClickListener click) {
        this.span = span; this.clickable = clickable; this.click = click;
        return this;
    }
}
