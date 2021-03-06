import ast
import dis
import re
import sys
import types

title = "The Program Which Generates This Book"
author = "Martin O'Leary"

preface = """
This book describes a computer program which, when executed, generates this
book. The program is described in three ways:

First, a source code listing is given, in the Python programming language. This
is the form of the program which was typed by the author, in text form.

Second, an *abstract syntax tree* is described, which is the computer's
interpretation of the textual source code in terms of the language constructs
available in the Python programming language.

Finally, the program is described in terms of *bytecode*, the computer's internal
representation of the source code, a sequence of unambiguous instructions which
can be executed to perform the computation described by the program.

The descriptions given in this book are generated by the program it describes, in
conjunction with a Python interpreter, starting from the source code form. Both 
the abstract syntax tree and the bytecode representation are somewhat unstable.
Different versions of the Python interpreter may yield different abstract syntax
trees and different bytecode representations of the same program. This book was
generated using `Python {}`.
""".format(sys.version)


def title_block():
    return "% {}\n% {}\n".format(title, author)


def describe_op(op, codes):
    f = descriptors.get(op.opname, None)
    if f:
        s = f(op, codes)
    else:
        s = ''
    if op.is_jump_target:
        s = "\n\n### Offset {}\n\n".format(op.offset) + s
    return s


def describe_file(filename):
    codetxt = open(filename).read()
    txt = title_block()
    txt += "# About this book\n\n"
    txt += preface
    txt += "\n\n## License\n\n"
    txt += open("LICENSE.md").read()
    txt += '\n\n# Source code\n\n'
    txt += '```\n' + codetxt + '\n```\n\n'
    txt += '# Abstract syntax tree\n\n'
    txt += describe_node(ast.parse(codetxt))
    txt += '\n\n# Bytecode\n\n'
    codes = [(filename, compile(codetxt, filename, 'exec', optimize=1))]
    while codes:
        name, code = codes.pop(0)
        txt += '## {}'.format(name)
        for op in dis.get_instructions(code):
            desc = describe_op(op, codes)
            if not desc: continue
            if op.starts_line:
                txt += '\n\n'
            txt += desc + ' '
        txt += '\n\n'
    return txt


def describe_number(num):
    words = [
        "zero", "one", "two", "three", "four", "five", "six", "seven", "eight",
        "nine", "ten"
    ]
    if 0 <= num <= 10:
        return words[num]
    elif num >= -10:
        return "minus " + words[-num]
    return str(num)


def as_list(items):
    items = list(items)
    if len(items) == 1:
        return items[0]
    else:
        return ', '.join(items[:-1]) + ", and " + items[-1]


def escape_string(s):
    s = re.sub(r'([_`\*\\#])', r'\\\1', s)
    s = re.sub(r'\n', r'\\\\n', s)
    return s


def describe_value(value, codes):
    if isinstance(value, types.CodeType):
        # print(dir(value))
        name = value.co_name
        if name.startswith('<'):
            name = value.co_name[1:-1] + ':' + str(value.co_firstlineno)
        codes.append((name, value))
        return "the code object described under {}".format(name)
    elif isinstance(value, str):
        return "the literal string *'{}'*".format(escape_string(value))
    elif isinstance(value, int):
        return "the integer constant {}".format(describe_number(value))
    elif value is None:
        return "the constant None"
    elif isinstance(value, tuple):
        return "the tuple consisting of " + as_list(
            describe_value(x, codes) for x in value)
    else:
        print("Uninterpretable constant:", value)
    return repr(value)


def describe_node(node):
    f = descriptors.get(node.__class__.__name__, None)
    if f:
        return f(node)
    else:
        print(node, node._fields)
        return str(node)


descriptors = {}


def descriptor(f):
    descriptors[f.__name__] = f
    return f


@descriptor
def Module(node):
    return "A module, containing the following code:\n\n" + '\n\n'.join(
        describe_node(n) for n in node.body)


@descriptor
def Import(node):
    return "An import statement for a module named `{}`.".format(
        node.names[0].name)


@descriptor
def Assign(node):
    s = "An assignment to {}, of the value of {}.".format(
        describe_node(node.targets[0]), describe_node(node.value))
    return s


