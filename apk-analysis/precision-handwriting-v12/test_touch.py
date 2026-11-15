"""Exercise the compiled writing router and numbering helpers with JVM input fixtures."""
import os
import subprocess

from build import B, R, JAVA, T, write

fixtures = {
    'android/view/ViewParent.java': '''
package android.view;
public interface ViewParent { void requestDisallowInterceptTouchEvent(boolean disallow); }
''',
    'android/util/DisplayMetrics.java': '''
package android.util;
public class DisplayMetrics { public float density = 2f; }
''',
    'android/content/res/Resources.java': '''
package android.content.res;
public class Resources {
    public android.util.DisplayMetrics getDisplayMetrics() { return new android.util.DisplayMetrics(); }
}
''',
    'android/view/MotionEvent.java': '''
package android.view;

public class MotionEvent {
    public static class PointerProperties { public int id, toolType; }
    public static class PointerCoords { public float x, y, pressure, size; }
    public final long down, time;
    public int action;
    public final PointerProperties[] pointers;
    public final PointerCoords[] coordinates;
    public MotionEvent[] history = {};
    public MotionEvent(long down, long time, int action, PointerProperties[] pointers, PointerCoords[] coords) {
        this.down = down;
        this.time = time;
        this.action = action;
        this.pointers = new PointerProperties[pointers.length];
        this.coordinates = new PointerCoords[coords.length];
        for (int i = 0; i < coords.length; i++) {
            this.pointers[i] = new PointerProperties();
            this.pointers[i].id = pointers[i].id;
            this.pointers[i].toolType = pointers[i].toolType;
            this.coordinates[i] = new PointerCoords();
            copy(coords[i], this.coordinates[i]);
        }
    }
    public static MotionEvent obtain(long down, long time, int action, int count, PointerProperties[] pp,
        PointerCoords[] pc, int meta, int button, float xp, float yp, int dev, int edge, int src, int flags) {
        return new MotionEvent(down, time, action, pp, pc);
    }
    public static MotionEvent obtainNoHistory(MotionEvent event) {
        return new MotionEvent(event.down, event.time, event.action, event.pointers, event.coordinates);
    }
    private static void copy(PointerCoords from, PointerCoords to) {
        to.x = from.x; to.y = from.y; to.pressure = from.pressure; to.size = from.size;
    }
    public void getPointerProperties(int i, PointerProperties out) {
        out.id = pointers[i].id; out.toolType = pointers[i].toolType;
    }
    public void getPointerCoords(int i, PointerCoords out) { copy(coordinates[i], out); }
    public void getHistoricalPointerCoords(int i, int n, PointerCoords out) { history[n].getPointerCoords(i, out); }
    public long getHistoricalEventTime(int i) { return history[i].time; }
    public int getHistorySize() { return history.length; }
    public int getActionMasked() { return action & 255; }
    public int getActionIndex() { return action >> 8; }
    public void setAction(int action) { this.action = action; }
    public int getPointerCount() { return pointers.length; }
    public int getToolType(int i) { return pointers[i].toolType; }
    public int findPointerIndex(int id) {
        for (int i = 0; i < pointers.length; i++) if (pointers[i].id == id) return i;
        return -1;
    }
    public long getEventTime() { return time; }
    public float getSize(int i) { return coordinates[i].size; }
    public float getPressure(int i) { return coordinates[i].pressure; }
    public int getMetaState() { return 0; }
    public int getButtonState() { return 0; }
    public float getXPrecision() { return 1; }
    public float getYPrecision() { return 1; }
    public int getDeviceId() { return 0; }
    public int getEdgeFlags() { return 0; }
    public int getSource() { return 0; }
    public int getFlags() { return 0; }
    public void recycle() {}
}
''',
    'com/hailiang/question/widget/view/QuestionHandwriteView.java': '''
package com.hailiang.question.widget.view;
import android.view.*;

public class QuestionHandwriteView {
    public final java.util.List<MotionEvent> delivered = new java.util.ArrayList<>();
    public float width = 2;
    public boolean writable = true, interceptLocked;
    private final ViewParent parent = locked -> interceptLocked = locked;
    public boolean getCanDraw() { return writable; }
    public boolean isEnabled() { return true; }
    public boolean isInGeometryEditMode() { return false; }
    public ViewParent getParent() { return parent; }
    public android.content.res.Resources getResources() { return new android.content.res.Resources(); }
    public float getStrokeWidth() { return width; }
    public void setStrokeWidth(float width) { this.width = width; }
    public boolean modDispatchWritingEvent(MotionEvent event) { delivered.add(event); return true; }
}
''',
    'com/hailiang/question/text/QuestionSpannableBuilder.java': '''
package com.hailiang.question.text;
public class QuestionSpannableBuilder {
    public String text = "";
    public QuestionSpannableBuilder append(CharSequence value) { text += value; return this; }
}
''',
    'TouchTest.java': '''
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
''',
}


def main():
    source = B / 'test-fixtures'
    classes = B / 'test-classes'
    classes.mkdir(exist_ok=True)
    for name, contents in fixtures.items():
        write(source / name, contents)
    stdlib = R / 'tools/precision-compose/kotlin-stdlib-2.3.0.jar'
    cp = os.pathsep.join(map(str, (B / 'ui.jar', B / 'api.jar', stdlib)))
    subprocess.run(
        [JAVA, '-jar', T / 'ecj.jar', '-proc:none', '-encoding', 'UTF-8', '-source', '8', '-target', '8',
         '-cp', cp, '-d', classes, *[source / name for name in fixtures]], check=True,
    )
    subprocess.run([JAVA, '-cp', str(classes) + os.pathsep + cp, 'TouchTest'], check=True)


if __name__ == '__main__':
    main()
