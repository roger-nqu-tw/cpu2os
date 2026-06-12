from enum import Enum, auto
from typing import List, Dict, Any
from dataclasses import dataclass
import voxast
from voxast import *

class OpCode(Enum):
    LOAD_CONST = auto()
    LOAD_VAR = auto()
    STORE_VAR = auto()
    LOAD_GLOBAL = auto()
    STORE_GLOBAL = auto()

    ADD = auto()
    SUB = auto()
    MUL = auto()
    DIV = auto()
    MOD = auto()

    EQ = auto()
    NEQ = auto()
    LT = auto()
    GT = auto()
    LE = auto()
    GE = auto()

    AND = auto()
    OR = auto()
    NOT = auto()

    JUMP = auto()
    JUMP_IF_FALSE = auto()
    JUMP_IF_TRUE = auto()

    CALL = auto()
    RETURN = auto()
    POP = auto()

    LOAD_ARRAY = auto()
    STORE_ARRAY = auto()
    ARRAY_LEN = auto()

    PRINT = auto()
    INPUT = auto()
    LEN = auto()

    HALT = auto()

@dataclass
class Instruction:
    opcode: OpCode
    operand: Any = None

@dataclass
class Function:
    name: str
    params: List[str]
    instructions: List[Instruction]
    local_vars: int
    return_type: str

@dataclass
class BytecodeProgram:
    constants: List[Any]
    globals: Dict[str, int]
    functions: Dict[str, Function]
    main: List[Instruction]

