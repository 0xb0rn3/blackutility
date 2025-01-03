#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <sys/ioctl.h>
#include <termios.h>   
#include <ncurses.h>
#include <time.h>
#include <errno.h>
#include <signal.h>
#include <sys/statvfs.h>
#include <pwd.h>
#include <limits.h>
#include <fcntl.h>
#include <ctype.h>
#include <sys/stat.h>
#include <sys/sysinfo.h>

/* Configuration Constants */
#define OUTPUT_BUFFER_SIZE 4096
#define PACMAN_OUTPUT_FILE "/tmp/pacman_output.tmp"
#define BACKUP_LOG "/var/log/blackutility.log.bak"
#define LOCK_FILE "/var/lock/blackutility.lock"
#define LOG_FILE "/var/log/blackutility.log"
#define TEMP_FILE "results.txt"
#define KALI_SOURCES_FILE "/etc/apt/sources.list.d/blackutil.list"
#define KALI_KEYRING_URL "https://http.kali.org/pool/main/k/kali-archive-keyring/kali-archive-keyring_2024.1_all.deb"
#define KALI_REPO_LINE "deb http://http.kali.org/kali kali-rolling main contrib non-free non-free-firmware"
#define TEMP_KEYRING_DEB "/tmp/kali-keyring.deb"

/* System Requirements */
#define MIN_DISK_SPACE 10737418240  // 10GB in bytes
#define MIN_RAM 4096                 // 4GB in MB
#define MAX_RETRIES 3
#define TIMEOUT_SECONDS 300

/* UI Constants */
#define LOADER_WIDTH 50
#define LOADER_UPDATE_INTERVAL 100000  // 100ms in microseconds
#define MAX_CMD_LENGTH 1024
#define MAX_LINE_LENGTH 256
#define PROGRESS_BAR_WIDTH 40
#define SPINNER_DELAY 100000 // Microseconds between spinner updates

/* Unicode Symbols for UI */
#define SYMBOL_SUCCESS "✓"
#define SYMBOL_ERROR "✗"
#define SYMBOL_WARNING "⚠"
#define SYMBOL_INFO "ℹ"
#define SYMBOL_ARROW "➜"
#define SYMBOL_LOCK "🔒"
#define SYMBOL_TOOL "🛠"
#define SYMBOL_UPDATE "⟳"
#define SYMBOL_INSTALL "📦"
#define BLOCK_FULL "█"
#define BLOCK_MEDIUM "▓"
#define BLOCK_LIGHT "░"

/* ANSI Color Codes */
#define ESC "\x1b"
#define RESET    ESC "[0m"
#define BOLD     ESC "[1m"
#define DIM      ESC "[2m"
#define ITALIC   ESC "[3m"
#define UNDER    ESC "[4m"

/* Modern RGB Colors */
#define FG_BLACK      ESC "[38;2;40;42;54m"
#define FG_RED        ESC "[38;2;255;85;85m"
#define FG_GREEN      ESC "[38;2;80;250;123m"
#define FG_YELLOW     ESC "[38;2;241;250;140m"
#define FG_BLUE       ESC "[38;2;98;114;164m"
#define FG_MAGENTA    ESC "[38;2;255;121;198m"
#define FG_CYAN       ESC "[38;2;139;233;253m"
#define FG_WHITE      ESC "[38;2;248;248;242m"

#define BG_BLACK      ESC "[48;2;40;42;54m"
#define BG_RED        ESC "[48;2;255;85;85m"
#define BG_GREEN      ESC "[48;2;80;250;123m"
#define BG_BLUE       ESC "[48;2;98;114;164m"

