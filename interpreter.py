import yacc
import operator
from astree import *
from symbol_table import Scope, Symbol


class SemanticError(Exception):
    def __init__(self, msg):
        self.msg = msg

input_file = 'test.c'
parser = yacc.parser  # import the parser

code_lines = []  # keep track of lines of code
try:
    s = ''
    with open(input_file, 'r') as f:
        for l in f.readlines():
            s += l
            code_lines.append(l)
except EOFError:
    print('EOFError')
print(s)

# parsing step
ast_root = parser.parse(s, tracking=True)
if parser.main_func is None:
    raise SemanticError('No main function!')

# print(parser.errorlines)  # lines where syntax error occurred
print('Result AST tree')
ast_root.show()

# mark the starting line
curr_lineno = parser.main_func.linespan[0]  # starting line number of main()

# register function names - interpreter only recognizes the name
# and does not have function closure
root_scope = Scope(symbol_table={})
for func in parser.functions:
    root_scope.add_symbol(
            symbol_name=func.name(),
            symbol_info=Symbol(name=func.name(), astnode=func))
scope = root_scope  # current evaluation scope

# evaluation stack - initial stack with function call of main
main_call = FunctionCall(func_name=String('main'), argument_list=ArgList([]))
main_call.linespan = (curr_lineno, curr_lineno)

exec_stack = [main_call]
call_stack = []
env = ExecutionEnvironment(exec_stack, curr_lineno, scope, call_stack)

# evalutaion loop
while True:
    input('Next line {}'.format(env.currline))  # next line
    print(code_lines[env.currline - 1])
    currline = env.currline

    while True:
        stacklen = len(exec_stack)
        print('Executing {}'.format(exec_stack[-1]))
        exec_done, env = exec_stack[-1].execute(env)

        stack_val_print = ''
        for stack_val in env.value_stack:
            stack_val_print += (stack_val.__repr__() + ' :: ')
        print(stack_val_print)
        # print([ast.linespan for ast in env.exec_stack])
        # print(exec_stack[-1].linespan)
        if (not exec_done and len(exec_stack) == stacklen) or (currline != env.currline):
            break

    # update line number
    if currline == env.currline:
        env.update_currline(1)  # 1 line just for now

    # do booked updates (++, -- used as postfixes)
    env.exec_booked_updates()
