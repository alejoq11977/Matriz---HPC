CC      = gcc
CFLAGS  = -Wall -Wextra -Iinclude
BIN_DIR = bin

# --- Base secuencial (Lab 1 y Lab 2) ---
SEQ_SRCS = src/matriz_monotonic.c modules/llenado.c modules/memoria.c modules/tiempo_mult.c
SEQ_HDRS = include/llenado.h include/memoria.h include/tiempo_mult.h
SEQ_BIN  = $(BIN_DIR)/matriz_monotonic

# --- Version transpuesta (Lab 2) ---
TRANS_SRCS = src/matriz_monotonic_t.c modules/llenado_trans.c modules/memoria.c modules/tiempo_mult_trans.c
TRANS_HDRS = include/llenado_trans.h include/memoria.h include/tiempo_mult_trans.h
TRANS_BIN  = $(BIN_DIR)/matriz_monotonic_t

.PHONY: all clean lab1 lab2

.DEFAULT:
	@:

all: $(SEQ_BIN) $(TRANS_BIN)

lab1: $(SEQ_BIN)
lab2: $(SEQ_BIN) $(TRANS_BIN)

$(SEQ_BIN): $(SEQ_SRCS) $(SEQ_HDRS) | $(BIN_DIR)
	$(CC) $(CFLAGS) -O2 $(SEQ_SRCS) -o $@

$(TRANS_BIN): $(TRANS_SRCS) $(TRANS_HDRS) | $(BIN_DIR)
	$(CC) $(CFLAGS) -O2 $(TRANS_SRCS) -o $@

$(BIN_DIR):
	mkdir -p $(BIN_DIR)

clean:
	rm -f $(SEQ_BIN) $(TRANS_BIN)
	rmdir $(BIN_DIR) 2>/dev/null || true
