package com.hljzjx.classroom.repairs;

/** PDF coordinates are fitted by width; translation must use the same length unit as ink. */
public final class DocumentGeometry {
    private DocumentGeometry(){}
    public static boolean validSource(int width,int height){return width>=200&&width<=16384&&height>=200&&height<=131072;}
    public static float factor(int localWidth,int sourceWidth){
        if(localWidth<=0||sourceWidth<=0)return 1f;
        return (float)localWidth/sourceWidth;
    }
    public static float translation(float value,int localWidth,int sourceWidth){return value*factor(localWidth,sourceWidth);}
}
