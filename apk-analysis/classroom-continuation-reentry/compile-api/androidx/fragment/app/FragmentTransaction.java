package androidx.fragment.app;

public class FragmentTransaction {
    public FragmentTransaction add(int container,Fragment fragment,String tag){return this;}
    public FragmentTransaction remove(Fragment fragment){return this;}
    public void commitNow(){}
    public int commitAllowingStateLoss(){return 0;}
}