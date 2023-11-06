package com.example.utilities;

public class StringUtil {
    public String capitalize(String input) {
        return input.substring(0, 1).toUpperCase() + input.substring(1);
    }
}