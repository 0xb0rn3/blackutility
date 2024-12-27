#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <ncurses.h>
#include <time.h>
#include <errno.h>

// Base ANSI escape code for all terminal control sequences
#define ESC "\x1b"

// Text styling codes - these control how text appears
#define ANSI_RESET    ESC "[0m"  // Returns text to normal
#define ANSI_BOLD     ESC "[1m"  // Makes text bold
#define ANSI_DIM      ESC "[2m"  // Makes text slightly darker
#define ANSI_ITALIC   ESC "[3m"  // Makes text italic
#define ANSI_UNDER    ESC "[4m"  // Adds underline

// Foreground (text) colors
#define ANSI_RED      ESC "[1;31m"
#define ANSI_GREEN    ESC "[1;32m"
#define ANSI_YELLOW   ESC "[1;33m"
#define ANSI_BLUE     ESC "[1;34m"
#define ANSI_MAGENTA  ESC "[1;35m"
#define ANSI_CYAN     ESC "[1;36m"
#define ANSI_WHITE    ESC "[1;37m"

// Background colors
#define BG_BLACK      ESC "[40m"
#define BG_RED        ESC "[41m"
#define BG_GREEN      ESC "[42m"
#define BG_BLUE       ESC "[44m"

// Program constants
#define LOG_FILE "/var/log/blackutility.log"
#define MAX_CMD_LENGTH 1024
#define MAX_LINE_LENGTH 256
#define PROGRESS_BAR_WIDTH 50
#define TEMP_FILE "results.txt"

// Banner display - using ANSI codes for colored output
const char* BANNER = 
    "\n" ESC "[1;36m█▄▄ █░░ ▄▀█ █▀▀ █▄▀ █░█ ▀█▀ █ █░░ █ ▀█▀ █▄█\n"
    "█▄█ █▄▄ █▀█ █▄▄ █░█ █▄█ ░█░ █ █▄▄ █ ░█░ ░█░" ESC "[0m\n"
    ESC "[1;37m    [ Advanced Cybersecurity Arsenal for Arch ]" ESC "[0m\n"
    ESC "[2m    Developer: " ESC "[0m" ESC "[1m0xb0rn3" ESC "[0m\n"
    ESC "[2m    Repository: " ESC "[0m" ESC "[1;34mgithub.com/0xb0rn3/blackutility" ESC "[0m\n"
    ESC "[3m    Stay Ethical. Stay Secure. Enjoy!" ESC "[0m\n";

// Global file pointer for logging
FILE* log_fp = NULL;

// Function prototypes
void initialize_logging(void);
void cleanup_logging(void);
void log_message(const char* message, const char* level);
void print_box(const char* text, const char* color);
void show_fancy_progress(const char* message, int current, int total);
void status_message(const char* message, const char* status);
int execute_command(const char* command);
int check_root_privileges(void);
void cleanup_resources(void);

// Initialize logging system
void initialize_logging(void) {
    log_fp = fopen(LOG_FILE, "a");
    if (!log_fp) {
        fprintf(stderr, "%sError opening log file: %s%s\n", 
                ANSI_RED, strerror(errno), ANSI_RESET);
        exit(1);
    }
}

// Clean up logging resources
void cleanup_logging(void) {
    if (log_fp) {
        fclose(log_fp);
        log_fp = NULL;
    }
}

// Log message with timestamp and level
void log_message(const char* message, const char* level) {
    time_t now;
    char timestamp[26];
    time(&now);
    ctime_r(&now, timestamp);
    timestamp[24] = '\0';  // Remove newline
    
    fprintf(log_fp, "[%s] [%s] %s\n", timestamp, level, message);
    fflush(log_fp);
}

// Create a stylized box around text
void print_box(const char* text, const char* color) {
    int len = strlen(text);
    printf("%s╭─%s%s\n", color, text, "─╮");
    printf("│ %s │\n", text);
    printf("╰");
    for(int i = 0; i < len + 2; i++) printf("─");
    printf("╯%s\n", ANSI_RESET);
}

