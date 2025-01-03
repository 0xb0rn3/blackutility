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

// Modern Unicode symbols for improved visual feedback
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

// File paths and constants
#define BACKUP_LOG "/var/log/blackutility.log.bak"
#define LOCK_FILE "/var/lock/blackutility.lock"
#define LOG_FILE "/var/log/blackutility.log"
#define TEMP_FILE "results.txt"
#define MIN_DISK_SPACE 10737418240  // 10GB in bytes
#define MIN_RAM 4096                 // 4GB in MB
#define MAX_RETRIES 3
#define TIMEOUT_SECONDS 300
#define LOADER_WIDTH 50
#define LOADER_UPDATE_INTERVAL 100000  // 100ms in microseconds
#define MAX_CMD_LENGTH 1024
#define MAX_LINE_LENGTH 256
#define PROGRESS_BAR_WIDTH 40
#define SPINNER_DELAY 100000 // Microseconds between spinner updates

// Terminal handling structures
static struct termios orig_termios;
static int terminal_initialized = 0;

// Enhanced ANSI color palette with modern colors
#define ESC "\x1b"
#define RESET    ESC "[0m"
#define BOLD     ESC "[1m"
#define DIM      ESC "[2m"
#define ITALIC   ESC "[3m"
#define UNDER    ESC "[4m"

// Vibrant foreground colors using RGB values
#define FG_BLACK      ESC "[38;2;40;42;54m"
#define FG_RED        ESC "[38;2;255;85;85m"
#define FG_GREEN      ESC "[38;2;80;250;123m"
#define FG_YELLOW     ESC "[38;2;241;250;140m"
#define FG_BLUE       ESC "[38;2;98;114;164m"
#define FG_MAGENTA    ESC "[38;2;255;121;198m"
#define FG_CYAN       ESC "[38;2;139;233;253m"
#define FG_WHITE      ESC "[38;2;248;248;242m"

// Modern background colors
#define BG_BLACK      ESC "[48;2;40;42;54m"
#define BG_RED        ESC "[48;2;255;85;85m"
#define BG_GREEN      ESC "[48;2;80;250;123m"
#define BG_BLUE       ESC "[48;2;98;114;164m"

// Modern ASCII art banner with compact design
const char* BANNER = 
    "\n" FG_CYAN BOLD
    "██████╗ ██╗      █████╗  ██████╗██╗  ██╗██╗   ██╗████████╗██╗██╗\n"
    "██╔══██╗██║     ██╔══██╗██╔════╝██║ ██╔╝██║   ██║╚══██╔══╝██║██║\n"
    "██████╔╝██║     ███████║██║     █████╔╝ ██║   ██║   ██║   ██║██║\n"
    "██╔══██╗██║     ██╔══██║██║     ██╔═██╗ ██║   ██║   ██║   ██║██║\n"
    "██████╔╝███████╗██║  ██║╚██████╗██║  ██╗╚██████╔╝   ██║   ██║███████╗\n"
    "╚═════╝ ╚══════╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝ ╚═════╝    ╚═╝   ╚═╝╚══════╝\n"
    RESET
    FG_WHITE "           [ Advanced Security Arsenal for Arch Linux ]\n"
    FG_CYAN "                      Version 0.3-ALFA\n" RESET
    FG_BLUE "         " SYMBOL_ARROW " Developed & Maintained by @0xb0rn3\n" RESET
    FG_MAGENTA "         " SYMBOL_LOCK " Stay Ethical. Stay Secure. Stay Vigilant.\n" RESET;

// Global variables and structures
volatile sig_atomic_t keep_running = 1;
volatile sig_atomic_t cleanup_needed = 0;
FILE* log_fp = NULL;
int lock_fd = -1;

// Enhanced output control structure
typedef struct {
    int suppress_output;
    char buffer[OUTPUT_BUFFER_SIZE];
    FILE* output_file;
} OutputControl;

// Global output control instance
OutputControl g_output = {
    .suppress_output = 1,
    .buffer = {0},
    .output_file = NULL
};

// Progress tracking structures
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

// Global progress instance
GlobalProgress g_progress = {0};

// Function to redirect command output
void redirect_output(void) {
    g_output.output_file = fopen(PACMAN_OUTPUT_FILE, "w+");
    if (g_output.output_file) {
        dup2(fileno(g_output.output_file), STDERR_FILENO);
    }
}

// Function to restore output
void restore_output(void) {
    if (g_output.output_file) {
        fclose(g_output.output_file);
        g_output.output_file = NULL;
    }
}

