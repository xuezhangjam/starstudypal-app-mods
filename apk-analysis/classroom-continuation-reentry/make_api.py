from build import B, write

types = {
    'androidx/fragment/app/Fragment': '''
public class Fragment {
    public android.app.Activity getActivity(){return null;}
    public android.view.View getView(){return null;}
    public android.os.Bundle getArguments(){return null;}
    public android.os.Bundle requireArguments(){return null;}
    public boolean isAdded(){return false;}
    public FragmentManager getParentFragmentManager(){return null;}
}''',
    'androidx/fragment/app/FragmentManager': '''
public class FragmentManager {
    public java.util.List<Fragment> getFragments(){return null;}
    public FragmentTransaction beginTransaction(){return null;}
    public boolean isStateSaved(){return false;}
}''',
    'androidx/fragment/app/FragmentTransaction': '''
public class FragmentTransaction {
    public FragmentTransaction add(int container,Fragment fragment,String tag){return this;}
    public FragmentTransaction remove(Fragment fragment){return this;}
    public void commitNow(){}
    public int commitAllowingStateLoss(){return 0;}
}''',
    'com/hailiang/common/util/AppRuntimeData': 'public class AppRuntimeData { public static long getUserId(){return 0;} }',
    'com/hailiang/xxb/room/server/entity/ask/QuestionAskType': '''
public enum QuestionAskType {
    OPTION, OPTION_MULTI;
    public int getValue(){return ordinal();}
}''',
    'com/hailiang/xxb/room/server/entity/ask/QuestionAskDetail': '''
public class QuestionAskDetail {
    public int getType(){return 0;}
    public int getOptionNumber(){return 0;}
    public int getQuestionNumber(){return 0;}
    public int getAnswerTimeLimit(){return 0;}
    public java.util.List<String> getScreenshotUrlList(){return null;}
    public java.util.List<QuestionAskItem> getAskList(){return null;}
}''',
    'com/hailiang/xxb/room/server/entity/ask/QuestionAskItem': '''
public class QuestionAskItem {
    public long getAskTitleId(){return 0;}
    public java.util.List<QuestionAskAnswer> getAskAnswerList(){return null;}
}''',
    'com/hailiang/xxb/room/server/entity/ask/QuestionAskAnswer': '''
public class QuestionAskAnswer {
    public long getAskTitleId(){return 0;}
    public long getAskAnswerId(){return 0;}
    public long getStudentId(){return 0;}
    public int getAnswerTime(){return 0;}
    public java.util.List<Integer> getAnswerOption(){return null;}
}''',
    'com/nice/room/ui/roomlive/fragment/ask/answer/QuestionAskAnswerBaseFragment': '''
public class QuestionAskAnswerBaseFragment extends androidx.fragment.app.Fragment {
    public long getClassroomId(){return 0;}
    public long getAskId(){return 0;}
    public boolean getSubmitted(){return false;}
    public boolean getFinished(){return false;}
    public void setSubmitted(boolean submitted){}
    public void setFinished(boolean finished){}
}''',
    'com/nice/room/ui/roomlive/fragment/ask/answer/QuestionAskOptionFragment': '''
public class QuestionAskOptionFragment extends QuestionAskAnswerBaseFragment {
    public static final Companion Companion = new Companion();
    public static class Companion {
        public QuestionAskOptionFragment newInstance(long classroomId,int type,long askId,int count,int options,
                java.util.List<Long> ids,int remaining,int limit,java.util.ArrayList<String> images){return null;}
    }
    public void restoreData(java.util.List<com.nice.room.ui.roomlive.fragment.ask.data.QuestionAskSubmitItem> data){}
}''',
    'com/nice/room/ui/roomlive/fragment/ask/result/QuestionAskAnswerResultBaseFragment': '''
public class QuestionAskAnswerResultBaseFragment extends androidx.fragment.app.Fragment {
    public long getClassroomId(){return 0;}
    public long getAskId(){return 0;}
}''',
    'com/nice/room/ui/roomlive/fragment/ask/result/QuestionAskOptionResultFragment': '''
public class QuestionAskOptionResultFragment extends QuestionAskAnswerResultBaseFragment {}''',
    'com/nice/room/ui/roomlive/fragment/ask/data/QuestionAskSubmitItem': '''
public class QuestionAskSubmitItem {
    public final long title, student;
    public final java.util.List<Integer> options;
    public QuestionAskSubmitItem(long title,java.util.List<Integer> options,String content,int time,int original,long user){
        this.title=title; this.options=options; this.student=user;
    }
}''',
    'com/hljzjx/classroom/mod/HandwriteContinuation': '''
public class HandwriteContinuation {
    public static void stateChanged(com.nice.room.ui.roomlive.fragment.ask.answer.QuestionAskAnswerBaseFragment fragment){}
    public static void attachResult(com.nice.room.ui.roomlive.fragment.ask.result.QuestionAskAnswerResultBaseFragment fragment,android.view.View root){}
}''',
    'com/hljzjx/classroom/mod/QuestionOverlayLayout': '''
public class QuestionOverlayLayout { public static boolean covered(android.view.View root){return false;} }''',
    'com/hljzjx/classroom/mod/QuestionPptReturn': '''
public class QuestionPptReturn { public static void suspend(android.view.View root){} }''',
    'com/nice/room/R': '''
public class R { public static class id { public static int fragment_container, draggable_layout; } }''',
}

def generate():
    for name, source in types.items():
        write(B / 'compile-api' / (name + '.java'), 'package ' + name.rsplit('/', 1)[0].replace('/', '.') + ';\n' + source)
