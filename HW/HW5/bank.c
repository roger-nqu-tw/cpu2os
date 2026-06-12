#include <stdio.h>
#include <pthread.h>

#define NUM_OPS 100000

int balance = 0;
pthread_mutex_t mutex = PTHREAD_MUTEX_INITIALIZER;

void *do_deposit(void *arg) {
    for (int i = 0; i < NUM_OPS; i++) {
        pthread_mutex_lock(&mutex);
        balance++;
        pthread_mutex_unlock(&mutex);
    }
    return NULL;
}

void *do_withdraw(void *arg) {
    for (int i = 0; i < NUM_OPS; i++) {
        pthread_mutex_lock(&mutex);
        balance--;
        pthread_mutex_unlock(&mutex);
    }
    return NULL;
}

int main() {
    pthread_t t1, t2;

    pthread_create(&t1, NULL, do_deposit, NULL);
    pthread_create(&t2, NULL, do_withdraw, NULL);

    pthread_join(t1, NULL);
    pthread_join(t2, NULL);

    printf("Final balance: %d (expected: 0)\n", balance);
    printf("Test %s\n", balance == 0 ? "PASSED" : "FAILED");
    return 0;
}
