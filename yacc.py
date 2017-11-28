import ply.yacc as yacc
from lex import tokens
from astree import *


"""
Grammar for semi-C.
Creates a shift-reduce parser from LALR table created from grammar

Referenced : http://www.quut.com/c/ANSI-C-grammar-y.html
Followed instructions of : http://www.dabeaz.com/ply/ply.html


primary_expression
    : ID
    | constant
    | string
    | '(' expression ')'

constant
    : INTEGER_NUM
    | FLOATING_POINT_NUM

string
    : STRING_LITERAL

postfix_expression
    : primary_expression
    | postfix_expression '[' expression ']'
    | postfix_expression '(' ')'
    | postfix_expression '(' argument_expression_list ')'
    | postfix_expression PPLUS
    | postfix_expression MMINUS

argument_expression_list
    : assignment_expression
    | argument_expression_list ',' assignment_expression

unary_expression
    : postfix_expression
    | MMINUS unary_expression
    | PPLUS unary_expression

type_name
    : specifier_qualifier_list

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
    : identifier
    | '(' declarator ')'
    | direct_declarator '[' ']'
    | direct_declarator '[' assignment_expression ']'
    | direct_declarator '(' parameter_type_list ')'
    | direct_declarator '(' ')'

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

abstract_declarator
    : pointer direct_abstract_declarator
    | pointer
    | direct_abstract_declarator

direct_abstract_declarator
    : '(' abstract_declarator ')'
    | '[' ']'
    | '[' assignment_expression ']'
    | direct_abstract_declarator '[' ']'
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
    : RETURN ';'
    | RETURN expression ';'

translation_unit  /* starting point */
    : external_declaration
    | translation_unit external_declaration

external_declaration
    : function_definition
    | declaration

function_definition
    : declaration_specifiers declarator compound_statement
"""
start = 'translation_unit'  # starting nonterminal

"""
p.lineno(2)  # line number of second token
p.lexpos(2)  # position of second token
"""
def register_lineinfo(p, tok_pos, reg_pos=-1):
    if reg_pos == -1:
        reg_pos = tok_pos
    p[reg_pos].linespan = p.linespan(tok_pos)
    p[reg_pos].lexspan = p.lexspan(tok_pos)


def p_primary_expression(p):
    """
    primary_expression : identifier
        | constant
        | string
        | '(' expression ')'
    """
    if len(p) == 4:
        p[0] = p[2]
        register_lineinfo(p, 2)
    else:
        register_lineinfo(p, 1)
        p[0] = p[1]


def p_identifier(p):
    """
    identifier : ID
    """
    p[0] = Id(id_name=p[1])
    register_lineinfo(p, 1, 0)


def p_constant(p):
    """
    constant : INTEGER_NUM
        | FLOATING_POINT_NUM
    """
    p[0] = Constant(value=p[1])
    register_lineinfo(p, 1, 0)


def p_string(p):
    """
    string : STRING_LITERAL
    """
    p[0] = String(string=p[1])
    register_lineinfo(p, 1, 0)

def p_type_name(p):
    """
    type_name : specifier_qualifier_list
    """
    # int or float
    register_lineinfo(p, 1)
    p[0] = p[1]

def p_postfix_expression(p):
    """
    postfix_expression : primary_expression
        | postfix_expression '[' expression ']'
        | postfix_expression '(' ')'
        | postfix_expression '(' argument_expression_list ')'
        | postfix_expression PPLUS
        | postfix_expression MMINUS
    """
    if len(p) == 2:
        register_lineinfo(p, 1)
        p[0] = p[1]
    elif len(p) == 3:  # postfix operators
        register_lineinfo(p, 1)
        p[0] = UnaryExpr(op_name=p[2], operand=p[1], is_postfix=True)
    elif len(p) == 4:  # func call with no args
        register_lineinfo(p, 1)
        p[0] = FunctionCall(func_name=p[1], argument_list=ArgList(argument_list=[]))
    elif len(p) == 5:  # array reference or function call with argument list
        if p[2] == '[':
            register_lineinfo(p, 1)
            register_lineinfo(p, 3)
            p[0] = ArrayReference(name=p[1], idx=p[3])
        elif p[2] == '(':
            register_lineinfo(p, 1)
            register_lineinfo(p, 3)
            p[0] = FunctionCall(func_name=p[1], argument_list=p[3])
    else:
        raise Exception


