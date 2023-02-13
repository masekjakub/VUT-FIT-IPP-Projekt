<?php

/**
 * @file Syntax.php
 * @brief IPPcode23 syntax analyser and XML generator
 * @author Jakub Mašek
 * @date 2023-2-13
 */

require_once("Errors.php");

class Syntax
{
    private $insIndex = 1;
    private $argIndex = 1;
    private $lexer;

    function __construct($file)
    {
        $this->insIndex = 1;
        $this->argIndex = 1;
        $this->lexer = new Lexer($file);
    }

    /**
     * @brief checks header
     */
    function checkHeader()
    {
        $token = $this->lexer->newToken();
        while ($token->getType() == tokenType::T_EOL) {
            $token = $this->lexer->newToken();
        }

        if ($token->getType() != tokenType::T_HEADER) {
            fwrite(STDERR, "Error: Expected head");
            exit(myError::E_NOHEAD->value);
        }
    }

    /**
     * @brief syntax check and XML generation of one instruction 
     */
    function analyse($simpleXML)
    {
        $token = $this->lexer->newToken();

        switch ($token->getType()) {
            case tokenType::T_EOL:
                break;

                //opcode var symb
            case tokenType::T_MOVE:
            case tokenType::T_INT2CHAR:
            case tokenType::T_STRLEN:
            case tokenType::T_TYPE:
            case tokenType::T_NOT:

                $instruction = $this->generateInstruction($simpleXML, $token);
                $token = $this->lexer->newToken();
                $this->checkType($token, tokenType::T_VAR);
                $this->generateArg($instruction, $token, "var");

                $token = $this->lexer->newToken();
                $this->check2Types($token, tokenType::T_VAR, tokenType::T_CONST);
                $this->generateArgSymb($instruction, $token);

                $token = $this->lexer->newToken();
                $this->checkType($token, tokenType::T_EOL);
                break;

                //opcode
            case tokenType::T_CREATEFRAME:
            case tokenType::T_PUSHFRAME:
            case tokenType::T_POPFRAME:
            case tokenType::T_RETURN:
            case tokenTYpe::T_BREAK:
                $instruction = $this->generateInstruction($simpleXML, $token);
                $token = $this->lexer->newToken();
                $this->checkType($token, tokenType::T_EOL);
                break;

                //opcode var
            case tokenType::T_DEFVAR:
            case tokenType::T_POPS:
                $instruction = $this->generateInstruction($simpleXML, $token);
                $token = $this->lexer->newToken();
                $this->checkType($token, tokenType::T_VAR);
                $this->generateArg($instruction, $token, "var");

                $token = $this->lexer->newToken();
                $this->checkType($token, tokenType::T_EOL);
                break;

                //opcode symb
            case tokenType::T_PUSHS:
            case tokenType::T_WRITE:
            case tokenType::T_EXIT:
            case tokenType::T_DPRINT:
                $instruction = $this->generateInstruction($simpleXML, $token);
                $token = $this->lexer->newToken();
                $this->check2Types($token, tokenType::T_VAR, tokenType::T_CONST);
                $this->generateArgSymb($instruction, $token);

                $token = $this->lexer->newToken();
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
                $instruction = $this->generateInstruction($simpleXML, $token);
                $token = $this->lexer->newToken();
                $this->checkType($token, tokenType::T_VAR);
                $this->generateArg($instruction, $token, "var");

                $token = $this->lexer->newToken();
                $this->check2Types($token, tokenType::T_VAR, tokenType::T_CONST);
                $this->generateArgSymb($instruction, $token);

                $token = $this->lexer->newToken();
                $this->check2Types($token, tokenType::T_VAR, tokenType::T_CONST);
                $this->generateArgSymb($instruction, $token);

                $token = $this->lexer->newToken();
                $this->checkType($token, tokenType::T_EOL);
                break;

                //opcode var type
            case tokenType::T_READ:
                $instruction = $this->generateInstruction($simpleXML, $token);
                $token = $this->lexer->newToken();
                $this->checkType($token, tokenType::T_VAR);
                $this->generateArg($instruction, $token, "var");

                $token = $this->lexer->newToken();
                $this->checkType($token, tokenType::T_VARTYPE);
                $this->generateArg($instruction, $token, "type");

                $token = $this->lexer->newToken();
                $this->checkType($token, tokenType::T_EOL);
                break;

                //opcode label
            case tokenType::T_LABEL:
            case tokenType::T_JUMP:
            case tokenType::T_CALL:
                $instruction = $this->generateInstruction($simpleXML, $token);
                $token = $this->lexer->newToken();
                $this->checkType($token, tokenType::T_LABELNAME);
                $this->generateArg($instruction, $token, "label");

                $token = $this->lexer->newToken();
                $this->checkType($token, tokenType::T_EOL);
                break;

                //opcode label symb symb
            case tokenType::T_JUMPIFEQ:
            case tokenType::T_JUMPIFNEQ:
                $instruction = $this->generateInstruction($simpleXML, $token);
                $token = $this->lexer->newToken();
                $this->checkType($token, tokenType::T_LABELNAME);
                $this->generateArg($instruction, $token, "label");

                $token = $this->lexer->newToken();
                $this->check2Types($token, tokenType::T_VAR, tokenType::T_CONST);
                $this->generateArgSymb($instruction, $token);

                $token = $this->lexer->newToken();
                $this->check2Types($token, tokenType::T_VAR, tokenType::T_CONST);
                $this->generateArgSymb($instruction, $token);

                $token = $this->lexer->newToken();
                $this->checkType($token, tokenType::T_EOL);
                break;

            default:
                fwrite(STDERR, "Error: Unexpected token ".$token->getValue());
                exit(myError::E_WRONGOPCODE->value);
        }
    }

