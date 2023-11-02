class ClassB {
    constructor(age) {
        this.age = age;
    }

    getAge() {
        console.log(`I am ${this.age} years old`);
    }
}

module.exports = ClassB;