def p_argument_expression_list(p):
    """
    argument_expression_list : assignment_expression
        | argument_expression_list ',' assignment_expression
    """
    if len(p) == 2:
        register_lineinfo(p, 1)
        p[0] = ArgList(argument_list=[p[1]])
    elif len(p) == 4:
        register_lineinfo(p, 3)
        p[1].append(p[3])  # add the argument
        p[0] = p[1]
    else:
        raise Exception


def p_unary_expression(p):
    """
    unary_expression : postfix_expression
        | MMINUS unary_expression
        | PPLUS unary_expression
    """
    if len(p) == 2:
        register_lineinfo(p, 1)
        p[0] = p[1]
    elif len(p) == 3:
        register_lineinfo(p, 1)
        register_lineinfo(p, 2)
        p[0] = UnaryExpr(op_name=p[1], operand=p[2], is_postfix=False)
    else:
        raise Exception


def p_cast_expression(p):
    """
    cast_expression : unary_expression
        | '(' type_name ')' cast_expression
    """
    if len(p) == 2:
        register_lineinfo(p, 1)
        p[0] = p[1]
    elif len(p) == 5:
        register_lineinfo(p, 2)
        register_lineinfo(p, 4)
        p[0] = TypeCast(type_name=p[2], cast_expr=p[4])
    else:
        raise Exception


def p_multiplicative_expression(p):
    """
    multiplicative_expression : cast_expression
        | multiplicative_expression '*' cast_expression
        | multiplicative_expression '/' cast_expression
        | multiplicative_expression '%' cast_expression
    """
    if len(p) == 2:
        register_lineinfo(p, 1)
        p[0] = p[1]
    elif len(p) == 4:
        register_lineinfo(p, 1)
        register_lineinfo(p, 3)
        opnode = Op(p[2])
        opnode.linespan = p.linespan(2)
        opnode.linespan = p.lexspan(2)
        p[0] = BinaryOp(op=opnode, arg1=p[1], arg2=p[3])
    else:
        raise Exception


def p_additive_expression(p):
    """
    additive_expression : multiplicative_expression
        | additive_expression '+' multiplicative_expression
        | additive_expression '-' multiplicative_expression
    """
    if len(p) == 2:
        register_lineinfo(p, 1)
        p[0] = p[1]
    elif len(p) == 4:
        register_lineinfo(p, 1)
        register_lineinfo(p, 3)
        opnode = Op(p[2])
        opnode.linespan = p.linespan(2)
        opnode.linespan = p.lexspan(2)
        p[0] = BinaryOp(op=opnode, arg1=p[1], arg2=p[3])
    else:
        raise Exception


def p_shift_expression(p):
    """
    shift_expression : additive_expression
    """
    # no shift operators in semi-c - equivalent to additive expression
    register_lineinfo(p, 1)
    p[0] = p[1]


def p_relational_expression(p):
    """
    relational_expression : shift_expression
        | relational_expression '<' shift_expression
        | relational_expression '>' shift_expression
        | relational_expression LEQ shift_expression
        | relational_expression GEQ shift_expression
    """
    if len(p) == 2:
        register_lineinfo(p, 1)
        p[0] = p[1]
    elif len(p) == 4:
        register_lineinfo(p, 1)
        register_lineinfo(p, 3)
        opnode = Op(p[2])
        opnode.linespan = p.linespan(2)
        opnode.linespan = p.lexspan(2)
        p[0] = BinaryOp(op=opnode, arg1=p[1], arg2=p[3])
    else:
        raise Exception


def p_equality_expression(p):
    """
    equality_expression : relational_expression
        | equality_expression EQUALS relational_expression
        | equality_expression NEQUALS relational_expression
    """
    if len(p) == 2:
        register_lineinfo(p, 1)
        p[0] = p[1]
    elif len(p) == 4:
        register_lineinfo(p, 1)
        register_lineinfo(p, 3)
        opnode = Op(p[2])
        opnode.linespan = p.linespan(2)
        opnode.linespan = p.lexspan(2)
        p[0] = BinaryOp(op=opnode, arg1=p[1], arg2=p[3])
    else:
        raise Exception


def p_and_expression(p):
    """
    and_expression : equality_expression
    """
    # no & operator
    register_lineinfo(p, 1)
    p[0] = p[1]


def p_exclusive_or_expression(p):
    """
    exclusive_or_expression : and_expression
    """
    # no ^ operator
    register_lineinfo(p, 1)
    p[0] = p[1]


