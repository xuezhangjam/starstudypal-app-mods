
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
