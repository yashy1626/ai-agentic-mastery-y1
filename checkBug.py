# calculator.py

def divide(a, b):
    return a / b

print("Simple Calculator")

num1 = input("Enter first number: ")
num2 = input("Enter second number: ")

choice = input("Choose (+, -, *, /): ")

if choice == "+":
    print("Result:", num1 + num2)

elif choice == "-":
    print("Result:", num1 - num2)

elif choice == "*":
    print("Result:", num1 * num2)

elif choice == "/":
    print("Result:", divide(num1, num2))

else:
    print("Invalid choice")