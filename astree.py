from symbol_table import TypeVal, Symbol


class AstNode:
    """
    Basic class for a node of abstract syntax tree.
    """
    def children(self):
        return list()

    def __lt__(self, other):
        if self.startline() < other.startline():
            return True
        elif self.startline() > other.startline():
            return False
        else:
            if self.startcol() < other.startcol():
                return True
            else:
                return False

    def startcol(self):
        return self.lexspan[0]

    def endcol(self):
        return self.lexspan[1]

    def startline(self):
        return self.linespan[0]

    def endline(self):
        return self.linespan[1]

    def execute(self, *args, **kwargs):
        raise NotImplemented

    def evaluate(self, *args, **kwargs):
        raise NotImplemented

    def show(self, depth=0):
        print('{}{}'.format('----' * depth, self))
        for child_node in self.children():
            child_node.show(depth + 1)

    def __str__(self):
        return '{}'.format(self.__class__.__name__)


class Id(AstNode):
    """
    Variable names or function names.
    ex) add or is_id
    """
    def __init__(self, id_name):
        self.id_name = id_name

    def name(self):
        return self.id_name

    def __str__(self):
        return '{}(name={})'.format(super().__str__(), self.id_name)


class Constant(AstNode):
    """
    ex) 2 or 3.2
    """
    def __init__(self, value):
        self.value = value
        self.const_type = 'int' if isinstance(value, int) else 'float'

    def __str__(self):
        return '{}(val={}, type={})'.format(
                super().__str__(), self.value, self.const_type)


class Op(AstNode):
    """
    An operator.
    """
    def __init__(self, op):
        self.op = op

    def __str__(self):
        return '{}(op="{}")'.format(super().__str__(), self.op)


class String(AstNode):
    """
    ex) "string"
    """
    def __init__(self, string):
        self.string = string

    def __str__(self):
        return '{}(string={})'.format(super().__str__(), self.string)


class Type(AstNode):
    """
    Represents a C type specifier.
    ex) int, float, void
    """
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return '{}(value={})'.format(super().__str__(), self.value)


class UnaryExpr(AstNode):
    """
    Unary operators - '++' and '--'.
    is_postfix denotes whether it is used as postfix or prefix.
    ex) i++, ++i
    """
    def __init__(self, op_name, operand, is_postfix: bool):
        self.op_name = op_name
        self.operand = operand
        self.is_postfix = is_postfix

    def children(self):
        children_nodes = []
        if self.operand is not None and isinstance(self.operand, AstNode):
            children_nodes.append(self.operand)
        return children_nodes

    def __str__(self):
        return '{}(op="{}", postfix={})'.format(super().__str__(), self.op_name, self.is_postfix)


class FunctionCall(AstNode):
    """
    Calling a function.
    """
    def __init__(self, func_name, argument_list):
        self.func_name = func_name
        self.argument_list = argument_list

    def children(self):
        ch_nodes = []
        if self.func_name is not None:
            assert isinstance(self.func_name, AstNode)
            ch_nodes.append(self.func_name)
        if self.argument_list is not None:
            assert isinstance(self.argument_list, AstNode)
            ch_nodes.append(self.argument_list)
        return ch_nodes

    def execute(self, scope, currline, eval_stack):
        # defer the execution until register is done - register first
        exec_done = False
        if currline == self.startline():
            eval_stack.append(scope.getsymbol(self.func_name).astnode)  # FunDef
        elif currline == self.endline():
            exec_done = True
        else:
            args = self.argument_list.evaluate()
            # TODO: check if arguments match the parameter types
            # TODO: create a new scope, register arguments, and start executing body
            eval_stack.append(scope.getsymbol(self.func_name).value.body)  # body ast
        return exec_done


class ArgList(AstNode, list):
    """
    List of arguments passed into function call.
    ex) add(1, 2) where arglist = [1, 2]
    """
    def __init__(self, argument_list):
        self.argument_list = super().__init__(argument_list)

    def children(self):
        children_nodes = []
        for arg in self:
            if arg is not None and isinstance(arg, AstNode):
                children_nodes.append(arg)
            else:
                raise Exception
        return children_nodes


