package android.content;public class Intent{
 public static final String ACTION_VIEW="android.intent.action.VIEW",ACTION_MAIN="android.intent.action.MAIN",CATEGORY_BROWSABLE="android.intent.category.BROWSABLE",CATEGORY_APP_BROWSER="android.intent.category.APP_BROWSER",ACTION_OPEN_DOCUMENT="OPEN_DOCUMENT",ACTION_GET_CONTENT="GET_CONTENT",CATEGORY_OPENABLE="OPENABLE",EXTRA_ALLOW_MULTIPLE="MULTIPLE";
 public static final int FLAG_GRANT_READ_URI_PERMISSION=1;public String action,type,category,pkg;public boolean multiple;public int flags;public android.net.Uri uri;public Intent selector;
 public Intent(String s){action=s;}public Intent(String s,android.net.Uri u){action=s;uri=u;}
 public Intent setPackage(String s){pkg=s;return this;}public void setSelector(Intent s){selector=s;}
 public Intent setType(String s){type=s;return this;}public Intent addCategory(String s){category=s;return this;}public Intent putExtra(String n,boolean v){multiple=v;return this;}public Intent addFlags(int f){flags|=f;return this;}public android.net.Uri getData(){return uri;}public ClipData getClipData(){return null;}
}
