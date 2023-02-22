<?php

/**
 * @file Syntax.php
 * @brief IPPcode23 syntax analyser and XML generator
 * @author Jakub Mašek
 * @date 2023-2-13
 */

require_once("error.php");
require_once("lex.php");

class Syntax
{
    private $insIndex = 1;
    private $argIndex = 1;

    public function __construct()
    {
        $this->insIndex = 1;
        $this->argIndex = 1;
    }

    /**
     * @brief checks header
     */
    public function checkHeader($lexer)
    {
        $token = $lexer->newToken();
        while ($token->getType() == tokenType::T_EOL) {
            $token = $lexer->newToken();
        }

        if ($token->getType() != tokenType::T_HEADER) {
            fwrite(STDERR, "Error: Expected head\n");
            exit(myError::E_NOHEAD->value);
        }
    }

    /**
     * @brief syntax check and XML generation of one instruction
     * @param $simpleXML SimpleXMLElement
     */
    public function analyse($simpleXML, $lexer)
    {
        while (1) {
            $token = $lexer->newToken();
            switch ($token->getType()) {
                case tokenType::T_EOL:
                    break;

                case tokenType::T_EOF:
                    return;

                    //opcode var symb
                case tokenType::T_MOVE:
                case tokenType::T_INT2CHAR:
                case tokenType::T_STRLEN:
                case tokenType::T_TYPE:
                case tokenType::T_NOT:

                    $instruction = $this->generateInstruction($simpleXML, $token);
                    $token = $lexer->newToken();
                    $this->checkType($token, tokenType::T_VAR);
                    $this->generateArg($instruction, $token, "var");

                    $token = $lexer->newToken();
                    $this->checkType($token, tokenType::T_VAR, tokenType::T_CONST);
                    $this->generateArgSymb($instruction, $token);

                    $token = $lexer->newToken();
                    $this->checkType($token, tokenType::T_EOL);
                    break;

                    //opcode
                case tokenType::T_CREATEFRAME:
                case tokenType::T_PUSHFRAME:
                case tokenType::T_POPFRAME:
                case tokenType::T_RETURN:
                case tokenTYpe::T_BREAK:
                    $instruction = $this->generateInstruction($simpleXML, $token);
                    $token = $lexer->newToken();
                    $this->checkType($token, tokenType::T_EOL);
                    break;

                    //opcode var
                case tokenType::T_DEFVAR:
                case tokenType::T_POPS:
                    $instruction = $this->generateInstruction($simpleXML, $token);
                    $token = $lexer->newToken();
                    $this->checkType($token, tokenType::T_VAR);
                    $this->generateArg($instruction, $token, "var");

                    $token = $lexer->newToken();
                    $this->checkType($token, tokenType::T_EOL);
                    break;

                    //opcode symb
                case tokenType::T_PUSHS:
                case tokenType::T_WRITE:
                case tokenType::T_EXIT:
                case tokenType::T_DPRINT:
                    $instruction = $this->generateInstruction($simpleXML, $token);
                    $token = $lexer->newToken();
                    $this->checkType($token, tokenType::T_VAR, tokenType::T_CONST);
                    $this->generateArgSymb($instruction, $token);

                    $token = $lexer->newToken();
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
                    $token = $lexer->newToken();
                    $this->checkType($token, tokenType::T_VAR);
                    $this->generateArg($instruction, $token, "var");

                    $token = $lexer->newToken();
                    $this->checkType($token, tokenType::T_VAR, tokenType::T_CONST);
                    $this->generateArgSymb($instruction, $token);

                    $token = $lexer->newToken();
                    $this->checkType($token, tokenType::T_VAR, tokenType::T_CONST);
                    $this->generateArgSymb($instruction, $token);

                    $token = $lexer->newToken();
                    $this->checkType($token, tokenType::T_EOL);
                    break;

                    //opcode var type
                case tokenType::T_READ:
                    $instruction = $this->generateInstruction($simpleXML, $token);
                    $token = $lexer->newToken();
                    $this->checkType($token, tokenType::T_VAR);
                    $this->generateArg($instruction, $token, "var");

                    $token = $lexer->newToken();
                    $this->checkType($token, tokenType::T_VARTYPE);
                    $this->generateArg($instruction, $token, "type");

                    $token = $lexer->newToken();
                    $this->checkType($token, tokenType::T_EOL);
                    break;

                    //opcode label
                case tokenType::T_LABEL:
                case tokenType::T_JUMP:
                case tokenType::T_CALL:
                    $instruction = $this->generateInstruction($simpleXML, $token);
                    $token = $lexer->newToken();
                    $this->checkType($token, tokenType::T_LABELNAME);
                    $this->generateArg($instruction, $token, "label");

                    $token = $lexer->newToken();
                    $this->checkType($token, tokenType::T_EOL);
                    break;

                    //opcode label symb symb
                case tokenType::T_JUMPIFEQ:
                case tokenType::T_JUMPIFNEQ:
                    $instruction = $this->generateInstruction($simpleXML, $token);
                    $token = $lexer->newToken();
                    $this->checkType($token, tokenType::T_LABELNAME);
                    $this->generateArg($instruction, $token, "label");

                    $token = $lexer->newToken();
                    $this->checkType($token, tokenType::T_VAR, tokenType::T_CONST);
                    $this->generateArgSymb($instruction, $token);

                    $token = $lexer->newToken();
                    $this->checkType($token, tokenType::T_VAR, tokenType::T_CONST);
                    $this->generateArgSymb($instruction, $token);

                    $token = $lexer->newToken();
                    $this->checkType($token, tokenType::T_EOL);
                    break;

                default:
                    fwrite(STDERR, "Error: Unexpected token: " . $token->getValue() . "\n");
                    exit(myError::E_WRONGOPCODE->value);
            }
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
     * @brief checks if token is one of given types
     * @param $token Token to check
     * @param Types to check
     */
    private function checkType($token)
    {
        $isSame = 0;
        for ($i = 1; $i < func_num_args(); $i++) {
            if ($token->getType() == func_get_arg($i)) {
                $isSame = 1;
            }
        }
        if ($isSame == 0) {
            fwrite(STDERR, "Error: Unexpected type " . $token->getType()->name . "\n");
            exit(myError::E_OTHER->value);
        }
    }
}
