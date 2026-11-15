package android.app;

import android.content.DialogInterface;
public class AlertDialog {
    public static DialogInterface.OnClickListener confirm;
    public static String message;
    public static class Builder {
        public Builder(Activity activity){}
        public Builder setTitle(CharSequence title){return this;}
        public Builder setMessage(CharSequence value){message=value.toString();return this;}
        public Builder setNegativeButton(CharSequence label,DialogInterface.OnClickListener click){return this;}
        public Builder setPositiveButton(CharSequence label,DialogInterface.OnClickListener click){confirm=click;return this;}
        public AlertDialog show(){return new AlertDialog();}
    }
}