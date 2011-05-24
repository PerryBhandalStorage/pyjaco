import py2js
import ast
import inspect

class JSError(Exception):
    pass

class BaseCompiler(object):

    name_map = {
        'self'   : 'this',

        'int' : '_int',
        'float' : '_float',

        'super' : '__super',

        # ideally we should check, that this name is available:
        'py_builtins' : '___py_hard_to_collide',
    }

    builtin = set([
        'NotImplementedError',
        'ZeroDivisionError',
        'AssertionError',
        'AttributeError',
        'RuntimeError',
        'ImportError',
        'TypeError',
        'ValueError',
        'NameError',
        'IndexError',
        'KeyError',
        'StopIteration',

        '_int',
        '_float',
        'max',
        'min',
        'sum',
        'filter',
        'reduce'
    ])

    bool_op = {
        'And'    : '&&',
        'Or'     : '||',
    }

    unary_op = {
        'Invert' : '~',
        'Not'    : '!',
        'UAdd'   : '+',
        'USub'   : '-',
    }

    binary_op = {
        'Add'    : '+',
        'Sub'    : '-',
        'Mult'   : '*',
        'Div'    : '/',
        'Mod'    : '%',
        'LShift' : '<<',
        'RShift' : '>>',
        'BitOr'  : '|',
        'BitXor' : '^',
        'BitAnd' : '&',
    }

    comparison_op = {
            'Eq'    : "==",
            'NotEq' : "!=",
            'Lt'    : "<",
            'LtE'   : "<=",
            'Gt'    : ">",
            'GtE'   : ">=",
            'Is'    : "===",
            'IsNot' : "is not", # Not implemented yet
        }

    def __init__(self):
        self.tmp_index = 0
        # This is the name of the classes that we are currently in:
        self._class_name = []

        # This lists all variables in the local scope:
        self._scope = []
        self._classes = {}
        self._exceptions = []

    def new_dummy(self):
        self.tmp_index += 1
        return "$v%d" % self.tmp_index

    def visit(self, node):
        try:
            visitor = getattr(self, 'visit_' + self.name(node))
        except AttributeError:
            raise JSError("syntax not supported (%s: %s)" % (node.__class__.__name__, node))

        return visitor(node)

    def indent(self, stmts):
        return [ "    " + stmt for stmt in stmts ]

    ## Shared code

    def name(self, node):
        return node.__class__.__name__

    def get_bool_op(self, node):
        return self.bool_op[node.op.__class__.__name__]

    def get_unary_op(self, node):
        return self.unary_op[node.op.__class__.__name__]

    def get_binary_op(self, node):
        return self.binary_op[node.op.__class__.__name__]

    def get_comparison_op(self, node):
        return self.comparison_op[node.__class__.__name__]

    ## Shared visit functions

    def visit_Assign(self, node):
        if len(node.targets) > 1:
            tmp = self.new_dummy()
            q = ["var %s = %s" % (tmp, self.visit(node.value))]
            for t in node.targets:
                q.extend(self.visit_AssignSimple(t, tmp))
            return q
        else:
            return self.visit_AssignSimple(node.targets[0], self.visit(node.value))