// Display an animated progress bar
void show_fancy_progress(const char* message, int current, int total) {
    static const char spinner[] = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏";
    static int spinner_index = 0;
    float percentage = (float)current / total * 100;
    int bar_width = (int)((float)current / total * PROGRESS_BAR_WIDTH);
    
    printf("\r" ESC "[K");  // Clear current line
    
    printf("%s%c %s%s [", 
           ANSI_CYAN, 
           spinner[spinner_index++ % strlen(spinner)],
           message,
           ANSI_RESET);
    
    // Draw progress bar
    for(int i = 0; i < PROGRESS_BAR_WIDTH; i++) {
        if(i < bar_width) {
            printf("%s█%s", ANSI_GREEN, ANSI_RESET);
        } else {
            printf("%s░%s", ANSI_DIM, ANSI_RESET);
        }
    }
    
    printf("] %s%.1f%%%s", ANSI_YELLOW, percentage, ANSI_RESET);
    fflush(stdout);
}

// Display status message with appropriate icon
void status_message(const char* message, const char* status) {
    const char* icon;
    const char* color;
    
    if(strcmp(status, "success") == 0) {
        icon = "✔";
        color = ANSI_GREEN;
    } else if(strcmp(status, "error") == 0) {
        icon = "✖";
        color = ANSI_RED;
    } else if(strcmp(status, "warning") == 0) {
        icon = "⚠";
        color = ANSI_YELLOW;
    } else {
        icon = "ℹ";
        color = ANSI_BLUE;
    }
    
    printf("%s%s %s%s\n", color, icon, message, ANSI_RESET);
    log_message(message, status);
}

// Execute system command and handle errors
int execute_command(const char* command) {
    int status = system(command);
    if (status == -1) {
        log_message("Failed to execute command", "error");
        return 0;
    }
    return 1;
}

// Check for root privileges
int check_root_privileges(void) {
    if(geteuid() != 0) {
        status_message("ROOT PRIVILEGES ARE REQUIRED!", "error");
        return 0;
    }
    return 1;
}

// Clean up temporary files and resources
void cleanup_resources(void) {
    if (access(TEMP_FILE, F_OK) != -1) {
        remove(TEMP_FILE);
    }
    cleanup_logging();
}

// Main program entry point
int main(void) {
    // Initialize logging
    initialize_logging();
    
    // Set up cleanup handler
    atexit(cleanup_resources);
    
    // Clear screen and show banner
    system("clear");
    printf("%s", BANNER);
    
    // Check root privileges
    if(!check_root_privileges()) {
        return 1;
    }
    
    // User confirmation
    print_box("System Modification Warning", ANSI_YELLOW);
    printf("%sConfirm system modifications (AGREE/DISAGREE):%s ", 
           ANSI_BOLD, ANSI_RESET);
    
    char response[10];
    scanf("%9s", response);
    if(strcmp(response, "AGREE") != 0) {
        status_message("Operation cancelled by user", "warning");
        return 1;
    }
    
    // Generate list of BlackArch tools
    status_message("Generating list of available BlackArch tools...", "info");
    if (!execute_command("pacman -Sgg | grep blackarch | cut -d' ' -f2 | sort -u > " TEMP_FILE)) {
        status_message("Failed to generate tool list", "error");
        return 1;
    }
    
    // Update system packages
    status_message("Updating system packages...", "info");
    if (!execute_command("pacman -Syyu --noconfirm")) {
        status_message("System update failed", "error");
        return 1;
    }
    
    // Install tools from the generated list
    FILE* tool_list = fopen(TEMP_FILE, "r");
    if (!tool_list) {
        status_message("Failed to read tool list", "error");
        return 1;
    }
    
    char tool[MAX_LINE_LENGTH];
    int tool_count = 0;
    
    // Count total tools first
    while (fgets(tool, sizeof(tool), tool_list) != NULL) {
        tool_count++;
    }
    rewind(tool_list);
    
    // Install each tool with progress indication
    int current_tool = 0;
    while (fgets(tool, sizeof(tool), tool_list)) {
        tool[strcspn(tool, "\n")] = 0;  // Remove newline
        if (strlen(tool) > 0) {
            char install_cmd[MAX_CMD_LENGTH];
            snprintf(install_cmd, sizeof(install_cmd), 
                    "pacman -S --noconfirm --needed --overwrite=\"*\" %s", tool);
            
            show_fancy_progress("Installing tools", ++current_tool, tool_count);
            if (!execute_command(install_cmd)) {
                status_message("Failed to install tool", "error");
                continue;
            }
        }
    }
    
    fclose(tool_list);
    printf("\n");  // New line after progress bar
    
    status_message("Installation completed successfully", "success");
    return 0;
}
