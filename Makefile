CC      = gcc
CFLAGS  = -Wall -Wextra -O2 -Iinclude
BIN_DIR = bin

SRCS = src/matriz_monotonic.c modules/memoria.c modules/llenado.c modules/tiempo_mult.c
HDRS = include/memoria.h include/llenado.h include/tiempo_mult.h
BIN  = $(BIN_DIR)/matriz_monotonic

.PHONY: all run clean

.DEFAULT:
	@:

all: $(BIN)

RUN_ARGS = $(wordlist 2,$(words $(MAKECMDGOALS)),$(MAKECMDGOALS))

run: $(BIN)
	./$(BIN) $(RUN_ARGS)

$(BIN): $(SRCS) $(HDRS) | $(BIN_DIR)
	$(CC) $(CFLAGS) $(SRCS) -o $@

$(BIN_DIR):
	mkdir -p $(BIN_DIR)

clean:
	rm -f $(BIN)
	rmdir $(BIN_DIR) 2>/dev/null || true
