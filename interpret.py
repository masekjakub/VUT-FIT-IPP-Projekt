import parse
import getopt
import sys
import error


class Interpret:
    inputFile = None

    def run(self):
        self.processArguments()
        parser = parse.Parser(self.inputFile)
        program = parser.run()
        self.execute(program)

    def processArguments(self):
        shortOpts = "hs:i:"
        longOpts = ["help", "source=", "input="]
        args = getopt.getopt(sys.argv[1:], shortOpts, longOpts)
        
        for opt, arg in args[0]:
            if opt in ("-h", "--help"):
                if not args.count() == 1:
                    sys.stderr.write(f"ERR: No arguments allowed while printing help.")
                    exit(error.wrongArguments)
                self.printHelp()
                exit(error.ok)
            elif opt in ("-s", "-i", "--source", "--input"):
                self.inputFile = arg

    def printHelp(self):
        print("IPP Interpret")
        print("")
        print("")
        print("")
        print("")
        print("")
    
    def execute(self, program:parse.XMLElements):
        executor = Executor()
        keys = sorted(program.getInstructions().keys())
        for index, key in enumerate(keys):
            if not index+1 == key:
                sys.stderr.write(f"ERR: Skipped one or more instructions.")
                exit(error.wrongXMLStructure)

            instruction = program.getInstruction(key)
            opcode = instruction.getOpcode()

            if opcode == "MOVE":
                pass
            elif opcode == "CREATEFRAME":
                pass
            elif opcode == "PUSHFRAME":
                pass
            elif opcode == "POPFRAME":
                pass
            elif opcode == "DEFVAR":
                pass
            elif opcode == "CALL":
                pass
            elif opcode == "RETURN":
                pass
            elif opcode == "PUSHS":
                pass
            elif opcode == "POPS":
                pass
            elif opcode == "ADD":
                pass
            elif opcode == "SUB":
                pass
            elif opcode == "MUL":
                pass
            elif opcode == "IDIV":
                pass
            elif opcode == "LT":
                pass
            elif opcode == "GT":
                pass
            elif opcode == "EQ":
                pass
            elif opcode == "AND":
                pass
            elif opcode == "OR":
                pass
            elif opcode == "NOT":
                pass
            elif opcode == "INT2CHAR":
                pass
            elif opcode == "STRI2INT":
                pass
            elif opcode == "READ":
                pass
            elif opcode == "WRITE":
                self.checkArgsCount(instruction, 1)
                executor.write(instruction)
            elif opcode == "CONCAT":
                pass
            elif opcode == "STRLEN":
                pass
            elif opcode == "GETCHAR":
                pass
            elif opcode == "SETCHAR":
                pass
            elif opcode == "TYPE":
                pass
            elif opcode == "LABEL":
                pass
            elif opcode == "JUMP":
                pass
            elif opcode == "JUMPIFEQ":
                pass
            elif opcode == "JUMPIFNEQ":
                pass
            elif opcode == "EXIT":
                pass
            elif opcode == "DPRINT":
                pass
            elif opcode == "BREAK":
                pass

    def checkArgsCount(self, instruction:parse.XMLInstruction, count):
        if not len(instruction.getArgumentsKeys()) == count:
            sys.stderr.write(f"ERR: Invalid count of arguments in {instruction.getOpcode()} instruction.")
            exit(error.semantics)

class Executor:
    symbols = {"int", "bool", "string"}
    def write(self, instruction:parse.XMLInstruction):
        arg = instruction.getArgument(1).getType()
        if arg in self.symbols:
            print(instruction.getArgument(1).getValue())
        else:
            # TODO: variable write
            pass

class Frame:
    GF = 1
    LF = 2
    TF = 3

    def __init__(self, frameType):
        self.frameType = frameType
        self.variables = {}
    
    def add(self, variable):
        pass

    def get(self, variable):
        pass

    def createFrame(self):
        pass

    def pushFrame(self):
        pass

    def popFrame(self):
        pass

class Stack:
    def __init__(self):
        self.stack = []

    def push(self, item):
        self.stack.append(item)

    def pop(self):
        return self.stack.pop()

    def top(self):
        return self.stack[-1]

    def isEmpty(self):
        return len(self.stack) == 0
    

if __name__ == "__main__":
    interpret = Interpret()
    interpret.run()
