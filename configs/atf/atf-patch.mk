define build-atf
	@echo 'ATF: Fix UART5 PL011 for PilotPi...'
	sed -i 's/serial0/serial5/g' $(atf_src)/plat/rpi/rpi4/rpi4_bl31_setup.c	
	sed -i 's/#define RPI4_IO_PL011_UART_OFFSET\tULL(0x00201000)/#define RPI4_IO_PL011_UART_OFFSET\tULL(0x00201a00)/' $(atf_src)/plat/rpi/rpi4/include/rpi_hw.h
	@echo 'ATF: Building...'
	$(MAKE) -C $(atf_src) bl31 PLAT=rpi4
endef
