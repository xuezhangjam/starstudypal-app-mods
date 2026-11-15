
import android.view.MotionEvent;
import com.hailiang.question.data.QuestionBean;
import com.hailiang.question.enums.EnumQuestionType;
import com.hailiang.question.text.QuestionSpannableBuilder;
import com.hailiang.question.widget.view.QuestionHandwriteView;
import com.hailiang.workcloud.student.md3e.v3.*;
import java.util.Arrays;

public class TouchTest {
    private static int assertions;
    private static void check(boolean value, String detail) {
        assertions++;
        if (!value) throw new AssertionError(detail);
    }
    private static MotionEvent event(int action, int time, int... ids) {
        MotionEvent.PointerProperties[] pp = new MotionEvent.PointerProperties[ids.length];
        MotionEvent.PointerCoords[] pc = new MotionEvent.PointerCoords[ids.length];
        for (int i = 0; i < ids.length; i++) {
            pp[i] = new MotionEvent.PointerProperties();
            pp[i].id = ids[i];
            pp[i].toolType = ids[i] == 4 ? 2 : ids[i] == 8 ? 5 : 1;
            pc[i] = new MotionEvent.PointerCoords();
            pc[i].x = time;
            pc[i].pressure = 0.05f;
        }
        return new MotionEvent(1, time, action, pp, pc);
    }
    private static void send(QuestionHandwriteView view, int action, int time, int... ids) {
        WritingTouch.dispatch(view, event(action, time, ids));
    }
    private static void actions(QuestionHandwriteView view, int... expected) {
        check(Arrays.equals(view.delivered.stream().mapToInt(e -> e.action).toArray(), expected),
            "native action order differs from " + Arrays.toString(expected));
    }
    public static void main(String[] args) {
        QuestionHandwriteView view = new QuestionHandwriteView();
        send(view, 0, 1, 4);
        send(view, 261, 2, 4, 8);
        MotionEvent move = event(2, 5, 8, 4);
        move.history = new MotionEvent[]{event(2, 3, 8, 4), event(2, 4, 8, 4)};
        check(WritingTouch.isPenEvent(move), "detect stylus beyond pointer zero");
        WritingTouch.dispatch(view, move);
        send(view, 6, 6, 8, 4);
        send(view, 1, 7, 4);
        actions(view, 0, 2, 2, 2, 1);
        check(view.delivered.stream().allMatch(e -> e.getPointerCount() == 1 && e.pointers[0].id == 4),
            "only the pen reached the native drawing core");
        check(view.delivered.get(1).time == 3 && view.delivered.get(2).time == 4,
            "historical samples arrive in chronological order");
        check(view.width >= 3.6f && view.delivered.get(0).getPressure(0) >= 0.35f, "pen is thicker");
        check(!view.interceptLocked, "interception released after last touch");

        view = new QuestionHandwriteView();
        view.width = 6;
        send(view, 0, 1, 8);
        send(view, 261, 2, 8, 4);
        send(view, 262, 3, 8, 4);
        check(view.interceptLocked, "palm stays excluded between strokes");
        send(view, 261, 4, 8, 4);
        send(view, 3, 5, 8);
        actions(view, 0, 1, 0, 3);
        check(view.width == 6 && !view.interceptLocked, "existing wider pen retained and cancel releases");
        check(view.delivered.get(3).pointers[0].id == 4, "cancel without stylus uses last pen");

        view = new QuestionHandwriteView();
        send(view, 0, 1, 1);
        send(view, 261, 2, 1, 2);
        send(view, 2, 3, 1, 2);
        send(view, 262, 4, 1, 2);
        send(view, 1, 5, 1);
        actions(view, 0, 261, 2, 262, 1);
        check(view.delivered.get(2).getPointerCount() == 2, "finger pinch keeps both contacts");
        view.delivered.clear();
        send(view, 0, 6, 1);
        send(view, 261, 7, 1, 4);
        send(view, 262, 8, 1, 4);
        send(view, 1, 9, 1);
        actions(view, 0, 3, 0, 1);
        view = new QuestionHandwriteView();
        view.writable = false;
        send(view, 0, 1, 4);
        check(view.width == 2 && !view.interceptLocked, "read-only view keeps native handling");

        QuestionBean fill = new QuestionBean() {
            public EnumQuestionType getQuestionTypeEnum() { return EnumQuestionType.QUESTION_TYPE_FILL; }
        };
        QuestionSpannableBuilder stem = new QuestionSpannableBuilder();
        BlankLabels.appendStemLabel(stem, fill, 12);
        check(stem.text.trim().equals("第12空"), "stem uses original one-based blank index");
        check(BlankLabels.boardTitle("作答区", fill, 12).equals("作答区 · " + stem.text.trim()),
            "board title matches the stem exactly");
        check(BlankLabels.boardTitle("作答区", null, 1).equals("作答区") &&
              BlankLabels.label(fill, 0) == null, "no fake numbering for non-fill or missing selection");
        System.out.println("Passed " + assertions + " handwriting and numbering assertions.");
    }
}