@descriptor
def AugAssign(node):
    s = "A modifying assignment to {}, using {}, of the value of {}.".format(
        describe_node(node.target),
        describe_node(node.op), describe_node(node.value))
    return s


@descriptor
def Add(node):
    return "the addition (or concatenation) operator"


@descriptor
def Mult(node):
    return "the multiplication operator"


@descriptor
def BitAnd(node):
    return "the bitwise 'AND' operator"


@descriptor
def Subscript(node):
    return "{}, subscripted by {}".format(
        describe_node(node.value), describe_node(node.slice))


@descriptor
def Index(node):
    return describe_node(node.value)


@descriptor
def Slice(node):
    if node.lower:
        return "a slice from {} to {}".format(
            describe_node(node.lower), describe_node(node.upper))
    else:
        return "a slice up to {}".format(describe_node(node.upper))


@descriptor
def For(node):
    s = "A for loop, where {} iterates over {}." \
        "The body of the loop is as follows:\n\n".format(
        describe_node(node.target), describe_node(node.iter))
    for nod in node.body:
        s += describe_node(nod) + "\n\n"
    s += "The for loop ends here."
    return s


@descriptor
def While(node):
    s = "A while loop, testing {}." \
        "The body of the loop is as follows:\n\n".format(
        describe_node(node.test))
    for nod in node.body:
        s += describe_node(nod) + "\n\n"
    s += "The while loop ends here."
    return s


@descriptor
def Continue(node):
    return "A 'continue' statement."


@descriptor
def Name(node):
    return "the name `{}`".format(node.id)


@descriptor
def NameConstant(node):
    return "the constant `{}`".format(node.value)


@descriptor
def List(node):
    if not node.elts:
        return "an empty list"
    else:
        return "a list containing " + as_list(
            describe_node(elt) for elt in node.elts)


@descriptor
def Tuple(node):
    if not node.elts:
        return "an empty tuple"
    else:
        return "a tuple containing " + as_list(
            describe_node(elt) for elt in node.elts)


@descriptor
def Dict(node):
    return "an empty dictionary"


@descriptor
def FunctionDef(node):
    s = "## {node.name}\n\n" \
        "A definition of a function named `{node.name}`".format(
        node=node)
    args = node.args
    if len(args.args) == 1:
        s += ", with argument `{}`.".format(args.args[0].arg)
    elif args.args:
        s += ", with positional arguments {args}.".format(args=as_list(
            ['`{}`'.format(a.arg) for a in args.args]))
    if node.decorator_list:
        s += " The definition is decorated with the function `{}`.".format(
            node.decorator_list[0].id)
    s += " The body of the function is as follows:\n\n"
    for nod in node.body:
        s += describe_node(nod) + '\n\n'

    s += "The function {} ends here.\n\n".format(node.name)
    return s


@descriptor
def Call(node):
    s = 'a function call, calling the value of {f}'.format(
        f=describe_node(node.func))
    if len(node.args) == 1:
        s += ', with argument {}'.format(describe_node(node.args[0]))
    elif node.args:
        s += ', with positional arguments {args}'.format(args=as_list(
            describe_node(a) for a in node.args))
    else:
        s += ' with no positional arguments'
    if node.keywords:
        if len(node.keywords) == 1:
            s += ', and keyword argument'
        else:
            s += ', and keyword arguments'
        for kw in node.keywords:
            s += ', assigning {} as `{}`'.format(
                describe_node(kw.value), kw.arg)
    return s


@descriptor
def Return(node):
    return "A return statement, returning the value of {}.".format(
        describe_node(node.value))


@descriptor
def Str(node):
    return "the literal string *'{}'*".format(escape_string(node.s))


@descriptor
def Attribute(node):
    return "an attribute lookup of `{}` on {}".format(
        node.attr, describe_node(node.value))


@descriptor
def Expr(node):
    return "A bare expression with value {}.".format(describe_node(node.value))


@descriptor
def BinOp(node):
    return "{}, with left hand side {}, and right hand side {}".format(
        describe_node(node.op),
        describe_node(node.left), describe_node(node.right))


