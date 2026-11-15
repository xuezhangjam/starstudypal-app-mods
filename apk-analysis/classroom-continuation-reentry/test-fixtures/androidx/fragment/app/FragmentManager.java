package androidx.fragment.app;

public class FragmentManager {
    public final java.util.List<Fragment> fragments = new java.util.ArrayList<>();
    public final android.widget.FrameLayout host = new android.widget.FrameLayout();
    public boolean saved;
    public int additions;
    public java.util.List<Fragment> getFragments(){return fragments;}
    public FragmentTransaction beginTransaction(){return new FragmentTransaction(this);}
    public boolean isStateSaved(){return saved;}
}