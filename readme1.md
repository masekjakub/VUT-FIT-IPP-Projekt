Implementační dokumentace k 1. úloze do IPP 2022/2023
Jméno a příjmení: Jakub Mašek
Login: xmasek19
## Analyzátor kódu v IPPcode23
Filtr je řízen syntaktickým analyzátorem a je rozdělen do pěti souborů: parse.php(hlavní skript), token.php(třída pro uložení tokenu) lex.php(lexikální analyzátor), syn_gen.php(syntaktický analyzátor a generátor XML), error.php(enumerační list s chybovými kódy). 
### Hlavní skript *parse.php*
Skript se stará o zpracování argumentů, otevření vstupního souboru(zde standardního vstupu), zavolání syntaktického analyzátoru a generátoru XML a vytištění výstupu na standardní výstup.
### Reprezentace tokenu *token.php*
Skript obsahuje enumerační list s typy tokenů a třídu *Token*
Třída obsahuje atributy pro uložení tokenu, přesněji jeho typ, hodnotu a případně typ konstanty. Jeho konstruktor se stará o uložení atrubutů a metody get(Type/Value/ConstType) vrací hodnotu daného atributu.
### Lexikální analyzátor *lex.php*
Analyzátor je jedináčkem třídy *Lexer* a stará se o rozdělení vstupu na tokeny. Tokeny jsou uloženy v poli *$row* a při každém volání metody *nextToken()* je vrácen další token, včetně konce řádku. Privátní metody *newRow* se stará o načtení nového řádku do pole a metoda *getType* pomocí regulárních výrazů zjistí typ tokenu.