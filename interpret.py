import parse
import getopt
import sys
import error
import copy

class Interpret:

    def __init__(self):
        self.sourceFile = None
        self.inputFile = None
        self.order = 0
        self.orderList = list()
        self.orderIndex = 0
        self.instructionCount = 0

    def run(self):
        self.processArguments()
        parser = parse.Parser(self.sourceFile)
        program = parser.run()
        self.execute(program)
        self.inputFile.close()

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
        
        # Check if at least one file is given
        if self.sourceFile is None and self.inputFile is None:
            sys.stderr.write(f"ERR: At least one file must be given.")
            exit(error.wrongInputFile)
        
        # Open input file
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
        print("Interpretation of XML representation of IPPcode23.")
        print("Author: Jakub Mašek (xmasek19)")
        print("Usage: interpret.py [options]")
        print("Options:")
        print("  -h, --help\t\tPrint this help.")
        print("  -s, --source=file\tRead XML from file.")
        print("  -i, --input=file\tRead input from file.")

    # Jump to next instruction after given order
    def jumpAfter(self, order):
        self.orderIndex = self.orderList.index(order)
        self.order = self.orderList[self.orderIndex]
        self.orderIndex += 1

    def getOrder(self):
        return self.order
    
    def getInstructionCount(self):
        return self.instructionCount
    
    # Execute program
    def execute(self, program:parse.XMLElements):
        executor = Executor()
        instructions = program.getInstructions()
        if len(instructions) == 0:
            exit(error.ok)

        maxOrder = max(instructions)
        self.orderList = sorted(list(instructions.keys()))

        # Save all labels
        for key in instructions:
            instruction = program.getInstruction(key)
            if instruction.getOpcode() == "LABEL":
                labelName = instruction.getArgument(1).getData().getValue()
                self.ensureLabelIsUnique(labelName, executor.labels)
                executor.labels[labelName] = key

        # Execute instructions
        while self.order != maxOrder:
            self.order = self.orderList[self.orderIndex]
            instruction = program.getInstruction(self.order)
            opcode = instruction.getOpcode()

            # Try to execute instruction
            try:
                getattr(executor, opcode)(instruction)
            except AttributeError:
                sys.stderr.write(f"ERR: Error while executing opcode {opcode}.")
                exit(error.wrongXMLStructure)

            self.orderIndex +=1
            self.instructionCount += 1

    # Check if label is unique in labels dictionary
    def ensureLabelIsUnique(self, labelName:str, labels:dict):
        if labels.get(labelName) is not None:
            sys.stderr.write(f"ERR: Label {labelName} already exists.")
            exit(error.semantics)

class Frame:
    GF = 1
    LF = 2
    TF = 3

    def __init__(self, frameType):
        self.frameType = frameType
        self.variables = {}

    # Add variable to frame
    def addVariable(self, variable:parse.Variable):
        # Check if variable already exists
        if self.variables.get(variable.getName()) is not None:
            sys.stderr.write(f"ERR: Variable {variable.getName()} already exists.")
            exit(error.semantics)

        self.variables[variable.getName()] = variable

    # Get variable from frame
    def getVariable(self, variableName:str) -> parse.Variable:
        # Check if variable exists
        if self.variables.get(variableName) is None:
            sys.stderr.write(f"ERR: Variable {variableName} does not exist.")
            exit(error.notExistingVariable)
    
        return self.variables[variableName]

