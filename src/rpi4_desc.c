struct platform platform = {
    .cpu_num = 4,
    .region_num = (RPI4_MEM_GB > 1) ? 2: 1,
    .regions =  (struct mem_region[]) {
        {   
            .base = 0x80000,
            .size = 0x40000000 - 0x80000 - 0x4c00000,
        },
        {
            .base = 0x40000000,
            .size = ((RPI4_MEM_GB-1) * 0x40000000ULL) - 0x4000000,
        },
    },
    .console = {
        .base = 0xfe201000, /**< Page aligned address; the offset is added on platform.h */
    },
    .arch = {
        .gic = {
            .gicd_addr = 0xff841000,
            .gicc_addr = 0xff842000,
            .gich_addr = 0xff844000,
            .gicv_addr = 0xff846000,
            .maintenance_id = 25,
        },
    },
};