/* Program Banner */
const char* BANNER = 
    "\n" FG_CYAN BOLD
    "                ╔╗ ╦  ╔═╗╔═╗╦╔═╦ ╦╔╦╗╦╦  ╦╔╦╗╦ ╦\n"
    "                ╠╩╗║  ╠═╣║  ╠╩╗║ ║ ║ ║║  ║ ║ └┬┘\n"
    "                ╚═╝╩═╝╩ ╩╚═╝╩ ╩╚═╝ ╩ ╩╩═╝╩ ╩  ┴ \n"
    RESET
    FG_WHITE "                [ Universal Security Arsenal & Package Manager ]\n"
    FG_WHITE "                [ For Arch Linux & Debian-based Systems ]\n"
    FG_CYAN "                        Version 1.0.0-STABLE\n" RESET
    FG_BLUE "                    " SYMBOL_ARROW " by @0xb0rn3\n"
    "                    " SYMBOL_INFO " 0xb0rn3@proton.me\n" 
    "                    " SYMBOL_ARROW " twitter.com/0xb0rn3\n" RESET;

typedef enum {
    SYSTEM_UNKNOWN,
    SYSTEM_ARCH,
    SYSTEM_DEBIAN
} SystemType;

/* Global Variables */
static struct termios orig_termios;
static int terminal_initialized = 0;
volatile sig_atomic_t keep_running = 1;
volatile sig_atomic_t cleanup_needed = 0;
FILE* log_fp = NULL;
int lock_fd = -1;

/* Data Structures */
typedef struct {
    int suppress_output;
    char buffer[OUTPUT_BUFFER_SIZE];
    FILE* output_file;
} OutputControl;

typedef struct {
    int width;
    int total_width;
    int current;
    int total;
    const char* message;
    const char* status;
    time_t start_time;
    time_t estimated_completion;
} ProgressBar;

typedef struct {
    char name[MAX_LINE_LENGTH];
    char version[MAX_LINE_LENGTH];
    char status[MAX_LINE_LENGTH];
    int retry_count;
    time_t install_time;
    size_t size_bytes;
} Package;

typedef struct {
    int total_packages;
    int completed_packages;
    char current_package[MAX_LINE_LENGTH];
    int show_details;
} GlobalProgress;

/* Global Instances */
OutputControl g_output = {
    .suppress_output = 1,
    .buffer = {0},
    .output_file = NULL
};

GlobalProgress g_progress = {0};

/* Function Declarations */
void log_message(const char* message, const char* level);
void cleanup_resources(void);
void signal_handler(int signum);
void show_smooth_progress(const char* package, float percentage);
int execute_command(const char* command);

/* Terminal Handling Functions */
void disable_raw_mode() {
    if (terminal_initialized) {
        tcsetattr(STDIN_FILENO, TCSAFLUSH, &orig_termios);
        terminal_initialized = 0;
    }
}

int enable_raw_mode() {
    if (tcgetattr(STDIN_FILENO, &orig_termios) == -1) {
        perror("tcgetattr");
        return -1;
    }

    atexit(disable_raw_mode);
    struct termios raw = orig_termios;
    raw.c_lflag &= ~(ECHO | ICANON);
    
    if (tcsetattr(STDIN_FILENO, TCSAFLUSH, &raw) == -1) {
        perror("tcsetattr");
        return -1;
    }
    
    terminal_initialized = 1;
    return 0;
}

/* Output Control Functions */
void redirect_output(void) {
    g_output.output_file = fopen(PACMAN_OUTPUT_FILE, "w+");
    if (g_output.output_file) {
        dup2(fileno(g_output.output_file), STDERR_FILENO);
    }
}

void restore_output(void) {
    if (g_output.output_file) {
        fclose(g_output.output_file);
        g_output.output_file = NULL;
    }
}

/* Signal Handlers */
void signal_handler(int signum) {
    keep_running = 0;
    cleanup_needed = 1;
    
    char signal_msg[MAX_LINE_LENGTH];
    snprintf(signal_msg, sizeof(signal_msg), "Received signal %d", signum);
    log_message(signal_msg, "info");
    
    if (signum == SIGINT || signum == SIGTERM) {
        printf("\n%sOperation cancelled by user%s\n", FG_YELLOW, RESET);
    }
}

void alarm_handler(int signum) {
    (void)signum;
    log_message("Operation timed out", "error");
    keep_running = 0;
    cleanup_needed = 1;
}

