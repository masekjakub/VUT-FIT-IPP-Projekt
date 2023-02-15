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
$shortopts  = "hs:lcjp:";
$longopts  = array(
    "help",
    "stats:",
    "loc",
    "comments",
    "labels",
    "jumps",
    "print:",

);
$opts = getopt($shortopts, $longopts, $index);

if ((isset($opts["help"]) || isset($opts["h"])) && count($opts) == 1) {
    echo "Usage:\n";
    echo "php parse.php [-h]\n\n";
    echo "Description:\n";
    echo "Script reads IPPcode23 code from STDIN, checks syntax and generates XML representation to STDOUT.\n";
    echo "\nJakub Mašek, 2023, VUT FIT\n";
    exit(myError::E_OK->value);
}

// setup
$file = fopen('php://stdin', 'r');
$simpleXML = new SimpleXMLElement('<?xml version="1.0" encoding="UTF-8"?><program language="IPPcode23"></program>');
$syntax = new Syntax();
$lexer = new Lexer($file);

$syntax->checkHeader($lexer);
while (!feof($file)) {
    $syntax->analyse($simpleXML, $lexer);
}
// read line with EOF
$syntax->analyse($simpleXML, $lexer);

print_r($simpleXML->asXML());

// stats
$statsArr = $lexer->getStatsArr();
$statsFileSet = 0;
for ($i = 1; $i < $argc; $i++) {
    if (preg_match("/^--stats=/", $argv[$i])) {
        $fileName = preg_replace("/^--stats=/", "", $argv[$i]);
        $statsFile = fopen("$fileName", "w") or die("Unable to open file!");
        $statsFileSet = 1;
    }

    if ($statsFileSet == 0) {
        fwrite(STDERR, "Mising file to write to! Try --help\n");
        exit(myError::E_WRONGPARAM->value);
    }

    if (preg_match("/^--print=/", $argv[$i])) {
        $value = preg_replace("/^--print=/", "", $argv[$i]);
        fwrite($statsFile, "$value\n");
    }

    if ($argv[$i] == "--loc") {
        fwrite($statsFile, $statsArr["loc"] . "\n");
    }

    if ($argv[$i] == "--comments") {
        fwrite($statsFile, $statsArr["comments"] . "\n");
    }

    if ($argv[$i] == "--labels") {
        fwrite($statsFile, $statsArr["labels"] . "\n");
    }

    if ($argv[$i] == "--jumps") {
        fwrite($statsFile, $statsArr["jumps"] . "\n");
    }

    if ($argv[$i] == "--fwjumps") {
        fwrite($statsFile, $statsArr["fwJumps"] . "\n");
    }

    if ($argv[$i] == "--backjumps") {
        fwrite($statsFile, $statsArr["backJumps"] . "\n");
    }

    if ($argv[$i] == "--badjumps") {
        fwrite($statsFile, $statsArr["badJumps"] . "\n");
    }

    if ($argv[$i] == "--eol") {
        fwrite($statsFile, "\n");
    }
}

exit(myError::E_OK->value);
