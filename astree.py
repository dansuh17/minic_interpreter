class AstNode:
    def children(self):
        return list()

    def evaluate(self):
        pass  # TODO

    def pre_order_traverse(self):
        pass


class Id(AstNode):
    """
    Variable names or function names.
    ex) add or is_id
    """
    def __init__(self, name):
        self.name = name


class Constant(AstNode):
    """
    ex) 2 or 3.2
    """
    def __init__(self, value):
        self.value = value
        self.const_type = 'int' if isinstance(value, int) else 'float'


class String(AstNode):
    """
    ex) "string"
    """
    def __init__(self, string):
        self.string = string


class UnaryExpr(AstNode):
    """
    Unary operators - '++' and '--'.
    is_postfix denotes whether it is used as postfix or prefix.
    ex) i++, ++i
    """
    def __init__(self, op_name, operand, is_postfix: bool):
        self.op_name = op_name
        self.operand = operand
        slef.is_postfix = is_postfix

    def children(self):
        children_nodes = []
        if self.operand is not None and isinstance(self.operand, AstNode):
            children_nodes.append(self.operand)
        return children_nodes


class FunctionCall(AstNode):
    def __init__(self, func_name, argument_list):
        self.func_name = func_name
        self.argument_list = argument_list


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


class Assignment(AstNode):
    """
    Assignment expression.
    ex) a = 1
    """
    def __init__(self, lvalue, rvalue):
        self.lvalue = lvalue
        self.rvalue = rvalue


class Expression(AstNode, list):
    """
    Represents an expression - can be either assignment or list of assignments.
    ex) a = 1
    ex2) a = 1, b = 3, a && b
    """
    def __init__(self, expr_list):
        super().__init__(expr_list)


class Declaration(AstNode):
    """
    Declaration of any types.
    It consists of specifiers and initial declaration list.
    ex) int c, a, x;
    """
    def __init__(self, declaration_spec, init_dec_list=[]):
        self.declaration_spec = declaration_spec
        self.init_dec_list = init_dec_list


class TypeSpecifiers(AstNode, list):
    def __init__(self, type_spec_list):
        super().__init__(type_spec_list)


class Pointer(AstNode):
    def __init__(self):
        self.order = 1

    def append_pointer(self):
        self.order += 1


class Declarator(AstNode):
    def __init__(self, of, pointer=None):
        self.of = of  # declarator of ...
        self.pointer = pointer


class ArrayDeclarator(AstNode, Declarator):
    def __init__(self, of, pointer=None, assignment_expr=None):
        super().__init__(of, pointer)
        self.assignment_expr = assignment_expr


class FuncDeclarator(AstNode, Declarator):
    def __init__(self, of, pointer=None, param_type_list=None):
        super().__init__(of, pointer)
        self.param_type_list = param_type_list
        self.id_list = id_list