/* File Operations */
int create_lock_file() {
    lock_fd = open(LOCK_FILE, O_CREAT | O_EXCL | O_RDWR, 0644);
    if (lock_fd < 0) {
        if (errno == EEXIST) {
            fprintf(stderr, "%sAnother instance is already running%s\n", FG_RED, RESET);
        } else {
            perror("Failed to create lock file");
        }
        return 0;
    }
    return 1;
}

void release_lock_file() {
    if (lock_fd >= 0) {
        close(lock_fd);
        unlink(LOCK_FILE);
    }
}

/* Logging System */
void initialize_logging() {
    if (access(LOG_FILE, F_OK) == 0) {
        rename(LOG_FILE, BACKUP_LOG);
    }
    
    log_fp = fopen(LOG_FILE, "w");
    if (!log_fp) {
        perror("Failed to open log file");
        return;
    }
    
    chmod(LOG_FILE, 0644);
}

void cleanup_logging() {
    if (log_fp) {
        fclose(log_fp);
        log_fp = NULL;
    }
}

void log_message(const char* message, const char* level) {
    if (!log_fp) return;

    time_t now;
    char timestamp[26];
    time(&now);
    ctime_r(&now, timestamp);
    timestamp[24] = '\0';
    
    fprintf(log_fp, "[%s] [%s] %s\n", timestamp, level, message);
    fflush(log_fp);
}

/* UI Helper Functions */
void get_terminal_width(int* width) {
    struct winsize w;
    ioctl(STDOUT_FILENO, TIOCGWINSZ, &w);
    *width = w.ws_col;
}

void print_modern_box(const char* text, const char* color, const char* symbol) {
    int width;
    get_terminal_width(&width);
    
    int text_len = strlen(text);
    int padding = 2;
    int total_width = text_len + (padding * 2) + 2;
    
    int left_margin = (width - total_width) / 2;
    if (left_margin < 0) left_margin = 0;
    
    printf("%s%*s╭", color, left_margin, "");
    for (int i = 0; i < total_width; i++) printf("─");
    printf("╮\n");
    
    printf("%*s│ %s %s %s│\n", 
           left_margin, "", symbol, text, RESET);
    
    printf("%s%*s╰", color, left_margin, "");
    for (int i = 0; i < total_width; i++) printf("─");
    printf("╯%s\n", RESET);
}

void show_smooth_progress(const char* package, float percentage) {
    static int last_percentage = -1;
    int current_percentage = (int)percentage;
    
    if (current_percentage == last_percentage && package == NULL) {
        return;
    }
    last_percentage = current_percentage;
    
    printf("\r\033[K");
    printf("%s%s%s ", FG_CYAN, SYMBOL_INSTALL, RESET);
    
    if (package) {
        printf("%-30.30s ", package);
    }
    
    printf("[");
    int bar_width = PROGRESS_BAR_WIDTH;
    int filled = (int)((percentage * bar_width) / 100.0);
    
    for (int i = 0; i < bar_width; i++) {
        if (i < filled) {
            printf("%s%s", FG_CYAN, BLOCK_FULL);
        } else if (i == filled) {
            printf("%s%s", FG_CYAN, BLOCK_MEDIUM);
        } else {
            printf("%s%s", DIM, BLOCK_LIGHT);
        }
    }
    
    printf("%s] %3d%%", RESET, current_percentage);
    
    static char spinner[] = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏";
    static int spinner_pos = 0;
    printf(" %s%c%s", FG_CYAN, spinner[spinner_pos++ % strlen(spinner)], RESET);
    
    fflush(stdout);
}

/* System Check Functions */
int check_root_privileges(void) {
    return (geteuid() == 0);
}

