package com.hailiang.xxb.room.server;
public abstract class Result<T> {public static class Success<T> extends Result<T> {public T getData(){return null;}}public static class Failure extends Result<Object> {public String getMsg(){return null;}}}
