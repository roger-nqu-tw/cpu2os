# 執行緒、Race Condition、Mutex、Deadlock

## 執行緒（Thread）

執行緒是 CPU 排程的最小單位，一個行程（Process）可以包含多個執行緒。

### 執行緒與行程的比較

| 特性 | 行程 | 執行緒 |
|------|------|--------|
| 位址空間 | 獨立 | 共享（同一行程內的執行緒共用記憶體） |
| 資源開銷 | 大（需要獨立 PCB、頁表等） | 小（共用程式碼、資料、檔案） |
| 切換速度 | 慢（需要切換頁表、TLB 刷新） | 快（只需切換暫存器與堆疊） |
| 通訊方式 | IPC（pipe、socket、shared memory） | 直接讀寫共享記憶體 |
| 獨立性 | 高（一個行程崩潰不影響其他行程） | 低（一個執行緒崩潰可能導致整個行程崩潰） |

### 執行緒的優點

1. **回應性**：GUI 程式中，一個執行緒處理使用者輸入，另一個執行緒在背景工作
2. **資源共享**：執行緒之間自然共享記憶體，不需要昂貴的 IPC 機制
3. **經濟性**：建立執行緒比建立行程快得多
4. **可擴展性**：多核心 CPU 上，不同執行緒可以在不同核心上同時執行

### 執行緒的型態

- **使用者層級執行緒（User-Level Thread）**：由執行緒程式庫管理，核心不知道執行緒存在
  - 優點：切換不需系統呼叫，速度快
  - 缺點：一個執行緒阻塞會阻塞整個行程
  
- **核心層級執行緒（Kernel-Level Thread）**：由作業系統核心管理
  - 優點：可以利用多核心，一個執行緒阻塞不影響其他執行緒
  - 缺點：切換需要系統呼叫，開銷較大

POSIX Threads（pthread）是 Unix/Linux 系統上標準的執行緒 API。

---

## Race Condition（競爭條件）

### 定義

Race Condition 是指多個執行緒同時存取共享資料，且最終結果取決於執行緒的執行順序（timing）的情況。當結果不正確時，就發生了 Race Condition。

### 經典範例：存提款

假設帳戶餘額為 1000 元，同時發生兩筆操作：

```
執行緒 A（存款 500 元）        執行緒 B（提款 200 元）
1. load balance (1000)         1. load balance (1000)
2. balance = 1000 + 500        2. balance = 1000 - 200
3. store balance (1500)        3. store balance (800)
```

執行緒 A 和 B 同時讀到餘額 1000 元，然後各自計算並寫回。
最後餘額可能是 1500（A 先寫回）或 800（B 先寫回），正確答案應該是 1300 元。
這導致了**資金遺失**的問題。

### 為什麼會發生 Race Condition

在機器碼層級，`balance = balance + 500` 實際上是多條指令：

```
ld  R1, [balance]     // 從記憶體載入
add R1, R1, #500      // 加法運算
st  [balance], R1     // 存回記憶體
```

當多個執行緒交錯執行這些指令時，就會產生 Race Condition。

### 臨界區段（Critical Section）

臨界區段是指存取共享資源的程式碼區段。為了解決 Race Condition，我們需要確保：

1. **互斥（Mutual Exclusion）**：同一時間只有一個執行緒在臨界區段中
2. **Progress**：如果沒有執行緒在臨界區段，想要進入的執行緒必須能進入
3. **Bounded Waiting**：一個執行緒不能無限等待進入臨界區段

---

## Mutex（互斥鎖）

### 定義

Mutex（Mutual Exclusion）是最基本的同步機制，用來保護臨界區段，確保同一時間只有一個執行緒可以存取共享資源。

### 使用方式

```c
pthread_mutex_t mutex = PTHREAD_MUTEX_INITIALIZER;

// 進入臨界區段前鎖定
pthread_mutex_lock(&mutex);

// 臨界區段：存取共享資源
balance = balance + amount;

// 離開臨界區段後解鎖
pthread_mutex_unlock(&mutex);
```

### Mutex 的運作原理

Mutex 有兩種狀態：

- ** unlocked（未鎖定）**：沒有執行緒持有鎖
- **locked（已鎖定）**：有執行緒持有鎖

當執行緒嘗試鎖定一個已被鎖定的 Mutex 時，它會進入**阻塞（Blocked）**狀態，直到 Mutex 被解鎖。

### Mutex 的實作

Mutex 可以透過硬體提供的原子指令來實作，最常見的是 **Test-and-Set**（或 x86 上的 `XCHG` 指令）：

```c
// Test-and-Set 的軟體模擬
int test_and_set(int *lock) {
    int old = *lock;
    *lock = 1;  // 設定為鎖定
    return old; // 回傳原值
}

// 使用 Test-and-Set 實作 Mutex
void lock(mutex_t *m) {
    while (test_and_set(&m->flag)) {
        // busy waiting（旋轉鎖）
    }
}

void unlock(mutex_t *m) {
    m->flag = 0;
}
```