int check_system_requirements(void) {
    struct statvfs fs_stats;
    if (statvfs("/", &fs_stats) != 0) {
        log_message("Failed to check disk space", "error");
        return 0;
    }
    
    unsigned long long available_space = fs_stats.f_bsize * fs_stats.f_bavail;
    if (available_space < MIN_DISK_SPACE) {
        char space_msg[MAX_LINE_LENGTH];
        snprintf(space_msg, sizeof(space_msg),
                "Insufficient disk space. Required: %.2f GB, Available: %.2f GB",
                (double)MIN_DISK_SPACE / (1024*1024*1024),
                (double)available_space / (1024*1024*1024));
        log_message(space_msg, "error");
        return 0;
    }
    
    struct sysinfo si;
    if (sysinfo(&si) != 0) {
        log_message("Failed to check system memory", "error");
        return 0;
    }
    
    unsigned long total_ram_mb = (si.totalram * si.mem_unit) / (1024*1024);
    if (total_ram_mb < MIN_RAM) {
        char ram_msg[MAX_LINE_LENGTH];
        snprintf(ram_msg, sizeof(ram_msg),
                "Insufficient RAM. Required: %d MB, Available: %lu MB",
                MIN_RAM, total_ram_mb);
        log_message(ram_msg, "error");
        return 0;
    }
    
    // Check if running on Arch Linux
    FILE* os_release = fopen("/etc/os-release", "r");
    if (!os_release) {
        log_message("Failed to check OS type", "error");
        return 0;
    }
    
    char line[MAX_LINE_LENGTH];
    int is_arch = 0;
    while (fgets(line, sizeof(line), os_release)) {
        if (strstr(line, "ID=arch")) {
            is_arch = 1;
            break;
        }
    }
    fclose(os_release);
    
    if (!is_arch) {
        log_message("This utility requires Arch Linux", "error");
        return 0;
    }
    
    return 1;
}

/* String Helper Functions */
void str_to_upper(char* str) {
    for(int i = 0; str[i]; i++) {
        str[i] = toupper((unsigned char)str[i]);
    }
}

/* System Detection Functions */
SystemType detect_system_type() {
    FILE* os_release = fopen("/etc/os-release", "r");
    if (!os_release) {
        log_message("Failed to detect OS type", "error");
        return SYSTEM_UNKNOWN;
    }

    char line[MAX_LINE_LENGTH];
    SystemType type = SYSTEM_UNKNOWN;

    while (fgets(line, sizeof(line), os_release)) {
        if (strstr(line, "ID=arch")) {
            type = SYSTEM_ARCH;
            break;
        } else if (strstr(line, "ID=debian") || strstr(line, "ID=ubuntu") || 
                   strstr(line, "ID=kali") || strstr(line, "ID=parrot")) {
            type = SYSTEM_DEBIAN;
            break;
        }
    }
    
    fclose(os_release);
    return type;
}

int setup_kali_repository() {
    log_message("Setting up Kali Linux repository...", "info");

    char wget_cmd[MAX_CMD_LENGTH];
    snprintf(wget_cmd, sizeof(wget_cmd), 
            "wget -q %s -O %s", KALI_KEYRING_URL, TEMP_KEYRING_DEB);
    
    if (!execute_command(wget_cmd)) {
        log_message("Failed to download Kali keyring", "error");
        return 0;
    }

    if (!execute_command("dpkg -i " TEMP_KEYRING_DEB)) {
        log_message("Failed to install Kali keyring", "error");
        return 0;
    }

    FILE* sources = fopen(KALI_SOURCES_FILE, "w");
    if (!sources) {
        log_message("Failed to create Kali sources file", "error");
        return 0;
    }

    fprintf(sources, "%s\n", KALI_REPO_LINE);
    fclose(sources);

    if (!execute_command("apt-get update")) {
        log_message("Failed to update package lists", "error");
        return 0;
    }

    return 1;
}

/* Package Management Functions */
int execute_command(const char* command) {
    int status = system(command);
    if (status == -1) {
        log_message("Command execution failed", "error");
        return 0;
    }
    
    if (WIFEXITED(status)) {
        int exit_status = WEXITSTATUS(status);
        if (exit_status != 0) {
            char error_msg[MAX_LINE_LENGTH];
            snprintf(error_msg, sizeof(error_msg), 
                    "Command failed with exit status: %d", exit_status);
            log_message(error_msg, "error");
            return 0;
        }
    }
    
    return 1;
}

