package com.nice.errorbook.m3e;

import android.graphics.Bitmap;
import android.graphics.PointF;
import android.graphics.drawable.Drawable;
import android.widget.TextView;
import com.hailiang.xxb.ai.camera.core.scan.EdgeArea;
import com.hailiang.xxb.ai.camera.view.SmartCameraPreview;
import java.util.Arrays;

/** Local capture accepts any valid photo; cropping begins at its real corners. */
public final class CameraCapturePolicy {
    public static EdgeArea full(Bitmap image){
        if(image==null)throw new IllegalArgumentException("Missing photo");
        int w=image.getWidth(),h=image.getHeight();
        if(w<=0 || h<=0)throw new IllegalArgumentException("Invalid photo size");
        return new EdgeArea(w,h,Arrays.asList(new PointF(0,0),new PointF(w,0),new PointF(w,h),new PointF(0,h)));
    }
    public static void status(SmartCameraPreview preview){
        TextView text=preview.getStatusTv();
        text.setText("自由拍照 · 可直接上传");
        text.setTextColor(Palette.argb(Palette.ON_CONTAINER));
        Drawable background=text.getBackground();
        if(background!=null)background.mutate().setTint(Palette.argb(Palette.PRIMARY_CONTAINER));
        preview.clearPoints();
    }
}
