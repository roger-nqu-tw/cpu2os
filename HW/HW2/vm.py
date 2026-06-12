from typing import List, Any, Dict, Callable
from dataclasses import dataclass
from codegen import BytecodeProgram, Instruction, OpCode, Function

@dataclass
class CallFrame:
    function: Function
    ip: int
    locals: List[Any]
    return_ip: int

class VirtualMachine:
    def __init__(self, program: BytecodeProgram):
        self.program = program
        self.stack: List[Any] = []
        self.call_stack: List[CallFrame] = []
        self.ip = 0
        self.globals: List[Any] = [None] * len(program.globals)

    def run(self):
        instructions = self.program.main

        while self.ip < len(instructions):
            instr = instructions[self.ip]

            if instr.opcode == OpCode.HALT:
                break

            elif instr.opcode == OpCode.LOAD_CONST:
                self.stack.append(self.program.constants[instr.operand])

            elif instr.opcode == OpCode.LOAD_VAR:
                if self.call_stack:
                    self.stack.append(self.call_stack[-1].locals[instr.operand])
                else:
                    raise ValueError(f"Cannot load from undefined variable")

            elif instr.opcode == OpCode.STORE_VAR:
                value = self.stack.pop()
                if self.call_stack:
                    self.call_stack[-1].locals[instr.operand] = value
                else:
                    raise ValueError("Cannot store to undefined variable")

            elif instr.opcode == OpCode.LOAD_GLOBAL:
                self.stack.append(self.globals[instr.operand])

            elif instr.opcode == OpCode.STORE_GLOBAL:
                value = self.stack.pop()
                self.globals[instr.operand] = value

            elif instr.opcode == OpCode.ADD:
                b = self.stack.pop()
                a = self.stack.pop()
                self.stack.append(self._add(a, b))

            elif instr.opcode == OpCode.SUB:
                b = self.stack.pop()
                a = self.stack.pop()
                self.stack.append(a - b)

            elif instr.opcode == OpCode.MUL:
                b = self.stack.pop()
                a = self.stack.pop()
                self.stack.append(a * b)

            elif instr.opcode == OpCode.DIV:
                b = self.stack.pop()
                a = self.stack.pop()
                if b == 0:
                    raise ValueError("Division by zero")
                self.stack.append(a / b)

            elif instr.opcode == OpCode.MOD:
                b = self.stack.pop()
                a = self.stack.pop()
                self.stack.append(a % b)

            elif instr.opcode == OpCode.EQ:
                b = self.stack.pop()
                a = self.stack.pop()
                self.stack.append(a == b)

            elif instr.opcode == OpCode.NEQ:
                b = self.stack.pop()
                a = self.stack.pop()
                self.stack.append(a != b)

            elif instr.opcode == OpCode.LT:
                b = self.stack.pop()
                a = self.stack.pop()
                self.stack.append(a < b)

            elif instr.opcode == OpCode.GT:
                b = self.stack.pop()
                a = self.stack.pop()
                self.stack.append(a > b)

            elif instr.opcode == OpCode.LE:
                b = self.stack.pop()
                a = self.stack.pop()
                self.stack.append(a <= b)

            elif instr.opcode == OpCode.GE:
                b = self.stack.pop()
                a = self.stack.pop()
                self.stack.append(a >= b)

            elif instr.opcode == OpCode.AND:
                b = self.stack.pop()
                a = self.stack.pop()
                self.stack.append(a and b)

            elif instr.opcode == OpCode.OR:
                b = self.stack.pop()
                a = self.stack.pop()
                self.stack.append(a or b)

            elif instr.opcode == OpCode.NOT:
                a = self.stack.pop()
                self.stack.append(not a)

            elif instr.opcode == OpCode.JUMP:
                self.ip = instr.operand - 1

            elif instr.opcode == OpCode.JUMP_IF_FALSE:
                cond = self.stack.pop()
                if not cond:
                    self.ip = instr.operand - 1

            elif instr.opcode == OpCode.JUMP_IF_TRUE:
                cond = self.stack.pop()
                if cond:
                    self.ip = instr.operand - 1

            elif instr.opcode == OpCode.CALL:
                func_name = instr.operand
                func = self.program.functions[func_name]

                args = []
                for _ in func.params:
                    args.append(self.stack.pop())
                args.reverse()

                call_frame = CallFrame(
                    function=func,
                    ip=0,
                    locals=args + [None] * (func.local_vars - len(args)),
                    return_ip=self.ip + 1
                )

                self.call_stack.append(call_frame)
                instructions = func.instructions
                self.ip = -1

            elif instr.opcode == OpCode.RETURN:
                return_value = self.stack.pop() if self.stack else None

                if self.call_stack:
                    frame = self.call_stack.pop()
                    instructions = self.program.main if not self.call_stack else self.call_stack[-1].function.instructions
                    self.ip = frame.return_ip - 1

                    if self.call_stack:
                        self.call_stack[-1].locals.append(return_value)
                    else:
                        self.stack.append(return_value)
                else:
                    self.stack.append(return_value)

            elif instr.opcode == OpCode.POP:
                if self.stack:
                    self.stack.pop()

            elif instr.opcode == OpCode.LOAD_ARRAY:
                index = self.stack.pop()
                arr = self.stack.pop()
                if isinstance(arr, list):
                    self.stack.append(arr[index])
                else:
                    raise ValueError(f"Cannot index non-array type")

            elif instr.opcode == OpCode.STORE_ARRAY:
                value = self.stack.pop()
                index = self.stack.pop()
                arr = self.stack.pop()
                if isinstance(arr, list):
                    arr[index] = value
                else:
                    raise ValueError(f"Cannot index non-array type")

            elif instr.opcode == OpCode.ARRAY_LEN:
                arr = self.stack.pop()
                self.stack.append(len(arr))

            elif instr.opcode == OpCode.PRINT:
                value = self.stack.pop()
                if isinstance(value, list):
                    print(value)
                else:
                    print(value)

            elif instr.opcode == OpCode.INPUT:
                value = input()
                self.stack.append(value)

            elif instr.opcode == OpCode.LEN:
                value = self.stack.pop()
                if isinstance(value, str):
                    self.stack.append(len(value))
                elif isinstance(value, list):
                    self.stack.append(len(value))
                else:
                    raise ValueError(f"len() not supported for type {type(value)}")

            self.ip += 1

    def _add(self, a: Any, b: Any) -> Any:
        if isinstance(a, str) or isinstance(b, str):
            return str(a) + str(b)
        return a + b

def execute(program: BytecodeProgram):
    vm = VirtualMachine(program)
    vm.run()

if __name__ == '__main__':
    import sys
    from lexer import lex
    from voxast import parse
    from codegen import generate_bytecode

    if len(sys.argv) < 2:
        print("Usage: python vm.py <source_file.vox>")
        sys.exit(1)

    with open(sys.argv[1], 'r') as f:
        source = f.read()

    tokens = lex(source)
    program = parse(tokens)
    bytecode = generate_bytecode(program)
    execute(bytecode)
