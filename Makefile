all: pack
pack:
	@zip xmasek19.zip parse.php lex.php syn_gen.php token.php error.php readme1.md rozsireni
	@echo "Pack done."

pack2:
	@zip xmasek19.zip interpret.py parse.py error.py readme2.md
	@echo "Pack done."

check:
	@bash is_it_ok.sh xmasek19.zip testdir 1
	@rm -rf testdir

check2:
	@bash is_it_ok.sh xmasek19.zip testdir 2
	@rm -rf testdir

clean:
	@rm -f xmasek19.zip
	@rm -rf testdir