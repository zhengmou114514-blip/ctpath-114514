#include <stdio.h>

int main() {
    int peach = 1;  // 第10天早上剩下的桃子数
    for (int day = 9; day >= 1; day--) {
        peach = (peach + 1) * 2;  // 逆推前一天的桃子数
    }
    printf("第一天共摘了 %d 个桃子\n", peach);
    return 0;
}