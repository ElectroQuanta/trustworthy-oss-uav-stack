#include <config.h>

VM_IMAGE(vm1_image, XSTR(BAO_DEMOS_WRKDIR_IMGS/linux_px4.bin)); /**< PX4 */
VM_IMAGE(vm2_image, XSTR(BAO_DEMOS_WRKDIR_IMGS/baremetal.bin)); /**< Interf */

/**< PX4 */
/* #define VM1_MEM1_BASE  0x0b400000ULL */
/* #define VM1_MEM1_SIZE  0x09000000ULL */
#define VM1_MEM1_BASE  0x0bc00000ULL
#define VM1_MEM1_SIZE  0x08800000ULL
#define VM1_MEM2_BASE  0x40000000ULL
#define VM1_MEM2_SIZE  0xbc000000ULL

/**< Cam */
#define VM2_MEM1_BASE  0x14400000ULL
//#define VM2_MEM1_SIZE  0x27000000ULL
#define VM2_MEM1_SIZE  0x01000000ULL
/* #define VM2_MEM2_BASE  0x100000000ULL */
/* #define VM2_MEM2_SIZE 0x80000000ULL */

//#define VM2_MEM1_SIZE 0x08000000ULL


/* #define VM2_MEM2_BASE  0x40000000ULL */
/* #define VM2_MEM2_SIZE  0x40000000ULL */
/* #define VM2_MEM2_BASE  0x40000000ULL */
/* #define VM2_MEM2_SIZE  0xbc000000ULL */
#define VM2_PCIE_MEM_BASE 0x600000000ULL
#define VM2_PCIE_MEM_SIZE 0x40000000ULL

struct config config = {

