package com.nice.room.ui.roomlive.fragment.ask.answer;

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
}