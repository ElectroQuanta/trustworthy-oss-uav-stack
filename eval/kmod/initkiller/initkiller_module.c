#include <linux/module.h>
#include <linux/pid.h>
#include <linux/sched.h>
#include <linux/mm.h>
#include <linux/highmem.h>
#include <linux/pgtable.h>
#include <linux/mm_types.h>

static int __init init_killer_init(void)
{
    struct task_struct *init_task;
    struct mm_struct *mm = NULL;
    struct vm_area_struct *vma;

    // Get init process (PID 1)
    init_task = pid_task(find_get_pid(1), PIDTYPE_PID);
    if (!init_task) return -ESRCH;

    mm = get_task_mm(init_task);
    if (!mm)
      return -EACCES;

    VMA_ITERATOR(vmi, mm, 0);

    pr_emerg("INIT_KILLER: Corrupting PID 1 (%s)\n", init_task->comm);

    // Modern VMA iteration for 6.6 kernel
    for_each_vma(vmi, vma) {
        unsigned long addr;
        for (addr = vma->vm_start; addr < vma->vm_end; addr += PAGE_SIZE) {
            struct page *page;
            void *kvirt;
            int ret;

            // Use FOLL_GET for page reference counting
            ret = get_user_pages_remote(mm, addr, 1,
                                      FOLL_WRITE | FOLL_GET,
                                      &page, NULL);
            if (ret != 1) continue;
            
            kvirt = kmap_local_page(page);
            memset(kvirt, 0xAA, PAGE_SIZE);
            kunmap_local(kvirt);
            put_page(page);
        }
    }

    mmput(mm);
    return 0;
}

module_init(init_killer_init);
MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("Init process memory corruptor (6.6 kernel)");
