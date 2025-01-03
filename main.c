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
#define BACKUP_LOG "/var/log/blackutility.log.bak"
#define LOCK_FILE "/var/lock/blackutility.lock"
#define MIN_DISK_SPACE 10737418240  // 10GB in bytes
#define MAX_RETRIES 3
#define TIMEOUT_SECONDS 300
#define LOADER_WIDTH 50
#define LOADER_UPDATE_INTERVAL 100000  // 100ms in microseconds

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

// Program constants
#define LOG_FILE "/var/log/blackutility.log"
#define MAX_CMD_LENGTH 1024
#define MAX_LINE_LENGTH 256
#define PROGRESS_BAR_WIDTH 40
#define TEMP_FILE "results.txt"
#define SPINNER_DELAY 100000 // Microseconds between spinner updates

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


void str_to_upper(char* str) {
    for(int i = 0; str[i]; i++) {
        str[i] = toupper((unsigned char)str[i]);
    }
}

// Global variables
volatile sig_atomic_t keep_running = 1;
volatile sig_atomic_t cleanup_needed = 0;
FILE* log_fp = NULL;
int lock_fd = -1;
// Data structures for better organization
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

// Function prototypes
void initialize_logging(void);
void cleanup_logging(void);
int generate_tool_list(void);
void log_message(const char* message, const char* level);
void print_modern_box(const char* text, const char* color, const char* symbol);
void show_modern_progress(ProgressBar* bar, Package* pkg);
void show_spinner(const char* message);
void status_message(const char* message, const char* status);
int execute_command(const char* command);
int check_root_privileges(void);
void cleanup_resources(void);
void signal_handler(int signum);
void get_terminal_width(int* width);
void parse_package_info(const char* line, Package* pkg);
void install_tools(void);


typedef struct {
    int total_packages;
    int completed_packages;
    char current_package[MAX_LINE_LENGTH];
    int show_details;  // Toggle for detailed logging
} GlobalProgress;

// Create a global instance
GlobalProgress g_progress = {0};

int create_lock_file(void) {
    lock_fd = open(LOCK_FILE, O_CREAT | O_EXCL | O_RDWR, 0644);
    if (lock_fd < 0) {
        if (errno == EEXIST) {
            log_message("Another instance is already running", "error");
        } else {
            log_message("Failed to create lock file", "error");
        }
        return 0;
    }
    return 1;
}

void release_lock_file(void) {
    if (lock_fd >= 0) {
        close(lock_fd);
        unlink(LOCK_FILE);
    }
}

size_t get_available_disk_space(const char* path) {
    struct statvfs stat;
    if (statvfs(path, &stat) != 0) {
        return 0;
    }
    return stat.f_bsize * stat.f_bavail;
}

int check_system_requirements(void) {
    // Check disk space
    size_t available = get_available_disk_space("/");
    if (available < MIN_DISK_SPACE) {
        status_message("Insufficient disk space (10GB required)", "error");
        return 0;
    }

    // Check memory
    FILE* meminfo = fopen("/proc/meminfo", "r");
    if (meminfo) {
        char line[256];
        unsigned long mem_total = 0;
        while (fgets(line, sizeof(line), meminfo)) {
            if (strncmp(line, "MemTotal:", 9) == 0) {
                sscanf(line, "MemTotal: %lu", &mem_total);
                break;
            }
        }
        fclose(meminfo);
        
        if (mem_total < 2097152) { // Less than 2GB RAM
            status_message("Insufficient memory (2GB required)", "error");
            return 0;
        }
    }

    return 1;
}
// Signal handler for graceful shutdown
void signal_handler(int signum) {
    keep_running = 0;
    printf("\n%sReceived signal %d, cleaning up...%s\n", 
           FG_YELLOW, signum, RESET);
    cleanup_resources();
    exit(1);
}

// Handle operation timeouts
void alarm_handler(int signum) {
    (void)signum;  // Prevent unused parameter warning
    log_message("Operation timed out", "error");
    status_message("Operation timed out", "error");
    keep_running = 0;
}

