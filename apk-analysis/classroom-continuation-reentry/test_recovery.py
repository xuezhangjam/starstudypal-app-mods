"""Exercise the compiled recovery controller against a small observable fragment host."""
import os
import subprocess
from build import B, JAVA, T, ANDROID, write

fixtures = {
    'android/os/Bundle': '''
public class Bundle {
    private final java.util.Map<String,Long> values = new java.util.HashMap<>();
    public long getLong(String key){return values.getOrDefault(key,0L);}
    public void putLong(String key,long value){values.put(key,value);}
}''',
    'android/app/Activity': 'public class Activity {}',
    'android/view/ViewParent': 'public interface ViewParent {}',
    'android/view/View': '''
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
}''',
    'android/widget/FrameLayout': '''
public class FrameLayout extends android.view.View implements android.view.ViewParent {
    public int getId(){return com.nice.room.R.id.fragment_container;}
}''',
    'com/nice/room/ui/RoomLiveActivity': 'public class RoomLiveActivity extends android.app.Activity {}',
    'androidx/fragment/app/Fragment': '''
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
}''',
    'androidx/fragment/app/FragmentManager': '''
public class FragmentManager {
    public final java.util.List<Fragment> fragments = new java.util.ArrayList<>();
    public final android.widget.FrameLayout host = new android.widget.FrameLayout();
    public boolean saved;
    public int additions;
    public java.util.List<Fragment> getFragments(){return fragments;}
    public FragmentTransaction beginTransaction(){return new FragmentTransaction(this);}
    public boolean isStateSaved(){return saved;}
}''',
    'androidx/fragment/app/FragmentTransaction': '''
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
}''',
    'com/hailiang/common/util/AppRuntimeData': '''
public class AppRuntimeData { public static long user=7;public static long getUserId(){return user;} }''',
    'com/nice/room/ui/roomlive/fragment/ask/answer/QuestionAskAnswerBaseFragment': '''
public class QuestionAskAnswerBaseFragment extends androidx.fragment.app.Fragment {
    public long classroom, ask;
    public boolean submitted, finished;
    public long getClassroomId(){return classroom;}
    public long getAskId(){return ask;}
    public boolean getSubmitted(){return submitted;}
    public boolean getFinished(){return finished;}
    public void setSubmitted(boolean value){submitted=value;}
    public void setFinished(boolean value){finished=value;}
}''',
    'com/nice/room/ui/roomlive/fragment/ask/answer/QuestionAskOptionFragment': '''
public class QuestionAskOptionFragment extends QuestionAskAnswerBaseFragment {
    public static final Companion Companion = new Companion();
    public static class Companion {
        public QuestionAskOptionFragment newInstance(long classroom,int type,long ask,int count,int options,
                java.util.List<Long> ids,int remaining,int limit,java.util.ArrayList<String> images){
            QuestionAskOptionFragment draft=new QuestionAskOptionFragment();
            draft.classroom=classroom; draft.ask=ask;
            draft.view.compact=images.isEmpty();
            if(remaining!=0)throw new AssertionError("restored timer was armed");
            return draft;
        }
    }
    public java.util.List<com.nice.room.ui.roomlive.fragment.ask.data.QuestionAskSubmitItem> items;
    public void restoreData(java.util.List<com.nice.room.ui.roomlive.fragment.ask.data.QuestionAskSubmitItem> data){items=data;}
}''',
    'com/hljzjx/classroom/mod/HandwriteContinuation': '''
public class HandwriteContinuation {
    public static int attachments;
    public static void stateChanged(com.nice.room.ui.roomlive.fragment.ask.answer.QuestionAskAnswerBaseFragment f){}
    public static void attachResult(com.nice.room.ui.roomlive.fragment.ask.result.QuestionAskAnswerResultBaseFragment f,android.view.View v){attachments++;}
}''',
    'com/hljzjx/classroom/mod/QuestionPptReturn': '''
public class QuestionPptReturn { public static void suspend(android.view.View root){root.shown=false;} }''',
    'com/hljzjx/classroom/reentry/RecoveryTest': '''
import androidx.fragment.app.FragmentManager;
import com.hailiang.xxb.room.server.entity.ask.*;
import com.hljzjx.classroom.mod.HandwriteContinuation;
import com.nice.room.ui.roomlive.fragment.ask.answer.QuestionAskOptionFragment;
import com.nice.room.ui.roomlive.fragment.ask.result.QuestionAskOptionResultFragment;
import java.util.*;

public class RecoveryTest {
    private static void check(boolean value,String reason){if(!value)throw new AssertionError(reason);}
    private static QuestionAskAnswer answer(long user,long title,long seq,Integer... options){
        return new QuestionAskAnswer(){
            public long getStudentId(){return user;}
            public long getAskTitleId(){return title;}
            public long getAskAnswerId(){return seq;}
            public List<Integer> getAnswerOption(){return Arrays.asList(options);}
        };
    }
    private static QuestionAskItem row(long title,QuestionAskAnswer... answers){
        return new QuestionAskItem(){
            public long getAskTitleId(){return title;}
            public List<QuestionAskAnswer> getAskAnswerList(){return Arrays.asList(answers);}
        };
    }
    private static QuestionAskDetail detail(boolean single,QuestionAskItem... rows){
        return new QuestionAskDetail(){
            public int getType(){return (single?QuestionAskType.OPTION:QuestionAskType.OPTION_MULTI).getValue();}
            public int getOptionNumber(){return 4;}
            public int getQuestionNumber(){return rows.length;}
            public List<QuestionAskItem> getAskList(){return Arrays.asList(rows);}
        };
    }
    public static void main(String[] args){
        FragmentManager host=new FragmentManager();
        QuestionAskOptionResultFragment result=new QuestionAskOptionResultFragment(){
            public long getClassroomId(){return 100;}
            public long getAskId(){return 200;}
        };
        result.view.parent=host.host; result.manager=host; result.added=true;
        QuestionAskDetail current=detail(true,row(15,answer(8,15,20,1),answer(7,15,5,2),answer(7,15,6,4)),row(20));
        ChoiceRecovery.stamp(current,100,201,7);
        ChoiceRecovery.onResult(result.view,result,current);
        check(host.additions==0,"another question cannot create a draft");
        ChoiceRecovery.stamp(current,100,200,8);
        ChoiceRecovery.onResult(result.view,result,current);
        check(host.additions==0,"another account cannot create a draft");
        ChoiceRecovery.stamp(current,100,200,7);
        ChoiceRecovery.onResult(result.view,result,current);
        check(host.additions==1 && HandwriteContinuation.attachments==1,"restored result gets one editor and entry");
        QuestionAskOptionFragment draft=(QuestionAskOptionFragment)host.fragments.get(0);
        check(draft.submitted && draft.finished && !draft.view.shown,"draft starts ended and behind the result");
        check(draft.items.size()==1 && draft.items.get(0).student==7 && draft.items.get(0).options.equals(Arrays.asList(4)),
            "latest own D restored, peer answer ignored, unanswered item remains empty");
        ChoiceRecovery.onResult(result.view,result,current);
        check(host.additions==1 && HandwriteContinuation.attachments==1,"refresh must not duplicate or overwrite editor");
        check(ChoiceRecovery.buildDraft(detail(false,row(15,answer(7,15,1,1,4))),7).items.size()==1,"multiple choice restored");
        check(ChoiceRecovery.buildDraft(detail(true,row(15,answer(7,15,1,0))),7)==null,"invalid native option rejected");
        check(ChoiceRecovery.buildDraft(detail(true,row(15),row(15)),7)==null,"duplicate question IDs rejected");
        android.view.View compact=new android.view.View(), full=new android.view.View(), button=new android.view.View();
        compact.compact=true;
        CompactQuestions.hidePptReturn(full,button);
        check(button.visibility==0,"full-size question retains PPT button");
        CompactQuestions.hidePptReturn(compact,button);
        check(button.visibility==8,"compact question hides PPT button");
        System.out.println("Passed re-entry scope, draft restoration, duplicate prevention, and compact button checks.");
    }
}''',
}


def main():
    source = B / 'test-fixtures'
    output = B / 'test-classes'
    output.mkdir(exist_ok=True)
    for name, body in fixtures.items():
        write(source / (name + '.java'), 'package ' + name.rsplit('/', 1)[0].replace('/', '.') + ';\n' + body)
    libraries = os.pathsep.join(map(str, (B / 'repairs.jar', B / 'compile-api.jar', ANDROID)))
    subprocess.run([JAVA, '-jar', T / 'ecj.jar', '-proc:none', '-source', '8', '-target', '8',
                    '-cp', libraries, '-d', output, *list(source.rglob('*.java'))], check=True)
    subprocess.run([JAVA, '-cp', str(output) + os.pathsep + libraries,
                    'com.hljzjx.classroom.reentry.RecoveryTest'], check=True)


if __name__ == '__main__':
    main()