    .vmlist_size = 1,
    .vmlist = {
        /* { */
        /*     //.image = {.base_addr = VM1_MEM1_BASE, */
        /*     //          .load_addr = VM_IMAGE_OFFSET(linux_image), */
        /*     //          .size = VM_IMAGE_SIZE(linux_image)}, */

        /*     .image = VM_IMAGE_BUILTIN(vm1_image, VM1_MEM1_BASE), */

        /*     .entry = VM1_MEM1_BASE, */
        /*     .cpu_affinity = 0b0001, // assign vCPUs 0 */

        /*     .platform = {.cpu_num = 1, */

        /*                  .region_num = 2, */
        /*                  .regions = */
		/* 	 (struct vm_mem_region[]){{.base = VM1_MEM1_BASE, */
		/* 				     .size = VM1_MEM1_SIZE, */
		/* 				     .place_phys = true, */
		/* 				     .phys = VM1_MEM1_BASE}, */
		/* 				  {.base = VM1_MEM2_BASE, */
		/* 				   .size = VM1_MEM2_SIZE, */
		/* 				   .place_phys = true, */
		/* 				   .phys = VM1_MEM2_BASE}}, */

        /*                  /\* .ipc_num = 1, *\/ */
        /*                  /\*  .ipcs = (struct ipc[]) { *\/ */
        /*                  /\*      { *\/ */
        /*                  /\*          .base = 0xf0000000, *\/ */
        /*                  /\*          .size = 0x00010000, *\/ */
        /*                  /\*          .shmem_id = 0, *\/ */
        /*                  /\*          .interrupt_num = 1, *\/ */
        /*                  /\*          .interrupts = (irqid_t[]) {52} *\/ */
        /*                  /\*      } *\/ */
        /*                  /\*  }, *\/ */

        /*                  .dev_num = 8, */
        /*                  .devs = */
        /*                      (struct vm_dev_region[]){ */
        /*                          /\**< Arch timer interrupt *\/ */
        /*                          {.interrupt_num = 1, */
        /*                           .interrupts = (irqid_t[]){27}}, */
        /*                          /\* /\\**< UARTs {0,2-5} (ttyAMA0, ttyAMA5) *\\/ *\/ */
        /*                          /\* {.pa = 0xfe201000, *\/ */
        /*                          /\*  .va = 0xfe201000, *\/ */
        /*                          /\*  .size = 0x1000, *\/ */
        /*                          /\*  .interrupt_num = 1, *\/ */
        /*                          /\*  .interrupts = (irqid_t[]){153}}, *\/ */
        /*                          /\**< Clock manager (cprman) *\/ */
        /*                          { */
        /*                              .pa = 0xfe101000, */
        /*                              .va = 0xfe101000, */
        /*                              .size = 0x2000, */
        /*                          }, */

        /*                          /\**< Mailbox (required for firmware) *\/ */
        /*                          { */
        /*                              //.pa = 0xfe00b880, */
        /*                              //.va = 0xfe00b880, */
        /*                              .pa = 0xfe00b000, */
        /*                              .va = 0xfe00b000, */
        /*                              .size = 0x1000, */
        /*                              /\* .interrupt_num = 1, *\/ */
        /*                              /\* .interrupts = (irqid_t[]){65} *\/ */
        /*                          }, */

        /*                          /\**< GPIO controller *\/ */
        /*                          {.pa = 0xfe200000, */
        /*                           .va = 0xfe200000, */
        /*                           //.size = 0xb4, */
        /*                           .size = 0x1000, */
        /*                           .interrupt_num = 2, */
        /*                           .interrupts = (irqid_t[]){145, 146}}, */

        /*                          /\**< SPI1 (ttySC0, ttySC1) and (aux) *\/ */
        /*                          {.pa = 0xfe215000, */
        /*                           .va = 0xfe215000, */
        /*                           .size = 0x1000, */
        /*                           .interrupt_num = 1, */
        /*                           .interrupts = (irqid_t[]){125}}, */

        /*                          /\**< spi0 (spidev) *\/ */
        /*                          {.pa = 0xfe204000, */
        /*                           .va = 0xfe204000, */
        /*                           .size = 0x1000, */
        /*                           .interrupt_num = 1, */
        /*                           .interrupts = (irqid_t[]){150}}, */

        /*                          /\**< dma (dma-controller) *\/ */
        /*                          {.pa = 0xfe007000, */
        /*                           .va = 0xfe007000, */
        /*                           .size = 0x1000, */
        /*                           .interrupt_num = 9, */
        /*                           .interrupts = (irqid_t[]){112, */
        /*                                                     113, 114, 115, 116, 117, 118, 119, 120}}, */
        /*                          /\**< i2c_arm (i2c1) *\/ */
        /*                          {.pa = 0xfe804000, */
        /*                           .va = 0xfe804000, */
        /*                           .size = 0x1000, */
        /*                           .interrupt_num = 1, */
        /*                           .interrupts = (irqid_t[]){149}}, */
        /*                      }, */

        /*                  .arch = {.gic = */
        /*                               { */
        /*                                   .gicd_addr = 0xff841000, */
        /*                                   .gicc_addr = 0xff842000, */
        /*                               }}}, */
        /* }, /\**< End VM1 *\/ */
        {.image = VM_IMAGE_BUILTIN(vm2_image, VM2_MEM1_BASE),

         .entry = VM2_MEM1_BASE,

         .cpu_affinity = 0b1110, // assign vCPUs 1, 2, and 3

         .platform = {.cpu_num = 3,

                      .region_num = 1,
                      .regions =
		      (struct vm_mem_region[]){{.base = VM2_MEM1_BASE,
						  .size = VM2_MEM1_SIZE,
						  /* .place_phys = true, */
						  /* .phys = VM2_MEM1_BASE, */
	      }},

                      .dev_num = 2,
                      .devs = (struct vm_dev_region[]){
                          /**< Arch timer interrupt */
                          {.interrupt_num = 1, .interrupts = (irqid_t[]){27}},
                                 /**< UARTs {0,2-5} (ttyAMA0, ttyAMA5) */
                                 {.pa = 0xfe201000,
                                  .va = 0xfe201000,
                                  .size = 0x1000,
                                  .interrupt_num = 1,
                                  .interrupts = (irqid_t[]){153}},
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