實際的 Mutex 實作會在使用者空間先用 spinlock 嘗試，如果鎖被佔用則透過系統呼叫讓出 CPU（futex），避免浪費 CPU 時間。

### Mutex 範例（銀行存提款）

```c
#include <pthread.h>

int balance = 0;
pthread_mutex_t mutex = PTHREAD_MUTEX_INITIALIZER;

void *deposit(void *arg) {
    for (int i = 0; i < 100000; i++) {
        pthread_mutex_lock(&mutex);
        balance++;
        pthread_mutex_unlock(&mutex);
    }
    return NULL;
}
```

### 使用 Mutex 的注意事項

1. **忘記解鎖**：會造成死結
2. **重複鎖定**：普通的 Mutex 不可重入，同一執行緒第二次鎖定會造成死結
3. **鎖的粒度**：鎖的範圍太大會降低並行性，太小會增加鎖的開銷
4. **鎖的順序**：不一致的鎖定順序會造成死結

---

## Deadlock（死結）

### 定義

Deadlock 是指兩個以上的執行緒互相等待對方釋放資源，導致所有執行緒都無法繼續執行的情況。

### 死結的四個必要條件（Coffman 條件）

1. **互斥（Mutual Exclusion）**：資源一次只能被一個執行緒使用
2. **持有並等待（Hold and Wait）**：執行緒持有至少一個資源，同時等待其他執行緒持有的資源
3. **不可搶佔（No Preemption）**：資源不能被強制從執行緒手中搶走
4. **循環等待（Circular Wait）**：存在一組執行緒 {T1, T2, ..., Tn}，T1 等待 T2 持有的資源，T2 等待 T3 持有的資源，...，Tn 等待 T1 持有的資源

### 經典範例：哲學家用餐問題

五位哲學家坐在圓桌前，每人左邊與右邊各有一根筷子。哲學家要吃飯時必須同時取得左右兩根筷子。如果每位哲學家都先拿左邊的筷子，再拿右邊的筷子，就會發生死結：

```
哲學家 1：拿到筷子 1，等待筷子 2
哲學家 2：拿到筷子 2，等待筷子 3
哲學家 3：拿到筷子 3，等待筷子 4
哲學家 4：拿到筷子 4，等待筷子 5
哲學家 5：拿到筷子 5，等待筷子 1（被哲學家 1 拿著）
```

所有人都在等別人放下筷子，沒有人能吃飯。

### 死結的處理策略

#### 1. 預防（Prevention）

破壞四個必要條件中的至少一個：

- **破壞互斥**：對某些資源不適用（如印表機無法同時使用）
- **破壞持有並等待**：要求執行緒在開始時一次取得所有需要的資源
- **破壞不可搶佔**：當執行緒無法取得所有資源時，釋放已持有的資源
- **破壞循環等待**：規定統一的資源取得順序（如先拿編號小的筷子）

#### 2. 避免（Avoidance）

使用銀行家演算法（Banker's Algorithm）等動態判斷是否分配資源，確保系統始終處於安全狀態。

#### 3. 偵測與回復（Detection & Recovery）

允許死結發生，但定期檢測死結，發生時終止其中一個執行緒或強制回收資源。

#### 4. 忽略（Ostrich Algorithm）

假設死結不會發生或發生的機率很低。大多數現代作業系統（包括 Linux/Windows）對死結採取這種策略。

### 預防死結的實作範例（筷子編號法）

```c
// 每位哲學家先拿編號小的筷子，再拿編號大的筷子
void *philosopher(void *arg) {
    int id = *(int *)arg;
    int left = id;               // 左筷子編號
    int right = (id + 1) % 5;    // 右筷子編號
    
    // 統一先拿編號小的筷子
    int first = (left < right) ? left : right;
    int second = (left < right) ? right : left;
    
    pthread_mutex_lock(chopsticks[first]);
    pthread_mutex_lock(chopsticks[second]);
    // 用餐...
    pthread_mutex_unlock(chopsticks[second]);
    pthread_mutex_unlock(chopsticks[first]);
}
```

---

## 總結

| 概念 | 說明 | 解決方案 |
|------|------|----------|
| Race Condition | 多執行緒同時存取共享資料造成結果不正確 | Mutex、Semaphore 等同步機制 |
| Mutex | 確保互斥存取的鎖機制 | lock/unlock |
| Deadlock | 執行緒互相等待造成永久阻塞 | 破壞循環等待（統一鎖定順序） |

### 參考資源

- POSIX Threads Programming: https://computing.llnl.gov/tutorials/pthreads/
- Operating System Concepts (Silberschatz) — Chapter 6: Synchronization
- Little Book of Semaphores (Allen B. Downey)
