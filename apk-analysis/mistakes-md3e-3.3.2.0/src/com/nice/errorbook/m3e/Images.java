package com.nice.errorbook.m3e;
import android.content.Context;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.ColorSpace;
import android.graphics.ImageDecoder;
import android.net.Uri;
import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
public final class Images {
    public static final class Photo {
        public final File file;public final int width,height;
        Photo(File f,int w,int h){file=f;width=w;height=h;}
    }
    public static Photo load(Context context,Uri uri)throws IOException{
        Bitmap decoded=null,flat=null;File output=null;boolean complete=false;
        try{
            decoded=ImageDecoder.decodeBitmap(ImageDecoder.createSource(context.getContentResolver(),uri),(decoder,info,source)->{
                int[] size=PhotoPolicy.target(info.getSize().getWidth(),info.getSize().getHeight());
                decoder.setAllocator(ImageDecoder.ALLOCATOR_SOFTWARE);decoder.setTargetColorSpace(ColorSpace.get(ColorSpace.Named.SRGB));decoder.setTargetSize(size[0],size[1]);
            });
            Bitmap image=decoded;
            if(decoded.hasAlpha()){flat=Bitmap.createBitmap(decoded.getWidth(),decoded.getHeight(),Bitmap.Config.ARGB_8888);Canvas canvas=new Canvas(flat);canvas.drawColor(Color.WHITE);canvas.drawBitmap(decoded,0f,0f,null);image=flat;}
            File dir=new File(context.getCacheDir(),"m3e-gallery");if(!dir.isDirectory() && !dir.mkdirs())throw new IOException("No image cache");
            output=File.createTempFile("gallery_",".jpg",dir);
            try(FileOutputStream stream=new FileOutputStream(output)){if(!image.compress(Bitmap.CompressFormat.JPEG,95,stream))throw new IOException("JPEG failed");}
            if(output.length()==0)throw new IOException("Empty image");complete=true;return new Photo(output,image.getWidth(),image.getHeight());
        }finally{if(flat!=null)flat.recycle();if(decoded!=null)decoded.recycle();if(!complete && output!=null)output.delete();}
    }
}