@descriptor
def If(node):
    s = "An `if` statement, testing {}. " \
        "The body of the main branch is as follows:\n\n".format(
        describe_node(node.test))
    for nod in node.body:
        s += describe_node(nod) + "\n\n"
    if node.orelse:
        s += "The other ('else') branch of the `if` statement is as follows:\n\n"
        for nod in node.orelse:
            s += describe_node(nod) + "\n\n"
    s += "The `if` statement ends here.\n\n"
    return s


@descriptor
def Num(node):
    return "a numeric constant with value {}".format(node.n)


@descriptor
def Compare(node):
    if len(node.ops) == 1:
        return "a comparison (using {}) of {} and {}".format(
            describe_node(node.ops[0]),
            describe_node(node.left), describe_node(node.comparators[0]))
    else:
        lefts = [node.left] + node.comparators[:-1]
        rights = node.comparators
        s = "a compound comparison, comparing "
        s += as_list("{} and {} using {}".format(
            describe_node(left), describe_node(right), describe_node(op))
                     for left, op, right in zip(lefts, node.ops, rights))
        return s


@descriptor
def Eq(node):
    return "the equality operator"


@descriptor
def GtE(node):
    return "the 'greater than or equal to' operator"

@descriptor
def LtE(node):
    return "the 'less than or equal to' operator"

@descriptor
def Gt(node):
    return "the 'greater than' operator"


@descriptor
def Is(node):
    return "the identity operator"


@descriptor
def UnaryOp(node):
    return "{} applied to {}".format(
        describe_node(node.op), describe_node(node.operand))


@descriptor
def Not(node):
    return "the unary 'not' operator"


@descriptor
def USub(node):
    return "the unary negation operator"


@descriptor
def GeneratorExp(node):
    gen = node.generators[0]
    return "a generator expression, taking the value of {}, " \
        "as {} ranges over {}".format(
        describe_node(node.elt),
        describe_node(gen.target), describe_node(gen.iter))


@descriptor
def ListComp(node):
    gen = node.generators[0]
    return "a list comprehension, taking the value of {}, " \
        "as {} ranges over {}".format(
        describe_node(node.elt),
        describe_node(gen.target), describe_node(gen.iter))


@descriptor
def Assert(node):
    return ""


@descriptor
def LOAD_CONST(op, codes):
    return "The computer places {} on top of the stack.".format(
        describe_value(op.argval, codes))


@descriptor
def LOAD_NAME(op, codes):
    return "The computer places the value associated with the name `{}` " \
        "on top of the stack.".format(
        op.argval)


@descriptor
def CALL_FUNCTION(op, codes):
    if op.argval == 0:
        return "The computer takes the top value from the stack " \
            "and calls it as a function (with no arguments), " \
            "placing the return value on top of the stack."
    elif op.argval == 1:
        return "The computer takes the top value from the stack, " \
            "along with another value which it calls as a function, " \
            "using the original value as an argument, " \
            "placing the return value on the stack.".format(
            op.argval)
    else:
        return "The computer takes {} values from the stack, " \
            "along with another value which it calls as a function, " \
            "using the original values as arguments, " \
            "placing the return value on the stack.".format(
            describe_number(op.argval))


@descriptor
def POP_TOP(op, codes):
    return "The computer discards the top value from the stack."


@descriptor
def RETURN_VALUE(op, codes):
    return "The computer exits the current function, " \
        "returning the top value on the stack."


@descriptor
def STORE_NAME(op, codes):
    return "The computer takes the top value from the stack, " \
        "and stores it under the name `{}`.".format(
        op.argval)


@descriptor
def BINARY_SUBSCR(op, codes):
    return "The computer takes the top two values from the stack " \
        "and retrieves the value of the second item, " \
        "subscripted by the value of the first item."


@descriptor
def LOAD_ATTR(op, codes):
    return "The computer takes the top value from the stack " \
        "and retrieves its attribute named `{}`, " \
        "placing it on the stack.".format(
        op.argval)


@descriptor
def POP_JUMP_IF_FALSE(op, codes):
    return "The computer takes the top value from the stack, " \
        "and if it is false-like (e.g. False, None or zero), " \
        "jumps to offset {}.".format(
        op.argval)