int generate_tool_list(void) {
    SystemType sys_type = detect_system_type();
    
    switch (sys_type) {
        case SYSTEM_ARCH:
            log_message("Setting up BlackArch repository...", "info");
            
            if (!execute_command("grep -q '\\[blackarch\\]' /etc/pacman.conf")) {
                const char* repo_cmd = "echo -e '[blackarch]\\nServer = https://blackarch.org/blackarch/$repo/os/$arch' >> /etc/pacman.conf";
                if (!execute_command(repo_cmd)) {
                    log_message("Failed to add BlackArch repository", "error");
                    return 0;
                }
                
                if (!execute_command("pacman-key --recv-key 4345771566D76038C7FEB43863EC0ADBEA87E4E3 && "
                                   "pacman-key --lsign-key 4345771566D76038C7FEB43863EC0ADBEA87E4E3")) {
                    log_message("Failed to install BlackArch keyring", "error");
                    return 0;
                }
            }
            
            if (!execute_command("pacman -Sy")) {
                log_message("Failed to update package database", "error");
                return 0;
            }
            
            if (!execute_command("pacman -Sg | grep -i security > " TEMP_FILE)) {
                log_message("Failed to generate tool list", "error");
                return 0;
            }
            break;
            
        case SYSTEM_DEBIAN:
            if (!setup_kali_repository()) {
                return 0;
            }
            
            FILE* tool_file = fopen(TEMP_FILE, "w");
            if (!tool_file) {
                log_message("Failed to create tool list", "error");
                return 0;
            }
            
            const char* categories[] = {
                "information-gathering", "vulnerability-analysis", 
                "wireless-attacks", "web-applications", "exploitation-tools",
                "forensics-tools", "stress-testing", "password-attacks",
                "reverse-engineering", "sniffing-spoofing", NULL
            };
            
            for (int i = 0; categories[i] != NULL; i++) {
                char cmd[MAX_CMD_LENGTH];
                snprintf(cmd, sizeof(cmd),
                        "apt-cache search '%s' | grep -i 'kali' >> " TEMP_FILE,
                        categories[i]);
                execute_command(cmd);
            }
            
            fclose(tool_file);
            break;
            
        default:
            log_message("Unsupported system type", "error");
            return 0;
    }
    
    return 1;
}

void install_tools(void) {
    SystemType sys_type = detect_system_type();
    if (sys_type == SYSTEM_UNKNOWN) {
        log_message("Unsupported system type", "error");
        return;
    }

    g_progress.completed_packages = 0;
    g_progress.show_details = 0;
    
    FILE* tool_list = fopen(TEMP_FILE, "r");
    if (!tool_list) {
        log_message("Failed to open tool list", "error");
        return;
    }
    
    // Count total packages
    char line[MAX_LINE_LENGTH];
    while (fgets(line, sizeof(line), tool_list)) {
        line[strcspn(line, "\n")] = 0;
        if (strlen(line) > 1) {
            g_progress.total_packages++;
        }
    }
    
    if (g_progress.total_packages == 0) {
        log_message("No packages found to install", "warning");
        fclose(tool_list);
        return;
    }
    
    rewind(tool_list);
    redirect_output();
    
    printf("\033[2J\033[H");  // Clear screen
    printf("%s", BANNER);
    show_smooth_progress("Preparing...", 0.0);
    
    while (fgets(line, sizeof(line), tool_list) && keep_running) {
        line[strcspn(line, "\n")] = 0;
        
        if (strlen(line) > 0) {
            strncpy(g_progress.current_package, line, MAX_LINE_LENGTH - 1);
            g_progress.current_package[MAX_LINE_LENGTH - 1] = '\0';
            
            float progress = ((float)g_progress.completed_packages / g_progress.total_packages) * 100.0;
            show_smooth_progress(line, progress);
            
    char install_cmd[MAX_CMD_LENGTH];
    if (sys_type == SYSTEM_ARCH) {
        snprintf(install_cmd, sizeof(install_cmd),
                "pacman -S --noconfirm --needed --overwrite=\"*\" %s >/dev/null 2>%s",
                line, PACMAN_OUTPUT_FILE);
    } else {
        snprintf(install_cmd, sizeof(install_cmd),
                "DEBIAN_FRONTEND=noninteractive apt-get install -y %s >/dev/null 2>%s",
                line, PACMAN_OUTPUT_FILE);
    }
            
            if (!execute_command(install_cmd)) {
                char error_msg[MAX_LINE_LENGTH];
                snprintf(error_msg, sizeof(error_msg), "Failed to install: %s", line);
                log_message(error_msg, "error");
            }
            
            g_progress.completed_packages++;
            usleep(LOADER_UPDATE_INTERVAL);
        }
    }
    
    show_smooth_progress("Installation Complete", 100.0);
    printf("\n");
    
    fclose(tool_list);
    restore_output();
    
    char completion_msg[MAX_LINE_LENGTH];
    snprintf(completion_msg, sizeof(completion_msg),
            "Completed installation of %d/%d packages",
            g_progress.completed_packages, g_progress.total_packages);
    log_message(completion_msg, "info");
}

