# COP 4600 PA2 — `make` builds the `chash` binary (Rust release).
# Windows (cmd/GNU Make): sets OS=Windows_NT and copies chash.exe to project root.

CARGO ?= cargo
BIN := chash

.PHONY: all clean test run

all:
	$(CARGO) build --release
ifeq ($(OS),Windows_NT)
	copy /Y "target\release\$(BIN).exe" "$(BIN).exe"
else
	cp -f "target/release/$(BIN)" "./$(BIN)"
endif

test:
	$(CARGO) test

clean:
	$(CARGO) clean
ifeq ($(OS),Windows_NT)
	-if exist "$(BIN).exe" del "$(BIN).exe"
	-if exist hash.log del hash.log
else
	rm -f "$(BIN)" "$(BIN).exe" hash.log
endif

run: all
ifeq ($(OS),Windows_NT)
	.\$(BIN).exe
else
	./$(BIN)
endif