void initialize_logging(void) {
    // First, make sure the log directory exists
    char log_dir[] = "/var/log";
    if (access(log_dir, F_OK) != 0) {
        // Try to create the directory if it doesn't exist
        if (mkdir(log_dir, 0755) != 0 && errno != EEXIST) {
            fprintf(stderr, "%sError creating log directory: %s%s\n", 
                    FG_RED, strerror(errno), RESET);
            return;
        }
    }
    
    // Try to open the log file for appending first
    log_fp = fopen(LOG_FILE, "a");
    if (!log_fp) {
        // If that fails, try to create it
        log_fp = fopen(LOG_FILE, "w");
        if (!log_fp) {
            fprintf(stderr, "%sError opening log file: %s%s\n", 
                    FG_RED, strerror(errno), RESET);
            return;
        }
        // Set proper permissions on the new file
        if (fchmod(fileno(log_fp), 0644) != 0) {
            fprintf(stderr, "%sWarning: Could not set log file permissions%s\n",
                    FG_YELLOW, RESET);
        }
    }
    
    // Write initial log entry
    log_message("Logging initialized", "info");
}

// Cleanup logging system
void cleanup_logging(void) {
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

void install_tools(void) {
    if (!check_system_requirements()) {
        status_message("System requirements not met", "error");
        return;
    }

    // Initialize global progress
    g_progress.completed_packages = 0;
    g_progress.show_details = 0;
    g_progress.total_packages = 0;  // Reset to ensure accurate counting
    
    // Count total packages first
    FILE* tool_list = fopen(TEMP_FILE, "r");
    if (!tool_list) {
        status_message("Failed to open tool list", "error");
        return;
    }
    
    // Count packages and validate file contents
    char line[MAX_LINE_LENGTH];
    while (fgets(line, sizeof(line), tool_list)) {
        // Remove trailing newline and whitespace
        line[strcspn(line, "\n")] = 0;
        if (strlen(line) > 1) {  // Only count non-empty lines
            g_progress.total_packages++;
        }
    }
    
    if (g_progress.total_packages == 0) {
        status_message("No packages found to install", "warning");
        fclose(tool_list);
        return;
    }
    
    // Rewind file for installation
    rewind(tool_list);
    
    // Install packages with unified progress
    while (fgets(line, sizeof(line), tool_list) && keep_running) {
        // Clean the line
        line[strcspn(line, "\n")] = 0;
        
        if (strlen(line) > 0) {
            // Update current package name with bounds checking
            strncpy(g_progress.current_package, line, MAX_LINE_LENGTH - 1);
            g_progress.current_package[MAX_LINE_LENGTH - 1] = '\0';
            
            // Construct install command with proper error handling
            char install_cmd[MAX_CMD_LENGTH];
            int ret = snprintf(install_cmd, sizeof(install_cmd), 
                    "pacman -S --noconfirm --needed --overwrite=\"*\" %s %s", 
                    line,
                    g_progress.show_details ? "" : "2>&1 >/dev/null");
            
            if (ret < 0 || ret >= sizeof(install_cmd)) {
                log_message("Command buffer overflow prevented", "warning");
                continue;
            }
            
            // Show progress before attempting install
            update_unified_loader(line, 1);
            
            // Execute with timeout protection
            alarm(TIMEOUT_SECONDS);
            if (!execute_command(install_cmd)) {
                char error_msg[MAX_LINE_LENGTH];
                snprintf(error_msg, sizeof(error_msg), "Failed to install: %s", line);
                log_message(error_msg, "error");
            }
            alarm(0);
            
            g_progress.completed_packages++;
            update_unified_loader(line, 1);
        }
        
        usleep(LOADER_UPDATE_INTERVAL);
    }
    
    fclose(tool_list);
    printf("\n");
    
    // Final status update
    char completion_msg[MAX_LINE_LENGTH];
    snprintf(completion_msg, sizeof(completion_msg), 
            "Completed installation of %d/%d packages", 
            g_progress.completed_packages, g_progress.total_packages);
    status_message(completion_msg, "info");
}
// Main program entry point
int main(void) {
    // Initialization Phase
    if (!create_lock_file()) {
        fprintf(stderr, "%sAnother instance is already running or cannot create lock%s\n",
                FG_RED, RESET);
        return 1;
    }

    initialize_logging();
    
    // Signal handlers
    signal(SIGINT, signal_handler);
    signal(SIGALRM, alarm_handler);
    signal(SIGTERM, signal_handler);
    
    atexit(cleanup_resources);

    // Setup Phase
    system("clear");
    printf("%s", BANNER);
    
    if (!check_root_privileges()) {
        print_modern_box("ROOT PRIVILEGES REQUIRED", FG_RED, SYMBOL_LOCK);
        return 1;
    }

    // User confirmation
    print_modern_box("System Modification Warning", FG_YELLOW, SYMBOL_WARNING);
    printf("%sType %sAGREE%s to continue or %sDISAGREE%s to cancel: %s", 
           FG_WHITE, FG_GREEN, FG_WHITE, FG_RED, FG_WHITE, RESET);

    // Clear input buffer and get response
    int c;
    while ((c = getchar()) != '\n' && c != EOF);
    
    char response[10] = {0};  // Initialize to zeros
    if (fgets(response, sizeof(response), stdin) == NULL) {
        status_message("Invalid input", "error");
        return 1;
    }
    
    response[strcspn(response, "\n")] = 0;
    str_to_upper(response);
    
    if (strcmp(response, "AGREE") != 0) {
        status_message("Operation cancelled by user", "warning");
        return 1;
    }

    // Main Installation Process
    if (!generate_tool_list()) {
        status_message("Failed to prepare tool list", "error");
        return 1;
    }

    // Single system update
    status_message("Updating system packages...", "info");
    if (!execute_command("pacman -Syyu --noconfirm")) {
        status_message("System update failed", "error");
        return 1;
    }

    // Install tools
    if (keep_running) {
        install_tools();
    }

    // Cleanup and Status
    status_message("Cleaning up...", "info");
    
    if (cleanup_needed) {
        log_message("Program terminated by user interrupt", "info");
        return 1;
    }
    
    log_message("Program completed successfully", "info");
    return 0;
}
    // ====== Main Program Loop ======
    
while (keep_running) {
    if (cleanup_needed) {
        printf("\n%sReceived interrupt signal, cleaning up...%s\n", 
               FG_YELLOW, RESET);
        break;
    }

    // Generate tool list first
    if (!generate_tool_list()) {
        status_message("Failed to prepare tool list", "error");
        break;
    }

    // Start with system update
    status_message("Updating system packages...", "info");
    if (!execute_command("pacman -Syyu --noconfirm")) {
        status_message("System update failed", "error");
        break;
    }

        // Start with system update
        status_message("Updating system packages...", "info");
        if (!execute_command("pacman -Syyu --noconfirm")) {
            status_message("System update failed", "error");
            break;
        }

        // If system update succeeded, proceed with tool installation
        if (keep_running) {
            // Create progress tracking structure
            ProgressBar progress_bar = {
                .width = PROGRESS_BAR_WIDTH,
                .total = 100,  // Will be updated by install_tools
                .current = 0,
                .message = "Installing tools...",
                .status = "in_progress",
                .start_time = time(NULL)
            };

            // Perform tool installation
            install_tools();

            // Check if installation completed successfully
            if (keep_running) {
                print_modern_box("Installation Complete!", FG_GREEN, SYMBOL_SUCCESS);
            }
        }

        // Break the loop after completing installation
        // This ensures we only run through once unless interrupted
        break;
    }

    // ====== Cleanup Phase ======
    
    // Perform cleanup operations
    status_message("Cleaning up...", "info");
    cleanup_resources();
    
    // Release the lock file last
    release_lock_file();
    
    // Log completion status
    if (cleanup_needed) {
        log_message("Program terminated by user interrupt", "info");
        return 1;
    } else {
        log_message("Program completed successfully", "info");
        return 0;
    }
}
