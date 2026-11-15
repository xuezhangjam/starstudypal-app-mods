package androidx.fragment.app;

public class FragmentTransaction {
    private final FragmentManager owner;
    private Fragment pending, removal;
    public FragmentTransaction(FragmentManager owner){this.owner=owner;}
    public FragmentTransaction add(int container,Fragment fragment,String tag){pending=fragment;return this;}
    public FragmentTransaction remove(Fragment fragment){removal=fragment;return this;}
    public void commitNow(){
        if(pending!=null){
            owner.additions++;
            pending.added=true;
            pending.view.parent=owner.host;
            pending.manager=owner;
            owner.fragments.add(pending);
        }
        if(removal!=null)owner.fragments.remove(removal);
    }
    public int commitAllowingStateLoss(){commitNow();return 0;}
}