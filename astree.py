from symbol_table import TypeVal, Symbol, Value, FunctionVal, Scope, DeclaratorVal, AssignmentVal
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

    def __repr__(self):
        return self.__str__()


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
        if env.currline < self.startline() or env.currline > self.endline():
            # execution line number not reached yet
            return False, env

        exec_done = False
        if not self.exec_visited:
            env.push_exec(self.operand)
            self.exec_visited = True
        else:
            operand = env.pop_val()
            operand_val = env.scope.getvalue(operand.name)

            inc = 1 if self.op_name == '++' else -1
            if self.is_postfix:
                # postpone update
                env.book_update({
                    'exec_target': env.scope.set_value,
                    'arg': (operand.name, Value(vtype=operand_val.vtype, val=operand_val.val + inc), env.currline),
                })
            else:
                env.scope.set_value(operand.name, operand + inc, env.currline)

            env.push_val(operand_val)  # indicate that the operation has been made successfuly
            exec_done = True
            self.exec_visited = False
            env.pop_exec()
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

        funcname = self.func_name.name()

        # handle printf - a hack!
        if funcname == 'printf':
            if not self.exec_visited:
                env.push_exec(self.argument_list)
                self.exec_visited = True
                return False, env
            else:
                if env.currline >= self.endline():  # call has been made!
                    args = env.pop_val()
                    string_lit = args[0].val
                    if len(args) == 1:
                        print(string_lit)
                    else:
                        if '%d' in string_lit:
                            string_lit.replace('%d', str(int(args[1].val)))
                        else:
                            string_lit.replace('%f', str(float(args[1].val)))
                        print(string_lit)
                env.pop_exec()  # function call done
                self.exec_visited = False
                return True, env


        if not self.exec_visited:
            if len(self.argument_list) != 0:
                env.push_exec(self.argument_list)
            # defer the execution until register is done - register first
            fundef_node = env.scope.getsymbol(funcname).astnode
            env.push_exec(fundef_node)
            env.scope.return_lineno = env.currline
            env.currline = fundef_node.startline()
            self.exec_visited = True
            self.wait_return = False
        else:
            if env.currline >= self.endline():  # call has been made!
                if not self.wait_return:
                    # function has not been executed and returned
                    if env.scope.getvalue(funcname) is None:
                        env.scope.show()
                        raise CRuntimeErr('No function named {} defined.'.format(funcname), env)

                    funcval = env.scope.getvalue(funcname)
                    args = []
                    if len(self.argument_list) > 0:
                        args = env.pop_val()
                    print(args)
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
                    func_scope.return_type = funcval.rtype

                    # type check the arguments with prameter declarations
                    # args are Values and params are (DeclaratorVal, TypeVal)s
                    for arg, param in zip(args, params):
                        param_type, param_dec = param
                        if not arg.vtype.castable(param_type):
                            raise CRuntimeErr('Argument type mismatch {}, {}'.format(arg, param), env)
                        arg.cast(param_type)

                        # bind argument values to their symbols
                        argsymbol = param_dec.getsymbol()
                        func_scope.add_symbol(
                                symbol_name=argsymbol.name,
                                symbol_info=argsymbol)
                        func_scope.set_value(argsymbol.name, arg, env.currline)

                    # start executing body
                    body_ast = env.scope.getsymbol(funcname).value.body
                    env.push_exec(body_ast)
                    env.scope = func_scope
                    env.currline = body_ast.startline()
                    env.call_stack.append(funcval)
                    self.wait_return = True
                else:
                    # execution has been done and returned
                    self.wait_return = False
                    exec_done = True
                    # TODO: type check for return value
                    retval = env.scope.get_return_val()
                    print(retval)

                    if not retval.vtype.castable(env.scope.return_type):
                        raise CRuntimeErr('Wrong return type! {} {}'.format(retval, env.scope.return_type), env)

                    env.push_val(retval)  # store the return value
                    env.currline = env.scope.return_lineno
                    env.scope = env.scope.return_scope  # reset to new scope
                    env.pop_exec()  # function call done
                    env.call_stack.pop()
                    self.exec_visited = False
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
                    argval = env.pop_val()
                    if isinstance(argval, Symbol):
                        argval = env.scope.getvalue(argval.name)
                    arglist.append(argval)
                arglist.reverse()

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
                idx_val = env.pop_val()[0]
                name_val = env.pop_val()

            arr_val = env.scope.getvalue(name_val.name)
            if isinstance(idx_val, Symbol):
                idx_val = env.scope.getvalue(idx_val.name)  # get value from variable

            # check if it is an array
            if arr_val.vtype.array == 0:
                raise CRuntimeErr('Name {} not array!'.format(arr_name), env)

            idx = idx_val.val
            if len(arr_val.val) <= idx:
                raise CRuntimeErr('Index error - array length {}, idx {}'.format(len(arr_val.val), idx), env)

            array_access_val = arr_val.val[idx]  # retrieve the actual value

            env.push_val(array_access_val)
            env.pop_exec()
            exec_done = True
            self.exec_visited = False
        return exec_done, env

    def children(self):
        children_nodes = []
        if self.name is not None and isinstance(self.name, AstNode):
            children_nodes.append(self.name)

        if self.idx is not None and isinstance(self.idx, AstNode):
            children_nodes.append(self.idx)
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

    def execute(self, env):
        if env.currline < self.startline() or env.currline > self.endline():
            # execution line number not reached yet
            return False, env

        exec_done = False
        if not self.exec_visited:
            self.add_child_executes(env.exec_stack)
            self.exec_visited = True
        else:
            # retrieve the operands
            op_val = env.pop_val()
            arg2_val = env.pop_val()
            arg1_val = env.pop_val()

            # get the values
            if isinstance(arg1_val, Symbol):
                arg1_val = env.scope.getvalue(arg1_val.name)
            if isinstance(arg2_val, Symbol):
                arg2_val = env.scope.getvalue(arg2_val.name)
            op_type = op_val.val

            if op_type == '*':
                res = arg1_val.val * arg2_val.val
                if not arg1_val.vtype.castable(arg2_val.vtype):
                    raise CRuntimeErr('Type not castable {} and {}'.format(arg1_val.vtype, arg2_val.vtype))

                if arg1_val.vtype.typename == 'int' and arg2_val.vtype.typename == 'int':
                    vtype = TypeVal('int')
                else:
                    vtype = TypeVal('float')
            elif op_type == '+':
                res = arg1_val.val + arg2_val.val
                if not arg1_val.vtype.castable(arg2_val.vtype):
                    raise CRuntimeErr('Type not castable {} and {}'.format(arg1_val.vtype, arg2_val.vtype))
                if arg1_val.vtype.typename == 'int' and arg2_val.vtype.typename == 'int':
                    vtype = TypeVal('int')
                else:
                    vtype = TypeVal('float')
            elif op_type == '-':
                res = arg1_val.val - arg2_val.val
                if not arg1_val.vtype.castable(arg2_val.vtype):
                    raise CRuntimeErr('Type not castable {} and {}'.format(arg1_val.vtype, arg2_val.vtype))
                if arg1_val.vtype.typename == 'int' and arg2_val.vtype.typename == 'int':
                    vtype = TypeVal('int')
                else:
                    vtype = TypeVal('float')
            elif op_type == '%':
                res = arg1_val.val % arg2_val.val
                vtype = TypeVal('int')
            elif op_type == '/':
                res = arg1_val.val / arg2_val.val
                vtype = TypeVal('float')
            elif op_type == '&&':
                res = 1 if arg1_val.val and arg2_val.val else 0
                if not arg1_val.vtype.castable(arg2_val.vtype):
                    raise CRuntimeErr('Type not castable {} and {}'.format(arg1_val.vtype, arg2_val.vtype))
                vtype = TypeVal('int')
            elif op_type == '||':
                res = 1 if arg1_val.val or arg2_val.val else 0
                if not arg1_val.vtype.castable(arg2_val.vtype):
                    raise CRuntimeErr('Type not castable {} and {}'.format(arg1_val.vtype, arg2_val.vtype))
                vtype = TypeVal('int')
            elif op_type == '<':
                res = 1 if arg1_val.val < arg2_val.val else 0
                if not arg1_val.vtype.castable(arg2_val.vtype):
                    raise CRuntimeErr('Type not castable {} and {}'.format(arg1_val.vtype, arg2_val.vtype))
                vtype = TypeVal('int')
            elif op_type == '>':
                res = 1 if arg1_val.val > arg2_val.val else 0
                if not arg1_val.vtype.castable(arg2_val.vtype):
                    raise CRuntimeErr('Type not castable {} and {}'.format(arg1_val.vtype, arg2_val.vtype))
                vtype = TypeVal('int')
            elif op_type == '>=':
                res = 1 if arg1_val.val >= arg2_val.val else 0
                if not arg1_val.vtype.castable(arg2_val.vtype):
                    raise CRuntimeErr('Type not castable {} and {}'.format(arg1_val.vtype, arg2_val.vtype))
                vtype = TypeVal('int')
            elif op_type == '<=':
                res = 1 if arg1_val.val <= arg2_val.val else 0
                if not arg1_val.vtype.castable(arg2_val.vtype):
                    raise CRuntimeErr('Type not castable {} and {}'.format(arg1_val.vtype, arg2_val.vtype))
                vtype = TypeVal('int')
            elif op_type == '==':
                res = 1 if arg1_val.val == arg2_val.val else 0
                if not arg1_val.vtype.castable(arg2_val.vtype):
                    raise CRuntimeErr('Type not castable {} and {}'.format(arg1_val.vtype, arg2_val.vtype))
                vtype = TypeVal('int')
            else:
                raise CRuntimeErr('Invalid binary operator {}'.format(op_val), env)

            env.push_val(Value(vtype, res))
            env.pop_exec()
            exec_done = True
            self.exec_visited = False
        return exec_done, env


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

    def execute(self, env):
        if env.currline < self.startline() or env.currline > self.endline():
            # execution line number not reached yet
            return False, env

        exec_done = False
        if not self.exec_visited:
            self.add_child_executes(env.exec_stack)
            self.exec_visited = True
        else:
            val = env.pop_val()
            lval = env.pop_val()
            assert isinstance(val, Value)

            if isinstance(lval, Symbol):
                if env.scope.getsymbol(lval.name) is None:
                    raise CRuntimeErr('Name {} does not exist!'.format(sym.name), env)
                # assign value to the name
                env.scope.set_value(lval.name, val, env.currline)
            elif isinstance(lval, Value):
                lval.val = val.val

            env.push_val(None)  # indicate that assignment has been done properly
            env.pop_exec()
            exec_done = True
            self.exec_visited = False
        return exec_done, env


