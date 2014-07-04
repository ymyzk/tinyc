#include <stdio.h>

extern int arith_l_var_var(int, int, int);
extern int arith_l_var_cons(int, int);
extern int arith_l_cons_var(int, int);
extern int arith_l_cons_cons(int);
extern int arith_r(int, int, int, int);
extern int fact(int);
extern int fib_iter(int);
extern int fib_rec(int);
extern int gcd(int, int);
extern int global_x;
extern int test_global_x();

int main() {
    printf("Arith (L)\n");
    for (int i = 0; i < 4; i++) {
        printf("arith_l_var_var(%d, %d, %d) -> %d\n",
                i, 6, 3, arith_l_var_var(i, 6, 3));
    }
    for (int i = 0; i < 4; i++) {
        printf("arith_l_var_cons(%d, %d) -> %d\n",
                i, 6, arith_l_var_cons(i, 6));
    }
    for (int i = 0; i < 4; i++) {
        printf("arith_l_cons_var(%d, %d) -> %d\n",
                i, 3, arith_l_cons_var(i, 3));
    }
    for (int i = 0; i < 4; i++) {
        printf("arith_l_cons_cons(%d) -> %d\n",
                i, arith_l_cons_cons(i));
    }
    printf("\n");

    printf("Arith (R)\n");
    for (int i = 0; i < 4; i++) {
        printf("arith_r(%d, %d, %d, %d) -> %d\n",
                i, 12, 6, 3, arith_r(i, 12, 6, 3));
    }
    printf("\n");

    printf("Fact\n");
    for (int i = 0; i < 10; i++) {
        printf("fact(%d) -> %d\n", i, fact(i));
    }
    printf("\n");
    printf("Fibonacci iterative\n");
    for (int i = 20; i < 30; i++) {
        printf("fib_iter(%d) -> %d\n", i, fib_iter(i));
    }
    printf("\n");
    printf("Fibonacci recursive\n");
    for (int i = 0; i < 10; i++) {
        printf("fib_rec(%d) -> %d\n", i, fib_rec(i));
    }
    printf("\n");
    printf("GCD\n");
    printf("gcd(%d, %d) -> %d\n", 1, 1, gcd(1, 1));
    printf("gcd(%d, %d) -> %d\n", 3, 5, gcd(3, 5));
    printf("gcd(%d, %d) -> %d\n", 5, 21, gcd(5, 21));
    printf("gcd(%d, %d) -> %d\n", 7, 21, gcd(7, 21));
    printf("\n");
    printf("Global\n");
    printf("global_x <- 2\n");
    global_x = 2;
    printf("test_global_x() -> %d\n", test_global_x());
    printf("global_x -> %d\n", global_x);

    return 0;
}
