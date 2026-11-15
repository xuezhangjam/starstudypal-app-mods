package com.nice.errorbook.m3e;
public final class PhotoPolicy {
    public static int remaining(int max,int existing){return max<=0?0:Math.max(0,max-Math.max(0,existing));}
    public static int[] target(int w,int h){
        if(w<=0 || h<=0)throw new IllegalArgumentException("Invalid image dimensions");
        double s=Math.min(1d,Math.min(4096d/Math.max(w,h),Math.sqrt(8000000d/((double)w*h))));
        return new int[]{Math.max(1,(int)Math.floor(w*s)),Math.max(1,(int)Math.floor(h*s))};
    }
}
