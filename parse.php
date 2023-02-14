<?php
/**
 * @file parse.php
 * @brief IPPcode23 parser
 * @author Jakub Mašek
 * @date 2023-2-13
 */

require_once("error.php");
require_once("syn_gen.php");
ini_set('display_errors', 'stderr');

// arguments
$shortopts  = "h";
$longopts  = array(
    "help",
);
$args = getopt($shortopts,$longopts);
if($argc != count($args)+1){
    fwrite(STDERR, "Wrong arguments!\n");
    exit(myError::E_WRONGPARAM->value);
}
if(isset($args["help"]) || isset($args["h"])){
    echo "helpasdasdasdas\n";
    exit(myError::E_OK->value);
}

// setup
$file = fopen('php://stdin', 'r');
$simpleXML = new SimpleXMLElement('<?xml version="1.0" encoding="UTF-8"?><program language="IPPcode23"></program>');
$syntax = new Syntax($file);

$syntax->checkHeader();
while(!feof($file)){
    $syntax->analyse($simpleXML);
}
// read line with EOF
$syntax->analyse($simpleXML);

print_r($simpleXML->asXML());
exit (myError::E_OK->value);
