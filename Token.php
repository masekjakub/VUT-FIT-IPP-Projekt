<?php
/**
 * @file Token.php
 * @brief token class
 * @author Jakub Mašek
 * @date 2023-2-13
 */
class Token{
    private $type;
    private $value;
    private $constType;

    function __construct($type, $value, $constType){
        $this->type = $type;
        $this->value = $value;
        $this->constType = $constType;
    }

    function getType(){
        return $this->type;
    }
    function getValue(){
        return $this->value;
    }
    function getConstType(){
        return $this->constType;
    }
}