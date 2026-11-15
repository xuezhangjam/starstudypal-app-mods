package com.nice.room.ui.roomlive.fragment.ask.answer;

public class QuestionAskAnswerBaseFragment extends androidx.fragment.app.Fragment {
    public long getClassroomId(){return 0;}
    public long getAskId(){return 0;}
    public boolean getSubmitted(){return false;}
    public boolean getFinished(){return false;}
    public void setSubmitted(boolean submitted){}
    public void setFinished(boolean finished){}
}