# Interpreter for Mini-C
A project from KAIST CS420 Course 'Compiler Design'.

## The Scope of Mini-C
The scope of Mini-C language to interpret is roughly defined by the sample code:

```
int avg(int count, int *value) {
  int i, total;
  total = 0;
  for (i = 0; i < count; i++) {
    total = total + value[i];
  }

  return (total / count);
}

int main(void) {
  int studentNumber, count, i, sum;
  int mark[4];
  float average;

  count = 4;
  sum = 0;
  for (i = 0; i < count; i++) {
    mark[i] = i * 30;
    sum = sum + mark[i];
    average = avg(i + 1, mark);
    if (average > 40) {
      printf("average");
    }
  }
}
```

However, additional specifications are provided below for clarification:
- initializer declarations available ("int i = 2, j = 5")
- all binary operators available
- unary operators available both in postfix and prefix form
- type casting among int and float types
- no global scope variables
- no pointer arithmetics ("\*i = 9", or "int \*p = &a" are not available, as well as summation or subtraciton of address values)
- no nested pointers / arrays
- no function pointers
- no while-loop
- no switch-case statement
- no bitwise operation
- no assigment-operations (+=, /=, etc.)
- no abstract declarations

## Installing

Prerequisite: `Python 3.5.2` or above

```
pip3 install -r requirements.txt
```

## Running

To start the interpreter, run:
```
python3 interpreter.py --cfile test.c
```
Where `--cfile` option specifies the file name to run the interpreter on.
The default file name is `test.c`.

Once the interpreter is running, the user can type in commands until the program executes properly
or user chooses to exit.

Available Interpreter Commands:
- next [lineno] : executes code by lineno lines. if lineno is not given, code executes one line.
- print [symbol] : prints the value of symbol
- trace [symbol] : shows the value history of symbol
- log : shows execution log
- scope : shows block scope stack and its contents
- exit : stops the interpreter

## Syntax Errors

In order to interpret without global scope, the interpreter must scan and build the abstract syntax tree
before executing the `main()` function.
Otherwise the interpreter whould not have function symbols registered in the scope for usage.
If a syntax error occurs during pre-scanning, it throws an according error message and terminates the session.

## Testing

Some of files written in mini-c for testing purposes are located in `cfiles` folder.
