import ply.yacc as yacc
from lex import tokens

# creates a shift-reduce parser from LALR table created from grammar
"""
Grammar for semi-C.
Referenced : http://www.quut.com/c/ANSI-C-grammar-y.html
Followed instructions of : http://www.dabeaz.com/ply/ply.html


primary_expression
    : ID
    | string
    | '(' expression ')'

string
    : STRING_LITERAL

postfix_expression
    : primary_expression
    | postfix_expression '[' expression ']'
    | postfix_expression '(' ')'
    | postfix_expression '(' argument_expression_list ')'
    | postfix_expression '.' ID
    | postfix_expression PPLUS
    | postfix_expression MMINUS
    | '(' type_name ')' '{' initializer_list '}'
    | '(' type_name ')' '{' initializer_list ',' '}'

argument_expression_list
    : assignment_expression
    | argument_expression_list ',' assignment_expression

unary_expression
    : postfix_expression
    | MMINUS unary_expression
    | PPLUS unary_expression

cast_expression
    : unary_expression
    | '(' type_name ')' cast_expression

multiplicative_expression
    : cast_expression
    | multiplicative_expression '*' cast_expression
    | multiplicative_expression '/' cast_expression
    | multiplicative_expression '%' cast_expression

additive_expression
    : multiplicative_expression
    | additive_expression '+' multiplicative_expression
    | additive_expression '-' multiplicative_expression

shift_expression   # no shift operators - equivalent to additive expression
    : additive_expression

relational_expression
    : shift_expression
    | relational_expression '<' shift_expression
    | relational_expression '>' shift_expression
    | relational_expression LEQ shift_expression
    | relational_expression GEQ shift_expression

equality_expression
    : relational_expression
    | equality_expression EQUALS relational_expression
    | equality_expression NEQUALS relational_expression

and_expression
    : equality_expression

exclusive_or_expression
    : and_expression

inclusive_or_expression
    : exclusive_or_expression

logical_and_expression
    : inclusive_or_expression
    | logical_and_expression AND inclusive_or_expression

logical_or_expression
    : logical_and_expression
    | logical_or_expression OR logical_and_expression

conditional_expression
    : logical_or_expression

assignment_expression
    : conditional_expression
    | unary_expression assignment_operator assignment_expression

assignment_operator
    : '='

expression
    : assignment_expression
    | expression ',' assignment_expression  ## ???

constant_expression
    : conditional_expression    /* with constraints */

declaration
    : declaration_specifiers ';'
    | declaration_specifiers init_declarator_list ';'

declaration_specifiers
    | type_specifier declaration_specifiers
    | type_specifier

init_declarator_list
    : init_declarator
    | init_declarator_list ',' init_declarator

init_declarator
    : declarator '=' initializer
    | declarator

type_specifier
    | VOID
    | INT
    | FLOAT

specifier_qualifier_list
    : type_specifier specifier_qualifier_list
    | type_specifier

declarator
    : pointer direct_declarator
    | direct_declarator

direct_declarator
    : ID
    | '(' declarator ')'
    | direct_declarator '[' ']'
    | direct_declarator '[' '*' ']'
    | direct_declarator '[' assignment_expression ']'
    | direct_declarator '(' parameter_type_list ')'
    | direct_declarator '(' ')'
    | direct_declarator '(' identifier_list ')'

pointer
    | '*' pointer
    | '*'

parameter_type_list
    | parameter_list

parameter_list
    : parameter_declaration
    | parameter_list ',' parameter_declaration

parameter_declaration
    : declaration_specifiers declarator
    | declaration_specifiers abstract_declarator
    | declaration_specifiers

identifier_list
    : ID
    | identifier_list ',' ID

type_name
    : specifier_qualifier_list abstract_declarator
    | specifier_qualifier_list

abstract_declarator
    : pointer direct_abstract_declarator
    | pointer
    | direct_abstract_declarator

direct_abstract_declarator
    : '(' abstract_declarator ')'
    | '[' ']'
    | '[' '*' ']'
    | '[' assignment_expression ']'
    | direct_abstract_declarator '[' ']'
    | direct_abstract_declarator '[' '*' ']'
    | direct_abstract_declarator '[' assignment_expression ']'
    | '(' ')'
    | '(' parameter_type_list ')'
    | direct_abstract_declarator '(' ')'
    | direct_abstract_declarator '(' parameter_type_list ')'

initializer
    : '{' initializer_list '}'
    | '{' initializer_list ',' '}'
    | assignment_expression

initializer_list
    : designation initializer
    | initializer
    | initializer_list ',' designation initializer
    | initializer_list ',' initializer

designation
    : designator_list '='

designator_list
    : designator
    | designator_list designator

designator
    : '[' constant_expression ']'
    | '.' IDENTIFIER

statement
    | compound_statement
    | expression_statement
    | selection_statement
    | iteration_statement
    | jump_statement

compound_statement
    : '{' '}'
    | '{'  block_item_list '}'

block_item_list
    : block_item
    | block_item_list block_item

block_item
    : declaration
    | statement

expression_statement
    : ';'
    | expression ';'

selection_statement
    : IF '(' expression ')' statement ELSE statement
    | IF '(' expression ')' statement

iteration_statement
    : WHILE '(' expression ')' statement
    | FOR '(' expression_statement expression_statement ')' statement
    | FOR '(' expression_statement expression_statement expression ')' statement
    | FOR '(' declaration expression_statement ')' statement
    | FOR '(' declaration expression_statement expression ')' statement

jump_statement
    | CONTINUE ';'
    | BREAK ';'
    | RETURN ';'
    | RETURN expression ';'

translation_unit  /* starting point */
    : external_declaration
    | translation_unit external_declaration

external_declaration
    : function_definition
    | declaration

function_definition
    : declaration_specifiers declarator declaration_list compound_statement
    | declaration_specifiers declarator compound_statement

declaration_list
    : declaration
    | declaration_list declaration
"""
start = 'translation_unit'

def p_expression_plus(p):
    "expression : expression '+' term"
    p[0] = p[1] + p[3]

# error rule
def p_error(p):
    print('Syntax Error!')

parser = yacc.yacc()
while True:
    try:
        s = input('Program')
    except EOFError:
        break
    if not s:
        continue
    result = parser.parse(s)
    print(result)

