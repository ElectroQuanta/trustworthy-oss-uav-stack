#include <linux/module.h>
#include <linux/io.h>
#include <asm/barrier.h>

static int __init crash_init(void) {
 // 1. Corrupt ARM system registers
  pr_info("CRASH KMOD: Corrupting ARM system registers");
    asm volatile(
        "msr sctlr_el1, %0 \n\t"   // Disable MMU/caches
        "msr ttbr0_el1, %1 \n\t"    // Invalidate translation tables
        "msr ttbr1_el1, %1 \n\t"
        "msr tcr_el1, %2 \n\t"      // Destroy memory translation config
        : 
        : "r"(0xDEAD0000), "r"(0xBADC0FFEE), "r"(0xBAD1BAD1)
    );
    return 0;
}

static void __exit crash_exit(void) {
  return;
}

module_init(crash_init);
module_exit(crash_exit);
MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("Cross-environment crash test module");
