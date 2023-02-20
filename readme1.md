
Implementační dokumentace k 1. úloze do IPP 2022/2023<br>
Jméno a příjmení: Jakub Mašek<br>
Login: xmasek19
## Analyzátor kódu v IPPcode23
Filtr je řízen syntaktickým analyzátorem a je rozdělen do pěti souborů: parse.php(hlavní skript), token.php(třída pro uložení tokenu) lex.php(lexikální analyzátor), syn_gen.php(syntaktický analyzátor a generátor XML), error.php(enumerační list s chybovými kódy). Je implementována možnost výpisu statistik do souboru.
### Hlavní skript *parse.php*
Skript se stará o zpracování argumentů, otevření vstupního souboru(zde standardního vstupu), zavolání syntaktického analyzátoru a generátoru XML a vytištění výstupu na standardní výstup.
### Reprezentace tokenu *token.php*
Skript obsahuje enumerační list s typy tokenů a třídu *Token*
Třída obsahuje atributy pro uložení tokenu, přesněji jeho typ, hodnotu a případně typ konstanty. Jeho konstruktor se stará o uložení atrubutů a metody get(Type/Value/ConstType) vrací hodnotu daného atributu.
### Lexikální analyzátor *lex.php*
Analyzátor je jedináčkem třídy *Lexer* a stará se o rozdělení vstupu na tokeny. Tokeny jsou uloženy v poli *$row* a při každém volání metody *nextToken()* je vrácen další token, včetně konce řádku. Privátní metody *newRow* se stará o načtení nového řádku do pole a metoda *getType* pomocí regulárních výrazů zjistí typ tokenu. V případě, že je token konstanta, je zjištěn navíc typ konstanty (int/bool/string/nil).
### Syntaktický analyzátor a generátor XML *syn_gen.php*
Třída *Parser* je jedináčkem a stará se o syntaktickou analýzu a generování XML. Obsahuje veřejné metody *checkHeader* pro kontrolu správnosti hlavičky v překládaném souboru a *analyse* pro samotnou analýzu kódu a generování XML. Dále třída obsahuje privátní metody pro generování XML kódu a pro kontrolu typů tokenů, které jsou volány v metodě *analyse*. Díky nim je kód pro samotnou kontrolu a generování XML velmi krátký a přehledný. Například pro kontrolu a generování instrukce formátu *\<opcode> \<var> \<symb>* je použit následující kód:
```
$instruction = $this->generateInstruction($simpleXML, $token);
$token = $lexer->newToken();
$this->checkType($token, tokenType::T_VAR);
$this->generateArg($instruction, $token, "var");

$token = $lexer->newToken();
$this->checkType($token, tokenType::T_VAR, tokenType::T_CONST);
$this->generateArgSymb($instruction, $token);
```
Překlad je implementován pomocí metody rekurzivního sestupu.
### Enumerační list s chybovými kódy *error.php*
Obsahuje enumerační list s chybovými kódy používanými v programu.