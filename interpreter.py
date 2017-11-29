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
code_lines.append('EOF')

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
root_scope.return_lineno = len(code_lines) - 1

# evaluation stack - initial stack with function call of main
main_call = FunctionCall(func_name=Id('main'), argument_list=ArgList([]))
main_call.linespan = (curr_lineno, curr_lineno)

exec_stack = [main_call]
call_stack = []
env = ExecutionEnvironment(exec_stack, curr_lineno, scope, call_stack)

# evalutaion loop
total_line = 0
numlines = 0
while True:
    if numlines == 0:
        print('Next line : {}'.format(code_lines[env.currline - 1]))
        command = input('Command:')  # next line
        if command == '':
            commandlst = ['next', '1']
        else:
            commandlst = command.strip().split()
        cmd = commandlst[0]

        if cmd == 'next':
            numlines = int(commandlst[1])
        elif cmd == 'print':
            symbolname = commandlst[1]
            print(env.scope.getvalue(symbolname))
            continue
        elif cmd == 'trace':
            varname = commandlst[1]
            print(env.scope.getsymbol(varname).val_history)
            continue

    currline = env.currline  # store the current execution line
    while True:
        stacklen = len(exec_stack)
        if stacklen == 0:  # indicates end of program
            break

        print('Executing {} - {}'.format(exec_stack[-1], exec_stack[-1].linespan))
        exec_done, env = exec_stack[-1].execute(env)

        # print stack values for debugging
        stack_val_print = ''
        for stack_val in env.value_stack:
            stack_val_print += (stack_val.__repr__() + ' :: ')
        print(stack_val_print)
        print(env.exec_stack)

        if (not exec_done and len(exec_stack) == stacklen) or (currline != env.currline):
            break

    # update line number
    if currline == env.currline:
        env.update_currline(1)  # 1 line just for now
        # keep track of line numbers
        numlines -= 1
        total_line += 1

    # do booked updates (++, -- used as postfixes)
    env.exec_booked_updates()
    # env.scope.show()

    # end of program indicator
    if env.currline >= len(code_lines) or len(exec_stack) == 0:
        print('End of Program')
        break
