<?php
require_once("Token.php");
require_once("Errors.php");

enum tokenType{
    case T_HEADER;
    case T_VAR;
    case T_CONST;
    case T_EOL;
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
}

class Lexer extends Token{

    private $index = 0;
    private $count = 0;
    private $words;
    private $stringRegex = "^string@([^\\\]+|\\\\\d{3})*$";



    public function newToken($file){
        //echo $this->index;
        //echo $this->count;
        if($this->index == $this->count){
            if($this->index != 0){
                $this->setType(tokenType::T_EOL);
                return $this;
            }
            $this->newRow($file);
        }

        $word = $this->words[$this->index];
        $word = trim($word);

        $this->setValue($word);
        $type = $this->getType($word);

        //print_r($type);
        if($type == tokenType::T_CONST){
            $constExploded = explode("@",$word);
            $this->setConstType($constExploded[0]);
            $this->setValue($constExploded[1]);
        }
        $this->setType($type);

        $this->index++;
        return $this;
    }

    private function newRow($file){
        $row = fgets($file);
        $row = preg_replace("/#.*$/","",$row);
        $row = preg_replace("/[[:blank:]]+/"," ",$row);
        $this->words = explode(" ",$row);
        $this->count = count($this->words);
        $this->index = 0;
        return;
    }

    private function getType($word){
        if(preg_match("/^$/", $word)) return tokenType::T_EOL;
        if(preg_match("/^(TF|LF|GF)@[ěščřžýáíéóúůďťňĎŇŤŠČŘŽÝÁÍÉÚŮĚÓa-zA-Z|_|-|$|&|%|\\*|!|?][ěščřžýáíéóúůďťňĎŇŤŠČŘŽÝÁÍÉÚŮĚÓa-zA-Z0-9|_|-|$|&|%|\\*|!|?]*$/", $word)) return tokenType::T_VAR;
        if(preg_match("/^(TF|LF|GF)@/i", $word)){
            fwrite(STDERR, "ERROR: Wrong variable name $word\n");
            exit(myError::E_OTHER->value);
        }

        if(preg_match("/^int@[-+]?[0-9]+$/", $word)) return tokenType::T_CONST;
        if(preg_match("/^nil@nil$/", $word)) return tokenType::T_CONST;
        if(preg_match("/^bool@(true|false)$/", $word)) return tokenType::T_CONST;
        if(preg_match("/$this->stringRegex/", $word)) return tokenType::T_CONST;

        //if(preg_match("/^(int|float|nil|bool|type|string)@[ěščřžýáíéóúůďťňĎŇŤŠČŘŽÝÁÍÉÚŮĚÓa-zA-Z0-9|.|\\\|<|>|\\-|\\/|\\+|-]+$/", $word)) return tokenType::T_CONST;
        if(preg_match("/^(int|float|nil|bool|type|string)@/i", $word)){
            fwrite(STDERR, "ERROR: Wrong constant name $word\n");
            exit(myError::E_OTHER->value);
        }

        if(preg_match("/^(int|string|bool)/", $word)) return tokenType::T_VARTYPE;
        if(preg_match("/^MOVE$/i", $word)) return tokenType::T_MOVE;
        if(preg_match("/^CREATEFRAME$/i", $word)) return tokenType::T_CREATEFRAME;
        if(preg_match("/^PUSHFRAME$/i", $word)) return tokenType::T_PUSHFRAME;
        if(preg_match("/^POPFRAME$/i", $word)) return tokenType::T_POPFRAME;
        if(preg_match("/^DEFVAR$/i", $word)) return tokenType::T_DEFVAR;
        if(preg_match("/^CALL$/i", $word)) return tokenType::T_CALL;
        if(preg_match("/^RETURN$/i", $word)) return tokenType::T_RETURN;
        if(preg_match("/^PUSHS$/i", $word)) return tokenType::T_PUSHS;
        if(preg_match("/^POPS$/i", $word)) return tokenType::T_POPS;
        if(preg_match("/^ADD$/i", $word)) return tokenType::T_ADD;
        if(preg_match("/^SUB$/i", $word)) return tokenType::T_SUB;
        if(preg_match("/^MUL$/i", $word)) return tokenType::T_MUL;
        if(preg_match("/^IDIV$/i", $word)) return tokenType::T_IDIV;
        if(preg_match("/^LT$/i", $word)) return tokenType::T_LT;
        if(preg_match("/^GT$/i", $word)) return tokenType::T_GT;
        if(preg_match("/^EQ$/i", $word)) return tokenType::T_EQ;
        if(preg_match("/^AND$/i", $word)) return tokenType::T_AND;
        if(preg_match("/^OR$/i", $word)) return tokenType::T_OR;
        if(preg_match("/^NOT$/i", $word)) return tokenType::T_NOT;
        if(preg_match("/^INT2CHAR$/i", $word)) return tokenType::T_INT2CHAR;
        if(preg_match("/^STRI2INT$/i", $word)) return tokenType::T_STRI2INT;
        if(preg_match("/^READ$/i", $word)) return tokenType::T_READ;
        if(preg_match("/^WRITE$/i", $word)) return tokenType::T_WRITE;
        if(preg_match("/^CONCAT$/i", $word)) return tokenType::T_CONCAT;
        if(preg_match("/^STRLEN$/i", $word)) return tokenType::T_STRLEN;
        if(preg_match("/^GETCHAR$/i", $word)) return tokenType::T_GETCHAR;
        if(preg_match("/^SETCHAR$/i", $word)) return tokenType::T_SETCHAR;
        if(preg_match("/^TYPE$/i", $word)) return tokenType::T_TYPE;
        if(preg_match("/^LABEL$/i", $word) && $this->index == 0) return tokenType::T_LABEL;
        if(preg_match("/^JUMP$/i", $word)) return tokenType::T_JUMP;
        if(preg_match("/^JUMPIFEQ$/i", $word)) return tokenType::T_JUMPIFEQ;
        if(preg_match("/^JUMPIFNEQ$/i", $word)) return tokenType::T_JUMPIFNEQ;
        if(preg_match("/^EXIT$/i", $word)) return tokenType::T_EXIT;
        if(preg_match("/^DPRINT$/i", $word)) return tokenType::T_DPRINT;
        if(preg_match("/^BREAK$/i", $word)) return tokenType::T_BREAK;
        if(preg_match("/^[ěščřžýáíéóúůďťňĎŇŤŠČŘŽÝÁÍÉÚŮĚÓa-zA-Z|_|\\-|$|&|%|\\*|!|?][ěščřžýáíéóúůďťňĎŇŤŠČŘŽÝÁÍÉÚŮĚÓa-zA-Z0-9|_|\\-|$|&|%|\\*|!|?]*$/", $word)) return tokenType::T_LABELNAME;
        if(preg_match("/^.IPPcode23$/i", $word)) return tokenType::T_HEADER;

        if(preg_match("/^\./i", $word)){
            fwrite(STDERR, "ERROR: Wrong head: $word\n");
            exit(myError::E_NOHEAD->value);
        }

        if($this->index == 0){
        fwrite(STDERR,"ERROR: Unknown opcode: $word\n");
        exit(myError::E_WRONGOPCODE->value);
        }
        else{
        fwrite(STDERR,"ERROR: Unexpected token: $word\n");
        exit(myError::E_OTHER->value);
        }
    }
}
?>