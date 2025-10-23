#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/init.h>

static int __init nullptr_module_init(void)
{
  pr_info("Crash module loaded: triggering undefined instruction exception!\n");
  /* Execute an undefined instruction; on ARM, udf #0 causes a fatal exception */
  asm volatile("udf #0");
  return 0;  /* This line is never reached */
}

static void __exit nullptr_module_exit(void)
{
    pr_info("Crash module exit called (should never be reached)\n");
}

module_init(nullptr_module_init);
module_exit(nullptr_module_exit);
MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("Crash VM by dereferencing the NULL ptr");
