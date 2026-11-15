package com.nice.room.ui.roomlive.fragment.ask.data;

public class QuestionAskSubmitItem {
    public final long title, student;
    public final java.util.List<Integer> options;
    public QuestionAskSubmitItem(long title,java.util.List<Integer> options,String content,int time,int original,long user){
        this.title=title; this.options=options; this.student=user;
    }
}