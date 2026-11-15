package com.nice.room.ui.roomlive.fragment.ask.answer;

public class QuestionAskAnswerBaseFragment extends androidx.fragment.app.Fragment {
    public long classroom, ask;
    public boolean submitted, finished;
    public long getClassroomId(){return classroom;}
    public long getAskId(){return ask;}
    public boolean getSubmitted(){return submitted;}
    public boolean getFinished(){return finished;}
    public void setSubmitted(boolean value){submitted=value;}
    public void setFinished(boolean value){finished=value;}
}