class Expression(AstNode, list):
    """
    Represents an expression - can be either assignment or list of assignments.
    Assignment grammar can be an assignment (assigning value to symbol)
    or simply an expression returning value.
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

    def execute(self, env):
        if env.currline < self.startline() or env.currline > self.endline():
            # execution line number not reached yet
            return False, env

        exec_done = False
        if not self.exec_visited:
            self.add_child_executes(env.exec_stack)
            self.exec_visited = True
        else:
            asmt_vals = []
            for _ in range(len(self)):
                asmt_val = env.pop_val()
                if isinstance(asmt_val, list):  # () enclosed expression
                    if len(asmt_val) == 1:
                        asmt_val = asmt_val[0]
                asmt_vals.append(asmt_val)

            env.push_val(asmt_vals)
            env.pop_exec()
            exec_done = True
            self.exec_visited = False
        return exec_done, env


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
            # execution line number not reached yet
            return False, env

        exec_done = False
        if not self.exec_visited:
            self.add_child_executes(env.exec_stack)
            self.exec_visited = True
        else:
            if env.currline >= self.endline():
                init_dec_vals = env.pop_val()  # list of init declaration list
                type_val = env.pop_val()  # TypeVal indicating the type of initializers

                # bind symbols to scope
                for decval in init_dec_vals:
                    init_val = None
                    if isinstance(decval, tuple):
                        # contains an initializer, as in int c = 0
                        decval, init_val = decval
                    symbol = decval.getsymbol()
                    pointer = decval.pointer_val
                    vtype = TypeVal(typename=type_val.typename)
                    # pointers can be separately declared
                    # ex) int *x, y z -> x is a pointer, y, z are not
                    vtype.ptr = pointer.order if pointer is not None else 0
                    value = Value(vtype=vtype, val=init_val)
                    if decval.dec_type == 'array':
                        vtype.array = 1
                        value.arr_size = decval.arr_size_val.val
                        value.val = [Value(TypeVal(vtype.typename)) for _ in range(value.arr_size)]  # default array init

                    if env.scope.getsymbol(symbol.name) is None:
                        env.scope.add_symbol(symbol.name, symbol)
                        env.scope.set_value(symbol.name, value, env.currline)
                    else:
                        raise CRuntimeErr('Symbol "{}" already bound in this scope'.format(symbol.name), env)

                env.push_val(None)
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

    def execute(self, env):
        # simply put the order of pointer
        env.push_val(self.order)
        env.pop_exec()
        return True, env

    def __str__(self):
        return '{}(order:{}, {})'.format(
                super().__str__(), self.order, '*' * self.order)


class Declarator(AstNode):
    """
    Represents direct declarator and declarator (direct declarator with pointers).
    """
    def __init__(self, of, pointer=None):
        super().__init__()
        self.pointer = pointer
        self.of = of  # declarator of ...

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
                of_val = env.pop_val()
                pointer_val = None
                if self.pointer is not None:
                    pointer_val = env.pop_val()

                env.push_val(DeclaratorVal('default', of_val, pointer_val))
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
                assignment_expr_val = env.pop_val()
                pointer_val = None
                if self.pointer is not None:
                    pointer_val = env.pop_val()
                of_val = env.pop_val()

                dec_val = DeclaratorVal('array', of_val, pointer_val)
                dec_val.arr_size_val = assignment_expr_val
                env.push_val(dec_val)
                env.pop_exec()
                exec_done = True
                self.exec_visited = False
        return exec_done, env


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
                pointer_val = None
                if self.pointer is not None:
                    pointer_val = env.pop_val()
                funname_val = env.pop_val()  # returned from declarator

                dec_val = DeclaratorVal('function', funname_val, pointer_val)
                dec_val.param_typelist_val = param_list

                env.push_val(dec_val)
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
    ex1) 'sum = 0' translates into Declarator(sum) + Initializer(0)
    ex2) 'sum' (as in 'int sum') does not have an initializer part,
        but is not instantiated as InitDeclarator. See yacc.py.
    Initializer part is an assignment expression.
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
                init_val = env.pop_val()
                declarator_val = env.pop_val()

                env.push_val((declarator_val, init_val))  # pair of (Symbol, Value)
                env.pop_exec()
                exec_done = True
                self.exec_visited = False
        return exec_done, env


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
                initdec_vallist = []
                for _ in range(len(self)):
                    initdec_vallist.append(env.pop_val())

                env.push_val(initdec_vallist)
                env.pop_exec()
                exec_done = True
                self.exec_visited = False
        return exec_done, env


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
                declarator = None
                if self.declarator is not None:
                    declarator = env.pop_val()
                dec_specs = env.pop_val()  # TypeVal
                if declarator is not None:
                    if declarator.pointer_val is not None:
                        dec_specs.ptr = declarator.pointer_val
                    if declarator.dec_type == 'array':
                        dec_specs.array = 1

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
    """
    list of statements enclosed by braces, such as function bodies.
    """
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

        exec_done = False
        if not self.exec_visited:
            self.add_child_executes(env.exec_stack)
            self.exec_visited = True
        else:
            if env.currline >= self.endline():
                # compound statment ignores each statements' execution results
                for _ in range(len(self)):
                    env.pop_val()  # simply pop out all of them

                env.pop_exec()
                if env.scope.return_lineno is not None:
                    env.currline = env.scope.return_lineno
                exec_done = True
                self.exec_visited = False
        return exec_done, env


class Statement(AstNode):
    def __init__(self):
        super().__init__()
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

    def children(self):
        ch_nodes = []
        if self.if_cond is not None:
            assert isinstance(self.if_cond, AstNode)
            ch_nodes.append(self.if_cond)
        if self.if_expr is not None:
            assert isinstance(self.if_expr, AstNode)
            ch_nodes.append(self.if_expr)
        if self.else_expr is not None:
            assert isinstance(self.else_expr, AstNode)
            ch_nodes.append(self.else_expr)
        return ch_nodes

    def execute(self, env):
        if env.currline < self.startline() or env.currline > self.endline():
            # execution line number not reached yet
            return False, env

        exec_done = False
        if not self.exec_visited:
            env.push_exec(self.if_cond)

            # create a block scope for the statement
            block_scope = Scope({})
            block_scope.parent_scope = env.scope
            block_scope.return_scope = env.scope
            block_scope.return_lineno = self.endline()
            env.scope = block_scope

            self.phase = 'cond_eval'
            self.exec_visited = True
        else:
            if env.currline == self.startline():
                if self.phase == 'cond_eval':
                    cond_val = env.pop_val()  # evaluate the condition - returned from expression

                    if cond_val[0].val >= 1:  # into if-statement
                        env.push_exec(self.if_expr)
                        self.phase = 'done'
                    else:  # into else-statement or continue
                        if self.else_expr is None:
                            exec_done = True
                            self.exec_visited = False
                            env.currline = env.scope.return_lineno
                            env.scope = env.scope.return_scope  # return to parent scope
                            env.push_val(None)
                            env.pop_exec()
                            return exec_done, env
                        else:
                            env.currline = self.else_expr.startline()
                            env.push_exec(self.else_expr)
                            self.phase = 'done'
                else:  # 'done'
                    env.currline = env.scope.return_lineno
                    env.scope = env.scope.return_scope
                    exec_done = True
                    env.push_val(None)
                    env.pop_exec()
                    self.exec_visited = False
        return exec_done, env


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
                ret_val = None
                if self.expr is not None:
                    ret_val = env.pop_val()

                env.push_val(ret_val)
                env.pop_exec()
                exec_done = True
                self.exec_visited = False
        return exec_done, env


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

    def push_conditions(self, env):
        if self.iter_type == 'for':
            env.push_exec(self.exp2)
        elif self.iter_type == 'while':
            env.push_exec(self.exp1)  # push the condition and/or update assignment

    def execute(self, env):
        if env.currline < self.startline() or env.currline > self.endline():
            # execution line number not reached yet
            return False, env

        exec_done = False
        if not self.exec_visited:
            # create a new scope before executing anything
            iter_scope = Scope({})
            iter_scope.parent_scope = env.scope  # current scope is the parent
            iter_scope.return_lineno = self.startline()  # return to the first line of this loop
            iter_scope.return_scope = env.scope
            env.scope = iter_scope
            self.exec_visited = True

            # add declaration or 'prepare statement' for for-loop
            if self.iter_type == 'for':
                if self.exp1 is not None:
                    env.push_exec(self.exp1)
                    self.phase = 'preparation'
                else:
                    self.phase = 'condition'
            return False, env

        if env.currline >= self.body.startline():  # at the start of body...
            print(self.phase)
            if self.phase == 'preparation':
                env.pop_val()  # discard value for preparation
                self.push_conditions(env)
                self.phase = 'cond_eval'
            elif self.phase == 'condition':
                # add statement to evaluate the condition
                self.push_conditions(env)
                self.phase = 'cond_eval'
            elif self.phase == 'cond_eval':
                if self.iter_type == 'for':
                    # handle for-loop
                    cond_val = env.pop_val()

                    # determine from the conditional statement
                    # if the body should be executed
                    if cond_val is None or cond_val[0].val >= 1:
                        env.push_exec(self.body)
                        self.phase = 'body'
                    else:
                        print('ENTERED')
                        env.scope = env.scope.return_scope
                        env.currline = self.endline()  # finish the iteration and proceed

                        env.push_val(None)  # indicate end of statement
                        env.pop_exec()
                        exec_done = True
                        self.exec_visited = False
                elif self.iter_type == 'while':
                    # TODO: implement
                    pass
            elif self.phase == 'body':  # after the body has been executed
                # do the update
                env.currline = self.startline()  # revert the execution line to top of iter statement
                if self.exp3 is not None:
                    env.push_exec(self.exp3)
                    self.phase = 'update'
                else:
                    self.phase = 'condition'
            elif self.phase == 'update':
                env.pop_val()
                env.exec_booked_updates()  # if any value updates are deferred, update the values
                self.push_conditions(env)
                self.phase = 'cond_eval'
                env.currline = self.startline()
        return exec_done, env

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
                ret_val = None
                if self.what is not None:
                    ret_val = env.pop_val()

                env.scope.return_val = ret_val[0]
                env.push_val(ret_val)
                env.pop_exec()
                exec_done = True
                self.exec_visited = False
        return exec_done, env


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
        else:
            fun_dec_val = env.pop_val()

            params = fun_dec_val.param_typelist_val  # list of (TypeVal, Symbol)
            funname = fun_dec_val.of_val.of_val  # name of the function
            pointer = fun_dec_val.pointer_val
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
            env.currline = env.scope.return_lineno
            env.scope.return_lineno = None
            exec_done = True
        return exec_done, env
