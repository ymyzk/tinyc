TCC = tinyc
NASM = nasm
# clang
CC = clang
LD = clang
# GCC
# CC = gcc
# LD = gcc

CFLAGS = -m32 -c -std=c11
TCCFLAGS = --ast -O1 --debug --verbose
LDFLAGS = -m32 -Wl,-no_pie
NASMFLAGS = -f macho

PROGRAMS = ack arith compare fact fib gcd global label logical scope while
OBJS = utility.o

.PRECIOUS: %.nasm
.SUFFIXES: .c .nasm .o .tc

all: $(PROGRAMS)

.PHONY: test
test: $(PROGRAMS)
	@LIST="$(PROGRAMS)"; \
		for x in $$LIST; do \
			echo "$$x"; \
			./$$x; \
		done

ack: $(OBJS) ack.o
	$(LD) $(LDFLAGS) -o $@ $(OBJS) $@.o

arith: $(OBJS) arith.o
	$(LD) $(LDFLAGS) -o $@ $(OBJS) $@.o

compare: $(OBJS) compare.o
	$(LD) $(LDFLAGS) -o $@ $(OBJS) $@.o

fact: $(OBJS) fact.o
	$(LD) $(LDFLAGS) -o $@ $(OBJS) $@.o

fib: $(OBJS) fib.o
	$(LD) $(LDFLAGS) -o $@ $(OBJS) $@.o

gcd: $(OBJS) gcd.o
	$(LD) $(LDFLAGS) -o $@ $(OBJS) $@.o

global: $(OBJS) global.o
	$(LD) $(LDFLAGS) -o $@ $(OBJS) $@.o

label: $(OBJS) label.o
	$(LD) $(LDFLAGS) -o $@ $(OBJS) $@.o

logical: $(OBJS) logical.o
	$(LD) $(LDFLAGS) -o $@ $(OBJS) $@.o

scope: $(OBJS) scope.o
	$(LD) $(LDFLAGS) -o $@ $(OBJS) $@.o

while: $(OBJS) while.o
	$(LD) $(LDFLAGS) -o $@ $(OBJS) $@.o

.c.o:
	$(CC) $(CFLAGS) -o $@ $<

.tc.nasm:
	$(TCC) $(TCCFLAGS) -o $@ $< 2> $(basename $@).log

.nasm.o:
	$(NASM) $(NASMFLAGS) $<

.PHONY: clean
clean:
	rm -rf ./*.ast
	rm -rf ./*.log
	rm -rf ./*.nasm
	rm -rf ./*.o
	rm -rf $(PROGRAMS)
