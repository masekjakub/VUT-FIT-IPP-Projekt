import xml.parsers.expat as expat
import error
import sys

class Parser:
    def __init__(self, sourceFile):
        self.sourceFile = self.openSource(sourceFile)
        self.headerFound = 0
        self.currentInstruction = None
        self.currentArgument = None
        self.xmlElements = XMLElements()

    # Parse XML file and return list of instructions
    def run(self):
        self.expatParser = self.initParser()
        try:
            self.expatParser.ParseFile(self.sourceFile)
        except expat.ExpatError as e:
            sys.stderr.write(f"ERR: XML parsing error: {e}")
            exit(error.wrongXMLFormat)
        self.sourceFile.close()
        return self.xmlElements

    # Initialize XML parser 
    def initParser(self):
        expatParser = expat.ParserCreate()
        expatParser.StartElementHandler = self.startElement
        expatParser.EndElementHandler = self.endElement
        expatParser.CharacterDataHandler = self.charData
        expatParser.buffer_text = True
        return expatParser

    # Open source file or use stdin
    def openSource(self, fileName):
        if fileName is not None:
            file = self.tryOpenFile(fileName)
        else:
            file = sys.stdin.buffer
        return file

    # Try to open source file and exits if it fails
    def tryOpenFile(self, fileName):
        try:
            file = open(fileName, "rb")
        except IOError:
            sys.stderr.write("ERR: File does not appear to exist.")
            exit(error.wrongInputFile)
        return file

    # Process start elements from XML
    def startElement(self, name:str, attrs):
        # Check if program element is first
        if name == "program":
            self.headerFound = self.checkProgramAttributes(attrs)
            return
        
        # Handle instruction element
        if name == "instruction":
            if self.headerFound == 0:
                sys.stderr.write(f"ERR: Program element not found.")
                exit(error.wrongXMLFormat)
            self.currentInstruction = XMLInstruction(attrs)
            return

        # Handle argument element
        if name.startswith("arg"):
            if self.currentInstruction is None:
                sys.stderr.write(f"ERR: Instruction element not found.")
                exit(error.wrongXMLFormat)
            argNumber = int(name.replace("arg",""))
            self.currentArgument = self.currentInstruction.newArgument(argNumber, attrs)
            return

        # Handle wrong element
        sys.stderr.write(f"ERR: Wrong element name, expected only instruction or arg.")
        exit(error.wrongXMLStructure)
    
    # Process end elements from XML
    def endElement(self, name:str):
        # Handle instruction element
        if name.startswith("arg") and self.currentArgument is not None:
            if self.currentArgument.getData() is None:
                self.currentArgument._setValue("")
                self.currentInstruction.appendArgument(self.currentArgument)
                self.currentArgument = None

        # Handle instruction element
        if name == "instruction":
            self.xmlElements.appendInstruction(self.currentInstruction)
            self.currentInstruction = None

    # Process XML data
    def charData(self, data:str):
        if data.isspace():
            return

        data = data.strip()

        if self.currentInstruction is None:
            sys.stderr.write(f"ERR: Instruction element not found.")
            exit(error.wrongXMLFormat)

        if self.currentArgument is None:
            sys.stderr.write(f"ERR: Argument element not found.")
            exit(error.wrongXMLFormat)

        self.currentArgument._setValue(data)
        self.currentInstruction.appendArgument(self.currentArgument)

    # Checks validity of XML header
    def checkProgramAttributes(self, attrs) -> bool:
        if attrs["language"] != "IPPcode23":
            sys.stderr.write(f"ERR: Wrong program element language, expected only IPPcode23.")	
            exit(error.wrongXMLStructure)
        return 1

class Symbol:
    def __init__(self, value, type):
        if type == "string":
            value = self.replaceEscSeq(value)
        # Convert bool to int (internal bool representation)
        if type == "bool" and value is not None:
            if value.lower() == "true":
                value = 1
            elif value.lower() == "false":
                value = 0

        self.value = value
        self.type = type
    
    def getValue(self) -> str:
        return self.value
    
    def getType(self) -> str:
        return self.type

    def setValue(self, value):
        self.value = value

    def setType(self, type):
        self.type = type

    def isSet(self) -> bool:
        return self.value != None
    
    def replaceEscSeq(self, string:str) -> str:
        index = string.find('\\')
        while index != -1:
            char = string[index : index+4]
            # Replace escape sequence with character
            string = string.replace(char, chr(int(char[1:])))
            index = string.find("\\")
        return string
 
class Variable(Symbol):
    def __init__(self, name, type):
        self.name = name
        self.type = type
        self.value = None

    def getName(self)->str:
        return self.name
    
class XMLVariable(Variable):
    def __init__(self, name, frameName, type):
        self.name = name
        self.frameName = frameName
        self.type = type

    def getFrameName(self)->str:
        return self.frameName
    
class XMLArgument:
    def __init__(self, argNumber, type):
        self.argNumber = argNumber
        self.type = type
        self.value = None
    
    def _setValue(self, value:str) -> None:
        if self.type == "var":
            frameName, varName = value.split("@")
            self.value = XMLVariable(varName, frameName, self.type)
        else:
            self.value = Symbol(value, self.type)
            
    def getArgNumber(self) -> int:
        return self.argNumber
    
    def getXmlType(self) -> str:
        return self.type

    def getData(self) -> XMLVariable|Symbol:
        return self.value
    
class XMLInstruction():  
    def __init__(self, attrs): 
        try:
            self.opcode = str(attrs["opcode"]).upper()
            self.order = int(attrs["order"])
            if int(self.order) <= 0:
                sys.stderr.write(f"ERR: Wrong instruction element order.")
                exit(error.wrongXMLStructure)
        except:
            sys.stderr.write(f"ERR: Wrong instruction element structure.")
            exit(error.wrongXMLStructure)

        self.arguments = {}

    def getOpcode(self) -> str:
        return self.opcode
    
    def getArgument(self, name) -> XMLArgument:
        try:
            return self.arguments[name]
        except KeyError:
            sys.stderr.write(f"ERR: Argument {name} not found.")
            exit(error.wrongXMLStructure)
    
    def getArgumentsKeys(self) -> list:
        return self.arguments.keys()
    
    def getOrder(self) -> int:
        return self.order
    
    def newArgument(self, name, arguments) -> XMLArgument:
        try:
            xmlArgument = XMLArgument(name, arguments["type"])
        except:
            sys.stderr.write(f"ERR: Wrong argument element structure.")
            exit(error.wrongXMLStructure)
        return xmlArgument
    
    def appendArgument(self, argument:XMLArgument):
        argNumber = argument.getArgNumber()
        self.arguments[argNumber] = argument

class XMLElements:
    def __init__(self):
        self.elements = {}
    
    def appendInstruction(self, element:XMLInstruction):
        order = element.getOrder()
        if self.elements.get(order) != None:
            sys.stderr.write(f"ERR: Duplicit order of some instructions.")	
            exit(error.wrongXMLStructure)
            
        self.elements[element.order] = element

    def getInstructions(self) -> dict:
        return self.elements
    
    def getInstruction(self, order) -> XMLInstruction:
        return self.elements[order]