// Enhanced progress bar with smoother animation
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
// Forward declarations for signal handlers
void signal_handler(int signum);
void alarm_handler(int signum);

// Signal handler implementations
void signal_handler(int signum) {
    keep_running = 0;
    cleanup_needed = 1;
    
    // Log the signal received
    char signal_msg[MAX_LINE_LENGTH];
    snprintf(signal_msg, sizeof(signal_msg), "Received signal %d", signum);
    log_message(signal_msg, "info");
    
    if (signum == SIGINT || signum == SIGTERM) {
        printf("\n%sOperation cancelled by user%s\n", FG_YELLOW, RESET);
    }
}

void alarm_handler(int signum) {
    (void)signum;  // Unused parameter
    log_message("Operation timed out", "error");
    keep_running = 0;
    cleanup_needed = 1;
}

// System requirements check function
int check_system_requirements(void) {
    // Check available disk space
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
    
    // Check RAM
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

// Terminal handling functions
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

// Helper functions
void str_to_upper(char* str) {
    for(int i = 0; str[i]; i++) {
        str[i] = toupper((unsigned char)str[i]);
    }
}

// File operations
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

// Initialize logging system
void initialize_logging() {
    // Backup existing log if present
    if (access(LOG_FILE, F_OK) == 0) {
        rename(LOG_FILE, BACKUP_LOG);
    }
    
    log_fp = fopen(LOG_FILE, "w");
    if (!log_fp) {
        perror("Failed to open log file");
        return;
    }
    
    // Set proper permissions
    chmod(LOG_FILE, 0644);
}

void cleanup_logging() {
    if (log_fp) {
        fclose(log_fp);
        log_fp = NULL;
    }
}
// Log message with timestamp and level
void log_message(const char* message, const char* level) {
    if (!log_fp) return;

    time_t now;
    char timestamp[26];
    time(&now);
    ctime_r(&now, timestamp);
    timestamp[24] = '\0';  // Remove newline
    
    fprintf(log_fp, "[%s] [%s] %s\n", timestamp, level, message);
    fflush(log_fp);
}

// Get terminal width for proper formatting
void get_terminal_width(int* width) {
    struct winsize w;
    ioctl(STDOUT_FILENO, TIOCGWINSZ, &w);
    *width = w.ws_col;
}

// Parse package information from pacman output
void parse_package_info(const char* line, Package* pkg) {
    memset(pkg, 0, sizeof(Package));
    
    if (strstr(line, "is up to date")) {
        char* first_space = strchr(line, ' ');
        if (first_space) {
            int name_len = first_space - line;
            if (name_len >= MAX_LINE_LENGTH) {
                name_len = MAX_LINE_LENGTH - 1;
            }
            strncpy(pkg->name, line, name_len);
            pkg->name[name_len] = '\0';  // Ensure null-termination
            strncpy(pkg->status, "up-to-date", MAX_LINE_LENGTH - 1);
            pkg->status[MAX_LINE_LENGTH - 1] = '\0';
        }
    }
}
// Print modern-style box with symbol
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

// Show modern progress bar with package information
void show_modern_progress(ProgressBar* bar, Package* pkg) {
    get_terminal_width(&bar->total_width);
    int available_width = bar->total_width - 50;
    int filled_width = (int)(((float)bar->current / (float)bar->total) * available_width);
    float percentage = (float)bar->current / bar->total * 100;
    
    printf("\r\033[K");
    
    const char* status_symbol = strcmp(pkg->status, "up-to-date") == 0 ? 
                               SYMBOL_SUCCESS : SYMBOL_INSTALL;
    const char* status_color = strcmp(pkg->status, "up-to-date") == 0 ? 
                              FG_GREEN : FG_CYAN;
    
    printf("%s%s%s ", status_color, status_symbol, RESET);
    printf("%s%-30.30s%s ", BOLD, pkg->name, RESET);
    
    printf("%s[", DIM);
    for (int i = 0; i < available_width; i++) {
        if (i < filled_width) {
            printf("%s%s", FG_CYAN, BLOCK_FULL);
        } else if (i == filled_width) {
            printf("%s%s", FG_CYAN, BLOCK_MEDIUM);
        } else {
            printf("%s%s", DIM, BLOCK_LIGHT);
        }
    }
    printf("%s] ", RESET);
    
    printf("%s%5.1f%%%s", FG_YELLOW, percentage, RESET);
    
    if (strcmp(pkg->status, "up-to-date") == 0) {
        printf(" %s%s%s", FG_GREEN, "up to date", RESET);
    }
    
    fflush(stdout);
}

// Show animated spinner
void show_spinner(const char* message) {
    static const char spinner[] = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏";
    static int pos = 0;
    
    printf("\r%s %s %s", 
           FG_CYAN, 
           spinner[pos++ % strlen(spinner)], 
           message);
    
    fflush(stdout);
    usleep(SPINNER_DELAY);
}

// Status message with appropriate styling
void status_message(const char* message, const char* status) {
    const char* icon;
    const char* color;
    
    if (strcmp(status, "success") == 0) {
        icon = SYMBOL_SUCCESS;
        color = FG_GREEN;
    } else if (strcmp(status, "error") == 0) {
        icon = SYMBOL_ERROR;
        color = FG_RED;
    } else if (strcmp(status, "warning") == 0) {
        icon = SYMBOL_WARNING;
        color = FG_YELLOW;
    } else {
        icon = SYMBOL_INFO;
        color = FG_BLUE;
    }
    
    printf("%s%s %s%s\n", color, icon, message, RESET);
    log_message(message, status);
}

// Execute command with proper error handling
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

// Check for root privileges
int check_root_privileges(void) {
    if (geteuid() != 0) {
        return 0;
    }
    return 1;
}

// Cleanup resources before exit
void cleanup_resources(void) {
    if (access(TEMP_FILE, F_OK) != -1) {
        remove(TEMP_FILE);
    }
    cleanup_logging();
    printf("%s", RESET);
    fflush(stdout);
    release_lock_file();
}

// Install package with retry mechanism
int install_package(const char* package_name, Package* pkg) {
    char install_cmd[MAX_CMD_LENGTH];
    int retry_count = 0;
    
    // Safety check: Make sure package_name isn't NULL
    if (!package_name) {
        log_message("Package name is NULL", "error");
        return 0;
    }
    
    // Check if package name is too long
    // We subtract 100 to leave room for the command prefix and suffix
    if (strlen(package_name) > MAX_CMD_LENGTH - 100) {
        char error_msg[MAX_LINE_LENGTH];
        snprintf(error_msg, sizeof(error_msg), 
                "Package name too long: %s", package_name);
        log_message(error_msg, "error");
        return 0;
    }
    
    while (retry_count < MAX_RETRIES && keep_running) {
        // Build the command string safely
        int cmd_result = snprintf(install_cmd, sizeof(install_cmd),
                "pacman -S --noconfirm --needed --overwrite=\"*\" %s", 
                package_name);
        
        // Check if command string was built correctly
        if (cmd_result >= sizeof(install_cmd) || cmd_result < 0) {
            log_message("Failed to build install command", "error");
            return 0;
        }
        
        // Set timeout alarm
        alarm(TIMEOUT_SECONDS);
        
        if (execute_command(install_cmd)) {
            alarm(0);  // Clear the alarm
            pkg->install_time = time(NULL);
            return 1;  // Success!
        }
        
        alarm(0);  // Clear the alarm
        retry_count++;
        
        if (retry_count < MAX_RETRIES) {
            // Only sleep and log if we're going to retry
            sleep(2);  // Wait before retrying
            
            char retry_msg[MAX_LINE_LENGTH];
            snprintf(retry_msg, sizeof(retry_msg),
                    "Retrying installation of %s (attempt %d/%d)",
                    package_name, retry_count + 1, MAX_RETRIES);
            log_message(retry_msg, "warning");
        }
    }
    
    return 0;  // Installation failed after all retries
}
void update_unified_loader(const char* current_package, int force_update) {
    static time_t last_update = 0;
    time_t now = time(NULL);
    
    // Limit update frequency unless forced
    if (!force_update && (now - last_update) < 1) {
        return;
    }
    last_update = now;
    
    // Calculate progress
    float percentage = (float)g_progress.completed_packages / g_progress.total_packages * 100;
    int filled_width = (int)((percentage / 100.0) * LOADER_WIDTH);
    
    // Clear line and move to start
    printf("\r\033[K");
    
    // Show unified progress bar
    printf("%s%s%s Installing BlackArch Tools ", FG_CYAN, SYMBOL_INSTALL, RESET);
    printf("[");
    
    for (int i = 0; i < LOADER_WIDTH; i++) {
        if (i < filled_width) {
            printf("%s%s", FG_CYAN, BLOCK_FULL);
        } else if (i == filled_width) {
            printf("%s%s", FG_CYAN, BLOCK_MEDIUM);
        } else {
            printf("%s%s", DIM, BLOCK_LIGHT);
        }
    }
    
    printf("%s] %5.1f%%", RESET, percentage);
    
    // Show current package in a subtle way
    if (strlen(current_package) > 0) {
        printf(" %s%s%s", DIM, current_package, RESET);
    }
    
    fflush(stdout);
}

int generate_tool_list(void) {
    status_message("Querying BlackArch repository...", "info");
    
    // First, make sure the BlackArch repository is enabled
    if (!execute_command("grep -q '\\[blackarch\\]' /etc/pacman.conf")) {
        status_message("BlackArch repository not found. Adding repository...", "info");
        
        // Add BlackArch repository
        const char* repo_cmd = "echo -e '[blackarch]\\nServer = https://blackarch.org/blackarch/$repo/os/$arch' >> /etc/pacman.conf";
        if (!execute_command(repo_cmd)) {
            status_message("Failed to add BlackArch repository", "error");
            return 0;
        }
        
        // Install BlackArch keyring
        if (!execute_command("pacman-key --recv-key 4345771566D76038C7FEB43863EC0ADBEA87E4E3 && "
                           "pacman-key --lsign-key 4345771566D76038C7FEB43863EC0ADBEA87E4E3")) {
            status_message("Failed to install BlackArch keyring", "error");
            return 0;
        }
    }
    
    // Update package database
    if (!execute_command("pacman -Sy")) {
        status_message("Failed to update package database", "error");
        return 0;
    }
    
    // Query available BlackArch tools and save to results.txt
    if (!execute_command("pacman -Sl blackarch | awk '{print $2}' > " TEMP_FILE)) {
        status_message("Failed to generate tool list", "error");
        return 0;
    }
    
    return 1;
}

// Enhanced progress bar with smoother animation
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
// Enhanced install_tools function
void install_tools(void) {
    if (!check_system_requirements()) {
        status_message("System requirements not met", "error");
        return;
    }

    g_progress.completed_packages = 0;
    g_progress.show_details = 0;
    
    FILE* tool_list = fopen(TEMP_FILE, "r");
    if (!tool_list) {
        status_message("Failed to open tool list", "error");
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
        status_message("No packages found to install", "warning");
        fclose(tool_list);
        return;
    }
    
    rewind(tool_list);
    redirect_output();
    
    printf("\033[2J\033[H");
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
            snprintf(install_cmd, sizeof(install_cmd),
                    "pacman -S --noconfirm --needed --overwrite=\"*\" %s >/dev/null 2>%s",
                    line, PACMAN_OUTPUT_FILE);
            
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
    status_message(completion_msg, "info");
}

// Main program entry point
int main(void) {
    if (enable_raw_mode() == -1) {
        fprintf(stderr, "Failed to initialize terminal\n");
        return 1;
    }

    if (!create_lock_file()) {
        disable_raw_mode();
        return 1;
    }

    initialize_logging();
    
    signal(SIGINT, signal_handler);
    signal(SIGALRM, alarm_handler);
    signal(SIGTERM, signal_handler);
    
    atexit(cleanup_resources);

    printf("\x1b[2J\x1b[H");
    printf("%s", BANNER);
    fflush(stdout);
    
    if (!check_root_privileges()) {
        print_modern_box("ROOT PRIVILEGES REQUIRED", FG_RED, SYMBOL_LOCK);
        return 1;
    }

    if (!check_system_requirements()) {
        print_modern_box("SYSTEM REQUIREMENTS NOT MET", FG_RED, SYMBOL_ERROR);
        return 1;
    }

    print_modern_box("System Modification Warning", FG_YELLOW, SYMBOL_WARNING);
    printf("%sType %sAGREE%s to continue or %sDISAGREE%s to cancel: %s", 
           FG_WHITE, FG_GREEN, FG_WHITE, FG_RED, FG_WHITE, RESET);
    fflush(stdout);

    char response[10] = {0};
    alarm(30);
    if (fgets(response, sizeof(response), stdin) == NULL) {
        status_message("Input timeout or error", "error");
        return 1;
    }
    alarm(0);

    response[strcspn(response, "\n")] = 0;
    str_to_upper(response);
    
    if (strcmp(response, "AGREE") != 0) {
        status_message("Operation cancelled by user", "warning");
        return 1;
    }

    if (!generate_tool_list()) {
        status_message("Failed to generate tool list", "error");
        return 1;
    }

    install_tools();

    status_message("Cleaning up...", "info");
    cleanup_resources();
    disable_raw_mode();
    
    return 0;
}
