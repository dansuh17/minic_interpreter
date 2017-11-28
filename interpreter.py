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
print(curr_lineno)

# register function names - interpreter only recognizes the name
# and does not have function closure
root_scope = Scope(symbol_table={})
for func in parser.functions:
    root_scope.add_symbol(
            symbol_name=func.name(),
            symbol_info=Symbol(name=func.name(), astnode=func))
scope = root_scope  # current evaluation scope

# evaluation stack - initial stack with function call of main
exec_stack = [FunctionCall(func_name=String('main'), argument_list=ArgList([]))]
call_stack = []
env = ExecutionEnvironment(exec_stack, curr_lineno, scope, call_stack)

# evalutaion loop
while True:
    input('Next line {}'.format(curr_lineno))  # next line

    while True:
        exec_done, env = exec_stack[-1].execute(env)
        if not exec_done:
            break
    curr_lineno += 1  # 1 line just for now
