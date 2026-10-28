// maxrss.c
// Helper minimo para medir el footprint de memoria del proceso (max RSS)
// sin depender de /usr/bin/time. Se compila aparte y se usa como wrapper:
// el proceso hijo hace el trabajo y el padre reporta su max RSS.
//
// Uso: maxrss <programa> [args...]
// Salida: en stderr, una linea "MAXRSS_KB=<valor>"

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/wait.h>
#include <sys/resource.h>

int main(int argc, char **argv) {
    if (argc < 2) {
        fprintf(stderr, "Uso: %s <programa> [args...]\n", argv[0]);
        return 1;
    }

    pid_t pid = fork();

    if (pid == 0) {
        // Hijo: ejecuta el programa y hereda stdout/stderr
        execvp(argv[1], &argv[1]);
        perror("execvp");
        _exit(127);
    }

    if (pid < 0) {
        perror("fork");
        return 1;
    }

    int status = 0;
    waitpid(pid, &status, 0);

    // max RSS del hijo (ru_maxrss en KiB en Linux)
    struct rusage ru;
    if (getrusage(RUSAGE_CHILDREN, &ru) == 0) {
        fprintf(stderr, "MAXRSS_KB=%ld\n", ru.ru_maxrss);
    }

    if (WIFEXITED(status)) {
        return WEXITSTATUS(status);
    }
    return 1;
}
