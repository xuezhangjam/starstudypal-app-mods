package androidx.fragment.app;

public class Fragment {
    public android.app.Activity activity = new com.nice.room.ui.RoomLiveActivity();
    public android.view.View view = new android.view.View();
    public android.os.Bundle args = new android.os.Bundle();
    public FragmentManager manager;
    public boolean added;
    public android.app.Activity getActivity(){return activity;}
    public android.view.View getView(){return view;}
    public android.os.Bundle getArguments(){return args;}
    public android.os.Bundle requireArguments(){return args;}
    public boolean isAdded(){return added;}
    public FragmentManager getParentFragmentManager(){return manager;}
}