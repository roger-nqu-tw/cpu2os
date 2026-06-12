#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
哲學家用餐問題模擬程式

功能：模擬五位哲學家在圓桌上用餐的經典同步問題
說明：每位哲學家需要左右兩支叉子才能吃麵
      使用不同策略避免死結

執行：python3 哲學家用餐.py
"""

import threading
import time
import random

# 哲學家數量
NUM_PHILOSOPHERS = 5
# 每位哲學家需要吃的餐數
MEALS_TO_EAT = 3
# 思考時間 (秒)
THINKING_TIME = 0.1
# 吃飯時間 (秒)
EATING_TIME = 0.1


class DiningPhilosophers:
    def __init__(self):
        # 叉子狀態：False=可用，True=已被佔用
        self.forks = [False] * NUM_PHILOSOPHERS
        # 互斥鎖保護叉子
        self.lock = threading.Lock()
        # 策略：奇偶策略避免死結
        self.use_odd_even_strategy = True
    
    def print_forks(self):
        """顯示叉子狀態"""
        status = ", ".join(["1" if f else "0" for f in self.forks])
        print(f"叉子狀態: [{status}]")
    
    def try_pick_up_forks(self, philosopher_id):
        """嘗試拿起叉子"""
        left_fork = philosopher_id
        right_fork = (philosopher_id + 1) % NUM_PHILOSOPHERS
        
        if self.use_odd_even_strategy:
            # 奇偶策略：奇數號先左後右，偶數號先右後左
            if philosopher_id % 2 == 1:
                first, second = left_fork, right_fork
            else:
                first, second = right_fork, left_fork
        else:
            # 固定順序：先拿編號小的
            first, second = min(left_fork, right_fork), max(left_fork, right_fork)
        
        # 拿起第一支叉子
        while True:
            with self.lock:
                if not self.forks[first]:
                    self.forks[first] = True
                    print(f"  哲學家 {philosopher_id} 拿起叉子 {first}")
                    break
            time.sleep(0.001)
        
        # 拿起第二支叉子
        while True:
            with self.lock:
                if not self.forks[second]:
                    self.forks[second] = True
                    print(f"  哲學家 {philosopher_id} 拿起叉子 {second}")
                    break
            time.sleep(0.001)
        
        return left_fork, right_fork
    
    def put_down_forks(self, philosopher_id, left_fork, right_fork):
        """放下叉子"""
        with self.lock:
            self.forks[left_fork] = False
            self.forks[right_fork] = False
            print(f"  哲學家 {philosopher_id} 放下叉子 {left_fork} 和 {right_fork}")
    
    def philosopher(self, philosopher_id):
        """哲學家執行緒"""
        for meal in range(1, MEALS_TO_EAT + 1):
            print(f"哲學家 {philosopher_id} 正在思考... (餐 {meal}/{MEALS_TO_EAT})")
            time.sleep(THINKING_TIME + random.uniform(0, THINKING_TIME))
            
            # 嘗試拿起叉子
            print(f"哲學家 {philosopher_id} 嘗試拿叉子")
            left_fork, right_fork = self.try_pick_up_forks(philosopher_id)
            
            # 吃飯
            print(f">>> 哲學家 {philosopher_id} 開始吃飯 (餐 {meal}/{MEALS_TO_EAT}) <<<")
            self.print_forks()
            time.sleep(EATING_TIME + random.uniform(0, EATING_TIME))
            
            # 放下叉子
            self.put_down_forks(philosopher_id, left_fork, right_fork)
        
        print(f"★★★ 哲學家 {philosopher_id} 完成所有餐點 ★★★")


def main():
    dining = DiningPhilosophers()
    threads = []
    
    print("=======================================")
    print("     哲學家用餐問題模擬")
    print("=======================================")
    print(f"哲學家數量：{NUM_PHILOSOPHERS}")
    print(f"每位哲學家需吃：{MEALS_TO_EAT} 餐")
    print(f"使用策略：奇偶策略（避免死結）")
    print("=======================================\n")
    
    dining.print_forks()
    print()
    
    # 建立哲學家執行緒
    for i in range(NUM_PHILOSOPHERS):
        t = threading.Thread(target=dining.philosopher, args=(i,))
        threads.append(t)
    
    # 啟動所有執行緒
    for t in threads:
        t.start()
    
    # 等待所有執行緒完成
    for t in threads:
        t.join()
    
    print("\n=======================================")
    print("     所有哲學家都已吃完！")
    print("=======================================")


if __name__ == "__main__":
    main()
