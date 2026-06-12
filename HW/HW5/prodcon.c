#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>
#include <unistd.h>

#define BUFFER_SIZE 5
#define NUM_ITEMS  10

int buffer[BUFFER_SIZE];
int count = 0;
int in = 0;
int out = 0;

pthread_mutex_t mutex = PTHREAD_MUTEX_INITIALIZER;
pthread_cond_t cond_producer = PTHREAD_COND_INITIALIZER;
pthread_cond_t cond_consumer = PTHREAD_COND_INITIALIZER;

void *producer(void *arg) {
    int id = *(int *)arg;
    for (int i = 0; i < NUM_ITEMS; i++) {
        pthread_mutex_lock(&mutex);

        while (count == BUFFER_SIZE)
            pthread_cond_wait(&cond_producer, &mutex);

        buffer[in] = i;
        printf("Producer %d produced: %d\n", id, buffer[in]);
        in = (in + 1) % BUFFER_SIZE;
        count++;

        pthread_cond_signal(&cond_consumer);
        pthread_mutex_unlock(&mutex);
    }
    return NULL;
}

void *consumer(void *arg) {
    int id = *(int *)arg;
    for (int i = 0; i < NUM_ITEMS; i++) {
        pthread_mutex_lock(&mutex);

        while (count == 0)
            pthread_cond_wait(&cond_consumer, &mutex);

        int val = buffer[out];
        printf("Consumer %d consumed: %d\n", id, val);
        out = (out + 1) % BUFFER_SIZE;
        count--;

        pthread_cond_signal(&cond_producer);
        pthread_mutex_unlock(&mutex);
    }
    return NULL;
}

int main() {
    pthread_t producers[2], consumers[2];
    int ids[2] = {1, 2};

    for (int i = 0; i < 2; i++)
        pthread_create(&producers[i], NULL, producer, &ids[i]);
    for (int i = 0; i < 2; i++)
        pthread_create(&consumers[i], NULL, consumer, &ids[i]);

    for (int i = 0; i < 2; i++)
        pthread_join(producers[i], NULL);
    for (int i = 0; i < 2; i++)
        pthread_join(consumers[i], NULL);

    printf("\nAll done. Items remaining in buffer: %d\n", count);
    return 0;
}
