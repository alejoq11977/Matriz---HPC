#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <unistd.h>

#include "matrix_shm.h"

#define SHM_NAME_A "/matriz_fork_A"
#define SHM_NAME_B "/matriz_fork_B"
#define SHM_NAME_C "/matriz_fork_C"

static int *crear_una_matriz(const char *nombre, size_t bytes) {
    int fd = shm_open(nombre, O_CREAT | O_RDWR, 0600);
    if (fd < 0) {
        perror("shm_open");
        return NULL;
    }
    if (ftruncate(fd, (off_t)bytes) != 0) {
        perror("ftruncate");
        close(fd);
        return NULL;
    }
    void *ptr = mmap(NULL, bytes, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
    if (ptr == MAP_FAILED) {
        perror("mmap");
        close(fd);
        return NULL;
    }
    memset(ptr, 0, bytes);
    return (int *)ptr;
}

MatricesShm crear_matrices_compartidas(int N) {
    MatricesShm m = {0};
    m.N = N;
    m.total_elementos = (size_t)N * (size_t)N;
    m.bytes = m.total_elementos * sizeof(int);

    m.A = crear_una_matriz(SHM_NAME_A, m.bytes);
    m.B = crear_una_matriz(SHM_NAME_B, m.bytes);
    m.C = crear_una_matriz(SHM_NAME_C, m.bytes);

    if (!m.A || !m.B || !m.C) {
        fprintf(stderr, "Error: no se pudo crear memoria compartida\n");
        exit(1);
    }
    return m;
}

void liberar_matrices_compartidas(int N) {
    size_t bytes = (size_t)N * (size_t)N * sizeof(int);
    shm_unlink(SHM_NAME_A);
    shm_unlink(SHM_NAME_B);
    shm_unlink(SHM_NAME_C);
    (void)bytes;
}
