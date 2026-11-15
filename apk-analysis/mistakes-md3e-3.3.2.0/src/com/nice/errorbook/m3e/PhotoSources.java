package com.nice.errorbook.m3e;
import android.app.Activity;
import android.content.Context;
import android.content.Intent;
import com.hailiang.xxb.ai.camera.view.CameraIntent;
import com.hailiang.xxb.ai.camera.view.data.CaptureImage;
import com.hailiang.xxb.ai.camera.view.data.SmartCameraConfig;
import java.util.List;
public final class PhotoSources {
    public static void open(Context context,SmartCameraConfig config,List<CaptureImage> captures){
        Intent intent=new Intent(context,PhotoSourceActivity.class);
        CameraIntent.INSTANCE.putConfig(intent,config);CameraIntent.INSTANCE.putCaptures(intent,captures);
        if(!(context instanceof Activity))intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
        context.startActivity(intent);
    }
}
