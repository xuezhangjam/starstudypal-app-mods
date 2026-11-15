
package com.hailiang.question.text;
import com.hailiang.question.text.span.ReplacementClickableSpan;
public class SpanFactory {
    public static final SpanFactory INSTANCE = new SpanFactory();
    public ReplacementClickableSpan createHandwriteIdxSpan(String text, int color, int width, int height) {
        return new ReplacementClickableSpan(text, width);
    }
}