class ArrayReference(AstNode):
    def __init__(self, name, idx):
        self.name = name
        self.idx = idx

    def children(self):
        children_nodes = []
        if self.name is not None and isinstance(self.name, AstNode):
            children_nodes.append(self.name)

        if self.idx is not None and isinstance(self.idx, AstNode):
            children_nodes.append(self.name)
        return children_nodes


class TypeCast(AstNode):
    """
    Expression for type casting.
    ex) (float) 3
    """
    def __init__(self, type_name, cast_expr):
        self.type_name = type_name
        self.cast_expr = cast_expr

    def children(self):
        children_nodes = []
        if self.type_name is not None and isinstance(self.type_name, AstNode):
            children_nodes.append(self.type_name)
        if self.cast_expr is not None and isinstance(self.cast_expr, AstNode):
            children_nodes.append(self.cast_expr)
        return children_nodes


class BinaryOp(AstNode):
    """
    Binary operation.
    """
    def __init__(self, op, arg1, arg2):
        self.op = op
        self.arg1 = arg1
        self.arg2 = arg2

    def children(self):
        children_nodes = []
        if self.op is not None and isinstance(self.op, AstNode):
            children_nodes.append(self.op)
        if self.arg1 is not None and isinstance(self.arg1, AstNode):
            children_nodes.append(self.arg1)
        if self.arg2 is not None and isinstance(self.arg2, AstNode):
            children_nodes.append(self.arg2)
        return children_nodes


class Assignment(AstNode):
    """
    Assignment expression.
    ex) a = 1
    """
    def __init__(self, lvalue, rvalue):
        self.lvalue = lvalue
        self.rvalue = rvalue

    def children(self):
        ch_nodes = []
        if self.lvalue is not None:
            assert isinstance(self.lvalue, AstNode)
            ch_nodes.append(self.lvalue)
        if self.rvalue is not None:
            assert isinstance(self.rvalue, AstNode)
            ch_nodes.append(self.rvalue)
        return ch_nodes


class Expression(AstNode, list):
    """
    Represents an expression - can be either assignment or list of assignments.
    ex) a = 1
    ex2) a = 1, b = 3, a && b
    """
    def __init__(self, expr_list):
        super().__init__(expr_list)

    def children(self):
        children_nodes = []
        for child in self:
            if child is not None and isinstance(child, AstNode):
                children_nodes.append(child)
        return children_nodes


class Declaration(AstNode):
    """
    Declaration of any types.
    It consists of specifiers and initial declaration list.
    ex) int c, a, x;
    """
    def __init__(self, declaration_spec, init_dec_list):
        self.declaration_spec = declaration_spec
        self.init_dec_list = init_dec_list

    def children(self):
        ch_nodes = []
        if self.declaration_spec is not None and isinstance(self.declaration_spec, AstNode):
            ch_nodes.append(self.declaration_spec)
        if self.init_dec_list is not None and isinstance(self.init_dec_list, AstNode):
            ch_nodes.append(self.init_dec_list)
        return ch_nodes


class DeclarationSpecifiers(AstNode, list):
    """
    List of type specifiers.
    """
    def __init__(self):
        super().__init__()

    def evaluate(self):
        eval_list = []
        for child in self.children():
            eval_list.append(child.value)  # type name
        return eval_list

    def children(self):
        children_nodes = []
        for child in self:
            if child is not None and isinstance(child, AstNode):
                children_nodes.append(child)
        return children_nodes


class Pointer(AstNode):
    """
    The pointer notation ('*').
    """
    def __init__(self):
        self.order = 1

    def append_pointer(self):
        self.order += 1

    def __str__(self):
        return '{}(order:{}, {})'.format(
                super().__str__(), self.order, '*' * self.order)


class Declarator(AstNode):
    """
    Represents direct declarator and declarator (direct declarator with pointers).
    """
    def __init__(self, of, pointer=None):
        self.of = of  # declarator of ...
        self.pointer = pointer

    def name(self):
        return self.of.name()  # ID instance or Declarator

    def evaluate(self):
        return (self.name(), self.pointer.order if self.pointer is not None else 0)

    def children(self):
        ch_nodes = []
        ch_nodes.append(self.of)
        if self.pointer is not None and isinstance(self.pointer, AstNode):
            ch_nodes.append(self.pointer)
        return ch_nodes


