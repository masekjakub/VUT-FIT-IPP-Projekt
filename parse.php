<?php
require_once("Token.php");
require_once("Lexer.php");
require_once("Syntax.php");
ini_set('display_errors', 'stderr');


$keywords = array("");

$shortopts  = "h";
$longopts  = array(
    "help",     // Required value
);
$args = getopt($shortopts,$longopts);
#print_r($args);
if(isset($args["help"]) || isset($args["h"])){
    echo "helpasdasdasdas\n";
    exit;
}
#var_dump($args);

$file = fopen('php://stdin', 'r');

$syntax = new Syntax();

$simpleXML = new SimpleXMLElement('<?xml version="1.0" encoding="UTF-8"?><program language="IPPcode23"></program>');

while(!feof($file)){
    $syntax->analyse($file, $simpleXML);
}

print_r($simpleXML->asXML());
exit (0);
?>