class CodeGenerator:
    def __init__(self):
        self.constants = []
        self.globals: Dict[str, int] = {}
        self.global_vars: Dict[str, int] = {}
        self.global_count = 0
        self.functions: Dict[str, Function] = {}
        self.instructions: List[Instruction] = []

        self.local_vars: Dict[str, int] = {}
        self.local_count = 0
        self.loop_stack: List[Dict[str, int]] = []

        self.in_function = False

    def add_constant(self, value: Any) -> int:
        if value in self.constants:
            return self.constants.index(value)
        self.constants.append(value)
        return len(self.constants) - 1

    def generate(self, program: Program) -> BytecodeProgram:
        for stmt in program.statements:
            if isinstance(stmt, FunctionDecl):
                self.generate_function(stmt)

        self.instructions = []
        main_instructions = []
        for stmt in program.statements:
            if not isinstance(stmt, FunctionDecl):
                self.instructions = []
                self.local_vars = {}
                self.local_count = 0
                self.loop_stack = []
                self.generate_statement(stmt)
                main_instructions.extend(self.instructions)

        main_instructions.append(Instruction(OpCode.HALT))

        for name, idx in self.global_vars.items():
            if name not in self.globals:
                self.globals[name] = idx

        return BytecodeProgram(
            constants=self.constants,
            globals=self.globals,
            functions=self.functions,
            main=main_instructions
        )

    def generate_function(self, func: FunctionDecl):
        self.local_vars = {}
        self.local_count = 0
        self.loop_stack = []
        self.instructions = []
        self.in_function = True

        for param_name, _ in func.params:
            self.local_vars[param_name] = self.local_count
            self.local_count += 1

        for stmt in func.body.statements:
            self.generate_statement(stmt)

        self.in_function = False

        self.functions[func.name] = Function(
            name=func.name,
            params=[p[0] for p in func.params],
            instructions=self.instructions[:],
            local_vars=self.local_count,
            return_type=func.return_type.name
        )

    def generate_statement(self, stmt: ASTNode):
        if isinstance(stmt, VariableDecl):
            self.generate_expr(stmt.value)
            if not self.in_function:
                if stmt.name in self.global_vars:
                    idx = self.global_vars[stmt.name]
                else:
                    idx = self.global_count
                    self.global_vars[stmt.name] = self.global_count
                    self.global_count += 1
                self.instructions.append(Instruction(OpCode.STORE_GLOBAL, idx))
            else:
                if stmt.name in self.local_vars:
                    idx = self.local_vars[stmt.name]
                else:
                    idx = self.local_count
                    self.local_vars[stmt.name] = self.local_count
                    self.local_count += 1
                self.instructions.append(Instruction(OpCode.STORE_VAR, idx))

        elif isinstance(stmt, ExpressionStatement):
            self.generate_expr(stmt.expression)
            self.instructions.append(Instruction(OpCode.POP))

        elif isinstance(stmt, IfStatement):
            self.generate_expr(stmt.condition)
            else_label = len(self.instructions)
            self.instructions.append(Instruction(OpCode.JUMP_IF_FALSE, 0))

            for s in stmt.then_branch.statements:
                self.generate_statement(s)

            if stmt.else_branch:
                end_label = len(self.instructions)
                self.instructions.append(Instruction(OpCode.JUMP, 0))
                else_target = len(self.instructions)

                for s in stmt.else_branch.statements:
                    self.generate_statement(s)

                end_target = len(self.instructions)
                self.instructions[else_label] = Instruction(OpCode.JUMP_IF_FALSE, else_target)
                self.instructions[end_label] = Instruction(OpCode.JUMP, end_target)
            else:
                self.instructions[else_label] = Instruction(OpCode.JUMP_IF_FALSE, len(self.instructions))

        elif isinstance(stmt, WhileStatement):
            loop_start = len(self.instructions)
            self.loop_stack.append({'start': loop_start, 'break': None})

            self.generate_expr(stmt.condition)
            loop_end = len(self.instructions)
            self.instructions.append(Instruction(OpCode.JUMP_IF_FALSE, 0))

            for s in stmt.body.statements:
                self.generate_statement(s)

            self.instructions.append(Instruction(OpCode.JUMP, loop_start))

            break_target = len(self.instructions)
            self.loop_stack.pop()

            self.instructions[loop_end] = Instruction(OpCode.JUMP_IF_FALSE, break_target)

            for i, instr in enumerate(self.instructions):
                if instr.opcode == OpCode.JUMP and instr.operand is None:
                    if i > loop_start and i < break_target:
                        pass

        elif isinstance(stmt, ForStatement):
            init_idx = self.local_vars.get(stmt.init.name, self.local_count)
            if stmt.init.name not in self.local_vars:
                self.local_vars[stmt.init.name] = self.local_count
                self.local_count += 1

            self.instructions.append(Instruction(OpCode.LOAD_CONST, self.add_constant(stmt.init.value.value)))
            self.instructions.append(Instruction(OpCode.STORE_VAR, init_idx))

            loop_start = len(self.instructions)
            self.loop_stack.append({'start': loop_start, 'break': None})

            self.generate_expr(stmt.condition)
            loop_end = len(self.instructions)
            self.instructions.append(Instruction(OpCode.JUMP_IF_FALSE, 0))

            for s in stmt.body.statements:
                self.generate_statement(s)

            self.generate_expr(stmt.update)
            self.instructions.append(Instruction(OpCode.POP))
            self.instructions.append(Instruction(OpCode.JUMP, loop_start))

            break_target = len(self.instructions)
            self.loop_stack.pop()

            self.instructions[loop_end] = Instruction(OpCode.JUMP_IF_FALSE, break_target)

        elif isinstance(stmt, BreakStatement):
            if self.loop_stack:
                target = len(self.instructions)
                self.loop_stack[-1]['break'] = target
                self.instructions.append(Instruction(OpCode.JUMP, 0))

        elif isinstance(stmt, ContinueStatement):
            if self.loop_stack:
                target = self.loop_stack[-1]['start']
                self.instructions.append(Instruction(OpCode.JUMP, target))

        elif isinstance(stmt, ReturnStatement):
            if stmt.value:
                self.generate_expr(stmt.value)
            else:
                self.instructions.append(Instruction(OpCode.LOAD_CONST, self.add_constant(None)))
            self.instructions.append(Instruction(OpCode.RETURN))

        elif isinstance(stmt, Block):
            for s in stmt.statements:
                self.generate_statement(s)

    def generate_expr(self, expr: ASTNode):
        if isinstance(expr, Literal):
            idx = self.add_constant(expr.value)
            self.instructions.append(Instruction(OpCode.LOAD_CONST, idx))

        elif isinstance(expr, Identifier):
            if not self.in_function:
                if expr.name in self.global_vars:
                    self.instructions.append(Instruction(OpCode.LOAD_GLOBAL, self.global_vars[expr.name]))
                elif expr.name in self.functions:
                    idx = self.add_constant(expr.name)
                    self.instructions.append(Instruction(OpCode.LOAD_CONST, idx))
                else:
                    raise ValueError(f"Unknown identifier: {expr.name}")
            else:
                if expr.name in self.local_vars:
                    self.instructions.append(Instruction(OpCode.LOAD_VAR, self.local_vars[expr.name]))
                elif expr.name in self.functions:
                    idx = self.add_constant(expr.name)
                    self.instructions.append(Instruction(OpCode.LOAD_CONST, idx))
                else:
                    raise ValueError(f"Unknown identifier: {expr.name}")

        elif isinstance(expr, BinaryOp):
            if expr.operator == '=':
                if isinstance(expr.left, Identifier):
                    self.generate_expr(expr.right)
                    if not self.in_function:
                        if expr.left.name in self.global_vars:
                            self.instructions.append(Instruction(OpCode.STORE_GLOBAL, self.global_vars[expr.left.name]))
                        else:
                            idx = self.global_count
                            self.global_vars[expr.left.name] = idx
                            self.global_count += 1
                            self.instructions.append(Instruction(OpCode.STORE_GLOBAL, idx))
                    else:
                        if expr.left.name in self.local_vars:
                            self.instructions.append(Instruction(OpCode.STORE_VAR, self.local_vars[expr.left.name]))
                        else:
                            idx = self.local_count
                            self.local_vars[expr.left.name] = idx
                            self.local_count += 1
                            self.instructions.append(Instruction(OpCode.STORE_VAR, idx))
                else:
                    raise ValueError("Invalid assignment target")
                return

            self.generate_expr(expr.left)
            self.generate_expr(expr.right)

            op_map = {
                '+': OpCode.ADD, '-': OpCode.SUB, '*': OpCode.MUL,
                '/': OpCode.DIV, '%': OpCode.MOD,
                '==': OpCode.EQ, '!=': OpCode.NEQ,
                '<': OpCode.LT, '>': OpCode.GT,
                '<=': OpCode.LE, '>=': OpCode.GE,
                '&&': OpCode.AND, '||': OpCode.OR,
            }
            self.instructions.append(Instruction(op_map[expr.operator]))

        elif isinstance(expr, UnaryOp):
            self.generate_expr(expr.operand)
            if expr.operator == '!':
                self.instructions.append(Instruction(OpCode.NOT))
            elif expr.operator == '-':
                self.instructions.append(Instruction(OpCode.LOAD_CONST, self.add_constant(-1)))
                self.instructions.append(Instruction(OpCode.MUL))

        elif isinstance(expr, CallExpr):
            for arg in expr.arguments:
                self.generate_expr(arg)

            if expr.name == 'print':
                self.instructions.append(Instruction(OpCode.PRINT))
            elif expr.name == 'input':
                self.instructions.append(Instruction(OpCode.INPUT))
            elif expr.name == 'len':
                self.instructions.append(Instruction(OpCode.LEN))
            elif expr.name in self.functions:
                self.instructions.append(Instruction(OpCode.CALL, expr.name))
            else:
                raise ValueError(f"Unknown function: {expr.name}")

        elif isinstance(expr, ArrayAccess):
            self.instructions.append(Instruction(OpCode.LOAD_VAR, self.local_vars.get(expr.name, -1)))
            self.generate_expr(expr.index)
            self.instructions.append(Instruction(OpCode.LOAD_ARRAY))

def generate_bytecode(program: Program) -> BytecodeProgram:
    return CodeGenerator().generate(program)
