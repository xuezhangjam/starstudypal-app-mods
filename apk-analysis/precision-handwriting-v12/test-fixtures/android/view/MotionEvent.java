
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
