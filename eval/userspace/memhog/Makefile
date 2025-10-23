pwd_path := $(abspath .)

c_file := $(wildcard *.c)

app := $(basename $(c_file))

CC = $(CROSS_COMPILE)gcc

all:
	@echo "PWD: $(pwd_path)"
	@echo "C file: $(c_file)"
	@echo "app: $(app)"
	@echo "CC: $(CC)"
	$(CC) $(c_file) -O3 -lpthread -o $(app)

clean:
	@echo "Cleaning"
	@rm $(app) *.o