@descriptor
def POP_JUMP_IF_TRUE(op, codes):
    return "The computer takes the top value from the stack, " \
        "and if it is true-like (e.g. True, non-empty or non-zero), " \
        "jumps to offset {}.".format(
        op.argval)


@descriptor
def IMPORT_NAME(op, codes):
    return "The computer takes the top two values from the stack " \
        "and uses them as the 'fromlist' and 'level' of an import " \
        "for the module `{}`, which is placed on the stack.".format(
        op.argval)


@descriptor
def MAKE_FUNCTION(op, codes):
    txt = "The computer takes the top two values from the stack " \
        "and uses them as the qualified name and code of a new function, " \
        "which is placed on the stack."
    if op.argval & 8:
        txt += ' It also takes the next value as a tuple of cells ' \
            'for free variables, creating a closure.'
    if op.argval & 4:
        txt += ' It also takes the next value as a dictionary ' \
            'of function annotations.'
    if op.argval & 2:
        txt += ' It also takes the next value as a dictionary ' \
            'of keyword arguments.'
    if op.argval & 1:
        txt += ' It also takes the next value as a tuple of default arguments.'
    return txt


@descriptor
def COMPARE_OP(op, codes):
    if op.argval == '==':
        return "The computer takes the top two values from the stack " \
            "and compares them for equality, " \
            "placing the result on top of the stack."
    elif op.argval == 'is':
        return "The computer takes the top two values from the stack " \
            "and compares them for identity, " \
            "placing the result on top of the stack."
    return "The computer takes the top two values from the stack " \
        "and compares them using the operator `{}`, " \
        "placing the result on top of the stack.".format(
        op.argval)


@descriptor
def BUILD_MAP(op, codes):
    if op.argval == 0:
        return "The computer places an empty dictionary on top of the stack."
    return "The computer takes the top {} values from the stack, " \
        "and uses them as key-value pairs in a new dictionary, " \
        "which is placed on top of the stack.".format(
        describe_number(2 * op.argval))


@descriptor
def EXTENDED_ARG(op, codes):
    return ""


@descriptor
def BINARY_ADD(op, codes):
    return "The computer takes the top two values from the stack, " \
        "adds them together, and places the result on top of the stack."


@descriptor
def BINARY_MULTIPLY(op, codes):
    return "The computer takes the top two values from the stack, " \
        "multiplies them together, and places the result on top of the stack."


@descriptor
def BINARY_AND(op, codes):
    return "The computer takes the top two values from the stack, " \
        "applies a bitwise `AND` operator to them, " \
        "and places the result on top of the stack."


@descriptor
def BUILD_LIST(op, codes):
    if op.argval == 0:
        return "The computer places a new empty list on top of the stack."
    elif op.argval == 1:
        return "The computer takes the top value from the stack, " \
            "puts it in a list, and places it on top of the stack."
    else:
        return "The computer takes the top {} values from the stack, " \
            "puts them in a list, and places it on top of the stack.".format(
            describe_number(op.argval))


@descriptor
def BUILD_SLICE(op, codes):
    return "The computer takes the top two values from the stack, " \
        "creates a slice object from them, and places it on top of the stack."


@descriptor
def BUILD_TUPLE(op, codes):
    if op.argval == 1:
        return "The computer takes the top value from the stack, " \
            "creates a tuple from it, and places it on top of the stack."
    return "The computer takes the top {} values from the stack, " \
        "creates a tuple from them, and places it on top of the stack.".format(
        describe_number(op.argval))


@descriptor
def FOR_ITER(op, codes):
    return "The computer looks at the top value on the stack and " \
        "calls its `next()` method. If it returns a value, " \
        "it places it on top of the stack. If not, it removes " \
        "the top value from the stack and jumps to offset {}.".format(
        op.argval)


@descriptor
def GET_ITER(op, codes):
    return "The computer takes the top value from the stack, " \
        "turns it into an iterator (using `iter()`), " \
        "and places the result on top of the stack."


