package org.json;
import java.util.*;public class JSONArray {List<Object> values=new ArrayList<Object>();public JSONArray put(Object o){values.add(o);return this;}public int length(){return values.size();}public JSONObject getJSONObject(int i)throws JSONException {return (JSONObject)values.get(i);}}
