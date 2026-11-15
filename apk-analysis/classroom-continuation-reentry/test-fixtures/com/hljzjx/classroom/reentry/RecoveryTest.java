package com.hljzjx.classroom.reentry;

import androidx.fragment.app.FragmentManager;
import com.hailiang.common.util.AppRuntimeData;
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
}