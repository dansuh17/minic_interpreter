from symbol_table import TypeVal, Symbol, Value, FunctionVal, Scope
from environment import *


class AstNode:
    """
    Basic class for a node of abstract syntax tree.
    """
    def __init__(self):
        self.exec_visited = False

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

    def add_child_executes(self, exec_stack):
        """
        Add children ast nodes into execution stack.
        """
        for child in sorted(self.children(), reverse=True):
            exec_stack.append(child)

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
        super().__init__()
        self.id_name = id_name

    def name(self):
        return self.id_name

    def execute(self, env):
        env.push_val(Symbol(name=self.id_name, astnode=self))
        env.pop_exec()  # pop self
        return True, env

    def __str__(self):
        return '{}(name={})'.format(super().__str__(), self.id_name)


class Constant(AstNode):
    """
    ex) 2 or 3.2
    """
    def __init__(self, value):
        super().__init__()
        self.value = value
        self.const_type = 'int' if isinstance(value, int) else 'float'

    def execute(self, env):
        env.push_val(Value(TypeVal(self.const_type), self.value))
        env.pop_exec()
        return True, env

    def __str__(self):
        return '{}(val={}, type={})'.format(
                super().__str__(), self.value, self.const_type)


class Op(AstNode):
    """
    An operator.
    """
    def __init__(self, op):
        super().__init__()
        self.op = op

    def execute(self, env):
        env.push_val(Value(TypeVal('op'), self.op))
        env.pop_exec()
        return True, env

    def __str__(self):
        return '{}(op="{}")'.format(super().__str__(), self.op)


class String(AstNode):
    """
    ex) "string"
    """
    def __init__(self, string):
        super().__init__()
        self.string = string

    def execute(self, env):
        env.push_val(Value(TypeVal('string'), self.string))
        env.pop_exec()
        return True, env

    def __str__(self):
        return '{}(string={})'.format(super().__str__(), self.string)


class Type(AstNode):
    """
    Represents a C type specifier.
    ex) int, float, void
    """
    def __init__(self, value):
        super().__init__()
        self.value = value

    def execute(self, env):
        env.push_val(TypeVal(self.value))
        env.pop_exec()
        return True, env

    def __str__(self):
        return '{}(value={})'.format(super().__str__(), self.value)


class UnaryExpr(AstNode):
    """
    Unary operators - '++' and '--'.
    is_postfix denotes whether it is used as postfix or prefix.
    ex) i++, ++i
    """
    def __init__(self, op_name, operand, is_postfix: bool):
        super().__init__()
        self.op_name = op_name
        self.operand = operand
        self.is_postfix = is_postfix

    def children(self):
        children_nodes = []
        if self.operand is not None and isinstance(self.operand, AstNode):
            children_nodes.append(self.operand)
        return children_nodes

    def execute(self, env):
        exec_done = False
        if not self.exec_visited:
            env.push_exec(self.operand)
        else:
            operand = env.pop_val()
            operand_val = env.scope.getvalue(operand.name)
            inc = 1 if self.op_name == '++' else -1
            if self.is_postfix:
                # postpone update
                env.book_update({
                    'exec_target': env.scope.setvalue,
                    'arg': (operand.name, operand + inc, env.currline),
                })
            else:
                env.scope.set_value(operand.name, operand + inc, env.currline)
            exec_done = True
        return exec_done, env

    def __str__(self):
        return '{}(op="{}", postfix={})'.format(super().__str__(), self.op_name, self.is_postfix)


class FunctionCall(AstNode):
    """
    Calling a function.
    """
    def __init__(self, func_name, argument_list):
        super().__init__()
        self.func_name = func_name  # string literal
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

    def execute(self, env):
        exec_done = False

        funcname = self.func_name.string
        if not self.exec_visited:
            if len(self.argument_list) != 0:
                env.push_exec(self.argument_list)
            # defer the execution until register is done - register first
            env.push_exec(env.scope.getsymbol(funcname).astnode)
            self.exec_visited = True
        else:
            if env.currline == self.endline():  # call has been made!
                if not env.scope.get_return_val():
                    # function has not been executed and returned
                    if env.scope.getvalue(funcname) is None:
                        raise CRuntimeErr('No function named {} defined.'.format(funcname), env)

                    funcval = env.scope.getvalue(funcname)
                    args = []
                    if len(self.argument_list) > 0:
                        args = env.pop_val()  # list of (type, symbol string)
                    # args = self.argument_list.evaluate()
                    params = funcval.params
                    if len(args) != len(params):
                        if not (len(params) == 1 and params[0][0].typename == 'void'):
                            # exception for void case
                            raise CRuntimeErr('Argument number mismatch', env)

                    func_scope = Scope({})  # set arguments
                    func_scope.parent_scope = env.scope.root_scope()  # root scope is the parent
                    func_scope.return_lineno = self.startline()
                    func_scope.return_scope = env.scope

                    # type check the arguments with prameter declarations
                    for arg, ptype in zip(args, params):
                        if not arg.vtype.castable(ptype[0]):
                            raise CRuntimeError('Argument type mismatch', env)

                        # bind argument values to their symbols
                        argname = ptype[1].val
                        func_scope.add_symbol(
                                symbol_name=argname,
                                symbol_info=Symbol(argname, None))
                        arg.cast(ptype[0])
                        func_scope.set_value(argname, arg, env.currline)

                    # start executing body
                    body_ast = env.scope.getsymbol(funcname).value.body
                    env.push_exec(body_ast)
                    env.scope = func_scope
                    env.currline = body_ast.startline()
                    env.call_stack.append(funcval)
                else:
                    # execution has been done and returned
                    exec_done = True
                    retval = env.scope.get_return_val()
                    env.scope = env.scope.return_scope  # reset to new scope
                    env.call_stack.pop()
                    env.push_val(retval)
        return exec_done, env


