<?php
/**
 * @file Lexer.php
 * @brief IPPcode23 lexer
 * @author Jakub Mašek
 * @date 2023-2-13
 */

require_once("token.php");
require_once("error.php");
class Lexer
{

    private $index = 0;
    private $count = 0;
    private $words;
    private $file;

    public function __construct($file)
    {
        $this->file = $file;
        $this->newRow($file);
    }

    /**
     * @brief returns new token from file
     * @return $token 
     */
    public function newToken()
    {
        // end of line
        if ($this->index == $this->count) {
            if ($this->index != 0) {
                $token = new Token(tokenType::T_EOL,null,null);
                $this->newRow();
                return $token;
            }
            $this->newRow();
        }

        $word = $this->words[$this->index];
        $word = trim($word);

        $type = $this->getType($word);
        $constType = null;

        if ($type == tokenType::T_CONST) {
            $constExploded = explode("@", $word);
            $constType = $constExploded[0];
            $value = $constExploded[1];
        } else {
            $value = $word;
        }
        $token = new Token($type,$value,$constType);
        $this->index++;
        return $token;
    }

    /**
     * @brief reads new line from file
     */
    private function newRow()
    {
        $row = fgets($this->file);
        $row = preg_replace("/#.*$/", "", $row);
        $row = preg_replace("/[[:blank:]]+/", " ", $row);
        $this->words = explode(" ", $row);
        $this->count = count($this->words);
        $this->index = 0;
        return;
    }

    /**
     * @brief returns type of token
     * @param $word word to be checked
     * @return tokenType type of token
     */
    private function getType($word)
    {
        if (preg_match("/^$/", $word)) return tokenType::T_EOL;
        if (preg_match("/^(TF|LF|GF)@[ěščřžýáíéóúůďťňĎŇŤŠČŘŽÝÁÍÉÚŮĚÓa-zA-Z_\-$&%\*!?][ěščřžýáíéóúůďťňĎŇŤŠČŘŽÝÁÍÉÚŮĚÓa-zA-Z0-9_\-$&%\*!?]*$/", $word)) return tokenType::T_VAR;
        if (preg_match("/^int@[-+]?[0-9]+$/", $word)) return tokenType::T_CONST;
        if (preg_match("/^nil@nil$/", $word)) return tokenType::T_CONST;
        if (preg_match("/^bool@(true|false)$/", $word)) return tokenType::T_CONST;
        if (preg_match("/^string@([^\\\]+|\\\\\d{3})*$/", $word)) return tokenType::T_CONST;
        if (preg_match("/^(int|string|bool)$/", $word) && !preg_match("/^LABEL$/i", $this->words[0])) return tokenType::T_VARTYPE;
        if (preg_match("/^MOVE$/i", $word)) return tokenType::T_MOVE;
        if (preg_match("/^CREATEFRAME$/i", $word)) return tokenType::T_CREATEFRAME;
        if (preg_match("/^PUSHFRAME$/i", $word)) return tokenType::T_PUSHFRAME;
        if (preg_match("/^POPFRAME$/i", $word)) return tokenType::T_POPFRAME;
        if (preg_match("/^DEFVAR$/i", $word)) return tokenType::T_DEFVAR;
        if (preg_match("/^CALL$/i", $word)) return tokenType::T_CALL;
        if (preg_match("/^RETURN$/i", $word)) return tokenType::T_RETURN;
        if (preg_match("/^PUSHS$/i", $word)) return tokenType::T_PUSHS;
        if (preg_match("/^POPS$/i", $word)) return tokenType::T_POPS;
        if (preg_match("/^ADD$/i", $word)) return tokenType::T_ADD;
        if (preg_match("/^SUB$/i", $word)) return tokenType::T_SUB;
        if (preg_match("/^MUL$/i", $word)) return tokenType::T_MUL;
        if (preg_match("/^IDIV$/i", $word)) return tokenType::T_IDIV;
        if (preg_match("/^LT$/i", $word)) return tokenType::T_LT;
        if (preg_match("/^GT$/i", $word)) return tokenType::T_GT;
        if (preg_match("/^EQ$/i", $word)) return tokenType::T_EQ;
        if (preg_match("/^AND$/i", $word)) return tokenType::T_AND;
        if (preg_match("/^OR$/i", $word)) return tokenType::T_OR;
        if (preg_match("/^NOT$/i", $word)) return tokenType::T_NOT;
        if (preg_match("/^INT2CHAR$/i", $word)) return tokenType::T_INT2CHAR;
        if (preg_match("/^STRI2INT$/i", $word)) return tokenType::T_STRI2INT;
        if (preg_match("/^READ$/i", $word)) return tokenType::T_READ;
        if (preg_match("/^WRITE$/i", $word)) return tokenType::T_WRITE;
        if (preg_match("/^CONCAT$/i", $word)) return tokenType::T_CONCAT;
        if (preg_match("/^STRLEN$/i", $word)) return tokenType::T_STRLEN;
        if (preg_match("/^GETCHAR$/i", $word)) return tokenType::T_GETCHAR;
        if (preg_match("/^SETCHAR$/i", $word)) return tokenType::T_SETCHAR;
        if (preg_match("/^TYPE$/i", $word)) return tokenType::T_TYPE;
        if (preg_match("/^LABEL$/i", $word) && $this->index == 0) return tokenType::T_LABEL;
        if (preg_match("/^JUMP$/i", $word)) return tokenType::T_JUMP;
        if (preg_match("/^JUMPIFEQ$/i", $word)) return tokenType::T_JUMPIFEQ;
        if (preg_match("/^JUMPIFNEQ$/i", $word)) return tokenType::T_JUMPIFNEQ;
        if (preg_match("/^EXIT$/i", $word)) return tokenType::T_EXIT;
        if (preg_match("/^DPRINT$/i", $word)) return tokenType::T_DPRINT;
        if (preg_match("/^BREAK$/i", $word)) return tokenType::T_BREAK;
        if (preg_match("/^[a-zěščřžýáíéóúůďťň_\-$&%\*!?][0-9a-zěščřžýáíéóúůďťň_\-$&%\*!?]*$/i", $word)) return tokenType::T_LABELNAME;
        if (preg_match("/^.IPPcode23$/i", $word)) return tokenType::T_HEADER;

        if (preg_match("/^\./i", $word)) {
            fwrite(STDERR, "ERROR: Wrong head: $word\n");
            exit(myError::E_NOHEAD->value);
        }

        if ($this->index == 0) {
            fwrite(STDERR, "ERROR: Unknown opcode: $word\n");
            exit(myError::E_WRONGOPCODE->value);
        }

        fwrite(STDERR, "ERROR: Unexpected token: $word\n");
        exit(myError::E_OTHER->value);
    }
}
