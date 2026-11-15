package android.view;

public class View {
    public static final int GONE=8;
    public ViewParent parent;
    public boolean attached=true, shown=true, compact;
    public int visibility, posts;
    public int getVisibility(){return visibility;}
    public void setVisibility(int visibility){this.visibility=visibility;}
    public boolean isAttachedToWindow(){return attached;}
    public boolean isShown(){return shown;}
    public ViewParent getParent(){return parent;}
    @SuppressWarnings("unchecked") public <T extends View> T findViewById(int id){return compact?(T)this:null;}
    public boolean post(Runnable callback){posts++;callback.run();return true;}
}