#include <stdio.h>

void test(int x, int y) {
    if (x == y) printf("OK %d\n", x);
    else printf("NG %d %d\n", x, y);
}

/* for ss.tc */

int vv[10] = {3, 5, 1, 8, 7, 6, 2, 10, 4, 9};

int v(int i) {
    return vv[i];
}

void set_v(i, x) {
    vv[i] = x;
}
