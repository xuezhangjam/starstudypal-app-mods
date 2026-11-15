package com.hailiang.workcloud.student.shareui.core.components;
public abstract class LoadMoreState {public static class Idle extends LoadMoreState {}public static class Loading extends LoadMoreState {}public static class Error extends LoadMoreState {public String getMessage(){return null;}}}