    /**
     * @brief generates XML code for instruction
     * @param $simpleXML SimpleXMLElement
     * @param $token Token with opcode
     * @return SimpleXMLElement with instruction
     */
    private function generateInstruction($simpleXML, $token)
    {
        $instruction = $simpleXML->addChild("instruction");
        $instruction->addAttribute("order", $this->insIndex);
        $instruction->addAttribute("opcode", strtoupper($token->getValue()));
        $this->insIndex++;
        $this->argIndex = 1;
        return $instruction;
    }

    /**
     * @brief generates XML code for argument
     * @param $instruction SimpleXMLElement with instruction
     * @param $token Token with argument
     * @param $type Type of argument
     */
    private function generateArg($instruction, $token, $type)
    {
        $arg = $instruction->addChild("arg" . $this->argIndex, htmlspecialchars($token->getValue()));
        $arg->addAttribute("type", $type);
        $this->argIndex++;
    }

    /**
     * @brief generates XML code for symbol argument
     * @param $instruction SimpleXMLElement with instruction
     * @param $token Token with argument
     */
    private function generateArgSymb($instruction, $token)
    {
        if ($token->getType() == tokenType::T_VAR) {
            $this->generateArg($instruction, $token, "var");
            return;
        }

        $this->generateArg($instruction, $token, $token->getConstType());
    }

    /**
     * @brief checks if token is of given type
     * @param $token Token to check
     * @param $type Type to check
     */
    private function checkType($token, $type)
    {
        if ($token->getType() != $type) {
            fwrite(STDERR, "Error: Expected $type->name, got " . $token->getType()->name);
            exit(myError::E_OTHER->value);
        }
    }

    /**
     * @brief checks if token is one of given types
     * @param $token Token to check
     * @param $type1 First type to check
     * @param $type2 Second type to check
     */
    private function check2Types($token, $type1, $type2)
    {
        if ($token->getType() != $type1 && $token->getType() != $type2) {
            fwrite(STDERR, "Error: Expected $type1->name or $type2->name, got " . $token->getType()->name);
            exit(myError::E_OTHER->value);
        }
    }
}
