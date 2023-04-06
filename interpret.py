import parse
import getopt
import sys
import error


class Interpret:
    sourceFile = None
    inputFile = None
    order = 0

    def run(self):
        self.processArguments()
        parser = parse.Parser(self.sourceFile)
        program = parser.run()
        self.execute(program)

    # Process arguments from command line
    def processArguments(self):
        shortOpts = "hs:i:"
        longOpts = ["help", "source=", "input="]
        args = getopt.getopt(sys.argv[1:], shortOpts, longOpts)
        
        for opt, arg in args[0]:
            if opt in ("-h", "--help"):
                if len(sys.argv) != 2:
                    sys.stderr.write(f"ERR: No arguments allowed while printing help.")
                    exit(error.wrongArguments)
                self.printHelp()
                exit(error.ok)
            elif opt in ("-s", "--source"):
                self.sourceFile = arg
            elif opt in ("-i", "--input"):
                self.inputFile = arg
        
        if self.sourceFile is None and self.inputFile is None:
            sys.stderr.write(f"ERR: At least one file must be given.")
            exit(error.wrongInputFile)
        
        if self.inputFile is not None:
            try:
                self.inputFile = open(self.inputFile, "r")
            except IOError:
                sys.stderr.write("ERR: File does not appear to exist.")
                exit(error.wrongInputFile)
        else:
            self.inputFile = sys.stdin


    def printHelp(self):
        print("IPP Interpret")
        print("")
        print("")
        print("")
        print("")
        print("")
    
    def setInstructionsKey(self, order):
        self.instructionsKey = self.instructionsKeysList.index(order)
        self.order = self.instructionsKeysList[self.instructionsKey]
        self.instructionsKey += 1

    def getOrder(self):
        return self.order
    
    def getInstructionCount(self):
        return self.instructionCount

    def labelFilter(self, items):
        if items[1].getOpcode() != "LABEL":
            return False
        return True
    
    # Execute program
    def execute(self, program:parse.XMLElements):
        executor = Executor()
        instructions = program.getInstructions()
        if len(instructions) == 0:
            exit(error.ok)
        maxOrder = max(instructions)
        self.instructionCount = 0
        self.instructionsKeysList = sorted(list(instructions.keys()))
        self.instructionsKey = 0
        self.order = 0

        # Save all labels
        for key in instructions:
            instruction = program.getInstruction(key)
            if instruction.getOpcode() == "LABEL":
                labelName = instruction.getArgument(1).getData().getValue()
                if executor.labels.get(labelName) is not None:
                    sys.stderr.write(f"ERR: Label {labelName} already exists.")
                    exit(error.semantics)
                executor.labels[labelName] = key

        # Execute instructions
        while self.order != maxOrder:
            self.order = self.instructionsKeysList[self.instructionsKey]
            self.instructionsKey +=1
            self.instructionCount += 1

            instruction = program.getInstruction(self.order)
            opcode = instruction.getOpcode()
            #sys.stderr.write(f"{self.order}: {opcode} {instruction.getArgumentsKeys()}\n")

            # Try to execute instruction
            try:
                getattr(executor, opcode)(instruction)
            except AttributeError:
                sys.stderr.write(f"ERR: Error while executing opcode {opcode}.")
                exit(error.wrongXMLStructure)


class Frame:
    GF = 1
    LF = 2
    TF = 3

    def __init__(self, frameType):
        self.frameType = frameType
        self.variables = {}

    # Add variable to frame
    def addVariable(self, variable:parse.Variable):
        if self.variables.get(variable.getName()) is not None:
            sys.stderr.write(f"ERR: Variable {variable.getName()} already exists.")
            exit(error.semantics)

        self.variables[variable.getName()] = variable

    # Get variable from frame
    def getVariable(self, variableName:str) -> parse.Variable:
        if self.variables.get(variableName) is None:
            sys.stderr.write(f"ERR: Variable {variableName} does not exist.")
            exit(error.notExistingVariable)
    
        return self.variables[variableName]

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
    
