class Symbol:
    def __init__(self, name, dtype: TypeVal, astnode):
        self.name = name
        self.address = 0  # TODO: generate
        assert isinstance(dtype, TypeVal)
        self.dtype = dtype
        self.astnode = astnode
        self.val_history = []
        self.value = None


class TypeVal:
    def __init__(self, typename, ptr=0):
        self.typename = typename
        self.ptr = ptr


class Function:
    def __init__(self):
        self.rtype = None  # return type
        self.params = None  # list of (type, symbolname) pairs
        self.body = None  # ast root of body (compound statement)


class Scope:
    """
    Scope node for scope tree.
    """
    def __init__(self, symbol_table: dict):
        self.symbol_table = symbol_table
        self.child_scope = None
        self.parent_scope = None
        self.return_type = None

    def add_symbol(self, symbol_name: str, symbol_info: Symbol):
        if symbol_name not in self.symbol_table:
            self.symbol_table[symbol_name] = symbol_info

    def getsymbol(self, sym_name):
        return self.symbol_table[sym_name]

    def set_return_type(self, rtypes: list):
        self.return_type = rtypes  # list of type specifiers

    def set_value(self, sym_name, val, lineno):
        self.getsymbol(sym_name).value = val
        self.getsymbol(sym_name).val_history.append((val, lineno))