class ArgList(AstNode, list):
    """
    List of arguments passed into function call.
    ex) add(1, 2) where arglist = [1, 2]
    """
    def __init__(self, argument_list):
        super().__init__()
        # argument list is a list of assignment expression
        list.__init__(self, argument_list)

    def execute(self, env):
        """
        Evaluates a list of assignment expressions.
        """
        exec_done = False
        if not self.exec_visited:
            self.add_child_executes(env.exec_stack)
            self.exec_visited = True
        else:
            if env.currline >= self.endline():
                arglist = []
                for _ in range(len(self)):
                    arglist.append(env.pop_val())

                env.push_val(arglist)
                exec_done = True
                self.exec_visited = False
                env.pop_exec()
        return exec_done, env

    def children(self):
        children_nodes = []
        for arg in self:
            if arg is not None and isinstance(arg, AstNode):
                children_nodes.append(arg)
            else:
                raise Exception
        return children_nodes


class ArrayReference(AstNode):
    """
    Expression for array reference.
    ex) a[0]
    """
    def __init__(self, name, idx):
        super().__init__()
        self.name = name
        self.idx = idx

    def execution(self, env):
        if env.currline < self.startline():
            #TODO: make this a decorator
            # the executing line has not reached this statement yet
            return False, env

        exec_done = False
        if not self.exec_visited:
            self.add_child_executes()
            self.exec_visited = True
        else:
            if env.currline >= self.endline():
                idx_val = env.pop_val()
                name_val = env.pop_val()
            arr_name = name_val.val

            # check if it is an array
            if name_val.vtype.array == 0:
                raise CRuntimeErr('Name {} not array!'.format(arr_name), env)

            arr_symbol = env.scope.getsymbol(arr_name)
            idx = idx_val.val
            value_array = arr_sumbol.value.val
            if len(value_array) <= idx + 1:
                raise CRuntimeErr('Index error - array length {}, idx {}'.format(len(value_array), idx), env)

            array_access_val = value_array[idx]  # retrieve the actual value

            env.push_val(array_access_val)
            env.pop_val()
            exec_done = True
        return exec_done, env

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
        super().__init__()
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
        super().__init__()
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
        super().__init__()
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
        super().__init__()
        list.__init__(self, expr_list)

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
        super().__init__()
        self.declaration_spec = declaration_spec
        self.init_dec_list = init_dec_list

    def children(self):
        ch_nodes = []
        if self.declaration_spec is not None and isinstance(self.declaration_spec, AstNode):
            ch_nodes.append(self.declaration_spec)
        if self.init_dec_list is not None and isinstance(self.init_dec_list, AstNode):
            ch_nodes.append(self.init_dec_list)
        return ch_nodes

    def execute(self, env):
        if env.currline < self.startline() or env.currline > self.endline():
            print(self.linespan)
            # execution line number not reached yet
            return False, env

        exec_done = False
        if not self.exec_visited:
            self.add_child_executes(env.exec_stack)
            self.exec_visited = True
        else:
            if env.currline >= self.endline():
                dec_spec_val = env.pop_val()
                init_dec_vals = env.pop_val()

                env.push_val((dec_spec_val, init_dec_vals))
                env.pop_exec()
                exec_done = True
                self.exec_visited = False
        return exec_done, env


