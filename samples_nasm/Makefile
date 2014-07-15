TCC = tcc
NASM = nasm
# clang
CC = clang
LD = clang
# GCC
#CC = gcc
#LD = gcc

# OS X
CFLAGS = -m32 -c -std=c99 -O3
TCCFLAGS = --ast -O 1 -f macho --verbose
LDFLAGS = -m32 -Wl,-no_pie -O3
NASMFLAGS = -f macho
# Linux
#CFLAGS = -m32 -c -std=c99 -O3
#TCCFLAGS = --ast -O 1 -f elf --verbose
#LDFLAGS = -m32 -O3
#NASMFLAGS = -f elf

PROGRAMS = ack arith assign comment compare fact fib gcd global incdec label logical scope while
OBJS = utility.o

.PRECIOUS: %.asm
.SUFFIXES: .c .asm .o .tc

all: $(PROGRAMS)

.PHONY: test
test: $(PROGRAMS)
	@LIST="$(PROGRAMS)"; \
		for x in $$LIST; do \
			echo "$$x"; \
			./$$x | tee $$x.out; \
		done

.PHONY: clean
clean:
	rm -rf ./*.asm
	rm -rf ./*.ast
	rm -rf ./*.log
	rm -rf ./*.nasm
	rm -rf ./*.o
	rm -rf ./*.out
	rm -rf $(PROGRAMS)

.c.o:
	$(CC) $(CFLAGS) -o $@ $<

.tc.asm:
	$(TCC) $(TCCFLAGS) -o $@ $< 2> $(basename $@).log

.asm.o:
	$(NASM) $(NASMFLAGS) $<

ack: $(OBJS) ack.o
	$(LD) $(LDFLAGS) -o $@ $(OBJS) $@.o

arith: $(OBJS) arith.o
	$(LD) $(LDFLAGS) -o $@ $(OBJS) $@.o

assign: $(OBJS) assign.o
	$(LD) $(LDFLAGS) -o $@ $(OBJS) $@.o

comment: $(OBJS) comment.o
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

incdec: $(OBJS) incdec.o
	$(LD) $(LDFLAGS) -o $@ $(OBJS) $@.o

label: $(OBJS) label.o
	$(LD) $(LDFLAGS) -o $@ $(OBJS) $@.o

logical: $(OBJS) logical.o
	$(LD) $(LDFLAGS) -o $@ $(OBJS) $@.o

scope: $(OBJS) scope.o
	$(LD) $(LDFLAGS) -o $@ $(OBJS) $@.o

while: $(OBJS) while.o
	$(LD) $(LDFLAGS) -o $@ $(OBJS) $@.o