def p_inclusive_or_expression(p):
    """
    inclusive_or_expression : exclusive_or_expression
    """
    # no | operator
    register_lineinfo(p, 1)
    p[0] = p[1]


def p_logical_and_expression(p):
    """
    logical_and_expression : inclusive_or_expression
        | logical_and_expression AND inclusive_or_expression
    """
    if len(p) == 2:
        register_lineinfo(p, 1)
        p[0] = p[1]
    elif len(p) == 4:
        register_lineinfo(p, 1)
        register_lineinfo(p, 3)
        opnode = Op(p[2])
        opnode.linespan = p.linespan(2)
        opnode.linespan = p.lexspan(2)
        p[0] = BinaryOp(op=opnode, arg1=p[1], arg2=p[3])
    else:
        raise Exception


def p_logical_or_expression(p):
    """
    logical_or_expression : logical_and_expression
        | logical_or_expression OR logical_and_expression
    """
    if len(p) == 2:
        register_lineinfo(p, 1)
        p[0] = p[1]
    elif len(p) == 4:
        register_lineinfo(p, 1)
        register_lineinfo(p, 3)
        opnode = Op(p[2])
        opnode.linespan = p.linespan(2)
        opnode.linespan = p.lexspan(2)
        p[0] = BinaryOp(op=p[2], arg1=p[1], arg2=p[3])
    else:
        raise Exception


def p_conditional_expression(p):
    """
    conditional_expression : logical_or_expression
    """
    # no ternary expression!
    register_lineinfo(p, 1)
    p[0] = p[1]


def p_assignment_expression(p):
    """
    assignment_expression : conditional_expression
        | unary_expression assignment_operator assignment_expression
    """
    if len(p) == 2:
        register_lineinfo(p, 1)
        p[0] = p[1]
    elif len(p) == 4:
        register_lineinfo(p, 1)
        register_lineinfo(p, 3)
        p[0] = Assignment(lvalue=p[1], rvalue=p[3])
    else:
        raise Exception


def p_assignment_operator(p):
    """
    assignment_operator : '='
    """
    # TODO: deprecated?
    p[0] = p[1]


def p_expression(p):
    """
    expression : assignment_expression
        | expression ',' assignment_expression
    """
    if len(p) == 2:
        register_lineinfo(p, 1)
        p[0] = Expression(expr_list=[p[1]])
    elif len(p) == 4:
        register_lineinfo(p, 1)
        register_lineinfo(p, 3)
        p[1].append(p[3])
        p[0] = p[1]
    else:
        raise Exception


def p_constant_expression(p):
    """
    constant_expression : conditional_expression
    """
    # TODO: with constraints?!
    register_lineinfo(p, 1)
    p[0] = p[1]


def p_declaration(p):
    """
    declaration : declaration_specifiers ';'
        | declaration_specifiers init_declarator_list ';'
    """
    if len(p) == 3:
        register_lineinfo(p, 1)
        p[0] = Declaration(declaration_spec=p[1])
    elif len(p) == 4:
        register_lineinfo(p, 1)
        register_lineinfo(p, 2)
        p[0] = Declaration(declaration_spec=p[1], init_dec_list=p[2])
    else:
        raise Exception


def p_declaration_specifiers(p):
    """
    declaration_specifiers : type_specifier declaration_specifiers
        | type_specifier
    """
    # no alignment specifiers (ALIGNAS), no function specifiers (INLINE), no type qualifiers (CONST, VOLATILE),
    # no storage class specifiers (REGISTER, THREAD_LOCAL)
    # declaration specifiers are not basically FLOAT INT or VOID
    if len(p) == 2:
        dec_spec_list = DeclarationSpecifiers()
        register_lineinfo(p, 1)
        dec_spec_list.append(p[1])
        p[0] = dec_spec_list
    elif len(p) == 3:
        register_lineinfo(p, 1)
        register_lineinfo(p, 2)
        p[2].append(p[1])
        p[0] = p[2]
    else:
        raise Exception


def p_type_specifier(p):
    """
    type_specifier : VOID
        | INT
        | FLOAT
    """
    p[0] = Type(value=p[1])
    register_lineinfo(p, 1, 0)


def p_pointer(p):
    """
    pointer : '*' pointer
        | '*'
    """
    if len(p) == 2:
        p[0] = Pointer()
        register_lineinfo(p, 1, 0)
    elif len(p) == 3:
        register_lineinfo(p, 2)
        p[2].append_pointer()
        p[0] = p[2]


