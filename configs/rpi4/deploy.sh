#!/bin/bash
# src: https://github.com/bao-project/bao-demos/blob/master/platforms/rpi4/README.md

# Direct ANSI escape codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
ORANGE='\033[0;91m'
BLUE='\033[0;34m'
BOLD='\033[1m'
RESET='\033[0m'

#######################################################
# @brief Echoes text with syntax highlighting.
echo_with_syntax_highlighting() {
    local color="$1"
    local text="$2"
	printf "%b%s%b\n" "$color" "$text" "$RESET"
}

#######################################################
# @brief Prints info with the desired text
print_info() {
    echo_with_syntax_highlighting "$YELLOW$BOLD" "$1"
}

#######################################################
# @brief Prints error with the desired text
print_error() {
    echo_with_syntax_highlighting "$RED$BOLD" "$1"
}

##########################################
# @brief Get user choice from a list of options.
#
# This function presents a list of options to the user, prompts them to choose an option,
# and returns the index of the chosen option.
#
# @param options_array An array containing the available options.
# @return The index of the chosen option. Returns 255 if the choice is invalid.
#
# Example usage:
# options=("Option 1" "Option 2" "Option 3")
# get_user_choice "${options[@]}"
get_user_choice() {
    local options_array=("$@")
    local num_options=${#options_array[@]}

    # Print the options to the user
    echo "Please choose an option:"
    for ((i=0; i<num_options; i++)); do
        echo "$((i+1)). ${options_array[i]}"
    done

    read -rp "Enter the option number: " user_choice

    # Trim leading and trailing whitespace
    # The conditional statement checks two conditions:
    # 1. -n "$user_choice" ensures that the input is not empty.
    # 2. "$user_choice" =~ ^[0-9]+$ checks if the input contains only numeric
    # characters. This helps to ensure that the user enters a valid numeric choice.
    user_choice=${user_choice##*( )}
    user_choice=${user_choice%%*( )}

    if [[ -n "$user_choice" && "$user_choice" =~ ^[0-9]+$ ]]; then
	local index=$((user_choice - 1))
	if [ "$index" -ge 0 ] && [ "$index" -lt "$num_options" ]; then
	    return $index
	fi
    fi

    return 255 # Invalid choice (returning a non-zero value for error)
}

SD_DEVICE=""
BOOT_PART="BOOT"
ROOTFS_PART="rootfs"

YES_NO_OPTS=("yes" "no" "quit")

#export BAO_DEMOS_SDCARD_DEV=/dev/mmcblk0 # extracted from lsblk

check_requirements() {
	print_info "======================================"
	print_info "............... Checking requirements ................."
	print_info ">> Env setup?"
	if [ -z "$BAO_DEMOS_WRKDIR" ]; then
		if [ -z "$BAO_DEMOS" ] || [ -z "$PLATFORM" ]; then
			print_error "Info missing... Aborting"
			exit
		fi
		print_info "Rebuilding environment"
		export BAO_DEMOS_WRKDIR="${BAO_DEMOS}/wrkdir"
		export BAO_DEMOS_WRKDIR_SRC="${BAO_DEMOS_WRKDIR}/src"
		export BAO_DEMOS_WRKDIR_IMGS="${BAO_DEMOS_WRKDIR}/imgs"
		export BAO_DEMOS_WRKDIR_PLAT="${BAO_DEMOS_WRKDIR_IMGS}/${PLATFORM}"
	else
		print_info "Env correct!"
	fi

	export BAO_MOUNT_DIR="/run/media/$USER/SDCard"
	export BAO_DEMOS_SDCARD="${BAO_MOUNT_DIR}/$BOOT_PART"
	export BAO_DEMOS_FW="$BAO_DEMOS_WRKDIR_PLAT"/firmware
	export BAO_DEMOS_UBOOT="$BAO_DEMOS_WRKDIR_SRC"/u-boot
	export BAO_DEMOS_ATF="$BAO_DEMOS_WRKDIR_SRC"/arm-trusted-firmware

	valid_choice=false
	while [ "$valid_choice" = "false" ]; do
		print_info "SD Card inserted?"
		get_user_choice "${YES_NO_OPTS[@]}"
		answer_index=$?
		if [ $answer_index -eq 0 ]; then # yes
			valid_choice=true
		else
			if [ $answer_index -eq 2 ]; then #quit
				print_info "Quitting..."
				exit 1
			fi
		fi
	done

	# List block devices
	lsblk

	print_info ">> Setting SD card partition"
	# Read the user's choice
	read -rp "Enter the /dev/sdX partition (full): " answer
	if ls "$answer" >/dev/null 2>&1; then
		SD_DEVICE="$answer"
		print_info "SD device $answer found..."
		unmount_partitions "$SD_DEVICE"
	else
		print_error "Wrong device... aborting..."
		exit 1
	fi
	print_info "======================================"

	sudo mkdir -p "${BAO_MOUNT_DIR}"

	# check if it is mounted and unmount
}

unmount_partitions() {
	print_info ">> Unmounting partitions "
	target_device="$1"
	# Check if the target device is mounted
	if mount | grep -q "$target_device"; then
		echo "$target_device is currently mounted."

		# List mounted partitions of the target device
		mounted_partitions=$(mount | grep "$target_device" | awk '{print $1}')

		# Unmount each mounted partition
		for partition in $mounted_partitions; do
			echo "Unmounting $partition..."
			sudo umount "$partition"
		done

		print_info "All partitions of $target_device have been unmounted."
	else
		print_info "$target_device is not currently mounted... Proceeding..."
	fi
}

create_partition_fdisk() {
	local target_device="$1"
	print_info "====== Create Partition"

	# echo -e "o\nn\np\n\n16384\n\na\nt\nc\nw\n" | sudo fdisk "$target_device"

	# Table 1 layout
	# Bootloader (RAW partition) - should be copied using fdisk
	#raw_start_sectors=64
	#raw_size_sectors=20416
	# FAT32 partition (boot partition)
	fat_start_sectors=16384
	fat_size=500M
	# Root partition
	ext4_start_sectors=1228800

	# Remove any vfat signatures that may exist
	sudo wipefs -a "$target_device"1
	sudo wipefs -a "$target_device"2

	sudo fdisk "$target_device" <<EOF
o
n
p
1
$fat_start_sectors
+${fat_size}
t
0c
a
n
p
2
$ext4_start_sectors

p
w
EOF
	print_info "=================================================="
}

format_partition() {
	local target_partition="${1}1"
	# Format partitions
	print_info "==== Format partition"
	sudo mkfs.fat -v "$target_partition" -n BOOT
	print_info "=================================================="
}

copy_files() {
	target_device="$1"

	print_info "======================================"
	print_info "............... Copying files ................."
	print_info ">> Mounting partitions"

	sd1="${BAO_MOUNT_DIR}/${BOOT_PART}"
	target_partition="${target_device}1"

	if [ -d "$BAO_MOUNT_DIR" ]; then
		sudo rm -rf "$BAO_MOUNT_DIR"
	fi
	sudo mkdir -p "$sd1"
	sudo mount "$target_partition" "$sd1"
	lsblk

	print_info "==== Partition 1: $BOOT_PART"
	print_info "Erasing disk..."
	sudo rm -vrf "$sd1"/*

	print_info ">> Bootloader and firmware"

	# Copy firmware
	print_info ">> Overlays and dtbs..."
	sudo cp -rf "$BAO_DEMOS_WRKDIR_PLAT"/firmware/boot/* "$BAO_DEMOS_SDCARD"
	# Copy configuration txt
	print_info ">> Config.txt and comdline.txt..."
	sudo cp -v "$BAO_DEMOS/platforms/rpi4/config.txt" "$BAO_DEMOS_SDCARD"
	sudo cp -v "$BAO_DEMOS/platforms/rpi4/cmdline.txt" "$BAO_DEMOS_SDCARD"
	# Copy $DEMO binaries (linux.bin, freertos.bin, bao.bin)
	print_info ">> ${DEMO} binaries..."
	#sudo cp -v "$BAO_DEMOS_WRKDIR_PLAT/$DEMO"/bao.bin "$BAO_DEMOS_SDCARD"
	sudo cp -vr "$BAO_DEMOS_WRKDIR_PLAT/$DEMO"/*.bin "$BAO_DEMOS_SDCARD"
	#sudo cp -vr "$BAO_DEMOS_WRKDIR_PLAT/$DEMO"/*.elf "$BAO_DEMOS_SDCARD"
#	sudo cp -vr "$BAO_DEMOS_WRKDIR_PLAT/broadcom" "$BAO_DEMOS_SDCARD"
	# Copy Bootloader binaries(bl31.bin, u-boot.bin)
	print_info ">> Bootloader binaries..."
	sudo cp -v "$BAO_DEMOS_WRKDIR_PLAT"/*.bin "$BAO_DEMOS_SDCARD"
	# sudo cp -v $BAO_DEMOS_WRKDIR_PLAT/u-boot.bin $BAO_DEMOS_SDCARD
	# sudo cp -v $BAO_DEMOS_WRKDIR_IMGS/bao.bin $BAO_DEMOS_SDCARD

	sync
}

print_next_steps() {

	read -r -d '' my_string <<EOF
## 4) Setup board
Insert the sd card in the board's sd slot.

Connect to the Raspberry Pi's UART using a USB-to-TTL adapter to connect to the
Raspberry Pi's GPIO header UART pins. Use a terminal application such as 
"screen". For example:

"screen /dev/ttyUSB0 115200"

Turn on/reset your board.


## 5) Run u-boot commands

Quickly press any key to skip autoboot. If not possibly press "ctrl-c" until 
you get the u-boot prompt. Then load the bao image, and jump to it:

"fatload mmc 0 0x200000 bao.bin; go 0x200000"

You should see the firmware, bao and its guests printing on the UART.

At this point, depending on your demo, you might be able connect to one of the 
guests via ssh by connecting to the board's ethernet RJ45 socket.
EOF

	echo "$my_string"

}

sdcard_deploy() {
	ignore_error=false

	print_info ">> SD card deploy with ATF and U-Boot"

	check_requirements

	print_info "Format partitions?"
	get_user_choice "${YES_NO_OPTS[@]}"
	answer_index=$?
	case "$answer_index" in
	0) # yes
		create_partition_fdisk "$SD_DEVICE"
		format_partition "$SD_DEVICE"
		;;
	1) # no
		;;
	*)
		print_info "Quitting..."
		exit 1
		;;
	esac

	# Copy files
	copy_files "$SD_DEVICE"

	print_info ">> Deployment: SUCCESS!!"

	unmount_partitions "$SD_DEVICE"
	sudo eject "$SD_DEVICE"
	print_info "You can now safely eject the disk..."

	print_info "================== Next steps ================== "
	print_next_steps
}

sdcard_deploy
