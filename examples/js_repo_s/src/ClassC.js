const ClassA = require('./ClassA');
const ClassB = require('./ClassB');

class ClassC {
    constructor(name, age) {
        this.instanceA = new ClassA(name);
        this.instanceB = new ClassB(age);
    }

    introduceYourself() {
        this.instanceA.sayHello();
        this.instanceB.getAge();
    }
}

module.exports = ClassC;