def p_direct_declarator(p):
    """
    direct_declarator : identifier
        | '(' declarator ')'
        | direct_declarator '[' ']'
        | direct_declarator '[' assignment_expression ']'
        | direct_declarator '(' parameter_type_list ')'
        | direct_declarator '(' ')'
    """
    # function declaration with identifier list not supported!
    # refer: https://stackoverflow.com/questions/18202232/c-function-with-parameter-without-type-indicator-still-works

    # asterisk in array definition within function declaration [*] not supported
    # refer: https://stackoverflow.com/questions/17559631/what-are-those-strange-array-sizes-and-static-in-c99
    if len(p) == 2:
        register_lineinfo(p, 1)
        p[0] = Declarator(of=p[1])
    elif len(p) == 4:
        if p[1] == '(':
            register_lineinfo(p, 2)
            p[0] = p[2]
        elif p[2] == '[':
            register_lineinfo(p, 1)
            p[0] = ArrayDeclarator(of=p[1])
        elif p[2] == '(':
            register_lineinfo(p, 1)
            p[0] = FuncDeclarator(of=p[1])
        else:
            raise Exception
    elif len(p) == 5:
        if p[2] == '[':
            register_lineinfo(p, 1)
            register_lineinfo(p, 3)
            p[0] = ArrayDeclarator(of=p[1], assignment_expr=p[3])
        elif p[2] == '(':
            register_lineinfo(p, 1)
            register_lineinfo(p, 3)
            p[0] = FuncDeclarator(of=p[1], param_type_list=p[3])
        else:
            raise Exception
    else:
        raise Exception


def p_declarator(p):
    """
    declarator : pointer direct_declarator
        | direct_declarator
    """
    if len(p) == 2:
        register_lineinfo(p, 1)
        p[0] = p[1]
    elif len(p) == 3:
        assert isinstance(p[2], Declarator)
        register_lineinfo(p, 2)

        if p[2].pointer is None:
            p[2].pointer = Pointer()
        else:
            p[2].pointer.append_pointer()
        p[0] = p[2]
    else:
        raise Exception


def p_designator(p):
    """
    designator : '[' constant_expression ']'
    """
    register_lineinfo(p, 2)
    p[0] = p[2]


def p_designator_list(p):
    """
    designator_list : designator
        | designator_list designator
    """
    if len(p) == 2:
        register_lineinfo(p, 1)
        p[0] = Designators(first_designator=p[1])
    elif len(p) == 3:
        register_lineinfo(p, 1)
        register_lineinfo(p, 2)
        p[0] = p[1].append(p[2])
    else:
        raise Exception


def p_designation(p):
    """
    designation : designator_list '='
    """
    # delegate designator list
    register_lineinfo(p, 1)
    p[0] = p[1]


def p_initializer(p):
    """
    initializer : '{' initializer_list '}'
        | '{' initializer_list ',' '}'
        | assignment_expression
    """
    if len(p) == 2:
        register_lineinfo(p, 1)
        p[0] = p[1]
    elif len(p) == 4:
        register_lineinfo(p, 2)
        p[0] = p[2]
    elif len(p) == 5:
        register_lineinfo(p, 2)
        p[0] = p[2]
    else:
        raise Exception


def p_initializer_list(p):
    """
    initializer_list : designation initializer
        | initializer
        | initializer_list ',' designation initializer
        | initializer_list ',' initializer
    """
    if len(p) == 2:
        init_list = InitializerList()
        register_lineinfo(p, 1)
        init_list.append({'initializer': p[1], 'designation': None})
        p[0] = init_list
    elif len(p) == 3:
        init_list = InitializerList()
        register_lineinfo(p, 1)
        register_lineinfo(p, 2)
        init_list.append({'initializer': p[2], 'designation': p[1]})
        p[0] = init_list
    elif len(p) == 4:
        p[1].append({'initializer': p[3], 'designation': None})
        register_lineinfo(p, 1)
        register_lineinfo(p, 3)
        p[0] = p[1]
    elif len(p) == 5:
        register_lineinfo(p, 1)
        register_lineinfo(p, 3)
        register_lineinfo(p, 3)
        p[1].append({'initializer': p[4], 'designation': p[3]})
        p[0] = p[1]
    else:
        raise Exception


def p_init_declarator(p):
    """
    init_declarator : declarator '=' initializer
        | declarator
    """
    if len(p) == 2:
        register_lineinfo(p, 1)
        p[0] = p[1]
    elif len(p) == 4:
        register_lineinfo(p, 1)
        register_lineinfo(p, 3)
        p[0] = InitDeclarator(declarator=p[1], initializer=p[3])
    else:
        raise Exception


