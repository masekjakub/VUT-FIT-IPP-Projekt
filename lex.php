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

    private $seenLabels = array();
    private $jumpsNoLabel = array();
    private $loc = 0;
    private $comments = 0;
    private $labels = 0;
    private $jumps = 0;
    private $fwJumps = 0;
    private $backJumps = 0;
    private $badJumps = 0;

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
                $token = new Token(tokenType::T_EOL, null, null);
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
            $constExploded = explode("@", $word, 2);
            $constType = $constExploded[0];
            $value = $constExploded[1];
        } else {
            $value = $word;
        }
        $token = new Token($type, $value, $constType);
        $this->index++;
        return $token;
    }

    /**
     * @brief reads new line from file
     */
    private function newRow()
    {
        $row = fgets($this->file);
        $row = preg_replace("/#.*$/", "", $row, -1, $replaceCount);
        $this->comments += $replaceCount;
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
        if (preg_match("/^.IPPcode23$/i", $word)) return tokenType::T_HEADER;
        if (preg_match("/^(TF|LF|GF)@[\p{L}_\-$&%\*!?][\d\p{L}_\-$&%\*!?]*$/", $word)) return tokenType::T_VAR;
        if (preg_match("/^int@[-+]?[0-9]+$/", $word)) return tokenType::T_CONST;
        if (preg_match("/^nil@nil$/", $word)) return tokenType::T_CONST;
        if (preg_match("/^bool@(true|false)$/", $word)) return tokenType::T_CONST;
        if (preg_match("/^string@([^\\\]|\\\\\d{3})*$/", $word)) return tokenType::T_CONST;
        if (preg_match("/^(int|string|bool)$/", $word) && !preg_match("/^LABEL$/i", $this->words[0])) return tokenType::T_VARTYPE;
        if (preg_match("/^[\p{L}_\-$&%\*!?][\d\p{L}_\-$&%\*!?]*$/i", $word) && $this->index == 1) {return tokenType::T_LABELNAME;}
        $this->loc++;
        if (preg_match("/^MOVE$/i", $word) && $this->index == 0) return tokenType::T_MOVE;
        if (preg_match("/^CREATEFRAME$/i", $word) && $this->index == 0) return tokenType::T_CREATEFRAME;
        if (preg_match("/^PUSHFRAME$/i", $word) && $this->index == 0) return tokenType::T_PUSHFRAME;
        if (preg_match("/^POPFRAME$/i", $word) && $this->index == 0) return tokenType::T_POPFRAME;
        if (preg_match("/^DEFVAR$/i", $word) && $this->index == 0) return tokenType::T_DEFVAR;
        if (preg_match("/^CALL$/i", $word) && $this->index == 0) {$this->countJumps();return tokenType::T_CALL;}
        if (preg_match("/^RETURN$/i", $word) && $this->index == 0) {$this->countJumps();return tokenType::T_RETURN;}
        if (preg_match("/^PUSHS$/i", $word) && $this->index == 0) return tokenType::T_PUSHS;
        if (preg_match("/^POPS$/i", $word) && $this->index == 0) return tokenType::T_POPS;
        if (preg_match("/^ADD$/i", $word) && $this->index == 0) return tokenType::T_ADD;
        if (preg_match("/^SUB$/i", $word) && $this->index == 0) return tokenType::T_SUB;
        if (preg_match("/^MUL$/i", $word) && $this->index == 0) return tokenType::T_MUL;
        if (preg_match("/^IDIV$/i", $word) && $this->index == 0) return tokenType::T_IDIV;
        if (preg_match("/^LT$/i", $word) && $this->index == 0) return tokenType::T_LT;
        if (preg_match("/^GT$/i", $word) && $this->index == 0) return tokenType::T_GT;
        if (preg_match("/^EQ$/i", $word) && $this->index == 0) return tokenType::T_EQ;
        if (preg_match("/^AND$/i", $word) && $this->index == 0) return tokenType::T_AND;
        if (preg_match("/^OR$/i", $word) && $this->index == 0) return tokenType::T_OR;
        if (preg_match("/^NOT$/i", $word) && $this->index == 0) return tokenType::T_NOT;
        if (preg_match("/^INT2CHAR$/i", $word) && $this->index == 0) return tokenType::T_INT2CHAR;
        if (preg_match("/^STRI2INT$/i", $word) && $this->index == 0) return tokenType::T_STRI2INT;
        if (preg_match("/^READ$/i", $word) && $this->index == 0) return tokenType::T_READ;
        if (preg_match("/^WRITE$/i", $word) && $this->index == 0) return tokenType::T_WRITE;
        if (preg_match("/^CONCAT$/i", $word) && $this->index == 0) return tokenType::T_CONCAT;
        if (preg_match("/^STRLEN$/i", $word) && $this->index == 0) return tokenType::T_STRLEN;
        if (preg_match("/^GETCHAR$/i", $word) && $this->index == 0) return tokenType::T_GETCHAR;
        if (preg_match("/^SETCHAR$/i", $word) && $this->index == 0) return tokenType::T_SETCHAR;
        if (preg_match("/^TYPE$/i", $word) && $this->index == 0) return tokenType::T_TYPE;
        if (preg_match("/^LABEL$/i", $word) && $this->index == 0){$this->countLabels();return tokenType::T_LABEL;}
        if (preg_match("/^JUMP$/i", $word) && $this->index == 0) {$this->countJumps();return tokenType::T_JUMP;}
        if (preg_match("/^JUMPIFEQ$/i", $word) && $this->index == 0) {$this->countJumps();return tokenType::T_JUMPIFEQ;}
        if (preg_match("/^JUMPIFNEQ$/i", $word) && $this->index == 0) {$this->countJumps();return tokenType::T_JUMPIFNEQ;}
        if (preg_match("/^EXIT$/i", $word) && $this->index == 0) return tokenType::T_EXIT;
        if (preg_match("/^DPRINT$/i", $word) && $this->index == 0) return tokenType::T_DPRINT;
        if (preg_match("/^BREAK$/i", $word) && $this->index == 0) return tokenType::T_BREAK;

        if (preg_match("/^\./i", $word)) {
            fwrite(STDERR, "ERROR: Wrong head: $word\n");
            exit(myError::E_NOHEAD->value);
        }

        if ($this->index == 0) {
            return tokenType::T_UNKNOWNOPCODE;
        }

        return tokenType::T_UNEXPECTEDTOKEN;
    }

    /**
     * @brief Counts backjumps and saves unknown labels jumps
     */
    private function countJumps()
    {
        $this->jumps++;
        if (isset($this->words[1])) {
            if (in_array($this->words[1], $this->seenLabels)) {
                $this->backJumps++;
            } else {
                array_push($this->jumpsNoLabel, $this->words[1]);
            }
        }
    }

    /**
     * @brief Counts labels and saves them
     */
    private function countLabels()
    {
        $this->labels++;
        if (isset($this->words[1])) {
            array_push($this->seenLabels,$this->words[1]);
        }
    }

    /**
     * @brief Returns array of stats
     * @return array of stats
     */
    public function getStatsArr()
    {
        foreach ($this->jumpsNoLabel as $jump) {
            if (in_array($jump, $this->seenLabels, false)) {
                $this->fwJumps++;
            }else{
                $this->badJumps++;
            }
        }
        $statsArr = array(
            "loc" => $this->loc,
            "comments" => $this->comments,
            "labels" => $this->labels,
            "jumps" => $this->jumps,
            "fwJumps" => $this->fwJumps,
            "backJumps" => $this->backJumps,
            "badJumps" => $this->badJumps,
        );
        return $statsArr;
    }
}
