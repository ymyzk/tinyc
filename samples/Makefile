TCC = tinyc
NASM = nasm
# clang
CC = clang
LD = clang
# GCC
# CC = gcc
# LD = gcc

CFLAGS = -m32 -c -std=c11
TCCFLAGS = --ast -O1
LDFLAGS = -m32 -Wl,-no_pie
NASMFLAGS = -f macho

PROGRAM = main
OBJS = main.o arith.o fact.o fib.o gcd.o global.o

.SUFFIXES: .c .nasm .o .tc

$(PROGRAM): $(OBJS)
	$(LD) $(LDFLAGS) -o $(PROGRAM) $(OBJS)

.c.o:
	$(CC) $(CFLAGS) -o $@ $<

.tc.nasm:
	$(TCC) $(TCCFLAGS) -o $@ $<

.nasm.o:
	$(NASM) $(NASMFLAGS) $<

clean:
	rm -rf ./*.ast
	rm -rf ./*.nasm
	rm -rf $(OBJS)
	rm -rf $(PROGRAM)
