"""Run the compiled blank-label and tap logic using native API fixtures."""
import os
import subprocess

from build import B, R, JAVA, T, write

fixtures = {
    'com/hailiang/question/text/span/ReplacementClickableSpan.java': '''
package com.hailiang.question.text.span;
public class ReplacementClickableSpan {
    public final String text;
    public final int width;
    public ReplacementClickableSpan(String text, int width) { this.text = text; this.width = width; }
}
''',
    'com/hailiang/question/text/SpanFactory.java': '''
package com.hailiang.question.text;
import com.hailiang.question.text.span.ReplacementClickableSpan;
public class SpanFactory {
    public static final SpanFactory INSTANCE = new SpanFactory();
    public ReplacementClickableSpan createHandwriteIdxSpan(String text, int color, int width, int height) {
        return new ReplacementClickableSpan(text, width);
    }
}
''',
    'com/hailiang/question/text/QuestionSpannableBuilder.java': '''
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
''',
    'BlankTest.java': '''
import com.hailiang.question.data.QuestionBean;
import com.hailiang.question.enums.EnumQuestionType;
import com.hailiang.question.listener.InsertEventListener;
import com.hailiang.question.text.QuestionSpannableBuilder;
import com.hailiang.workcloud.student.md3e.v3.BlankLabels;
import com.hailiang.workcloud.student.shareui.uicore.question.QuestionComponentDisplay;

public class BlankTest {
    private static void check(boolean result, String reason) {
        if (!result) throw new AssertionError(reason);
    }
    public static void main(String[] args) {
        QuestionBean firstSubquestion = fill();
        QuestionBean secondSubquestion = fill();
        QuestionComponentDisplay question = new QuestionComponentDisplay() {
            public Data getData() { return new Data() { public int getQuestionNum() { return 7; } }; }
        };
        check(BlankLabels.boardTitle("作答区", firstSubquestion, 2, question).equals("作答区 · 第7题 · 第2空"),
            "title uses displayed question number and current blank");
        check(BlankLabels.boardTitle("作答区", null, 0, question).equals("作答区 · 第7题"),
            "no blank number for non-fill or absent selection");
        check(BlankLabels.label(firstSubquestion, 12).equals("（12）"), "multi-digit number in full-width parentheses");

        QuestionSpannableBuilder one = new QuestionSpannableBuilder();
        QuestionSpannableBuilder two = new QuestionSpannableBuilder();
        QuestionBean[] selected = {null};
        int[] index = {0};
        int[] originalLocation = {10, 20};
        InsertEventListener tap = (bean, idx, answer, options, location) -> {
            check(location == originalLocation, "native tap location preserved");
            selected[0] = bean;
            index[0] = idx;
        };
        check(BlankLabels.renderInline(one, firstSubquestion, 2, tap, 130), "render the first subquestion marker");
        check(BlankLabels.renderInline(two, secondSubquestion, 2, tap, 64), "render the second subquestion marker");
        check(one.span.text.equals("（2）") && one.span.width == 130 && one.clickable, "clickable underlined span");
        one.click.handleClick(null, null, one.span, originalLocation, null);
        check(selected[0] == firstSubquestion && index[0] == 2, "tap passes exact first question and blank");
        two.click.handleClick(null, null, two.span, originalLocation, null);
        check(selected[0] == secondSubquestion && index[0] == 2, "same blank number in another subquestion stays distinct");
        check(BlankLabels.renderInline(one, firstSubquestion, 3, null, 130) && !one.clickable && one.click == null,
            "read-only marker cannot dispatch an event");
        check(!BlankLabels.renderInline(one, new QuestionBean(), 1, tap, 130), "other question types retain native path");
        System.out.println("Passed question titles, numbered spans and exact blank navigation.");
    }
    private static QuestionBean fill() {
        return new QuestionBean() {
            public EnumQuestionType getQuestionTypeEnum() { return EnumQuestionType.QUESTION_TYPE_FILL; }
        };
    }
}
''',
}


def main():
    source = B / 'test-fixtures'
    classes = B / 'test-classes'
    classes.mkdir(exist_ok=True)
    for name, content in fixtures.items():
        write(source / name, content)
    stdlib = R / 'tools/precision-compose/kotlin-stdlib-2.3.0.jar'
    android = R / 'tools/android-sdk/android-34-ext12/android.jar'
    cp = os.pathsep.join(map(str, (B / 'ui.jar', B / 'api.jar', android, stdlib)))
    subprocess.run(
        [JAVA, '-jar', T / 'ecj.jar', '-proc:none', '-encoding', 'UTF-8', '-source', '8', '-target', '8',
         '-cp', cp, '-d', classes, *[source / name for name in fixtures]], check=True,
    )
    subprocess.run([JAVA, '-cp', str(classes) + os.pathsep + cp, 'BlankTest'], check=True)


if __name__ == '__main__':
    main()