class ArrayDeclarator(Declarator):
    """
    Array delcarator.
    ex) c[4], where c = Declarator and 4 = AssignmentExpression
    """
    def __init__(self, of, pointer=None, assignment_expr=None):
        super().__init__(of, pointer)
        self.assignment_expr = assignment_expr

    def children(self):
        ch_nodes = super().children()
        if self.assignment_expr is not None:
            assert isinstance(self.assignment_expr, AstNode)
            ch_nodes.append(self.assignment_expr)
        return ch_nodes


class FuncDeclarator(Declarator):
    """
    Declarator of function (it's name) such as 'avg' or 'main'.
    """
    def __init__(self, of, pointer=None, param_type_list=None):
        super().__init__(of, pointer)
        self.param_type_list = param_type_list

    def evaluate(self):
        funcname = self.name()
        num_ptrs = self.pointer.order if self.pointer is not None else 0
        param_list = self.param_type_list.evaluate()  # ParameterList instance
        return num_ptrs, funcname, param_list

    def children(self):
        ch_nodes = super().children()
        if self.param_type_list is not None and isinstance(self.param_type_list, AstNode):
            ch_nodes.append(self.param_type_list)
        return ch_nodes


class InitDeclarator(AstNode):
    """
    Declaration that are initialized.
    ex) 'sum = 0' translates into Declarator(sum) + Initializer(0)
    """
    def __init__(self, declarator: Declarator, initializer):
        self.declarator = declarator
        self.initializer = initializer

    def children(self):
        ch_nodes = []
        if self.declarator is not None and isinstance(self.declarator, AstNode):
            ch_nodes.append(self.declarator)
        if self.initializer is not None and isinstance(self.initializer, AstNode):
            ch_nodes.append(self.initializer)

        return ch_nodes

class InitDeclaratorList(AstNode, list):
    """
    List of initialized declarators.
    """
    def __init__(self):
        super().__init__()

    def children(self):
        children_nodes = []
        for child in self:
            if child is not None and isinstance(child, AstNode):
                children_nodes.append(child)
        return children_nodes


class Designators(AstNode, list):
    def __init__(self, first_designator):
        super().__init__()
        self.append(designator)

    def children(self):
        children_nodes = []
        for child in self:
            if child is not None and isinstance(child, AstNode):
                children_nodes.append(child)
        return children_nodes


class InitializerList(AstNode, list):
    def __init__(self, first_initializer):
        super().__init__()

    def children(self):
        children_nodes = []
        for child in self:
            if child is not None and isinstance(child, AstNode):
                children_nodes.append(child)
        return children_nodes


class ParameterDeclaration(AstNode):
    """
    Parameter declaration like those in function declaration.
    Dec_specs are delcaration specifiers, such as types of declarator.
    The declarator is the name of the parameter.

    ex) 'int count' translates to DeclarationSpecifiers(int) + Declarator(count)
    """
    def __init__(self, dec_specs, declarator=None):
        self.dec_specs = dec_specs
        self.declarator = declarator

    def evaluate(self):
        return (self.dec_specs.evaluate(), self.declarator.evaluate())

    def children(self):
        ch_nodes = []
        if self.dec_specs is not None and isinstance(self.dec_specs, AstNode):
            ch_nodes.append(self.dec_specs)
        if self.declarator is not None and isinstance(self.declarator, AstNode):
            ch_nodes.append(self.declarator)
        return ch_nodes


class SpecifierQualifierList(AstNode, list):
    def __init__(self):
        super().__init__()

    def children(self):
        children_nodes = []
        for child in self:
            if child is not None and isinstance(child, AstNode):
                children_nodes.append(child)
        return children_nodes


class ParameterList(AstNode, list):
    """
    List of parameters declarations.
    """
    def __init__(self):
        super().__init__()

    def evaluate(self):
        param_list = []
        for param_dec in self.children():
            param_list.append(param_dec.evaluate())
        return param_list

    def children(self):
        children_nodes = []
        for child in self:
            if child is not None and isinstance(child, AstNode):
                children_nodes.append(child)
        return children_nodes


class CompoundStatement(AstNode, list):
    # list of statements enclosed by braces, such as function bodies.
    def __init__(self):
        super().__init__()

    def children(self):
        children_nodes = []
        for child in self:
            if child is not None and isinstance(child, AstNode):
                children_nodes.append(child)
        return children_nodes


class Statement(AstNode):
    def __init__(self):
        pass

    def evaluate(self):
        pass


