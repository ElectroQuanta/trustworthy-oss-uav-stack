#include <config.h>

VM_IMAGE(vm2_image, XSTR(BAO_DEMOS_WRKDIR_IMGS/linux_cam.bin)); /**< Cam */


/**< Cam */
#define VM2_MEM1_BASE  0x14400000ULL
#define VM2_MEM1_SIZE  0x27000000ULL
#define VM2_MEM2_BASE  0x100000000ULL
#define VM2_MEM2_SIZE  0x80000000ULL
/* #define VM2_MEM2_BASE  0x40000000ULL */
/* #define VM2_MEM2_SIZE  0x40000000ULL */
/* #define VM2_MEM2_BASE  0x40000000ULL */
/* #define VM2_MEM2_SIZE  0xbc000000ULL */
#define VM2_PCIE_MEM_BASE 0x600000000ULL
#define VM2_PCIE_MEM_SIZE 0x40000000ULL

struct config config = {

    .vmlist_size = 1,
    .vmlist = {
        {.image = VM_IMAGE_BUILTIN(vm2_image, VM2_MEM1_BASE),

         .entry = VM2_MEM1_BASE,

         .platform = {.cpu_num = 3,

                      .region_num = 3,
                      .regions = (struct vm_mem_region[]){
                          {.base = VM2_MEM1_BASE,
                           .size = VM2_MEM1_SIZE,
                           .place_phys = true,
                           .phys = VM2_MEM1_BASE},
                          {.base = VM2_MEM2_BASE,
                           .size = VM2_MEM2_SIZE,
                           .place_phys = true,
                           .phys = VM2_MEM2_BASE},
                          {.base = VM2_PCIE_MEM_BASE,
                           .size = VM2_PCIE_MEM_SIZE,
                           .place_phys = true,
                           .phys = VM2_PCIE_MEM_BASE}
                          },

                      .dev_num = 4,
                      .devs = (struct vm_dev_region[]){
                          /**< Arch timer interrupt */
                          {.interrupt_num = 1, .interrupts = (irqid_t[]){27}},
                          /**< Mailbox (required for firmware) */
                          {
                              //.pa = 0xfe00b880,
                              //.va = 0xfe00b880,
                              .pa = 0xfe00b000,
                              .va = 0xfe00b000,
                              .size = 0x1000,
                              /* .interrupt_num = 1, */
                              /* .interrupts = (irqid_t[]){65} */
                          },
                          /**< PCIE (required for USB devices) */
                          {.pa = 0xfd500000,
                           .va = 0xfd500000,
                           .size = 0x10000,
                           .interrupt_num = 2,
                           .interrupts = (irqid_t[]){179, 180}},

                          /**< Ethernet controller */
                          {/* GENET */
                           .pa = 0xfd580000,
                           .va = 0xfd580000,
                           .size = 0x10000,
                           .interrupt_num = 2,
                           .interrupts = (irqid_t[]){189, 190}},
		},

		.arch = {
		  .gic = {
			.gicd_addr = 0xff841000,
			.gicc_addr = 0xff842000,
		  }
		}
	  },
	}, /**< End VM2 */
  }, /**< End vm_list */
}; /**< End config */
