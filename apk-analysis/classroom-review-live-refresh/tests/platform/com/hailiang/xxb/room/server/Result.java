package com.hailiang.xxb.room.server;
public abstract class Result<T> {public static class Success<T> extends Result<T> {T data;public Success(T t){data=t;}public T getData(){return data;}}public static class Failure extends Result<Object> {String msg;public Failure(String m){msg=m;}public String getMsg(){return msg;}}}
