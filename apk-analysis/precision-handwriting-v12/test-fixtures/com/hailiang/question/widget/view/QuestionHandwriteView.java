
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
