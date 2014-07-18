TCC = tcc
CC = clang
LD = clang
LLC = llc-3.3
OPT = opt-3.3

TCCFLAGS = --ast -O 1 --verbose -f llvm
OPTFLAGS = -dot-callgraph -dot-cfg -dot-dom -dot-postdom -dot-regions
# x86
#CFLAGS = -m32 -c -std=c99 -O3
#LLCFLAGS = -O3 -march=x86
# host
CFLAGS = -c -std=c99 -O3
LLCFLAGS = -O3
# OS X (x86)
#LDFLAGS = -m32 -Wl,-no_pie -O3
# OS X (host)
LDFLAGS = -Wl,-no_pie -O3
# Linux (x86)
#LDFLAGS = -m32 -O3
# Linux (host)
#LDFLAGS = -O3

PROGRAMS = ack arith assign comment compare fact fib gcd global incdec label logical scope ss while
OBJS = utility.o

.PRECIOUS: %.ll %.s
.SUFFIXES: .c .ll .o .s .tc

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
	rm -rf ./*.dot
	rm -rf ./*.ll
	rm -rf ./*.log
	rm -rf ./*.nasm
	rm -rf ./*.o
	rm -rf ./*.out
	rm -rf ./*.s
	rm -rf dots/*.dot
	rm -rf $(PROGRAMS)

.PHONY: dots
dots: $(PROGRAMS)
	if [ ! -d dots ]; then mkdir dots; fi
	@LIST="$(PROGRAMS)"; \
		for x in $$LIST; do \
			$(OPT) $(OPTFLAGS) "$$x.ll" > /dev/null; \
			for f in *.dot; do mv "$$f" "dots/$$x.$$f"; done; \
		done

.c.o:
	$(CC) $(CFLAGS) -o $@ $<

.tc.ll:
	$(TCC) $(TCCFLAGS) -o $@ $< 2> $(basename $@).log

.ll.s:
	$(LLC) $(LLCFLAGS) $<

.s.o:
	$(CC) $(CFLAGS) -o $@ $<

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

ss: $(OBJS) ss.o
	$(LD) $(LDFLAGS) -o $@ $(OBJS) $@.o

while: $(OBJS) while.o
	$(LD) $(LDFLAGS) -o $@ $(OBJS) $@.o