def p_init_declarator_list(p):
    """
    init_declarator_list : init_declarator
        | init_declarator_list ',' init_declarator
    """
    if len(p) == 2:
        register_lineinfo(p, 1)
        init_dec_list = InitDeclaratorList()
        init_dec_list.append(p[1])
        p[0] = init_dec_list
    elif len(p) == 4:
        register_lineinfo(p, 1)
        register_lineinfo(p, 3)
        p[1].append(p[3])
        p[0] = p[1]
    else:
        raise Exception


def p_parameter_declaration(p):
    """
    parameter_declaration : declaration_specifiers declarator
        | declaration_specifiers abstract_declarator
        | declaration_specifiers
    """
    # decl_specifiers + delarator : ex) 'int a[]' or 'int *a'. 'int[] a' is illegal.
    if len(p) == 2:
        register_lineinfo(p, 1)
        p[0] = ParameterDeclaration(dec_specs=p[1])
    elif len(p) == 3:
        register_lineinfo(p, 1)
        register_lineinfo(p, 2)
        p[0] = ParameterDeclaration(dec_specs=p[1], declarator=p[2])  # covers abstract declarator
    else:
        raise Exception


def p_direct_abstract_declarator(p):
    """
    direct_abstract_declarator : '(' abstract_declarator ')'
        | '[' ']'
        | '[' assignment_expression ']'
        | direct_abstract_declarator '[' ']'
        | direct_abstract_declarator '[' assignment_expression ']'
        | '(' ')'
        | '(' parameter_type_list ')'
        | direct_abstract_declarator '(' ')'
        | direct_abstract_declarator '(' parameter_type_list ')'
    """
    # abstract declarators are declarators without identifiers
    # it is used for casting, or as arguments of sizeof()
    # see : https://msdn.microsoft.com/en-us/library/b198y5xs.aspx
    # TODO: support?


def p_abstract_declarator(p):
    """
    abstract_declarator : pointer direct_abstract_declarator
        | pointer
        | direct_abstract_declarator
    """
    # TODO: support?


def p_specifier_qualifier_list(p):
    """
    specifier_qualifier_list : type_specifier specifier_qualifier_list
        | type_specifier
        | specifier_qualifier_list
    """
    # list of int float void
    if len(p) == 2:
        register_lineinfo(p, 1)
        if isinstance(p[1], list):
            spec_qual_list = SpecifierQualifierList()
            spec_qual_list.append(p[1])
            p[0] = spec_qual_list
        else:
            p[0] = p[1]
    elif len(p) == 3:
        register_lineinfo(p, 1)
        register_lineinfo(p, 2)
        p[2].append(p[1])
        p[0] = p[2]
    else:
        raise Exception


def p_parameter_type_list(p):
    """
    parameter_type_list : parameter_list
    """
    # same as parameter list
    register_lineinfo(p, 1)
    p[0] = p[1]


def p_parameter_list(p):
    """
    parameter_list : parameter_declaration
        | parameter_list ',' parameter_declaration
    """
    # [int a[], int count]
    if len(p) == 2:
        param_list = ParameterList()
        register_lineinfo(p, 1)
        param_list.append(p[1])
        p[0] = param_list
    elif len(p) == 4:
        register_lineinfo(p, 1)
        register_lineinfo(p, 3)
        p[1].append(p[3])
        p[0] = p[1]
    else:
        raise Exception


def p_statement(p):
    """
    statement : compound_statement
        | expression_statement
        | selection_statement
        | iteration_statement
        | jump_statement
    """
    # statements are those that end with ';'
    register_lineinfo(p, 1)
    p[0] = p[1]


def p_compound_statement(p):
    """
    compound_statement : '{' '}'
        | '{'  block_item_list '}'
    """
    if len(p) == 3:
        p[0] = CompoundStatement()
    elif len(p) == 4:
        compound_statement = CompoundStatement()
        register_lineinfo(p, 2)
        p[0] = p[2]  # block item list should be represented as CompundStatement
    else:
        raise Exception


def p_block_item_list(p):
    """
    block_item_list : block_item
        | block_item_list block_item
    """
    if len(p) == 2:
        compound_statement = CompoundStatement()
        register_lineinfo(p, 1)
        compound_statement.append(p[1])
        p[0] = compound_statement
    elif len(p) == 3:
        register_lineinfo(p, 1)
        register_lineinfo(p, 2)
        p[1].append(p[2])
        p[0] = p[1]
    else:
        raise Exception


