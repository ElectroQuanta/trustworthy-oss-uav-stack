#include <linux/init.h>
#include <linux/module.h>
#include <linux/ioport.h>
#include <linux/io.h>

static u64 reserved_phys_addr = 0;    // Set via module parameter
#define RESERVED_SIZE 0x100000        // 1MB

module_param_named(reserved_phys_addr, reserved_phys_addr, ullong, 0);
MODULE_PARM_DESC(reserved_phys_addr, "Physical address of reserved memory region (hex)");

static int __init memcorrupt_init(void)
{
    void __iomem *addr;

    if (reserved_phys_addr == 0) {
        pr_err("[MEM CORRUPT]: reserved_phys_addr not specified!\n");
        return -EINVAL;
    }

    // Request access to the reserved memory region
    if (!request_mem_region(reserved_phys_addr, RESERVED_SIZE, "memcorrupt_module")) {
        pr_err("[MEM CORRUPT]: Failed to request memory region at 0x%llx\n", reserved_phys_addr);
        return -EBUSY;
    }

    // Map the physical address to kernel virtual address
    addr = ioremap(reserved_phys_addr, RESERVED_SIZE);
    if (!addr) {
        pr_err("[MEM CORRUPT]: Failed to ioremap 0x%llx\n", reserved_phys_addr);
        release_mem_region(reserved_phys_addr, RESERVED_SIZE);
        return -ENOMEM;
    }

    // Write to the reserved memory to trigger a crash
    pr_info("[MEM CORRUPT]: Writing to reserved memory at %px (physical 0x%llx)\n", addr, reserved_phys_addr);
    iowrite32(0xdeadbeef, addr);

    // Cleanup (unreachable if the write crashes the system)
    iounmap(addr);
    release_mem_region(reserved_phys_addr, RESERVED_SIZE);
    return 0;
}

static void __exit memcorrupt_exit(void)
{
    // No cleanup needed if the system crashes
}

module_init(memcorrupt_init);
module_exit(memcorrupt_exit);
MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("Crash VM by writing to reserved memory (with configurable address)");
