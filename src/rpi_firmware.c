#define RPI_MAILBOX_IRQ_ID 65
#define RPI_HYP_ARG_START  1
#define RPI_HYP_ARG_END    2

spinlock_t rpi_firmware_lock = SPINLOCK_INITVAL;

static void rpi_mailbox_irq_handler(irqid_t irq_id) {
  vcpu_inject_irq(cpu()->vcpu, irq_id);
  interrupts_cpu_enable(irq_id, false);
}

void plat_rpi_init(void) {
  interrupts_reserve(RPI_MAILBOX_IRQ_ID, rpi_mailbox_irq_handler);
}

long rpi_mailbox_hypercall(unsigned long arg0, unsigned long arg1, unsigned long arg2)
{
  switch (arg0) {
  case RPI_HYP_ARG_START:
	spin_lock(&rpi_firmware_lock);
	interrupts_cpu_enable(RPI_MAILBOX_IRQ_ID, true);
	break;

  case RPI_HYP_ARG_END:
	interrupts_cpu_enable(RPI_MAILBOX_IRQ_ID, false);
	spin_unlock(&rpi_firmware_lock);
	break;

  default:
    ERROR("func %s, unknown arg0 = %lu", __func__, arg0);
  }

  return 0;
}
