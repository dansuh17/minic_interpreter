import ply.lex as lex

# token names
tokens = [
        'FLOATING_POINT_NUM',
        'INTEGER_NUM',
        'ID',
        'STRING_LITERAL',
        'EQUALS',
        'NEQUALS',
        'GEQ',  # greater than or equal to
        'LEQ',  # less than or equal to
        'AND',
        'OR',
        'PPLUS',
        'MMINUS',
]

# define reserved words for C
reserved = {
        'if': 'IF',
        'then': 'THEN',
        'else': 'ELSE',
        'while': 'WHILE',
        'for': 'FOR',
        'return': 'RETURN',
        'break': 'BREAK',
        'continue': 'CONTINUE',
        'int': 'INT',
        'float': 'FLOAT',
}

# define language literals
literals = ['=', '(', ')', '+', '*', '-',
        '/', ';', '{', '}', '[', ']', ':', '>', '<', ',', '~', '!']

tokens = tokens + list(reserved.values())

# regular expressions for simple tokens
t_STRING_LITERAL = r'\".*\"'  # TODO: ??
t_EQUALS = r'=='
t_NEQUALS = r'\!='
t_GEQ = r'>='
t_LEQ = r'<='
t_AND = r'&&'
t_OR = r'\|\|'
t_PPLUS = r'\+\+'
t_MMINUS = r'--'


def t_ID(t):
    r'[a-zA-Z_][a-zA-Z_0-9]*'
    t.type = reserved.get(t.value, 'ID')  # check for reserved words
    return t

def t_INTEGER_NUM(t):
    r'\d+'
    t.value = int(t.value)
    return t

def t_FLOATING_POINT_NUM(t):
    r'\d*\.\d+'
    t.value = float(t.value)
    return t

# rule for tracking line numbers
def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

# handle error
def t_error(t):
    print('illegal character {}'.format(t.value[0]))

# handle EOF
def t_eof(t):
    more = input('Get more input?')
    if more:
        self.lexer.input(more)
        return self.lexer.token()
    return None


# string containing ignored characters (spaces & tabs)
t_ignore = '\t '

lexer = lex.lex()

# tokenize
data = '3 + 4 ++ 9 == 100 abc19 .1'  # TEST
data = ''
with open('test.c', 'r') as f:
    for lin in f.readlines():
        data += lin

print(data)
lexer.input(data)
for tok in lexer:
    print(tok)

