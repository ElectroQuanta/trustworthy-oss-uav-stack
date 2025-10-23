#define RPI_HYP_ARG_START  1
#define RPI_HYP_ARG_END 2
enum {HC_INVAL = 0, HC_IPC = 1, HC_RPI_FIRMWARE = 2};

static int
rpi_firmware_transaction(struct rpi_firmware *fw, u32 chan, u32 data)
{
    u32 message = MBOX_MSG(chan, data);
    int ret;

    WARN_ON(data & 0xf);

    mutex_lock(&transaction_lock);

    /* HYP call to lock mailbox access */
    register uint64_t x0 asm("x0") =
        ARM_SMCCC_CALL_VAL(ARM_SMCCC_FAST_CALL, ARM_SMCCC_SMC_64, ARM_SMCCC_OWNER_VENDOR_HYP, HC_RPI_FIRMWARE);
    register uint64_t aux = x0;
    register uint64_t x1 asm("x1") = RPI_HYP_ARG_START;
    register uint64_t x2 asm("x2") = 0; /* DO NOT CARE */
    asm volatile("hvc 0" : "=r"(x0) : "r"(x0), "r"(x1), "r"(x2) : "memory", "cc");

	/* Check for errors */
	if ((int64_t)x0 < 0) {
	  dev_err(fw->cl.dev, "HYPCALL START failed: ret = 0x%llx\n", x0);
	  return -EINVAL; /* Abort */
	}

    reinit_completion(&fw->c);
    ret = mbox_send_message(fw->chan, &message);
    if (ret >= 0) {
        if (wait_for_completion_timeout(&fw->c, HZ)) {
            ret = 0;
        } else {
            ret = -ETIMEDOUT;
            WARN_ONCE(1, "Firmware transaction timeout");
        }
    } else {
        dev_err(fw->cl.dev, "mbox_send_message failed for chan: %u, data: 0x%08x, ret: %d\n", chan, data, ret);
    }

    /* HYP call to unlock mailbox access */
    x0 = ARM_SMCCC_CALL_VAL(ARM_SMCCC_FAST_CALL, ARM_SMCCC_SMC_64,
			    ARM_SMCCC_OWNER_VENDOR_HYP, HC_RPI_FIRMWARE);
	aux = x0;
    x1 = RPI_HYP_ARG_END;
    x2 = 0; /* DO NOT CARE */
    asm volatile("hvc 0" : "=r"(x0) : "r"(x0), "r"(x1), "r"(x2) : "memory", "cc");

	/* Check for errors */
	if ((int64_t)x0 < 0) {
	  dev_err(fw->cl.dev, "HYPCALL END failed: ret = 0x%llx\n", x0);
	  return -EINVAL; /* Abort */
	}

    mutex_unlock(&transaction_lock);

    return ret;
}