/* Cleanup Function */
void cleanup_resources(void) {
    if (access(TEMP_FILE, F_OK) != -1) {
        remove(TEMP_FILE);
    }
    if (access(TEMP_KEYRING_DEB, F_OK) != -1) {
        remove(TEMP_KEYRING_DEB);
    }
    cleanup_logging();
    printf("%s", RESET);
    fflush(stdout);
    release_lock_file();
}

/* Main Program Entry */
int main(void) {
    // Initialize terminal
    if (enable_raw_mode() == -1) {
        fprintf(stderr, "Failed to initialize terminal\n");
        return 1;
    }

    // Check for existing instance
    if (!create_lock_file()) {
        disable_raw_mode();
        return 1;
    }

    // Initialize logging
    initialize_logging();
    
    // Set up signal handlers
    signal(SIGINT, signal_handler);
    signal(SIGALRM, alarm_handler);
    signal(SIGTERM, signal_handler);
    
    // Register cleanup function
    atexit(cleanup_resources);

    // Clear screen and show banner
    printf("\x1b[2J\x1b[H");
    printf("%s", BANNER);
    fflush(stdout);
    
    // Check privileges
    if (!check_root_privileges()) {
        print_modern_box("ROOT PRIVILEGES REQUIRED", FG_RED, SYMBOL_LOCK);
        return 1;
    }

    // Check system requirements
    if (!check_system_requirements()) {
        print_modern_box("SYSTEM REQUIREMENTS NOT MET", FG_RED, SYMBOL_ERROR);
        return 1;
    }

    // Show warning and get user confirmation
    print_modern_box("System Modification Warning", FG_YELLOW, SYMBOL_WARNING);
    printf("%sType %sAGREE%s to continue or %sDISAGREE%s to cancel: %s", 
           FG_WHITE, FG_GREEN, FG_WHITE, FG_RED, FG_WHITE, RESET);
    fflush(stdout);

    char response[10] = {0};
    alarm(30);  // Set 30-second timeout
    if (fgets(response, sizeof(response), stdin) == NULL) {
        log_message("Input timeout or error", "error");
        return 1;
    }
    alarm(0);  // Clear timeout

    response[strcspn(response, "\n")] = 0;
    str_to_upper(response);
    
    if (strcmp(response, "AGREE") != 0) {
        log_message("Operation cancelled by user", "warning");
        return 1;
    }

    // Generate tool list and install packages
    if (!generate_tool_list()) {
        log_message("Failed to generate tool list", "error");
        return 1;
    }

    install_tools();

    // Cleanup and exit
    log_message("Cleaning up...", "info");
    cleanup_resources();
    disable_raw_mode();
    
    return 0;
}
