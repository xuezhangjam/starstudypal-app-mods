package android.app;

import android.content.Intent;
import android.content.pm.PackageManager;
public class Activity {
    public final PackageManager pm=new PackageManager();
    public boolean stopped;
    public Intent opened;
    public boolean isFinishing(){return stopped;}
    public boolean isDestroyed(){return false;}
    public PackageManager getPackageManager(){return pm;}
    public void startActivity(Intent intent){opened=intent;}
}