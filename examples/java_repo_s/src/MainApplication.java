package com.example;

import com.example.module.UserEntity;
import com.example.utilities.StringUtil;

/**
 * This is the main class of the application.
 */
public class MainApplication {

    /**
     * The main method which is the entry point to the application.
     * @param args Any command line arguments received by the application.
     */
    public static void main(String[] args) {
        UserEntity user = new UserEntity("John Doe", 30);
        StringUtil stringUtil = new StringUtil();
        String message = stringUtil.capitalize(user.getName());

        System.out.println("Hello, " + message + ". You are " + user.getAge() + " years old.");
    }
}