class Stack:
    def __init__(self):
        self.stack = []    

    def push(self, item):
        self.stack.append(item)

    def pop(self) -> parse.Symbol|parse.Variable:
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

        self.myAssert(arg1.getXmlType() == "var", instruction, error.wrongType)
        
        variableElement = arg1.getData()
        frame = self.getFrame(variableElement.getFrameName())
        variable = frame.getVariable(variableElement.getName())
        
        valToAssign = self.getSymbolValue(arg2)
        typeToAssign = self.getSymbolType(arg2)

        variable.setValue(self.convertToType(valToAssign, typeToAssign))
        variable.setType(typeToAssign)

    # CREATEFRAME instruction
    def CREATEFRAME(self, instruction:parse.XMLInstruction):
        self.checkArgCount(instruction, 0)
        self.tempFrame = Frame(Frame.TF)

    # PUSHFRAME instruction
    def PUSHFRAME(self, instruction:parse.XMLInstruction):
        self.checkArgCount(instruction, 0)
        self.ensureFrameExists(self.tempFrame)
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
        self.myAssert(arg.getXmlType() == "var", instruction, error.wrongType)

        varElement = instruction.getArgument(1).getData()
        frame = self.getFrame(varElement.getFrameName())
        var = parse.Variable(varElement.getName(), None)
        frame.addVariable(var)

    # CALL instruction
    def CALL(self, instruction:parse.XMLInstruction):
        self.checkArgCount(instruction, 1)
        arg = instruction.getArgument(1)
        self.myAssert(arg.getXmlType() == "label", instruction, error.wrongType)

        self.callStack.push(interpret.getOrder())
        self.JUMP(instruction)

    # RETURN instruction
    def RETURN(self, instruction:parse.XMLInstruction):
        self.checkArgCount(instruction, 0)
        if self.callStack.isEmpty():
            sys.stderr.write(f"ERR: Call stack is empty.")
            exit(error.missingValue)

        interpret.jumpAfter(self.callStack.pop())

    # PUSHS instruction
    def PUSHS(self, instruction:parse.XMLInstruction):
        self.checkArgCount(instruction, 1)
        arg = instruction.getArgument(1)

        self.myAssert(self.getSymbolType(arg) in ["int", "string", "bool", "nil"], instruction, error.wrongType)
        
        if arg.getXmlType() == "var":
            frame = self.getFrame(arg.getData().getFrameName())
            var = frame.getVariable(arg.getData().getName())
            self.dataStack.push(copy.deepcopy(var))
            return

        self.dataStack.push(arg.getData())

    # POPS instruction
    def POPS(self, instruction:parse.XMLInstruction):
        self.checkArgCount(instruction, 1)
        arg = instruction.getArgument(1)

        self.myAssert(arg.getXmlType() == "var", instruction, error.wrongType)

        if self.dataStack.isEmpty():
            sys.stderr.write(f"ERR: Data stack is empty.")
            exit(error.missingValue)

        frame = self.getFrame(arg.getData().getFrameName())
        var = frame.getVariable(arg.getData().getName())
        data = self.dataStack.pop()

        var.setValue(data.getValue())
        var.setType(data.getType())

    # ADD instruction
    def ADD(self, instruction:parse.XMLInstruction):
        self.checkArgCount(instruction, 3)
        arg1 = instruction.getArgument(1)
        arg2 = instruction.getArgument(2)
        arg3 = instruction.getArgument(3)

        self.myAssert(arg1.getXmlType() == "var", instruction, error.wrongType)
        self.myAssert(self.getSymbolType(arg2) == "int", instruction, error.wrongType)
        self.myAssert(self.getSymbolType(arg3) == "int", instruction, error.wrongType)

        val1 = self.getSymbolValue(arg2)
        val2 = self.getSymbolValue(arg3)

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

        self.myAssert(arg1.getXmlType() == "var", instruction, error.wrongType)
        self.myAssert(self.getSymbolType(arg2) == "int", instruction, error.wrongType)
        self.myAssert(self.getSymbolType(arg3) == "int", instruction, error.wrongType)

        val1 = self.getSymbolValue(arg2)
        val2 = self.getSymbolValue(arg3)
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

        self.myAssert(arg1.getXmlType() == "var", instruction, error.wrongType)
        self.myAssert(self.getSymbolType(arg2) == "int", instruction, error.wrongType)
        self.myAssert(self.getSymbolType(arg3) == "int", instruction, error.wrongType)

        val1 = self.getSymbolValue(arg2)
        val2 = self.getSymbolValue(arg3)
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

        self.myAssert(arg1.getXmlType() == "var", instruction, error.wrongType)
        self.myAssert(self.getSymbolType(arg2) == "int", instruction, error.wrongType)
        self.myAssert(self.getSymbolType(arg3) == "int", instruction, error.wrongType)

        val1 = self.getSymbolValue(arg2)
        val2 = self.getSymbolValue(arg3)

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

        self.myAssert(arg1.getXmlType() == "var", instruction, error.wrongType)
        self.myAssert(self.getSymbolType(arg2) == self.getSymbolType(arg3), instruction, error.wrongType)
        self.myAssert(self.getSymbolType(arg2) in ["int", "string", "bool"], instruction, error.wrongType)
        self.myAssert(self.getSymbolType(arg3) in ["int", "string", "bool"], instruction, error.wrongType)

        val1 = self.getSymbolValue(arg2)
        val2 = self.getSymbolValue(arg3)

        frame = self.getFrame(arg1.getData().getFrameName())
        var = frame.getVariable(arg1.getData().getName())
        var.setValue(self.boolToInt(val1 < val2))
        var.setType("bool")

    # GT instruction
    def GT(self, instruction:parse.XMLInstruction):
        self.checkArgCount(instruction, 3)
        arg1 = instruction.getArgument(1)
        arg2 = instruction.getArgument(2)
        arg3 = instruction.getArgument(3)

        self.myAssert(arg1.getXmlType() == "var", instruction, error.wrongType)
        self.myAssert(self.getSymbolType(arg2) == self.getSymbolType(arg3), instruction, error.wrongType)
        self.myAssert(self.getSymbolType(arg2) in ["int", "string", "bool"], instruction, error.wrongType)
        self.myAssert(self.getSymbolType(arg3) in ["int", "string", "bool"], instruction, error.wrongType)

        val1 = self.getSymbolValue(arg2)
        val2 = self.getSymbolValue(arg3)

        frame = self.getFrame(arg1.getData().getFrameName())
        var = frame.getVariable(arg1.getData().getName())

        var.setValue(self.boolToInt(val1 > val2))
        var.setType("bool")

    # EQ instruction
    def EQ(self, instruction:parse.XMLInstruction):
        self.checkArgCount(instruction, 3)
        arg1 = instruction.getArgument(1)
        arg2 = instruction.getArgument(2)
        arg3 = instruction.getArgument(3)

        self.myAssert(arg1.getXmlType() == "var", instruction, error.wrongType)
        self.myAssert(self.getSymbolType(arg2) in ["int", "string", "bool", "nil"], instruction, error.wrongType)
        self.myAssert(self.getSymbolType(arg3) in ["int", "string", "bool", "nil"], instruction, error.wrongType)
        self.myAssert(self.getSymbolType(arg2) == self.getSymbolType(arg3) or self.getSymbolType(arg2) == "nil" or self.getSymbolType(arg3) == "nil" , instruction, error.wrongType)

        val1 = self.getSymbolValue(arg2)
        val2 = self.getSymbolValue(arg3)

        frame = self.getFrame(arg1.getData().getFrameName())
        var = frame.getVariable(arg1.getData().getName())
        var.setValue(self.boolToInt(val1 == val2))
        var.setType("bool")

    # AND instruction
    def AND(self, instruction:parse.XMLInstruction):
        self.checkArgCount(instruction, 3)
        arg1 = instruction.getArgument(1)
        arg2 = instruction.getArgument(2)
        arg3 = instruction.getArgument(3)

        self.myAssert(arg1.getXmlType() == "var", instruction, error.wrongType)
        self.myAssert(self.getSymbolType(arg2) == "bool", instruction, error.wrongType)
        self.myAssert(self.getSymbolType(arg3) == "bool", instruction, error.wrongType)

        val1 = self.getSymbolValue(arg2)
        val2 = self.getSymbolValue(arg3)

        frame = self.getFrame(arg1.getData().getFrameName())
        var = frame.getVariable(arg1.getData().getName())
        var.setValue(self.boolToInt(val1 and val2))
        var.setType("bool")

    # OR instruction
    def OR(self, instruction:parse.XMLInstruction):
        self.checkArgCount(instruction, 3)
        arg1 = instruction.getArgument(1)
        arg2 = instruction.getArgument(2)
        arg3 = instruction.getArgument(3)

        self.myAssert(arg1.getXmlType() == "var", instruction, error.wrongType)
        self.myAssert(self.getSymbolType(arg2) == "bool", instruction, error.wrongType)
        self.myAssert(self.getSymbolType(arg3) == "bool", instruction, error.wrongType)

        val1 = self.getSymbolValue(arg2)
        val2 = self.getSymbolValue(arg3)

        frame = self.getFrame(arg1.getData().getFrameName())
        var = frame.getVariable(arg1.getData().getName())
        var.setValue(self.boolToInt(val1 or val2))
        var.setType("bool")

    # NOT instruction
    def NOT(self, instruction:parse.XMLInstruction):
        self.checkArgCount(instruction, 2)
        arg1 = instruction.getArgument(1)
        arg2 = instruction.getArgument(2)

        self.myAssert(arg1.getXmlType() == "var", instruction, error.wrongType)
        self.myAssert(self.getSymbolType(arg2) == "bool", instruction, error.wrongType)

        val1 = self.getSymbolValue(arg2)

        frame = self.getFrame(arg1.getData().getFrameName())
        var = frame.getVariable(arg1.getData().getName())
        var.setValue(self.boolToInt(not val1))
        var.setType("bool")

    # INT2CHAR instruction
    def INT2CHAR(self, instruction:parse.XMLInstruction):
        self.checkArgCount(instruction, 2)
        arg1 = instruction.getArgument(1)
        arg2 = instruction.getArgument(2)

        self.myAssert(arg1.getXmlType() == "var", instruction, error.wrongType)
        self.myAssert(self.getSymbolType(arg2) == "int", instruction, error.wrongType)

        val1 = self.getSymbolValue(arg2)

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

        self.myAssert(arg1.getXmlType() == "var", instruction, error.wrongType)
        self.myAssert(self.getSymbolType(arg2) == "string", instruction, error.wrongType)
        self.myAssert(self.getSymbolType(arg3) == "int", instruction, error.wrongType)

        string = self.getSymbolValue(arg2)
        index = self.getSymbolValue(arg3)

        frame = self.getFrame(arg1.getData().getFrameName())
        var = frame.getVariable(arg1.getData().getName())

        self.myAssert(index >= 0 and index < len(string), instruction, error.invalidString)

        var.setValue(ord(string[index]))
        var.setType("int")


    # READ instruction
    def READ(self, instruction:parse.XMLInstruction):
        self.checkArgCount(instruction, 2)
        arg1 = instruction.getArgument(1)
        arg2 = instruction.getArgument(2)

        self.myAssert(arg1.getXmlType() == "var", instruction, error.wrongType)
        self.myAssert(arg2.getXmlType() == "type", instruction, error.wrongType)

        frame = self.getFrame(arg1.getData().getFrameName())
        var = frame.getVariable(arg1.getData().getName())

        try:
            val = interpret.inputFile.readline().strip()
            if arg2.getData().getValue() == "bool":
                val = val.lower()
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
        string = self.getSymbolValue(arg1)
        string = self.convertToWriteType(string, self.getSymbolType(arg1))
        print(string, end="", flush=True)
    
    # CONCAT instruction
    def CONCAT(self, instruction:parse.XMLInstruction):
        self.checkArgCount(instruction, 3)
        arg1 = instruction.getArgument(1)
        arg2 = instruction.getArgument(2)
        arg3 = instruction.getArgument(3)

        self.myAssert(arg1.getXmlType() == "var", instruction, error.wrongType)
        self.myAssert(self.getSymbolType(arg2) == "string", instruction, error.wrongType)
        self.myAssert(self.getSymbolType(arg3) == "string", instruction, error.wrongType)

        val1 = self.getSymbolValue(arg2)
        val2 = self.getSymbolValue(arg3)

        frame = self.getFrame(arg1.getData().getFrameName())
        var = frame.getVariable(arg1.getData().getName())
        var.setValue(val1 + val2)
        var.setType("string")

    # STRLEN instruction
    def STRLEN(self, instruction:parse.XMLInstruction):
        self.checkArgCount(instruction, 2)
        arg1 = instruction.getArgument(1)
        arg2 = instruction.getArgument(2)

        self.myAssert(arg1.getXmlType() == "var", instruction, error.wrongType)
        self.myAssert(self.getSymbolType(arg2) == "string", instruction, error.wrongType)

        frame = self.getFrame(arg1.getData().getFrameName())
        var = frame.getVariable(arg1.getData().getName())
        var.setValue(len(self.getSymbolValue(arg2)))
        var.setType("int")

    # GETCHAR instruction
    def GETCHAR(self, instruction:parse.XMLInstruction):
        self.checkArgCount(instruction, 3)
        arg1 = instruction.getArgument(1)
        arg2 = instruction.getArgument(2)
        arg3 = instruction.getArgument(3)

        self.myAssert(arg1.getXmlType() == "var", instruction, error.wrongType)
        self.myAssert(self.getSymbolType(arg2) == "string", instruction, error.wrongType)
        self.myAssert(self.getSymbolType(arg3) == "int", instruction, error.wrongType)

        string = self.getSymbolValue(arg2)
        index = self.getSymbolValue(arg3)

        frame = self.getFrame(arg1.getData().getFrameName())
        var = frame.getVariable(arg1.getData().getName())

        # Is index in range of string
        self.myAssert(index >= 0 and index < len(string), instruction, error.invalidString)

        var.setValue(string[index])
        var.setType("string")

    # SETCHAR instruction
    def SETCHAR(self, instruction:parse.XMLInstruction):
        self.checkArgCount(instruction, 3)
        arg1 = instruction.getArgument(1)
        arg2 = instruction.getArgument(2)
        arg3 = instruction.getArgument(3)

        self.myAssert(self.getSymbolType(arg1) == "string", instruction, error.wrongType)
        self.myAssert(self.getSymbolType(arg2) == "int", instruction, error.wrongType)
        self.myAssert(self.getSymbolType(arg3) == "string", instruction, error.wrongType)
        
        stringTo = self.getSymbolValue(arg1)
        index = self.getSymbolValue(arg2)
        stringFrom = self.getSymbolValue(arg3)

        self.myAssert(len(stringTo) > index and len(stringFrom) != 0 and index >= 0, instruction, error.invalidString)

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

        self.myAssert(arg1.getXmlType() == "var", instruction, error.wrongType)

        frame = self.getFrame(arg1.getData().getFrameName())
        var = frame.getVariable(arg1.getData().getName())

        if arg2.getXmlType() == "var":
            frame = self.getFrame(arg2.getData().getFrameName())
            type = frame.getVariable(arg2.getData().getName()).getType()
        else: 
            type = arg2.getXmlType()
    
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
        arg = instruction.getArgument(1)
        self.myAssert(arg.getXmlType() == "label", instruction, error.wrongType)
        labelName = arg.getData().getValue()
        self.checkLabelExistance(labelName)
        
        labelOrder = self.labels[labelName]
        interpret.jumpAfter(labelOrder)

    # JUMPIFEQ instruction
    def JUMPIFEQ(self, instruction:parse.XMLInstruction):
        self.checkArgCount(instruction, 3)
        arg1 = instruction.getArgument(1)
        arg2 = instruction.getArgument(2)
        arg3 = instruction.getArgument(3)

        self.myAssert(arg1.getXmlType() == "label", instruction, error.wrongType)
        self.myAssert(self.getSymbolType(arg2) in ["int", "string", "bool", "nil"], instruction, error.wrongType)
        self.myAssert(self.getSymbolType(arg3) in ["int", "string", "bool", "nil"], instruction, error.wrongType)
        self.myAssert(self.getSymbolType(arg2) == self.getSymbolType(arg3) or self.getSymbolType(arg2) == "nil" or self.getSymbolType(arg3) == "nil" , instruction, error.wrongType)

        labelName = arg1.getData().getValue()
        self.checkLabelExistance(labelName)

        val1 = self.getSymbolValue(arg2)
        val2 = self.getSymbolValue(arg3)
  
        if val1 == val2:            
            labelOrder = self.labels[labelName]
            interpret.jumpAfter(labelOrder)
        

    # JUMPIFNEQ instruction
    def JUMPIFNEQ(self, instruction:parse.XMLInstruction):
        self.checkArgCount(instruction, 3)
        arg1 = instruction.getArgument(1)
        arg2 = instruction.getArgument(2)
        arg3 = instruction.getArgument(3)

        self.myAssert(arg1.getXmlType() == "label", instruction, error.wrongType)
        self.myAssert(self.getSymbolType(arg2) in ["int", "string", "bool", "nil"], instruction, error.wrongType)
        self.myAssert(self.getSymbolType(arg3) in ["int", "string", "bool", "nil"], instruction, error.wrongType)
        self.myAssert(self.getSymbolType(arg2) == self.getSymbolType(arg3) or self.getSymbolType(arg2) == "nil" or self.getSymbolType(arg3) == "nil" , instruction, error.wrongType)

        labelName = arg1.getData().getValue()
        self.checkLabelExistance(labelName)

        val1 = self.getSymbolValue(arg2)
        val2 = self.getSymbolValue(arg3)
  
        if val1 != val2:            
            labelOrder = self.labels[labelName]
            interpret.jumpAfter(labelOrder)

    # EXIT instruction
    def EXIT(self, instruction:parse.XMLInstruction):
        self.checkArgCount(instruction, 1)
        arg1 = instruction.getArgument(1)

        self.myAssert(self.getSymbolType(arg1) == "int", instruction, error.wrongType)
        
        exitCode = self.getSymbolValue(arg1)

        self.myAssert(exitCode >= 0 and exitCode <= 49, instruction, error.wrongOperandValue)

        exit(exitCode)

    # DPRINT instruction
    def DPRINT(self, instruction:parse.XMLInstruction):
        arg = instruction.getArgument(1)
        sys.stderr.write(self.getSymbolValue(arg))

    # BREAK instruction
    def BREAK(self, instruction:parse.XMLInstruction):
        print("Current instruction order: ", interpret.getOrder(), file=sys.stderr)
        print("Instruction count: ", interpret.getInstructionCount(), file=sys.stderr)

        # Global frame
        print("Global frame: ", file=sys.stderr)
        for key in self.getFrame("GF").variables.keys():
            print(f"    {key} = {self.getFrame('GF').variables[key].getValue()}", file=sys.stderr)

        # Temporary frame
        if self.tempFrame is not None:
            print("Temporary frame: ", file=sys.stderr)
            for key in self.getFrame("TF").variables.keys():
                print(f"    {key} = {self.getFrame('TF').variables[key].getValue()}", file=sys.stderr)
        else:
            print("Temporary frame: None", file=sys.stderr)

        # Local frame
        if self.localFrameStack.isEmpty() == 0:
            print("Local frame: ", file=sys.stderr)
            for key in self.getFrame("LF").variables.keys():
                print(f"    {key} = {self.getFrame('LF').variables[key].getValue()}", file=sys.stderr)
        else:
            print("Local frame: None", file=sys.stderr)
        
        # Data stack
        print("Data stack: ", file=sys.stderr) 
        while self.dataStack.isEmpty() == 0:
            data:parse.XMLArgument = self.dataStack.pop()
            print(f"    {data.getData().getValue()}", file=sys.stderr)
            
    ## EXECUTOR HELPERS ##

    # Return frame by name
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

    # Get value of symbol (int, string, bool, nil)
    def getSymbolValue(self, argument:parse.XMLArgument) -> str:
        if argument.getXmlType() == "var":
            frame = self.getFrame(argument.getData().getFrameName())
            var = frame.getVariable(argument.getData().getName())
            value = var.getValue()
            self.convertToType(value, var.getType())
            return value
        else:
            value = argument.getData().getValue()
            return self.convertToType(value, argument.getData().getType())
        
    # Get type of symbol (int, string, bool, nil)
    def getSymbolType(self, argument:parse.XMLArgument) -> str:
        if argument.getXmlType() == "var":
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
        if str(value).lower() == "true":
            return 1
        else:
            return 0
    
    def intToBool(self, value:int) -> str:
        if value == 1:
            return "true"
        else:
            return "false"
    
    def convertToType(self, value, type):
        try:
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
        except:
            sys.stderr.write(f"ERR: Invalid value in instruction.")
            exit(error.wrongXMLStructure)
    
    # Convert to writeable value
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
        
    # Check if variable is set
    def checkIfSet(self, argument:parse.XMLArgument):
        if self.getSymbolValue(argument) == None:
            sys.stderr.write(f"ERR: Variable {argument.getData().getName()} is not set.")
            exit(error.missingValue)

    # Check if label exists
    def checkLabelExistance(self, labelName):
        if self.labels.get(labelName) is None:
            sys.stderr.write(f"ERR: Label {labelName} does not exist.")
            exit(error.semantics)

    # If input is not 0, exit with error code
    def myAssert(self, value, instruction:parse.XMLInstruction, errorCode):
        if value == 0:
            sys.stderr.write(f"ERR: Error in {instruction.getOpcode()} instruction with order {instruction.getOrder()}. Error code: {errorCode}.")
            exit(errorCode)


if __name__ == "__main__":
    interpret = Interpret()
    interpret.run()