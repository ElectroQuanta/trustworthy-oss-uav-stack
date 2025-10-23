#include <linux/module.h>
#include <linux/kernel.h>

static int __init panic_init(void)
{
    panic("Forced kernel panic!");
    return 0;
}

static void __exit panic_exit(void){
  return;
}

module_init(panic_init);
module_exit(panic_exit);
MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("Crash VM by writing to reserved memory");
