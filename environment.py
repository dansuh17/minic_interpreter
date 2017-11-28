class ExecutionEnvironment:
    def __init__(self, exec_stack, currline, scope, call_stack, value_stack):
        self.exec_stack = exec_stack
        self.currline = currline
        self.scope = scope
        self.call_stack = call_stack
        self.value_stack = value_stack

    def update_currline(self, no):
        self.currline += no

    def add_value(self, val):
        self.value_stack.append(val)


class CRuntimeErr(Exception):
    def __init__(self, msg, env=None):
        self.msg = msg
        self.env = env