@descriptor
def INPLACE_ADD(op, codes):
    return "The computer takes the top value from the stack and (in place)" \
        "adds the second from top value from the stack to it, " \
        "placing the result on top of the stack."


@descriptor
def JUMP_ABSOLUTE(op, codes):
    return "The computer jumps to offset {}.".format(op.argval)


@descriptor
def JUMP_FORWARD(op, codes):
    return "The computer jumps forward to offset {}.".format(op.argval)


@descriptor
def LIST_APPEND(op, codes):
    return "The computer takes the top value from the stack and appends it " \
        "to the list stored {} places from the top of the stack.".format(
        describe_number(op.argval))


@descriptor
def LOAD_CLOSURE(op, codes):
    return "The computer loads a reference to the free variable named `{}` " \
        "and places it on top of the stack.".format(
        op.argval)


@descriptor
def LOAD_DEREF(op, codes):
    return "The computer loads the contents of the free variable named `{}` " \
        "and places it on top of the stack.".format(
        op.argval)


@descriptor
def LOAD_FAST(op, codes):
    return "The computer loads a reference to the local variable named `{}` " \
        "and places it on top of the stack.".format(
        op.argval)


@descriptor
def LOAD_GLOBAL(op, codes):
    return "The computer loads a reference to the global variable named `{}` " \
        "and places it on top of the stack.".format(
        op.argval)


@descriptor
def POP_BLOCK(op, codes):
    return "The computer removes one block from the block stack."


@descriptor
def SETUP_LOOP(op, codes):
    return "The computer places a new block for a loop on top of " \
        "the block stack, extending until offset {}.".format(
        op.argval)


@descriptor
def STORE_DEREF(op, codes):
    return "The computer takes the top value from the stack and stores " \
        "it in the free variable named `{}`.".format(
        op.argval)


@descriptor
def STORE_FAST(op, codes):
    return "The computer takes the top value from the stack and stores " \
        "it in the local variable named `{}`.".format(
        op.argval)


@descriptor
def STORE_SUBSCR(op, codes):
    return "The computer takes the top value from the stack, " \
        "uses it to index into the next-from-top value, " \
        "and stores the value below that in that location."


@descriptor
def UNPACK_SEQUENCE(op, codes):
    return "The computer takes the top value from the stack, " \
        "unpacks it into {} values, " \
        "then places them each on top of the stack.".format(
        describe_number(op.argval))


@descriptor
def YIELD_VALUE(op, codes):
    return "The computer takes the top value from the stack " \
        "and yields it from the current generator."


@descriptor
def CALL_FUNCTION_KW(op, codes):
    return "The computer takes the top value from the stack " \
        "and interprets it as a tuple of keyword names. " \
        "It then takes values from the top of the stack as " \
        "corresponding values, followed by positional arguments " \
        "up to a total of {} values (both keyword and positional). " \
        "Then it takes the next value from the top of the stack and " \
        "calls it as a function with these arguments, " \
        "placing the return value on top of the stack.".format(
        op.argval)


@descriptor
def DUP_TOP(op, codes):
    return "The computer duplicates the top value on the stack, " \
        "placing the new copy on top of the stack."


@descriptor
def ROT_TWO(op, codes):
    return "The computer takes the top two values from the stack, " \
        "swaps them, and replaces them on top of the stack."


@descriptor
def ROT_THREE(op, codes):
    return "The computer takes the top three values from the stack, " \
        "rotates them so that the top value is now on the bottom, " \
        "and replaces them on top of the stack."


@descriptor
def UNARY_NEGATIVE(op, codes):
    return "The computer takes the top value from the stack, negates it, " \
        "and places the result on top of the stack."


@descriptor
def JUMP_IF_FALSE_OR_POP(op, codes):
    return "The computer looks at the top value on the stack. " \
        "If it is false-like (e.g. False, None or zero), it jumps " \
        "to offset {}. Otherwise it removes the top value from the stack."


if __name__ == '__main__':
    outfile = sys.argv[1]
    filename = __file__
    if len(sys.argv) > 2:
        filename = sys.argv[2]
    f = open(outfile, "w")
    f.write(describe_file(filename))
    f.close()
