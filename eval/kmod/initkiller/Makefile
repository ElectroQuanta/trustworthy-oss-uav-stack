# Get the current directory path
pwd_path := $(abspath .)

# Find the .c file in the current directory
kmod := initkiller

# Generate the corresponding .o file for obj-m
obj-m := $(kmod)_module.o

all:
	@echo "PWD: $(pwd_path)"
	@echo "Building module: $(basename $(obj-m))"
	make -C $(KERNEL_DIR) M=$(pwd_path) modules

clean:
	make -C $(KERNEL_DIR) M=$(pwd_path) clean
