package android.view;

public class View {
    private Object tag;
    public OnClickListener listener;
    public interface OnClickListener {void onClick(View view);}
    public void setTag(Object value){tag=value;}
    public Object getTag(){return tag;}
    public void setOnClickListener(OnClickListener value){listener=value;}
}