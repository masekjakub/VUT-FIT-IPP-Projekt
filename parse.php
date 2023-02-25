<?php

/**
 * @file parse.php
 * @brief IPPcode23 parser
 * @author Jakub Mašek
 * @date 2023-2-16
 */

require_once("error.php");
require_once("syn_gen.php");
ini_set('display_errors', 'stderr');

// arguments
$shortopts  = "h";
$longopts  = array(
    "help",
    "stats:",
    "loc",
    "comments",
    "labels",
    "jumps",
    "fwjumps",
    "backjumps",
    "badjumps",
    "print:",

);
$opts = getopt($shortopts, $longopts, $index);

if (isset($opts["help"]) || isset($opts["h"])) {
    if (count($opts) != 1) {
        fwrite(STDERR, "Help option cannot be combinated with another one! Try only --help\n");
        exit(myError::E_WRONGPARAM->value);
    }
    echo "Usage:\n";
    echo "\tphp parse.php [options]\n\n";
    echo "Options:\n";
    echo "--help\t\t\tPrints this help.\n";
    echo "--stats=file\t\tSet file to print statistics to. Has to be set before following options.\n";
    echo "--loc\t\t\tPrints number of lines.\n";
    echo "--comments\t\tPrints number of comments.\n";
    echo "--labels\t\tPrints number of labels.\n";
    echo "--jumps\t\t\tPrints number of jumps.\n";
    echo "--fwjumps\t\tPrints number of forward jumps.\n";
    echo "--backjumps\t\tPrints number of backward jumps.\n";
    echo "--badjumps\t\tPrints number of bad jumps.\n";
    echo "--frequent\t\tPrints instructions ordered by number of occurrences.\n";
    echo "--print=\"string\"\tPrints string representation to file.\n";
    echo "\nDescription:\n";
    echo "Script reads IPPcode23 code from STDIN, checks syntax and generates XML representation to STDOUT.\n";
    echo "Every statistic is printed to file set before. Multiple files are possible.\n";
    echo "\nJakub Mašek, 2023, VUT FIT\n";
    exit(myError::E_OK->value);
}

if (isset($opts["stats"])) {
    if (is_array($opts["stats"]) && count($opts["stats"]) !== count(array_unique($opts["stats"]))) {
        fwrite(STDERR, "Duplicated --stats options! Try --help\n");
        exit(myError::E_WRONGOUTFILE->value);
    }
}

// setup
$fileName = "php://stdin";
$simpleXML = new SimpleXMLElement('<?xml version="1.0" encoding="UTF-8"?><program language="IPPcode23"></program>');
$syntax = new Syntax();
$lexer = new Lexer($fileName);

$syntax->checkHeader($lexer);
$syntax->analyse($simpleXML, $lexer);

print_r($simpleXML->asXML());

// stats
$statsArr = $lexer->getStatsArr();
$statsFileSet = 0;
for ($i = 1; $i < $argc; $i++) {

    if (preg_match("/^--stats=/", $argv[$i])) {
        if ($statsFileSet == 1) {
            fclose($statsFile);
        }
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
    
    if ($argv[$i] == "--frequent") {
        $opcodeStatArr = $statsArr["frequent"];
        foreach ($opcodeStatArr as $opcodeName => $count) {
            fwrite($statsFile, $opcodeName);
            if ($opcodeName !== array_key_last($opcodeStatArr)) {
                fwrite($statsFile, ",");
            }
        }
        fwrite($statsFile, "\n");
    }
    if ($argv[$i] == "--eol") {
        fwrite($statsFile, "\n");
    }
}

if ($statsFileSet == 1) {
    fclose($statsFile);
}

if($statsArr["badJumps"] != 0) {
    fwrite(STDERR, "Jump to undefined label found!\n");
    exit(myError::E_SEMANTIC->value);
}
exit(myError::E_OK->value);
