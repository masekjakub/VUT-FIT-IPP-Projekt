all: pack
pack:
	@zip xmasek19.zip parse.php Lexer.php Syntax.php Token.php Errors.php readme1.md
	@echo "Pack done."

check:
	@bash is_it_ok.sh xmasek19.zip testdir 1
	@rm -f xmasek19.zip
	@rm -rf testdir

clean:
	@rm -f xmasek19.zip
	@rm -rf testdir