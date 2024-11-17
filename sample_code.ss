// Variable declarations
var integer x = 5;
var integer y = 10;
var string greeting = "Hello, World!";
var boolean flag = true;

// Array declaration
var integer array = [1, 2, 3, 4, 5];

// Function declaration
function add(a, b) {
    return a + b;
}

// Function call and assignment
var integer result = add(x, y);
print(result);

// Array access and modification
array[2] = 10;
print(array[2]);

// Using built-in functions
var integer len = length(array);
print(len);

// If-Else statement
if (result > 10) {
    print("Result is greater than 10");
} else {
    print("Result is 10 or less");
}

// While loop
var integer counter = 0;
while (counter < 3) {
    print("Counter is " + counter);
    counter = counter + 1;
}

// For loop
for (var integer i = 0; i < 5; i = i + 1) {
    print("For loop iteration: " + i);
}

// Printing string and boolean
print(greeting);
print(flag);

// Using math constants
import "math";
var float sqrt_result = math.sqrt(result);
print(sqrt_result);