def p_block_item(p):
    """
    block_item : declaration
        | statement
    """
    register_lineinfo(p, 1)
    p[0] = p[1]


def p_expression_statement(p):
    """
    expression_statement : ';'
        | expression ';'
    """
    if len(p) == 2:
        p[0] = ExpressionStatement()
    elif len(p) == 3:
        register_lineinfo(p, 1)
        p[0] = ExpressionStatement(expr=p[1])
    else:
        raise Exception


def p_selection_statement(p):
    """
    selection_statement : IF '(' expression ')' statement ELSE statement
        | IF '(' expression ')' statement
    """
    # if-else clauses
    if len(p) == 6:
        register_lineinfo(p, 3)
        register_lineinfo(p, 5)
        p[0] = SelectionStatement(if_cond=p[3], if_expr=p[5])
    elif len(p) == 8:
        register_lineinfo(p, 3)
        register_lineinfo(p, 5)
        register_lineinfo(p, 7)
        p[0] = SelectionStatement(if_cond=p[3], if_expr=p[5], else_expr=p[7])
    else:
        raise Exception


def p_iteration_statement(p):
    """
    iteration_statement : WHILE '(' expression ')' statement
        | FOR '(' expression_statement expression_statement ')' statement
        | FOR '(' expression_statement expression_statement expression ')' statement
        | FOR '(' declaration expression_statement ')' statement
        | FOR '(' declaration expression_statement expression ')' statement
    """
    if len(p) == 6:  # while loop
        register_lineinfo(p, 3)
        p[0] = IterationStatement(iter_type='while', exp1=p[3], body=statement)
    elif len(p) == 7:  # where one of for-conditions are omitted
        if isinstance(p[4], Statement):
            register_lineinfo(p, 3)
            register_lineinfo(p, 4)
            register_lineinfo(p, 6)
            p[0] = IterationStatement(iter_type='for', exp2=p[3], exp3=p[4], body=p[6])
        else:
            register_lineinfo(p, 3)
            register_lineinfo(p, 4)
            register_lineinfo(p, 6)
            p[0] = IterationStatement(iter_type='for', exp1=p[3], exp2=p[4], body=p[6])
    elif len(p) == 8:
        register_lineinfo(p, 3)
        register_lineinfo(p, 4)
        register_lineinfo(p, 5)
        register_lineinfo(p, 7)
        p[0] = IterationStatement(iter_type='for', exp1=p[3], exp2=p[4], exp3=p[5], body=p[7])
    else:
        raise Exception


def p_jump_statement(p):
    """
    jump_statement : RETURN ';'
        | RETURN expression ';'
    """
    if len(p) == 3:
        p[0] = JumpStatement()
    elif len(p) == 4:
        register_lineinfo(p, 2)
        p[0] = JumpStatement(what=p[2])
    else:
        raise Exception


def p_translation_unit(p):
    """
    translation_unit : external_declaration
        | translation_unit external_declaration
    """
    # starting point
    if len(p) == 2:
        translation_unit = TranslationUnit()
        translation_unit.append(p[1])
        register_lineinfo(p, 1)
        p[0] = translation_unit
    elif len(p) == 3:
        register_lineinfo(p, 1)
        register_lineinfo(p, 2)
        p[1].append(p[2])
        p[0] = p[1]
    else:
        raise Exception


def p_external_declaration(p):
    """
    external_declaration : function_definition
        | declaration
    """
    register_lineinfo(p, 1)
    p[0] = p[1]


def p_function_definition(p):
    """
    function_definition : declaration_specifiers declarator compound_statement
    """
    # declaration-list style function definition not supported!
    # see: https://stackoverflow.com/questions/1585390/c-function-syntax-parameter-types-declared-after-parameter-list
    register_lineinfo(p, 1)
    register_lineinfo(p, 2)
    register_lineinfo(p, 3)
    p[0] = FunDef(return_type=p[1], name_params=p[2], body=p[3])
    parser.functions.append(p[0])
    if p[0].name() == 'main':  # detect main function
        parser.main_func = p[0]


# error rule
def p_error(t):
    print('Syntax Error at token {}!'.format(t))
    parser.errorlines.append(t.lineno)

# create a parser
parser = yacc.yacc(debug=True)
parser.errorlines = []
parser.main_func = None  # starting main function
parser.functions = []