class SelectionStatement(Statement):
    """
    If-else statements.
    """
    def __init__(self, if_cond, if_expr, else_expr=None):
        super().__init__()
        self.if_cond = if_cond
        self.if_expr = if_expr
        self.else_expr = else_expr

    def evaluate(self):
        # TODO
        pass

    def children(self):
        ch_nodes = []
        if self.if_cond is not None:
            assert isinstance(self.if_cond, AstNode)
            ch_nodes.append(self.if_cond)
        if self.if_expr is not None:
            assert isinstance(self.if_expr, AstNode)
            ch_nodes.append(self.if_expr)
        if self.if_cond is not None:
            assert isinstance(self.if_cond, AstNode)
            ch_nodes.append(self.if_cond)
        return ch_nodes


class ExpressionStatement(Statement):
    """
    Any expressions that ends with ';'.
    """
    def __init__(self, expr=None):
        self.expr = expr

    def children(self):
        if self.expr is not None:
            assert isinstance(self.expr, AstNode)
        return [self.expr]


class IterationStatement(Statement):
    """
    For- or while-loops.
    """
    def __init__(self, iter_type, exp1, exp2, exp3, body):
        self.iter_type = iter_type  # 'for' or 'while'
        self.exp1 = exp1  # 1st part of for-condition or while-condition
        self.exp2 = exp2  # 2nd part of for-condition
        self.exp3 = exp3  # 3rd part of for-condition
        self.body = body

    def children(self):
        ch_nodes = []
        if self.exp1 is not None:
            assert isinstance(self.exp1, AstNode)
            ch_nodes.append(self.exp1)
        if self.exp2 is not None:
            assert isinstance(self.exp2, AstNode)
            ch_nodes.append(self.exp2)
        if self.exp3 is not None:
            assert isinstance(self.exp3, AstNode)
            ch_nodes.append(self.exp3)
        if self.body is not None:
            assert isinstance(self.body, AstNode)
            ch_nodes.append(self.body)
        return ch_nodes


    def __str__(self):
        return '{}(type={})'.format(super().__str__(), self.iter_type)


class JumpStatement(Statement):
    """
    Return statements.
    """
    def __init__(self, what=None):
        self.what = what

    def children(self):
        ch_nodes = []
        if self.what is not None and isinstance(self.what, AstNode):
            ch_nodes.append(self.what)
        return ch_nodes


class TranslationUnit(AstNode, list):
    """
    Starting point for C grammar - contains function definitions and declarations.
    """
    def __init__(self):
        super().__init__()

    def children(self):
        children_nodes = []
        for child in self:
            if child is not None and isinstance(child, AstNode):
                children_nodes.append(child)
        return children_nodes


class FunDef(AstNode):
    """
    Function definition.
    """
    def __init__(self, return_type, name_params, body):
        self.return_type = return_type
        self.name_params = name_params  # function declarator = declarator(function name) + parameterlist(params)
        self.body = body  # compund statement

    def name(self):
        """
        Retrieve the name of the function.
        """
        assert isinstance(self.name_params, FuncDeclarator)
        return self.name_params.name()

    def children(self):
        children_nodes = []
        if self.return_type is not None and isinstance(self.return_type, AstNode):
            children_nodes.append(self.return_type)
        if self.name_params is not None and isinstance(self.name_params, AstNode):
            children_nodes.append(self.name_params)
        if self.body is not None and isinstance(self.body, AstNode):
            children_nodes.append(self.body)
        return children_nodes

    def execute(self, scope, currline, eval_stack):
        """
        Execute a function definition - only register the function (return type, name, etc).
        """
        exec_done = False
        if currline == self.body.startline():  # keep the execution until the start of body
            rtypes = self.return_type.evaluate()  # list of type specifiers
            rtype_pntr, funname, params = self.name_params.evaluate()  # FuncDeclarator

            # register the symbol in the scope if it does not exist
            scope.add_symbol(
                    funname, Symbol(funname, Type('function'), self))

            # create definition information for function
            funsymbol = scope.getsymbol(funname)
            typeval = TypeVal(rtypes, rtype_ptr)  # define a type
            funsymbol.value.rtype = typeval
            funsymbol.value.params = params
            funsymbol.value.body = self.body  # ast node - not executed yet - only registered
        elif currline == self.body.endline():
            exec_done = True
        return exec_done
