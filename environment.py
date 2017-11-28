class ExecutionEnvironment:
    def __init__(self, exec_stack, currline, scope, call_stack, value_stack=[]):
        self.exec_stack = exec_stack
        self.currline = currline
        self.scope = scope
        self.call_stack = call_stack
        self.value_stack = value_stack
        self.booked_updates = []

    def book_update(self, update):
        self.booked_updates.append(update)

    def exec_booked_updates(self):
        for update in self.booked_updates:
            update['exec_target'](*update['arg'])

    def update_currline(self, no):
        self.currline += no

    def pop_exec(self):
        self.exec_stack.pop()

    def push_exec(self, exc):
        self.exec_stack.append(exc)

    def push_val(self, val):
        self.value_stack.append(val)

    def pop_val(self):
        return self.value_stack.pop()


class CRuntimeErr(Exception):
    def __init__(self, msg, env=None):
        self.msg = msg
        self.env = env

