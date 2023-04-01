import xml.parsers.expat as expat
import error
import sys

class Parser:
    def __init__(self, fileName):
        self.fileName = self.openInput(fileName)
        self.headerFound = 0
        self.currentInstruction = None
        self.currentArgument = None
        self.xmlElements = XMLElements()

    def run(self):
        expatParser = self.initParser()
        expatParser.ParseFile(self.fileName)
        return self.xmlElements

    def initParser(self):
        expatParser = expat.ParserCreate()
        expatParser.StartElementHandler = self.startElement
        expatParser.EndElementHandler = self.endElement
        expatParser.CharacterDataHandler = self.charData
        return expatParser

    def openInput(self, fileName):
        if fileName is not None:
            file = self.tryOpenFile(fileName)
        else:
            file = sys.stdin.buffer
        return file

    def tryOpenFile(self, fileName):
        try:
            file = open(fileName, "rb")
        except IOError:
            sys.stderr.write("ERR: File does not appear to exist.")
            exit(error.wrongInputFile)
        return file

    # Process start elements from XML
    def startElement(self, name:str, attrs):
        if name == "program":
            self.headerFound = self.checkProgramAttributes(attrs)
            return
        
        elif name == "instruction":
            if self.headerFound == 0:
                sys.stderr.write(f"ERR: Program element not found.")
                exit(error.wrongXMLFormat)
            self.currentInstruction = XMLInstruction(attrs)

        elif name.startswith("arg"):
            argNumber = int(name.replace("arg",""))
            self.currentArgument = self.currentInstruction.newArgument(argNumber, attrs)

        else:
            sys.stderr.write(f"ERR: Wrong element name, expected only instruction or arg.")
            exit(error.wrongXMLStructure)
    
    # Process end elements from XML
    def endElement(self, name):
        if name == "instruction":
            self.xmlElements.appendInstruction(self.currentInstruction)
            self.currentInstruction = None

    # Process XML data
    def charData(self, data:str):
        if data.isspace():
            return
        
        if self.currentInstruction is None:
            sys.stderr.write(f"ERR: Instruction element not found.")
            exit(error.wrongXMLFormat)

        self.currentArgument._setValue(data)
        self.currentInstruction.appendArgument(self.currentArgument)
        self.currentArgument = None

    # Checks validity of XML header
    def checkProgramAttributes(self, attrs):
        if len(attrs) != 1 or attrs["language"] != "IPPcode23":
            sys.stderr.write(f"ERR: Wrong program element language, expected only IPPcode23.")	
            exit(error.wrongXMLStructure)
        return 1
    
class XMLArgument:
    def __init__(self, argNumber, type):
        self.argNumber = argNumber
        self.type = type
        self.value = None
    
    def _setValue(self, value):
        self.value = value

    def getArgNumber(self):
        return self.argNumber
    
    def getType(self):
        return self.type

    def getValue(self):
        return self.value
    
class XMLInstruction():  
    def __init__(self, attrs): 
        self.order = int(attrs["order"])
        self.opcode = attrs["opcode"]
        self.arguments = {}

    def getOpcode(self):
        return self.opcode
    
    def getArgument(self, name) -> XMLArgument:
        return self.arguments[name]
    
    def getArgumentsKeys(self):
        return self.arguments.keys()
    
    def getOrder(self):
        return self.order
    
    def newArgument(self, name, arguments):
        xmlArgument = XMLArgument(name, arguments["type"])
        return xmlArgument
    
    def appendArgument(self, argument:XMLArgument):
        argNumber = argument.getArgNumber()
        self.arguments[argNumber] = argument

class XMLElements:
    def __init__(self):
        self.elements = {}
    
    def appendInstruction(self, element:XMLInstruction):
        order = element.getOrder()
        if self.elements.get(order) == None:
            self.elements[element.order] = element
            return
        
        sys.stderr.write(f"ERR: Duplicit order of some instructions.")	
        exit(error.wrongXMLStructure)

    def getInstructions(self) -> dict:
        return self.elements
    
    def getInstruction(self, order) -> XMLInstruction:
        return self.elements[order]