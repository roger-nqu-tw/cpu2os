
一、 while 迴圈實作機制
while 迴圈的本質是條件判斷加上向後跳轉（Backward Jump）。編譯器在解析到 while 語句時，會自動生成對應的標籤（Labels）與跳轉指令（Jump Instructions）。

1. 結構拆解
一個標準的 while 迴圈語法：

Delphi
while (condition) do
begin
    // body (迴圈主體)
end;
2. 指令生成（Assembly/P-Code）
編譯器在遍歷抽象語法樹（AST）時，會將上述結構翻譯成類似以下的虛擬機指令（P-Code）：

Plaintext
L_START:                  // [標籤 1] 迴圈起點
    <評估 condition 的指令> 
    JPC L_END             // [條件跳轉] 如果 condition 為 False (0)，跳轉到 L_END
    <執行 body 的指令>
    JMP L_START           // [無條件跳轉] 執行完主體後，跳回迴圈起點重新判斷
L_END:                    // [標籤 2] 迴圈結束點
3. 實作細節與挑戰
標籤管理： 在 P0 編譯器中，通常會使用一個全域計數器來動態產生唯一的標籤名稱（例如 L1, L2），確保巢狀迴圈（Nested Loops）不會發生標籤衝突。

回填（Backpatching）： 在單遍編譯（Single-pass Compiler）中，當編譯器遇到 while 的條件判斷並需要生成 JPC 跳轉指令時，此時 L_END 的確切位址可能還未知。編譯器會先留下一個空位，等到迴圈主體編譯完成，確定位址後，再回頭將 L_END 的真實位址填入該跳轉指令中。

二、 函數呼叫（Function Call）機制
函數呼叫比迴圈複雜得多，因為它不僅涉及指令的跳轉，還涉及狀態保存與資料傳遞。這一切都是透過呼叫堆疊（Call Stack）和堆疊框（Stack Frame / Activation Record）來完成的。

1. 核心暫存器
在理解函數呼叫前，必須認識兩個關鍵的暫存器：

SP (Stack Pointer - 堆疊指標)： 永遠指向堆疊的最頂端。

BP (Base Pointer - 基底指標)： 指向當前函數堆疊框的基準位置。透過 BP + 偏移量 可以讀取參數，BP - 偏移量 可以讀取區域變數。

2. 函數呼叫的生命週期
當 Caller（呼叫者）呼叫 Callee（被呼叫者）時，會經歷以下標準流程：

階段 A：前言 (Prologue) - 準備與進入

傳遞參數： Caller 將參數由右至左（或左至右，依呼叫慣例）推入堆疊 (Push)。

保存返回位址： 執行 CALL 指令，硬體或虛擬機自動將下一條指令的位址（Return Address）推入堆疊。

保存舊的 BP： Callee 開始執行，第一件事是將 Caller 的 BP 推入堆疊，確保未來能恢復。

建立新的 BP： 將目前的 SP 值賦予 BP（BP = SP），這標誌著 Callee 堆疊框的建立。

分配區域變數： 增加/減少 SP 的值，在堆疊上為 Callee 的區域變數預留空間。

階段 B：函數主體執行

此時，程式可以透過 BP 穩定地存取參數和區域變數，因為無論 SP 如何隨意 Push/Pop 暫存資料，BP 在函數執行期間都是固定的。

階段 C：結語 (Epilogue) - 清理與返回

釋放區域變數： 將 SP 移回 BP 的位置，直接丟棄區域變數的空間。

恢復舊的 BP： 從堆疊中彈出 (Pop) 舊的 BP 值並恢復。

返回 (Return)： 執行 RET 指令，從堆疊彈出返回位址，並將 PC 指向該位址，將控制權交還給 Caller。

為了讓你更直觀地理解函數呼叫時記憶體堆疊的變化，我為你準備了一個互動式的堆疊視覺化工具。你可以透過點擊按鈕，觀察 SP 和 BP 是如何在函數呼叫與返回過程中移動的。