class Executor:
    symbolList = {"int", "bool", "string", "nil", "float", "var"}
    labels = {}
    callStack = Stack()
    dataStack = Stack()

    def __init__(self):
        self.stack = Stack()
        self.localFrameStack = Stack()
        self.globalFrame = Frame(Frame.GF)
        self.tempFrame = None

    # MOVE instruction
    def MOVE(self, instruction:parse.XMLInstruction):
        arg1 = instruction.getArgument(1)
        arg2 = instruction.getArgument(2)
        self.checkArgCount(instruction, 2)

        if arg1.getType() != "var":
            sys.stderr.write(f"ERR: Invalid argument type in {instruction.getOpcode()} instruction.")
            exit(error.wrongType)
        
        variableElement = arg1.getData()
        frame = self.getFrame(variableElement.getFrameName())
        variable = frame.getVariable(variableElement.getName())
        
        valToAssign = self.getRealValue(arg2)
        typeToAssign = self.getRealType(arg2)

        variable.setValue(self.convertToType(valToAssign, typeToAssign))
        variable.setType(typeToAssign)

    # CREATEFRAME instruction
    def CREATEFRAME(self, instruction:parse.XMLInstruction):
        self.checkArgCount(instruction, 0)
        self.tempFrame = Frame(Frame.TF)

    # PUSHFRAME instruction
    def PUSHFRAME(self, instruction:parse.XMLInstruction):
        self.checkArgCount(instruction, 0)
        if self.tempFrame == None:
            sys.stderr.write(f"ERR: Temp frame is not defined.")
            exit(error.notExistingFrame)

        self.localFrameStack.push(self.tempFrame)
        self.tempFrame = None

    # POPFRAME instruction
    def POPFRAME(self, instruction:parse.XMLInstruction):
        self.checkArgCount(instruction, 0)
        if self.localFrameStack.isEmpty():
            sys.stderr.write(f"ERR: Local frame stack is empty.")
            exit(error.notExistingFrame)

        self.tempFrame = self.localFrameStack.pop()

    # DEFVAR instruction
    def DEFVAR(self, instruction:parse.XMLInstruction):
        self.checkArgCount(instruction, 1)
        arg = instruction.getArgument(1)
        if arg.getType() != "var":
            sys.stderr.write(f"ERR: Invalid argument type in {instruction.getOpcode()} instruction.")
            exit(error.wrongType)

        varElement = instruction.getArgument(1).getData()
        frame = self.getFrame(varElement.getFrameName())
        var = parse.Variable(varElement.getName(), None)
        frame.addVariable(var)

    # CALL instruction
    def CALL(self, instruction:parse.XMLInstruction):
        self.checkArgCount(instruction, 1)
        arg = instruction.getArgument(1)
        if arg.getType() != "label":
            sys.stderr.write(f"ERR: Invalid argument type in {instruction.getOpcode()} instruction.")
            exit(error.wrongType)

        self.callStack.push(interpret.getOrder())
        self.JUMP(instruction)

    # RETURN instruction
    def RETURN(self, instruction:parse.XMLInstruction):
        self.checkArgCount(instruction, 0)
        if self.callStack.isEmpty():
            sys.stderr.write(f"ERR: Call stack is empty.")
            exit(error.missingValue)

        interpret.setInstructionsKey(self.callStack.pop())

    # PUSHS instruction
    def PUSHS(self, instruction:parse.XMLInstruction):
        self.checkArgCount(instruction, 1)
        arg = instruction.getArgument(1)
        if arg.getType() not in self.symbolList:
            sys.stderr.write(f"ERR: Invalid argument type in {instruction.getOpcode()} instruction.")
            exit(error.wrongType)
        
        if arg.getType() == "var":
            frame = self.getFrame(arg.getData().getFrameName())
            var = frame.getVariable(arg.getData().getName())
            if not var.isSet():
                sys.stderr.write(f"ERR: Variable {var.getName()} is not set.")
                exit(error.missingValue)
            self.dataStack.push(var)

        self.dataStack.push(arg)

    # POPS instruction
    def POPS(self, instruction:parse.XMLInstruction):
        self.checkArgCount(instruction, 1)
        arg = instruction.getArgument(1)
        if arg.getType() != "var":
            sys.stderr.write(f"ERR: Invalid argument type in {instruction.getOpcode()} instruction.")
            exit(error.wrongType)

        if self.dataStack.isEmpty():
            sys.stderr.write(f"ERR: Data stack is empty.")
            exit(error.missingValue)

        frame = self.getFrame(arg.getData().getFrameName())
        var = frame.getVariable(arg.getData().getName())
        data = self.dataStack.pop()

        var.setValue(self.getRealValue(data))
        var.setType(self.getRealType(data))


    # ADD instruction
    def ADD(self, instruction:parse.XMLInstruction):
        self.checkArgCount(instruction, 3)
        arg1 = instruction.getArgument(1)
        arg2 = instruction.getArgument(2)
        arg3 = instruction.getArgument(3)

        if arg1.getType() != "var" or self.getRealType(arg2) != "int" or self.getRealType(arg3) != "int":
            sys.stderr.write(f"ERR: Invalid argument type in {instruction.getOpcode()} instruction.")
            exit(error.wrongType)
        
        try:
            val1 = int(self.getRealValue(arg2))
            val2 = int(self.getRealValue(arg3))
        except ValueError:
            sys.stderr.write(f"ERR: Invalid argument type in {instruction.getOpcode()} instruction.")
            exit(error.wrongXMLStructure)

        frame = self.getFrame(arg1.getData().getFrameName())
        var = frame.getVariable(arg1.getData().getName())
        var.setValue(val1 + val2)
        var.setType("int")

    # SUB instruction
    def SUB(self, instruction:parse.XMLInstruction):
        self.checkArgCount(instruction, 3)
        arg1 = instruction.getArgument(1)
        arg2 = instruction.getArgument(2)
        arg3 = instruction.getArgument(3)

        if arg1.getType() != "var" or self.getRealType(arg2) != "int" or self.getRealType(arg3) != "int":
            sys.stderr.write(f"ERR: Invalid argument type in {instruction.getOpcode()} instruction.")
            exit(error.wrongType)

        val1 = int(self.getRealValue(arg2))
        val2 = int(self.getRealValue(arg3))
        frame = self.getFrame(arg1.getData().getFrameName())
        var = frame.getVariable(arg1.getData().getName())
        var.setValue(val1 - val2)
        var.setType("int")

    # MUL instruction
    def MUL(self, instruction:parse.XMLInstruction):
        self.checkArgCount(instruction, 3)
        arg1 = instruction.getArgument(1)
        arg2 = instruction.getArgument(2)
        arg3 = instruction.getArgument(3)

        if arg1.getType() != "var" or self.getRealType(arg2) != "int" or self.getRealType(arg3) != "int":
            sys.stderr.write(f"ERR: Invalid argument type in {instruction.getOpcode()} instruction.")
            exit(error.wrongType)

        val1 = int(self.getRealValue(arg2))
        val2 = int(self.getRealValue(arg3))
        frame = self.getFrame(arg1.getData().getFrameName())
        var = frame.getVariable(arg1.getData().getName())
        var.setValue(val1 * val2)
        var.setType("int")

    # IDIV instruction
    def IDIV(self, instruction:parse.XMLInstruction):
        self.checkArgCount(instruction, 3)
        arg1 = instruction.getArgument(1)
        arg2 = instruction.getArgument(2)
        arg3 = instruction.getArgument(3)

        if arg1.getType() != "var" or self.getRealType(arg2) != "int" or self.getRealType(arg3) != "int":
            sys.stderr.write(f"ERR: Invalid argument type in {instruction.getOpcode()} instruction.")
            exit(error.wrongType)

        val1 = int(self.getRealValue(arg2))
        val2 = int(self.getRealValue(arg3))

        if val2 == 0:
            sys.stderr.write(f"ERR: Division by zero.")
            exit(error.wrongOperandValue)

        frame = self.getFrame(arg1.getData().getFrameName())
        var = frame.getVariable(arg1.getData().getName())
        var.setValue(val1 // val2)
        var.setType("int")

    # LT instruction
    def LT(self, instruction:parse.XMLInstruction):
        self.checkArgCount(instruction, 3)
        arg1 = instruction.getArgument(1)
        arg2 = instruction.getArgument(2)
        arg3 = instruction.getArgument(3)

        if arg1.getType() != "var" or self.getRealType(arg2) != self.getRealType(arg3) or self.getRealType(arg2) not in ["int", "string", "bool"] or self.getRealType(arg3) not in ["int", "string", "bool"]:
            sys.stderr.write(f"ERR: Invalid argument type in {instruction.getOpcode()} instruction.")
            exit(error.wrongType)

        val1 = self.convertToType(self.getRealValue(arg2), self.getRealType(arg2))
        val2 = self.convertToType(self.getRealValue(arg3), self.getRealType(arg3))

        frame = self.getFrame(arg1.getData().getFrameName())
        var = frame.getVariable(arg1.getData().getName())
        var.setValue(val1 < val2)
        var.setType("bool")


    # GT instruction
    def GT(self, instruction:parse.XMLInstruction):
        self.checkArgCount(instruction, 3)
        arg1 = instruction.getArgument(1)
        arg2 = instruction.getArgument(2)
        arg3 = instruction.getArgument(3)

        if arg1.getType() != "var" or self.getRealType(arg2) != self.getRealType(arg3) or self.getRealType(arg2) not in ["int", "string", "bool"] or self.getRealType(arg3) not in ["int", "string", "bool"]:
            sys.stderr.write(f"ERR: Invalid argument type in {instruction.getOpcode()} instruction.")
            exit(error.wrongType)

        val1 = self.convertToType(self.getRealValue(arg2), self.getRealType(arg2))
        val2 = self.convertToType(self.getRealValue(arg3), self.getRealType(arg3))

        frame = self.getFrame(arg1.getData().getFrameName())
        var = frame.getVariable(arg1.getData().getName())
        var.setValue(val1 > val2)
        var.setType("bool")

    # EQ instruction
    def EQ(self, instruction:parse.XMLInstruction):
        self.checkArgCount(instruction, 3)
        arg1 = instruction.getArgument(1)
        arg2 = instruction.getArgument(2)
        arg3 = instruction.getArgument(3)

        if arg1.getType() != "var" or (self.getRealType(arg2) != self.getRealType(arg3) and self.getRealType(arg2) != "nil" and self.getRealType(arg3) != "nil"):
            sys.stderr.write(f"ERR: Invalid argument type in {instruction.getOpcode()} instruction.")
            exit(error.wrongType)

        val1 = self.convertToType(self.getRealValue(arg2), self.getRealType(arg2))
        val2 = self.convertToType(self.getRealValue(arg3), self.getRealType(arg3))

        frame = self.getFrame(arg1.getData().getFrameName())
        var = frame.getVariable(arg1.getData().getName())
        var.setValue(val1 == val2)
        var.setType("bool")

    # AND instruction
    def AND(self, instruction:parse.XMLInstruction):
        self.checkArgCount(instruction, 3)
        arg1 = instruction.getArgument(1)
        arg2 = instruction.getArgument(2)
        arg3 = instruction.getArgument(3)

        if arg1.getType() != "var" or self.getRealType(arg2) != "bool" or self.getRealType(arg3) != "bool":
            sys.stderr.write(f"ERR: Invalid argument type in {instruction.getOpcode()} instruction.")
            exit(error.wrongType)

        val1 = self.convertToType(self.getRealValue(arg2), self.getRealType(arg2))
        val2 = self.convertToType(self.getRealValue(arg3), self.getRealType(arg3))

        frame = self.getFrame(arg1.getData().getFrameName())
        var = frame.getVariable(arg1.getData().getName())
        var.setValue(val1 and val2)
        var.setType("bool")

    # OR instruction
    def OR(self, instruction:parse.XMLInstruction):
        self.checkArgCount(instruction, 3)
        arg1 = instruction.getArgument(1)
        arg2 = instruction.getArgument(2)
        arg3 = instruction.getArgument(3)

        if arg1.getType() != "var" or self.getRealType(arg2) != "bool" or self.getRealType(arg3) != "bool":
            sys.stderr.write(f"ERR: Invalid argument type in {instruction.getOpcode()} instruction.")
            exit(error.wrongType)

        val1 = self.convertToType(self.getRealValue(arg2), self.getRealType(arg2))
        val2 = self.convertToType(self.getRealValue(arg3), self.getRealType(arg3))

        frame = self.getFrame(arg1.getData().getFrameName())
        var = frame.getVariable(arg1.getData().getName())
        var.setValue(val1 or val2)
        var.setType("bool")

    # NOT instruction
    def NOT(self, instruction:parse.XMLInstruction):
        self.checkArgCount(instruction, 2)
        arg1 = instruction.getArgument(1)
        arg2 = instruction.getArgument(2)

        if arg1.getType() != "var" or self.getRealType(arg2) != "bool":
            sys.stderr.write(f"ERR: Invalid argument type in {instruction.getOpcode()} instruction.")
            exit(error.wrongType)

        val1 = self.convertToType(self.getRealValue(arg2), self.getRealType(arg2))

        frame = self.getFrame(arg1.getData().getFrameName())
        var = frame.getVariable(arg1.getData().getName())
        var.setValue(not val1)
        var.setType("bool")

    # INT2CHAR instruction
    def INT2CHAR(self, instruction:parse.XMLInstruction):
        self.checkArgCount(instruction, 2)
        arg1 = instruction.getArgument(1)
        arg2 = instruction.getArgument(2)

        if arg1.getType() != "var" or self.getRealType(arg2) != "int":
            sys.stderr.write(f"ERR: Invalid argument type in {instruction.getOpcode()} instruction.")
            exit(error.wrongType)

        val1 = self.convertToType(self.getRealValue(arg2), self.getRealType(arg2))

        frame = self.getFrame(arg1.getData().getFrameName())
        var = frame.getVariable(arg1.getData().getName())
        try:
            var.setValue(chr(val1))
        except ValueError:
            sys.stderr.write(f"ERR: Invalid value in {instruction.getOpcode()} instruction.")
            exit(error.invalidString)
        
        var.setType("string")

    # STRI2INT instruction
    def STRI2INT(self, instruction:parse.XMLInstruction):
        self.checkArgCount(instruction, 3)
        arg1 = instruction.getArgument(1)
        arg2 = instruction.getArgument(2)
        arg3 = instruction.getArgument(3)

        if arg1.getType() != "var" or self.getRealType(arg2) != "string" or self.getRealType(arg3) != "int":
            sys.stderr.write(f"ERR: Invalid argument type in {instruction.getOpcode()} instruction.")
            exit(error.wrongType)

        val1 = self.convertToType(self.getRealValue(arg2), self.getRealType(arg2))
        val2 = self.convertToType(self.getRealValue(arg3), self.getRealType(arg3))

        frame = self.getFrame(arg1.getData().getFrameName())
        var = frame.getVariable(arg1.getData().getName())

        if val2 < 0 or val2 >= len(val1):
            sys.stderr.write(f"ERR: Invalid value in {instruction.getOpcode()} instruction.")
            exit(error.invalidString)

        var.setValue(ord(val1[val2]))
        var.setType("int")


    # READ instruction
    def READ(self, instruction:parse.XMLInstruction):
        self.checkArgCount(instruction, 2)
        arg1 = instruction.getArgument(1)
        arg2 = instruction.getArgument(2)

        if arg1.getType() != "var" or arg2.getType() != "type":
            sys.stderr.write(f"ERR: Invalid argument type in {instruction.getOpcode()} instruction.")
            exit(error.wrongType)

        frame = self.getFrame(arg1.getData().getFrameName())
        var = frame.getVariable(arg1.getData().getName())

        try:
            val = interpret.inputFile.readline().strip()
        except EOFError:
            var.setValue(val)
            var.setType(arg2.getData().getValue())
        
        if arg2.getData().getValue() == "bool":
            val = val.lower()
        
        try:
            val = self.convertToType(val, arg2.getData().getValue())
        except:
            var.setValue("nil")
            var.setType("nil")
            return

        var.setValue(val)
        var.setType(arg2.getData().getValue())

    # WRITE instruction
    def WRITE(self, instruction:parse.XMLInstruction):
        self.checkArgCount(instruction, 1)
        arg1 = instruction.getArgument(1)
        string = self.getRealValue(arg1)
        string = self.convertToWriteType(string, self.getRealType(arg1))
        print(string, end="")
    
    # CONCAT instruction
    def CONCAT(self, instruction:parse.XMLInstruction):
        self.checkArgCount(instruction, 3)
        arg1 = instruction.getArgument(1)
        arg2 = instruction.getArgument(2)
        arg3 = instruction.getArgument(3)

        if arg1.getType() != "var" or self.getRealType(arg2) != "string" or self.getRealType(arg3) != "string":
            sys.stderr.write(f"ERR: Invalid argument type in {instruction.getOpcode()} instruction.")
            exit(error.wrongType)

        val1 = self.convertToType(self.getRealValue(arg2), self.getRealType(arg2))
        val2 = self.convertToType(self.getRealValue(arg3), self.getRealType(arg3))

        frame = self.getFrame(arg1.getData().getFrameName())
        var = frame.getVariable(arg1.getData().getName())
        var.setValue(val1 + val2)
        var.setType("string")

    # STRLEN instruction
    def STRLEN(self, instruction:parse.XMLInstruction):
        self.checkArgCount(instruction, 2)
        arg1 = instruction.getArgument(1)
        arg2 = instruction.getArgument(2)

        if arg1.getType() != "var" or self.getRealType(arg2) != "string":
            sys.stderr.write(f"ERR: Invalid argument type in {instruction.getOpcode()} instruction.")
            exit(error.wrongType)

        frame = self.getFrame(arg1.getData().getFrameName())
        var = frame.getVariable(arg1.getData().getName())
        var.setValue(len(self.getRealValue(arg2)))
        var.setType("int")

    # GETCHAR instruction
    def GETCHAR(self, instruction:parse.XMLInstruction):
        self.checkArgCount(instruction, 3)
        arg1 = instruction.getArgument(1)
        arg2 = instruction.getArgument(2)
        arg3 = instruction.getArgument(3)

        if arg1.getType() != "var" or self.getRealType(arg2) != "string" or self.getRealType(arg3) != "int":
            sys.stderr.write(f"ERR: Invalid argument type in {instruction.getOpcode()} instruction.")
            exit(error.wrongType)

        string = self.convertToType(self.getRealValue(arg2), self.getRealType(arg2))
        index = self.convertToType(self.getRealValue(arg3), self.getRealType(arg3))

        frame = self.getFrame(arg1.getData().getFrameName())
        var = frame.getVariable(arg1.getData().getName())

        if index < 0 or index >= len(string):
            sys.stderr.write(f"ERR: Invalid index value in {instruction.getOpcode()} instruction.")
            exit(error.invalidString)

        var.setValue(string[index])
        var.setType("string")

    # SETCHAR instruction
    def SETCHAR(self, instruction:parse.XMLInstruction):
        self.checkArgCount(instruction, 3)
        arg1 = instruction.getArgument(1)
        arg2 = instruction.getArgument(2)
        arg3 = instruction.getArgument(3)

        if self.getRealType(arg1) != "string" or self.getRealType(arg2) != "int" or self.getRealType(arg3) != "string":
            sys.stderr.write(f"ERR: Invalid argument type in {instruction.getOpcode()} instruction.")
            exit(error.wrongType)
        
        stringTo = self.convertToType(self.getRealValue(arg1), self.getRealType(arg1))
        index = self.convertToType(self.getRealValue(arg2), self.getRealType(arg2))
        stringFrom = self.convertToType(self.getRealValue(arg3), self.getRealType(arg3))

        if len(stringTo) <= index or len(stringFrom) == 0 or index < 0:
            sys.stderr.write(f"ERR: Invalid index value in {instruction.getOpcode()} instruction.")
            exit(error.invalidString)

        frame = self.getFrame(arg1.getData().getFrameName())
        var = frame.getVariable(arg1.getData().getName())
        
        stringTo = stringTo[:index] + stringFrom[0] + stringTo[index + 1:]
        
        var.setValue(stringTo)
        var.setType("string")

    # TYPE instruction
    def TYPE(self, instruction:parse.XMLInstruction):
        self.checkArgCount(instruction, 2)
        arg1 = instruction.getArgument(1)
        arg2 = instruction.getArgument(2)

        if arg1.getType() != "var":
            sys.stderr.write(f"ERR: Invalid argument type in {instruction.getOpcode()} instruction.")
            exit(error.wrongType)

        frame = self.getFrame(arg1.getData().getFrameName())
        var = frame.getVariable(arg1.getData().getName())

        if arg2.getType() == "var":
            frame = self.getFrame(arg2.getData().getFrameName())
            type = frame.getVariable(arg2.getData().getName()).getType()
        else: 
            type = arg2.getType()
    
        if type is None:
            var.setValue("")
        else:
            var.setValue(type)
        var.setType("string")

    # LABEL instruction
    def LABEL(self, instruction:parse.XMLInstruction):
        self.checkArgCount(instruction, 1)

    # JUMP instruction
    def JUMP(self, instruction:parse.XMLInstruction):
        self.checkArgCount(instruction, 1)
        labelName = instruction.getArgument(1).getData().getValue()
        if self.labels.get(labelName) is None:
            sys.stderr.write(f"ERR: Label {labelName} does not exist.")
            exit(error.semantics)
        
        labelOrder = self.labels[labelName]
        interpret.setInstructionsKey(labelOrder)

    # JUMPIFEQ instruction
    def JUMPIFEQ(self, instruction:parse.XMLInstruction):
        self.checkArgCount(instruction, 3)
        arg1 = instruction.getArgument(1)
        arg2 = instruction.getArgument(2)
        arg3 = instruction.getArgument(3)

        if arg1.getType() != "label" or (self.getRealType(arg2) != self.getRealType(arg3) and self.getRealType(arg2) != "nil" and self.getRealType(arg3) != "nil"):
            sys.stderr.write(f"ERR: Invalid argument type in {instruction.getOpcode()} instruction.")
            exit(error.wrongType)

        if arg1.getData().getValue() not in self.labels:
            sys.stderr.write(f"ERR: Label {arg1.getData().getValue()} does not exist.")
            exit(error.semantics)

        val1 = self.convertToType(self.getRealValue(arg2), self.getRealType(arg2))
        val2 = self.convertToType(self.getRealValue(arg3), self.getRealType(arg3))
  
        if val1 == val2:
            labelName = arg1.getData().getValue()
            if self.labels.get(labelName) is None:
                sys.stderr.write(f"ERR: Label {labelName} does not exist.")
                exit(error.semantics)
            
            labelOrder = self.labels[labelName]
            interpret.setInstructionsKey(labelOrder)
        

    # JUMPIFNEQ instruction
    def JUMPIFNEQ(self, instruction:parse.XMLInstruction):
        self.checkArgCount(instruction, 3)
        arg1 = instruction.getArgument(1)
        arg2 = instruction.getArgument(2)
        arg3 = instruction.getArgument(3)

        if arg1.getType() != "label" or (self.getRealType(arg2) != self.getRealType(arg3) and self.getRealType(arg2) != "nil" and self.getRealType(arg3) != "nil"):
            sys.stderr.write(f"ERR: Invalid argument type in {instruction.getOpcode()} instruction.")
            exit(error.wrongType)

        if arg1.getData().getValue() not in self.labels:
            sys.stderr.write(f"ERR: Label {arg1.getData().getValue()} does not exist.")
            exit(error.semantics)
        val1 = self.convertToType(self.getRealValue(arg2), self.getRealType(arg2))
        val2 = self.convertToType(self.getRealValue(arg3), self.getRealType(arg3))
  
        if val1 != val2:
            labelName = arg1.getData().getValue()
            if self.labels.get(labelName) is None:
                sys.stderr.write(f"ERR: Label {labelName} does not exist.")
                exit(error.semantics)
            
            labelOrder = self.labels[labelName]
            interpret.setInstructionsKey(labelOrder)

    # EXIT instruction
    def EXIT(self, instruction:parse.XMLInstruction):
        self.checkArgCount(instruction, 1)
        arg1 = instruction.getArgument(1)

        if self.getRealType(arg1) != "int":
            sys.stderr.write(f"ERR: Invalid argument type in {instruction.getOpcode()} instruction.")
            exit(error.wrongType)
        
        exitCode = self.convertToType(self.getRealValue(arg1), self.getRealType(arg1))

        if exitCode < 0 or exitCode > 49:
            sys.stderr.write(f"ERR: Invalid exit code in {instruction.getOpcode()} instruction.")
            exit(error.wrongOperandValue)

        exit(exitCode)

    # DPRINT instruction
    def DPRINT(self, instruction:parse.XMLInstruction):
        arg = instruction.getArgument(1)
        sys.stderr.write(self.getRealValue(arg))

    # BREAK instruction
    def BREAK(self, instruction:parse.XMLInstruction):
        print("Current instruction order: ", interpret.getOrder())
        print("Instruction count: ", interpret.getInstructionCount())

        print("Global frame: ")
        for key in self.getFrame("GF").variables.keys():
            print(f"    {key} = {self.getFrame('GF').variables[key].getValue()}")

        if self.tempFrame is not None:
            print("Temporary frame: ")
            for key in self.getFrame("TF").variables.keys():
                print(f"    {key} = {self.getFrame('TF').variables[key].getValue()}")
        else:
            print("Temporary frame: None")

        if self.localFrameStack.isEmpty() == 0:
            print("Local frame: ")
            for key in self.getFrame("LF").variables.keys():
                print(f"    {key} = {self.getFrame('LF').variables[key].getValue()}")
        else:
            print("Local frame: None")
        
        print("Data stack: ") 
        while self.dataStack.isEmpty() == 0:
            data:parse.XMLArgument = self.dataStack.pop()
            print(f"    {data.getData().getValue()}")
            


    ## EXECUTOR HELPERS ##
    def getFrame(self, frameName:str) -> Frame:
        if frameName == "GF":
            self.ensureFrameExists(self.globalFrame)
            return self.globalFrame
        elif frameName == "LF":
            if self.localFrameStack.isEmpty() == 1:
                sys.stderr.write(f"ERR: Local frame is not defined.")
                exit(error.notExistingFrame)
            localFrame = self.localFrameStack.top()
            return localFrame
        elif frameName == "TF":
            self.ensureFrameExists(self.tempFrame)
            return self.tempFrame
        else:
            sys.stderr.write(f"ERR: Invalid frame name {frameName}.")
            exit(error.notExistingFrame)

    # Check if instruction has correct count of arguments
    def checkArgCount(self, instruction:parse.XMLInstruction, count):
        if not len(instruction.getArgumentsKeys()) == count:
            sys.stderr.write(f"ERR: Invalid count of arguments in {instruction.getOpcode()} instruction.")
            exit(error.wrongXMLStructure)

    # Check if frame exists
    def ensureFrameExists(self, frame):
        if frame == None:
            sys.stderr.write(f"ERR: Frame is not defined.")
            exit(error.notExistingFrame)

    def getRealValue(self, argument:parse.XMLArgument) -> str:
        if argument.getType() == "var":
            frame = self.getFrame(argument.getData().getFrameName())
            var = frame.getVariable(argument.getData().getName())
            value = var.getValue()
            return value
        else:
            return argument.getData().getValue()
        
    def getRealType(self, argument:parse.XMLArgument) -> str:
        if argument.getType() == "var":
            frame = self.getFrame(argument.getData().getFrameName())
            type = frame.getVariable(argument.getData().getName()).getType()
            if type is None:
                sys.stderr.write(f"ERR: Variable {argument.getData().getName()} is not set.")
                exit(error.missingValue)
            return type
        else: 
            return argument.getData().getType()
    
    def boolToInt(self, value:str) -> int:
        if type(value) == int:
            return value
        if value == "true":
            return 1
        else:
            return 0
    
    def intToBool(self, value:int) -> str:
        if value == 1:
            return "true"
        else:
            return "false"
    
    def convertToType(self, value, type):
        if type == "bool":
            return self.boolToInt(value)
        elif type == "int":
            return int(value)
        elif type == "nil":
            return value
        elif type == "string":
            return value
        elif type is None:
            return None
        
    def convertToWriteType(self, value, type):
        if type == "bool":
            return self.intToBool(value)
        elif type == "int":
            return str(value)
        elif type == "nil":
            return ""
        elif type == "string":
            return value
        elif type is None:
            return ""
        
    def checkIfSet(self, argument:parse.XMLArgument):
        if self.getRealValue(argument) == None:
            sys.stderr.write(f"ERR: Variable {argument.getData().getName()} is not set.")
            exit(error.missingValue)

if __name__ == "__main__":
    interpret = Interpret()
    interpret.run()
