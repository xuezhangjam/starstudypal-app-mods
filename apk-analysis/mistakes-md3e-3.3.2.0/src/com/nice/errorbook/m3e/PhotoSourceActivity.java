package com.nice.errorbook.m3e;

import android.app.Activity;
import android.content.ActivityNotFoundException;
import android.content.Context;
import android.content.Intent;
import android.content.ClipData;
import android.content.pm.PackageManager;
import android.content.res.ColorStateList;
import android.content.res.Configuration;
import android.graphics.drawable.Drawable;
import android.graphics.PointF;
import android.net.Uri;
import android.os.Bundle;
import android.provider.MediaStore;
import android.view.Gravity;
import android.view.View;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;
import com.hailiang.xxb.ai.camera.core.scan.EdgeArea;
import com.hailiang.xxb.ai.camera.view.CameraIntent;
import com.hailiang.xxb.ai.camera.view.SmartCamera;
import com.hailiang.xxb.ai.camera.view.data.CaptureImage;
import com.hailiang.xxb.ai.camera.view.data.ImageData;
import com.hailiang.xxb.ai.camera.view.data.SmartCameraConfig;
import androidx.core.content.FileProvider;
import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.StandardCopyOption;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/** The album route never opens the camera or requests broad storage access. */
public final class PhotoSourceActivity extends Activity {
    private static final int PICK=0x6b32;
    private static final int CAPTURE=0x6b33, CAMERA_PERMISSION=0x6b34;
    private SmartCameraConfig config;
    private List<CaptureImage> existing;
    private boolean handoff,working,selecting;
    private TextView gallery,camera,status;
    private ProgressBar progress;
    private File cameraFile;
    private Uri cameraUri;
    private final ExecutorService worker=Executors.newSingleThreadExecutor();
    @Override protected void onCreate(Bundle saved){
        super.onCreate(saved);Palette.init(this);
        try{config=CameraIntent.INSTANCE.getConfig(getIntent());if(config==null)throw new IllegalArgumentException("Missing camera config");List<CaptureImage> old=CameraIntent.INSTANCE.getCaptures(getIntent());existing=old==null?new ArrayList<>():new ArrayList<>(old);}
        catch(RuntimeException invalid){toast("照片入口已失效，请返回后重试");cancel();return;}
        FrameLayout root=new FrameLayout(this);root.setBackgroundColor(Palette.argb(Palette.SURFACE));
        LinearLayout body=NativeUi.column(this,32);body.setBackground(NativeUi.shape(this,Palette.argb(Palette.HIGH),32));
        int width=Math.min(NativeUi.dp(this,620),getResources().getDisplayMetrics().widthPixels-NativeUi.dp(this,48));
        ScrollView scroll=new ScrollView(this);scroll.setVerticalScrollBarEnabled(false);scroll.addView(body);root.addView(scroll,new FrameLayout.LayoutParams(width,-2,Gravity.CENTER));
        root.addOnLayoutChangeListener((v,left,top,right,bottom,ol,ot,orr,ob)->{int available=Math.max(1,right-left-NativeUi.dp(this,48));int target=Math.min(NativeUi.dp(this,620),available);if(scroll.getLayoutParams().width!=target){scroll.getLayoutParams().width=target;scroll.requestLayout();}});
        NativeUi.row(body,NativeUi.text(this,"添加错题照片",30,Palette.argb(Palette.ON_SURFACE),true),0);
        NativeUi.row(body,NativeUi.text(this,"拍摄纸质错题，或选择相册里的照片。",16,Palette.argb(Palette.VARIANT),false),12);
        camera=NativeUi.button(this,"系统相机拍照",true);gallery=NativeUi.button(this,"从相册选择",false);
        icon(camera,android.R.drawable.ic_menu_camera);icon(gallery,android.R.drawable.ic_menu_gallery);
        NativeUi.row(body,camera,28);NativeUi.row(body,gallery,12);
        status=NativeUi.text(this,"最多 "+config.getMaxCaptureCount()+" 张 · 当前已选 "+existing.size()+" 张",14,Palette.argb(Palette.VARIANT),false);NativeUi.row(body,status,20);
        progress=new ProgressBar(this);progress.setIndeterminateTintList(ColorStateList.valueOf(Palette.argb(Palette.PRIMARY)));progress.setVisibility(View.GONE);NativeUi.row(body,progress,12);
        TextView back=NativeUi.button(this,"返回",false);NativeUi.row(body,back,20);
        back.setOnClickListener(v->cancel());gallery.setOnClickListener(v->pick());camera.setOnClickListener(v->camera());
        setContentView(root);NativeUi.window(this);
        if(saved!=null){String path=saved.getString("m3eCameraFile");if(path!=null){File f=new File(path);try{if(f.getCanonicalPath().startsWith(new File(getCacheDir(),"m3e-camera").getCanonicalPath()+File.separator)){cameraFile=f;String uri=saved.getString("m3eCameraUri");cameraUri=uri==null?null:Uri.parse(uri);}}catch(IOException ignored){}}}
    }
    private void icon(TextView button,int resource){Drawable d=getDrawable(resource).mutate();d.setTint(button.getCurrentTextColor());d.setBounds(0,0,NativeUi.dp(this,24),NativeUi.dp(this,24));button.setCompoundDrawables(d,null,null,null);button.setCompoundDrawablePadding(NativeUi.dp(this,10));}
    @Override public void onConfigurationChanged(Configuration config){super.onConfigurationChanged(config);if(!working && !selecting)recreate();}
    private void camera(){
        if(working || selecting)return;
        if(PhotoPolicy.remaining(config.getMaxCaptureCount(),existing.size())==0){toast("已达到照片数量上限");return;}
        if(checkSelfPermission(android.Manifest.permission.CAMERA)!=PackageManager.PERMISSION_GRANTED){requestPermissions(new String[]{android.Manifest.permission.CAMERA},CAMERA_PERMISSION);return;}
        try{
            File dir=new File(getCacheDir(),"m3e-camera");if(!dir.isDirectory() && !dir.mkdirs())throw new IOException("No camera cache");
            cameraFile=File.createTempFile("shot_",".jpg",dir);cameraUri=FileProvider.getUriForFile(this,getPackageName()+".fileProvider",cameraFile);
            Intent intent=new Intent(MediaStore.ACTION_IMAGE_CAPTURE).putExtra(MediaStore.EXTRA_OUTPUT,cameraUri);
            intent.setClipData(ClipData.newRawUri("photo",cameraUri));intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION|Intent.FLAG_GRANT_WRITE_URI_PERMISSION);
            selecting=true;controls(false);startActivityForResult(intent,CAPTURE);
        }catch(IOException | RuntimeException error){selecting=false;controls(true);clearCamera();toast(error instanceof ActivityNotFoundException?"没有可用的系统相机，可从相册选择照片":"无法打开系统相机，可使用相册重试");}
    }
    @Override public void onRequestPermissionsResult(int request,String[] permissions,int[] grants){super.onRequestPermissionsResult(request,permissions,grants);if(request==CAMERA_PERMISSION){if(grants.length>0 && grants[0]==PackageManager.PERMISSION_GRANTED)camera();else toast("未获得相机权限，仍可从相册选择照片");}}
    private Intent picker(String action){return new Intent(action).setType("image/*").addCategory(Intent.CATEGORY_OPENABLE).putExtra(Intent.EXTRA_ALLOW_MULTIPLE,PhotoPolicy.remaining(config.getMaxCaptureCount(),existing.size())>1).addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);}
    private void pick(){
        if(working || selecting)return;
        if(PhotoPolicy.remaining(config.getMaxCaptureCount(),existing.size())==0){toast("已达到照片数量上限");return;}
        selecting=true;controls(false);
        try{try{startActivityForResult(picker(Intent.ACTION_OPEN_DOCUMENT),PICK);}catch(ActivityNotFoundException absent){startActivityForResult(picker(Intent.ACTION_GET_CONTENT),PICK);}}
        catch(RuntimeException absent){selecting=false;controls(true);toast("无法打开相册，请检查相册或文件选择器");}
    }
    private void controls(boolean enabled){if(gallery!=null)gallery.setEnabled(enabled);if(camera!=null)camera.setEnabled(enabled);}
    @Override protected void onActivityResult(int request,int result,Intent data){
        super.onActivityResult(request,result,data);if(working)return;
        if(request==CAPTURE){
            selecting=false;revokeCamera();
            if(result!=RESULT_OK){clearCamera();controls(true);return;}
            ArrayList<Uri> captured=new ArrayList<>();File source=cameraFile;cameraFile=null;
            if(source!=null && source.length()>0)captured.add(Uri.fromFile(source));
            else if(data!=null && data.getData()!=null && ("content".equals(data.getData().getScheme()) || "file".equals(data.getData().getScheme())))captured.add(data.getData());
            if(captured.isEmpty()){if(source!=null)source.delete();controls(true);toast("相机未返回原图，请重试或从相册选择");return;}
            importUris(captured,source);return;
        }
        if(request!=PICK)return;selecting=false;
        if(result!=RESULT_OK || data==null){controls(true);return;}
        LinkedHashSet<Uri> selected=new LinkedHashSet<>();
        if(data.getData()!=null)selected.add(data.getData());
        if(data.getClipData()!=null)for(int i=0;i<data.getClipData().getItemCount();i++)selected.add(data.getClipData().getItemAt(i).getUri());
        final ArrayList<Uri> uris=new ArrayList<>();int limit=PhotoPolicy.remaining(config.getMaxCaptureCount(),existing.size());
        for(Uri uri:selected)if(uri!=null && ("content".equals(uri.getScheme()) || "file".equals(uri.getScheme())) && uris.size()<limit)uris.add(uri);
        if(uris.isEmpty()){controls(true);toast("没有选择可读取的照片");return;}
        if(selected.size()>uris.size())toast("按当前数量上限导入前 "+uris.size()+" 张照片");
        importUris(uris,null);
    }
    private void importUris(final List<Uri> uris,final File cameraSource){
        working=true;controls(false);progress.setVisibility(View.VISIBLE);status.setText("正在导入照片…");final Context app=getApplicationContext();
        worker.execute(()->{
            final ArrayList<CaptureImage> captures=new ArrayList<>(existing);final ArrayList<File> owned=new ArrayList<>();String failure=null;
            try{
                for(int i=0;i<uris.size();i++){
                    if(Thread.currentThread().isInterrupted())throw new IOException("Cancelled");
                    Images.Photo photo=Images.load(app,uris.get(i));owned.add(photo.file);
                    String crop=CaptureImage.Companion.createCropPath(app);File cropFile=new File(crop);owned.add(cropFile);
                    File directory=cropFile.getParentFile();if(directory!=null && !directory.isDirectory() && !directory.mkdirs())throw new IOException("No crop directory");
                    Files.copy(photo.file.toPath(),cropFile.toPath(),StandardCopyOption.REPLACE_EXISTING);
                    // Preserve the complete image; manual cropping in the original
                    // preview starts at its four real corners, without camera insets.
                    EdgeArea edge=new EdgeArea(photo.width,photo.height,Arrays.asList(new PointF(0,0),new PointF(photo.width,0),new PointF(photo.width,photo.height),new PointF(0,photo.height)));
                    ImageData original=new ImageData(photo.file.getAbsolutePath(),crop,null,null,null,null,false,false,edge,null,0f);
                    ImageData enhanced=new ImageData(CaptureImage.Companion.createEnhancePath(app),CaptureImage.Companion.createCropPath(app),null,null,null,null,false,false,null,null,0f);
                    captures.add(new CaptureImage(Uri.fromFile(photo.file),photo.file.getAbsolutePath(),original,enhanced,config.getEnhancementEnable()?2:1,false));
                }
            }catch(IOException error){failure="照片无法读取，请重新选择";}
             catch(RuntimeException error){failure="照片格式无法导入，请更换照片";}
             catch(OutOfMemoryError error){failure="照片过大，请选择较小的图片";}
            if(cameraSource!=null)cameraSource.delete();
            final String message=failure;
            runOnUiThread(()->{
                if(isFinishing() || isDestroyed()){for(File file:owned)file.delete();return;}
                working=false;progress.setVisibility(View.GONE);
                if(message!=null){for(File file:owned)file.delete();controls(true);status.setText("导入失败，可重新选择");toast(message);return;}
                try{
                    SmartCamera.INSTANCE.previewCaptures$camera_view_release(this,config,captures);
                    handoff=true;finish();
                }catch(RuntimeException error){for(File file:owned)file.delete();controls(true);status.setText("预览未能打开，请重试");toast("无法打开照片预览");}
            });
        });
    }
    private void revokeCamera(){if(cameraUri!=null){revokeUriPermission(cameraUri,Intent.FLAG_GRANT_READ_URI_PERMISSION|Intent.FLAG_GRANT_WRITE_URI_PERMISSION);cameraUri=null;}}
    private void clearCamera(){revokeCamera();if(cameraFile!=null){cameraFile.delete();cameraFile=null;}}
    @Override protected void onSaveInstanceState(Bundle state){super.onSaveInstanceState(state);if(cameraFile!=null)state.putString("m3eCameraFile",cameraFile.getAbsolutePath());if(cameraUri!=null)state.putString("m3eCameraUri",cameraUri.toString());}
    private void toast(String text){Toast.makeText(this,text,Toast.LENGTH_LONG).show();}
    private void cancel(){if(!handoff){if(existing!=null && !existing.isEmpty() && config!=null){SmartCamera.INSTANCE.previewCaptures$camera_view_release(this,config,existing);}else SmartCamera.INSTANCE.callbackCancel$camera_view_release();handoff=true;}finish();}
    @Override public void onBackPressed(){cancel();}
    @Override protected void onDestroy(){worker.shutdownNow();if(isFinishing()){clearCamera();if(!handoff)SmartCamera.INSTANCE.callbackCancel$camera_view_release();}super.onDestroy();}
}
