<?php

/**
 * @file Token.php
 * @brief token class and tokenType enum
 * @author Jakub Mašek
 * @date 2023-2-13
 */

enum tokenType
{
    case T_HEADER;
    case T_VAR;
    case T_CONST;
    case T_EOL;
    case T_EOF;
    case T_UNDEF;
    case T_VARTYPE;
    case T_LABELNAME;

    case T_MOVE;
    case T_CREATEFRAME;
    case T_PUSHFRAME;
    case T_POPFRAME;
    case T_DEFVAR;
    case T_CALL;
    case T_RETURN;
    case T_PUSHS;
    case T_POPS;
    case T_ADD;
    case T_SUB;
    case T_MUL;
    case T_IDIV;
    case T_LT;
    case T_GT;
    case T_EQ;
    case T_AND;
    case T_OR;
    case T_NOT;
    case T_INT2CHAR;
    case T_STRI2INT;
    case T_READ;
    case T_WRITE;
    case T_CONCAT;
    case T_STRLEN;
    case T_GETCHAR;
    case T_SETCHAR;
    case T_TYPE;
    case T_LABEL;
    case T_JUMP;
    case T_JUMPIFEQ;
    case T_JUMPIFNEQ;
    case T_EXIT;
    case T_DPRINT;
    case T_BREAK;

    case T_UNKNOWNOPCODE;
    case T_UNEXPECTEDTOKEN;
}

class Token
{
    private $type;
    private $value;
    private $constType;

    public function __construct($type, $value, $constType)
    {
        $this->type = $type;
        $this->value = $value;
        $this->constType = $constType;
    }

    public function getType()
    {
        return $this->type;
    }

    public function getValue()
    {
        return $this->value;
    }
    
    public function getConstType()
    {
        return $this->constType;
    }
}
