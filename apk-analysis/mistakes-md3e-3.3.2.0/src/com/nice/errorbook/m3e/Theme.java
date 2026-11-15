package com.nice.errorbook.m3e;

import android.app.Activity;
import android.app.Dialog;
import android.content.res.ColorStateList;
import android.graphics.Typeface;
import android.graphics.drawable.ColorDrawable;
import android.graphics.drawable.GradientDrawable;
import android.graphics.drawable.StateListDrawable;
import android.os.Handler;
import android.os.Looper;
import android.view.View;
import android.view.ViewGroup;
import android.view.ViewTreeObserver;
import android.widget.ImageView;
import android.widget.TextView;
import java.lang.ref.WeakReference;
import java.util.WeakHashMap;
import com.google.android.material.tabs.TabLayout;

public final class Theme implements ViewTreeObserver.OnGlobalLayoutListener {
    private static final WeakHashMap<Activity,Theme> INSTALLED=new WeakHashMap<Activity,Theme>();
    private final WeakReference<Activity> activity;
    private final WeakHashMap<View,Boolean> footer=new WeakHashMap<View,Boolean>();
    private final WeakHashMap<View,Integer> actions=new WeakHashMap<View,Integer>();
    private boolean painting;
    private int lastSurface;
    private Theme(Activity a){activity=new WeakReference<Activity>(a);}
    public static void begin(final Activity a){Palette.init(a);new Handler(Looper.getMainLooper()).post(()->{if(!a.isFinishing() && !a.isDestroyed())install(a);});}
    public static void install(final Activity a){
        Palette.init(a);if(INSTALLED.containsKey(a))return;
        Theme t=new Theme(a);INSTALLED.put(a,t);View root=a.getWindow().getDecorView();root.getViewTreeObserver().addOnGlobalLayoutListener(t);root.post(t::paint);
    }
    private static View named(View root,String name){
        int id=root.getResources().getIdentifier(name,"id","com.nice.errorbook");return id==0?null:root.findViewById(id);
    }
    private static void color(View root,String id,int role){View v=named(root,id);if(v instanceof TextView){TextView t=(TextView)v;int c=Palette.argb(role);if(t.getCurrentTextColor()!=c)t.setTextColor(c);}}
    private void paint(){
        Activity a=activity.get();if(a==null || a.isFinishing() || a.isDestroyed() || painting)return;painting=true;
        try{
            NativeUi.window(a);View root=a.getWindow().getDecorView();
            int surface=Palette.argb(Palette.SURFACE);if(lastSurface!=surface){a.getWindow().setBackgroundDrawable(new ColorDrawable(surface));lastSurface=surface;}
            String name=a.getClass().getName();
            ViewGroup content=(ViewGroup)a.findViewById(android.R.id.content);
            if(content!=null && content.getChildCount()>0)content.getChildAt(0).setBackgroundColor(surface);
            if(name.equals("com.nice.errorbook.ui.MainActivity")){
                color(root,"tv_name",Palette.ON_SURFACE);color(root,"tv_empty",Palette.VARIANT);color(root,"tv_version",Palette.VARIANT);
                View version=named(root,"tv_version");
                if(version instanceof TextView && !"3.3.2.0 · MD3e · 外观".contentEquals(((TextView)version).getText()))((TextView)version).setText("3.3.2.0 · MD3e · 外观");
                if(version!=null && version.getBackground() instanceof GradientDrawable){GradientDrawable d=(GradientDrawable)version.getBackground();int c=Palette.argb(Palette.CONTAINER);if(d.getColor()!=null && d.getColor().getDefaultColor()!=c)d.setColor(c);}
                if(version instanceof TextView && !footer.containsKey(version)){
                    TextView t=(TextView)version;t.setPadding(NativeUi.dp(a,12),NativeUi.dp(a,4),NativeUi.dp(a,12),NativeUi.dp(a,4));t.setMinHeight(NativeUi.dp(a,30));
                    t.setBackground(NativeUi.shape(a,Palette.argb(Palette.CONTAINER),20));
                    t.setText("3.3.2.0 · MD3e · 外观");t.setContentDescription("外观设置");t.setClickable(true);t.setFocusable(true);
                    final WeakReference<Activity> target=activity;t.setOnClickListener(v->{Activity owner=target.get();if(owner!=null)NativeUi.appearance(owner);});footer.put(version,true);
                }
                View tabs=named(root,"tabLayout");
                if(tabs instanceof TabLayout){TabLayout layout=(TabLayout)tabs;
                    for(int i=0;i<layout.getTabCount();i++){
                        TabLayout.Tab tab=layout.getTabAt(i);View custom=tab==null?null:tab.getCustomView();if(custom==null)continue;
                        boolean selected=i==layout.getSelectedTabPosition();View label=named(custom,"tv_tab_name"),indicator=named(custom,"iv_tab_selected");
                        if(label instanceof TextView){TextView t=(TextView)label;int c=Palette.argb(selected?Palette.ON_CONTAINER:Palette.VARIANT);if(t.getCurrentTextColor()!=c)t.setTextColor(c);t.setTypeface(Typeface.DEFAULT,selected?Typeface.BOLD:Typeface.NORMAL);}
                        if(indicator instanceof ImageView){ImageView image=(ImageView)indicator;int c=Palette.argb(Palette.PRIMARY_CONTAINER);if(!footer.containsKey(image)){image.setImageDrawable(NativeUi.shape(a,c,24));footer.put(image,true);}else if(image.getDrawable() instanceof GradientDrawable){GradientDrawable d=(GradientDrawable)image.getDrawable();if(d.getColor()!=null && d.getColor().getDefaultColor()!=c)d.setColor(c);}}
                    }
                }
            }
            // Keep question paper, formulas, handwriting and photographic pixels
            // untouched; only named native chrome gets a semantic color.
            for(String id:new String[]{"tv_title","title_tv","tv_back"})color(root,id,Palette.ON_SURFACE);
            for(String id:new String[]{"tv_time","tv_reminder","tv_draft_switch"}){
                color(root,id,Palette.VARIANT);View v=named(root,id);
                if(v instanceof TextView)((TextView)v).setCompoundDrawableTintList(ColorStateList.valueOf(Palette.argb(Palette.VARIANT)));
            }
            View back=named(root,"iv_back");if(back instanceof ImageView){ImageView image=(ImageView)back;int c=Palette.argb(Palette.ON_SURFACE);if(image.getImageTintList()==null || image.getImageTintList().getDefaultColor()!=c)image.setImageTintList(ColorStateList.valueOf(c));}
            View submit=named(root,"tv_submit");int primary=Palette.argb(Palette.PRIMARY);
            if(submit instanceof TextView && (!actions.containsKey(submit) || actions.get(submit)!=primary)){
                StateListDrawable states=new StateListDrawable();states.addState(new int[]{-android.R.attr.state_enabled},NativeUi.shape(a,Palette.argb(Palette.HIGH),26));states.addState(new int[]{},NativeUi.shape(a,primary,26));
                submit.setBackground(states);((TextView)submit).setTextColor(new ColorStateList(new int[][]{new int[]{-android.R.attr.state_enabled},new int[]{}},new int[]{Palette.argb(Palette.VARIANT),Palette.argb(Palette.ON_PRIMARY)}));actions.put(submit,primary);
            }
        }finally{painting=false;}
    }
    public static void dialog(View root){
        Palette.init(root.getContext());root.setBackground(NativeUi.shape(root.getContext(),Palette.argb(Palette.HIGH),32));dialogText(root);
        for(String id:new String[]{"dialog_confirm","dialog_cancel"}){
            View v=named(root,id);if(v instanceof TextView){boolean primary=id.equals("dialog_confirm");TextView t=(TextView)v;
                t.setTextColor(Palette.argb(primary?Palette.ON_PRIMARY:Palette.ON_CONTAINER));
                t.setBackground(NativeUi.shape(root.getContext(),Palette.argb(primary?Palette.PRIMARY:Palette.PRIMARY_CONTAINER),26));t.setMinHeight(NativeUi.dp(root.getContext(),48));
            }
        }
    }
    private static void dialogText(View view){if(view instanceof TextView)((TextView)view).setTextColor(Palette.argb(Palette.ON_SURFACE));if(view instanceof ViewGroup){ViewGroup g=(ViewGroup)view;for(int i=0;i<g.getChildCount();i++)dialogText(g.getChildAt(i));}}
    public static void dialogWindow(Dialog dialog){if(dialog.getWindow()!=null)dialog.getWindow().setBackgroundDrawable(NativeUi.shape(dialog.getContext(),Palette.argb(Palette.HIGH),32));}
    public void onGlobalLayout(){paint();}
}
