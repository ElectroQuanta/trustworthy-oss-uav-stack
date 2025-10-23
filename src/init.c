void init(cpuid_t cpu_id, paddr_t load_addr) {
  /**< Initialize CPUs, memory, and console */      
  cpu_init(cpu_id, load_addr);
  mem_init(load_addr);
  console_init();

  if (cpu_is_master())
	console_printk("Bao Hypervisor\n\r");

  interrupts_init(); /**< Initialize interrupt manager */

  if (cpu_is_master())
	plat_rpi_init(); /**< Initialize RPi platform */

  vmm_init(); /**< Initialize VM Manager */

  /* Should never reach here */
  while (1) { }
}
