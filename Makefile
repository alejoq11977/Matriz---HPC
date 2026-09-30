CC      = gcc
CFLAGS  = -Wall -Wextra -O2 -Iinclude
BIN_DIR = bin

# --- version secuencial (CLOCK_MONOTONIC_RAW) ---
SEQ_SRCS = src/matriz_monotonic.c modules/memoria.c modules/llenado.c modules/tiempo_mult.c
SEQ_HDRS = include/memoria.h include/llenado.h include/tiempo_mult.h
SEQ_BIN  = $(BIN_DIR)/matriz_monotonic

# --- version paralela (pthreads) ---
PAR_SRCS = src/matriz_pthreads.c modules/memoria.c modules/llenado.c modules/pthread_mult.c
PAR_HDRS = include/memoria.h include/llenado.h include/pthread_mult.h
PAR_BIN  = $(BIN_DIR)/matriz_pthreads

# --- version paralela (fork + POSIX shm) ---
FORK_SRCS = src/matriz_fork.c modules/llenado.c modules/matrix_shm.c
FORK_HDRS = include/llenado.h include/matrix_shm.h
FORK_BIN  = $(BIN_DIR)/matriz_fork

.PHONY: all run run_par run_fork clean

.DEFAULT:
	@:

all: $(SEQ_BIN) $(PAR_BIN) $(FORK_BIN)

run: $(SEQ_BIN)
	./$(SEQ_BIN) $(filter-out $@,$(MAKECMDGOALS))

run_par: $(PAR_BIN)
	./$(PAR_BIN) $(filter-out $@,$(MAKECMDGOALS))

run_fork: $(FORK_BIN)
	./$(FORK_BIN) $(filter-out $@,$(MAKECMDGOALS))

$(SEQ_BIN): $(SEQ_SRCS) $(SEQ_HDRS) | $(BIN_DIR)
	$(CC) $(CFLAGS) $(SEQ_SRCS) -o $@

$(PAR_BIN): $(PAR_SRCS) $(PAR_HDRS) | $(BIN_DIR)
	$(CC) $(CFLAGS) $(PAR_SRCS) -o $@ -lpthread

$(FORK_BIN): $(FORK_SRCS) $(FORK_HDRS) | $(BIN_DIR)
	$(CC) $(CFLAGS) $(FORK_SRCS) -o $@ -lrt

$(BIN_DIR):
	mkdir -p $(BIN_DIR)

clean:
	rm -f $(SEQ_BIN) $(PAR_BIN) $(FORK_BIN)
	rmdir $(BIN_DIR) 2>/dev/null || true
