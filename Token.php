<?php
class Token{
    public $type;
    public $value;
    public $constType;

    function setValue($inString){
        $this->value = $inString;
    }
    function setType($inType){
        $this->type = $inType;
    }
    function setConstType($inType){
        $this->constType = $inType;
    }
}