#include <stdio.h>

chk(int x, int y)
{
    printf(x == y ? "OK\n" : "NG\n");
}

/* for ss.c */

int vv[10] = {3, 5, 1, 8, 7, 6, 2, 10, 4, 9};

int v(int i)
{
    return vv[i];
}

set_v(i, x)
{
    vv[i] = x;
}
