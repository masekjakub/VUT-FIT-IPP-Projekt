<?php
require_once("Errors.php");

class Syntax{
    private $insIndex = 1;
    private $argIndex = 1;
    private $headerFound = 0;
    
function analyse($file, $simpleXML){
    $token = new Token();
    $lexer = new Lexer();

    $token = $lexer->newToken($file);

    if($this->headerFound == 0){
       // print_r($token);
        if($token->type == tokenType::T_EOL){
            return;
        }

        if($token->type != tokenType::T_HEADER){
            fwrite(STDERR, "Error: Expected head");
            exit(myError::E_NOHEAD->value);
        }

        $this->headerFound = 1;
        return;
    }

    switch($token->type){
        case tokenType::T_EOL:
            break;

        //opcode var symb
        case tokenType::T_MOVE:
        case tokenType::T_INT2CHAR:
        case tokenType::T_STRLEN:
        case tokenType::T_TYPE:
        case tokenType::T_NOT:

            $instruction = $this->generateInstruction($simpleXML,$token);
            $token = $lexer->newToken($file);
            $this->checkType($token, tokenType::T_VAR);
            $this->generateArg($instruction, $token, "var");

            $token = $lexer->newToken($file);
            $this->check2Types($token, tokenType::T_VAR, tokenType::T_CONST);
            $this->generateArgSymb($instruction, $token);

            $token = $lexer->newToken($file);
            $this->checkType($token, tokenType::T_EOL);
            break;
        
        //opcode
        case tokenType::T_CREATEFRAME:
        case tokenType::T_PUSHFRAME:
        case tokenType::T_POPFRAME:
        case tokenType::T_RETURN:
        case tokenTYpe::T_BREAK:
            $instruction = $this->generateInstruction($simpleXML,$token);
            $token = $lexer->newToken($file);
            $this->checkType($token, tokenType::T_EOL);
            break;

        //opcode var
        case tokenType::T_DEFVAR:
        case tokenType::T_POPS:
            $instruction = $this->generateInstruction($simpleXML,$token);
            $token = $lexer->newToken($file);
            $this->checkType($token, tokenType::T_VAR);
            $this->generateArg($instruction, $token, "var");

            $token = $lexer->newToken($file);
            $this->checkType($token, tokenType::T_EOL);
            break;

        //opcode symb
        case tokenType::T_PUSHS:
        case tokenType::T_WRITE:
        case tokenType::T_EXIT:
        case tokenType::T_DPRINT:
            $instruction = $this->generateInstruction($simpleXML,$token);
            $token = $lexer->newToken($file);
            $this->check2Types($token, tokenType::T_VAR, tokenType::T_CONST);
            $this->generateArgSymb($instruction, $token);

            $token = $lexer->newToken($file);
            $this->checkType($token, tokenType::T_EOL);
            break;

        //opcode var symb symb
        case tokenType::T_ADD:
        case tokenType::T_SUB:
        case tokenType::T_MUL:
        case tokenType::T_IDIV:
        case tokenType::T_LT:
        case tokenType::T_GT:
        case tokenType::T_EQ:
        case tokenType::T_AND:
        case tokenType::T_OR:
        case tokenType::T_STRI2INT:
        case tokenType::T_CONCAT:
        case tokenType::T_GETCHAR:
        case tokenType::T_SETCHAR:
            $instruction = $this->generateInstruction($simpleXML,$token);
            $token = $lexer->newToken($file);
            $this->checkType($token, tokenType::T_VAR);
            $this->generateArg($instruction, $token, "var");

            $token = $lexer->newToken($file);
            $this->check2Types($token, tokenType::T_VAR, tokenType::T_CONST);
            $this->generateArgSymb($instruction, $token);

            $token = $lexer->newToken($file);
            $this->check2Types($token, tokenType::T_VAR, tokenType::T_CONST);
            $this->generateArgSymb($instruction, $token);

            $token = $lexer->newToken($file);
            $this->checkType($token, tokenType::T_EOL);
            break;

        //opcode var type
        case tokenType::T_READ:
            $instruction = $this->generateInstruction($simpleXML,$token);
            $token = $lexer->newToken($file);
            $this->checkType($token, tokenType::T_VAR);
            $this->generateArg($instruction, $token, "var");

            $token = $lexer->newToken($file);
            $this->checkType($token, tokenType::T_VARTYPE);
            $this->generateArg($instruction, $token, "type");

            $token = $lexer->newToken($file);
            $this->checkType($token, tokenType::T_EOL);
            break;

        //opcode label
        case tokenType::T_LABEL:
        case tokenType::T_JUMP:
        case tokenType::T_CALL:
            $instruction = $this->generateInstruction($simpleXML,$token);
            $token = $lexer->newToken($file);
            $this->checkType($token, tokenType::T_LABELNAME);
            $this->generateArg($instruction, $token, "label");

            $token = $lexer->newToken($file);
            $this->checkType($token, tokenType::T_EOL);
            break;

        //opcode label symb symb
        case tokenType::T_JUMPIFEQ:
        case tokenType::T_JUMPIFNEQ:
            $instruction = $this->generateInstruction($simpleXML,$token);
            $token = $lexer->newToken($file);
            $this->checkType($token, tokenType::T_LABELNAME);
            $this->generateArg($instruction, $token, "label");

            $token = $lexer->newToken($file);
            $this->check2Types($token, tokenType::T_VAR, tokenType::T_CONST);
            $this->generateArgSymb($instruction, $token);

            $token = $lexer->newToken($file);
            $this->check2Types($token, tokenType::T_VAR, tokenType::T_CONST);
            $this->generateArgSymb($instruction, $token);

            $token = $lexer->newToken($file);
            $this->checkType($token, tokenType::T_EOL);
            break;

        default:
            fwrite(STDERR, "Error: Unexpected token $token->value.");
            exit(myError::E_WRONGOPCODE->value);
    }

}
private function generateInstruction($simpleXML,$token){
    $instruction = $simpleXML->addChild("instruction");
    $instruction->addAttribute("order", $this->insIndex);
    $instruction->addAttribute("opcode", strtoupper($token->value));
    $this->insIndex++;
    $this->argIndex = 1;
    return $instruction;
}

private function generateArg($instruction ,$token, $type){
    $arg = $instruction->addChild("arg".$this->argIndex, htmlspecialchars($token->value));
    $arg->addAttribute("type", $type);
    $this->argIndex++;
}

private function generateArgSymb($instruction ,$token){
    if($token->type == tokenType::T_VAR){
        $this->generateArg($instruction, $token, "var");
        return;
    }

    $this->generateArg($instruction, $token, $token->constType);

}

private function checkType($token, $type){
    if($token->type != $type){
        fwrite(STDERR, "Error: Expected $type->name, got ".$token->type->name);
        exit (myError::E_OTHER->value);
    }
}

private function check2Types($token, $type1, $type2){
    if($token->type != $type1 && $token->type != $type2){
        fwrite(STDERR, "Error: Expected $type1->name or $type2->name, got ".$token->type->name);
        exit (myError::E_OTHER->value);
    }
}
}

?>