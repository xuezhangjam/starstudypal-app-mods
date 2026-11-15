package kotlin;
public class ResultKt {public static void throwOnFailure(Object result){if(result instanceof Throwable)throw new RuntimeException((Throwable)result);}}
