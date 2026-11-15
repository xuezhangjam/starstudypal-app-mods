package android.widget;

public class Toast {
    public static final int LENGTH_SHORT=0;
    public static int errors;
    public static Toast makeText(android.app.Activity activity,CharSequence text,int length){return new Toast();}
    public void show(){errors++;}
}