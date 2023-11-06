package com.example.module;

// Random inline comment
public class UserEntity {
    private String name;
    private int age;

    public UserEntity(String name, int age) {
        this.name = name;
        this.age = age;
    }

    public String getName() {
        return name;
    }

    public int getAge() {
        return age;
    }
}

/**
 * Test JavaDoc.
 */
class AdminEntity extends UserEntity {
    private boolean isAdmin;

    public AdminEntity(String name, int age, boolean isAdmin) {
        super(name, age);
        this.isAdmin = isAdmin;
    }

    public boolean getIsAdmin(){
        return this.isAdmin;
    }
}