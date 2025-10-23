uboot_repo:=https://github.com/u-boot/u-boot.git
uboot_version:=v2024.07
uboot_src:=$(wrkdir_src)/u-boot
uboot_load_bin:=linux.bin
uboot_load_bin_addr:=0x80000
env_file:=$(uboot_src)/board/raspberrypi/rpi/rpi.env
uboot_defconfig:=rpi_4_defconfig
uboot_image:=$(wrkdir_plat_imgs)/u-boot.bin

$(uboot_src):
	@echo 'U-BOOT: Downloading...'
	git clone --depth 1 --branch $(uboot_version) $(uboot_repo) $(uboot_src)

define build-uboot
$(strip $1): $(uboot_src)
	@echo 'U-BOOT: Configuring...'
	$(MAKE) -C $(uboot_src) $(strip $2)
	@echo 'U-BOOT: Modifying environment...'
	@printf "\n\nbootcmd_fatload=fatload mmc 0 $(uboot_load_bin_addr) $(uboot_load_bin); go $(uboot_load_bin_addr)\n" >> $(env_file)
	@printf "bootcmd=run bootcmd_fatload\n" >> $(env_file)
	@echo 'U-BOOT: Building...'
	$(MAKE) -C $(uboot_src) -j$(nproc)
endef

$(eval $(call build-uboot, $(uboot_image), $(uboot_defconfig)))
