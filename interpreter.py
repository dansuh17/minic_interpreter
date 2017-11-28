import yacc
import operator
from astree import *
from symbol_table import Scope, Symbol

class SemanticError(Exception):
    def __init__(self, msg):
        self.msg = msg

input_file = 'error_test.c'
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

print(parser.errorlines)  # lines where syntax error occurred
print('Result AST tree')
ast_root.show()

# mark the starting line
main_ast = parser.main_func
curr_lineno = main_ast.linespan[0]  # starting line number of main()
print(curr_lineno)
astnode = main_ast

# register functions
root_scope = Scope(symbol_table={})
for func in parser.functions:
    root_scope.add_symbol(
            symbol_name=func.name(),
            symbol_info=Symbol(name=func.name(), dtype='function', astnode=func))
scope = root_scope  # current evaluation scope

# evaluation stack - initial stack with function call of main
eval_stack = [FunctionCall(func_name='main', argument_list=ArgList([]))]

# evalutaion loop
while True:
    input('Next line {}'.format(curr_lineno))  # next line
    did_exec = eval_stack[-1].execute(scope, currline, eval_stack)
    if did_exec:
        eval_stack.pop()
    print(astnode)
    curr_lineno += 1  # 1 line just for now

