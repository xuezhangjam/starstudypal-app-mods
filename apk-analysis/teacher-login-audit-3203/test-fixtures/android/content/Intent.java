package android.content;

public class Intent {
    public String target, activity;
    public Intent(){}
    public Intent(String target){this.target=target;}
    public Intent setComponent(ComponentName name){target=name.target; activity=name.activity;return this;}
}