class DeclarationSpecifiers(AstNode, list):
    """
    List of type specifiers.
    """
    def __init__(self):
        super().__init__()

    def execute(self, env):
        if env.currline < self.startline() or env.currline > self.endline():
            # execution line number not reached yet
            return False, env

        exec_done = False
        if not self.exec_visited:
            self.add_child_executes(env.exec_stack)
            self.exec_visited = True
        else:
            dec_spec = env.pop_val()
            env.push_val(dec_spec)
            env.pop_exec()
            exec_done = True
            self.exec_visited = False
        return exec_done, env

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
        super().__init__()
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
        super().__init__()
        self.of = of  # declarator of ...
        self.pointer = pointer

    def name(self):
        return self.of.name()  # ID instance or Declarator

    def execute(self, env):
        if env.currline < self.startline() or env.currline > self.endline():
            # execution line number not reached yet
            return False, env

        exec_done = False
        if not self.exec_visited:
            self.add_child_executes(env.exec_stack)
            self.exec_visited = True
        else:
            if env.currline >= self.endline():
                pointer_val = None
                if self.pointer is not None:
                    pointer_val = env.pop_val()
                of_val = env.pop_val()

                env.push_val((of_val, pointer_val))
                env.pop_exec()
                exec_done = True
                self.exec_visited = False
        return exec_done, env

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

    def execute(self, env):
        if env.currline < self.startline() or env.currline > self.endline():
            # execution line number not reached yet
            return False, env

        exec_done = False
        if not self.exec_visited:
            self.add_child_executes(env.exec_stack)
            self.exec_visited = True
        else:
            if env.currline >= self.endline():
                param_list = env.pop_val()
                funname_val = env.pop_val()  # returned from declarator

                env.push_val(funname_val)
                env.push_val(param_list)
                env.pop_exec()
                exec_done = True
                self.exec_visited = False
        return exec_done, env

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
        super().__init__()
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
        super().__init__()
        self.dec_specs = dec_specs
        self.declarator = declarator

    def execute(self, env):
        if env.currline < self.startline() or env.currline > self.endline():
            # execution line number not reached yet
            return False, env

        exec_done = False
        if not self.exec_visited:
            self.add_child_executes(env.exec_stack)
            self.exec_visited = True
        else:
            if env.currline >= self.endline():
                dec_specs = env.pop_val()  # list of TypeVal
                declarator = None
                if self.declarator is not None:
                    declarator = env.pop_val()

                env.push_val((dec_specs, declarator))
                env.pop_exec()
                exec_done = True
                self.exec_visited = False
        return exec_done, env


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

    def execute(self, env):
        if env.currline < self.startline() or env.currline > self.endline():
            # execution line number not reached yet
            return False, env

        exec_done = False
        if not self.exec_visited:
            self.add_child_executes(env.exec_stack)
            self.exec_visited = True
        else:
            if env.currline >= self.endline():
                param_list = []
                for _ in range(len(self)):
                    param_list.append(env.pop_val())
                param_list.reverse()

                env.push_val(param_list)
                env.pop_exec()
                exec_done = True
                self.exec_visited = False
        return exec_done, env

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

    def execute(self, env):
        if env.currline < self.startline() or env.currline > self.endline():
            # execution line number not reached yet
            return False, env

        # compound statement simply adds its children (block items) to execution stack
        self.add_child_executes(env.exec_stack)
        env.pop_exec()
        exec_done = True
        self.exec_visited = False
        exec_done = False
        return exec_done, env


class Statement(AstNode):
    def __init__(self):
        super().__init__()
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
        super().__init__()
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
        super().__init__()
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
        super().__init__()
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
        super().__init__()
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

    def add_child_executes(self, exec_stack):
        # do not append body into the execution stack during definition!
        exec_stack.append(self.name_params)
        exec_stack.append(self.return_type)

    def execute(self, env: ExecutionEnvironment):
        """
        Execute a function definition.
        Unlike most other interpreters, the functions are defined as soon as it is called
        (to avoid premature syntax errors).
        So it is done executed as soon as the body section starts.
        """
        exec_done = False
        if not self.exec_visited:
            self.add_child_executes(env.exec_stack)
            self.exec_visited = True
        else:  # all child nodes have been executed and all required values are in the stack
            # rtypes = self.return_type.evaluate()  # list of type specifiers
            # rtype_pntr, funname, params = self.name_params.evaluate()  # FuncDeclarator
            params = env.pop_val()  # list of (TypeVal, Symbol)
            funname, pointer = env.pop_val()  # Symbol, Pointer
            rtype = env.pop_val()  # typeval

            # register the symbol in the scope if it does not exist
            funname.astnode = self
            env.scope.add_symbol(funname.name, funname)
            if env.scope.getvalue(funname.name) is None:
                env.scope.set_value(
                        funname.name,
                        FunctionVal(rtype, params, self.body),
                        self.startline())
            env.pop_exec()
            self.exec_visited = False
            exec_done = True
        return exec_done, env
