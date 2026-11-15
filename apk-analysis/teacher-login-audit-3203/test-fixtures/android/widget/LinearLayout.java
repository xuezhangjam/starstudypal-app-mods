package android.widget;

public class LinearLayout extends android.view.View {
    public final java.util.List<android.view.View> children=new java.util.ArrayList<>();
    public static class LayoutParams {
        public int gravity;
        public LayoutParams(int width,int height){}
    }
    public android.view.View findViewWithTag(Object tag){
        for(android.view.View v:children) if(tag.equals(v.getTag()))return v;
        return null;
    }
    public void addView(android.view.View view,LayoutParams params){children.add(view);}
}