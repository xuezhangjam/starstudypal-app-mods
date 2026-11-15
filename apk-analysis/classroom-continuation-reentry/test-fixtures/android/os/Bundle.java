package android.os;

public class Bundle {
    private final java.util.Map<String,Long> values = new java.util.HashMap<>();
    public long getLong(String key){return values.getOrDefault(key,0L);}
    public void putLong(String key,long value){values.put(key,value);}
}