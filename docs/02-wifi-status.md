# Wi-Fi 进度（QCA6490 / WCN6855，PCIe + MHI）

> 基线：**2026-11-11 深夜**，最后实测轮次 p487。
> 逐轮原始证据：`docs/history/CONTINUE-2026-11-10.md`（62 KB，含每次寄存器原文）、`docs/history/HANDOVER-2026-11-11.md`、`docs/history/VENDOR-MHI-AUDIT.md`。
> 本文只保留**已经跑过、且能复现**的结论。

---

## 1. 一句话

**固件能被主机拉起来并跑在 MISSION 模式，但跑起来之后它没有把 Wi-Fi 用的那对数据通道（IPCR ch20/ch21）接上。**
主机侧的 TRE、门铃、上下文、时序已经逐条与厂商驱动对齐、且在一对"固件确实提供"的通道（LOOPBACK ch0→ch1）上**双向跑通了数据**；
所以现在缺的不是主机代码，是 `AMSS` 固件内部那个 MHI 客户端的 attach。

进度条：`链路 ✅ → 固件下载 ✅ → MHI 控制面 ✅ → 命令环 ✅ → 数据面（测试通道）✅ → 数据面（业务通道）❌`

---

## 2. 硬件事实（全部来自真机 DTS + 运行态核实）

| 项 | 值 |
|---|---|
| 芯片 | **QCA6490**（厂商命名）＝ **WCN6855**（上游 ath11k 命名），**同一颗外挂芯片**，不是 QCA6391、也不在 SM8350 内部 |
| PCI | 根端口 `17cb:010c`（`00:00.0`）→ 端点 **`17cb:1103`**（`01:00.0`，BAR0 **2 MiB**） |
| 修订 | `TCSR_SOC_HW_VERSION = 0x400c0110` → **major 1 / minor `0x10`**（"QCA6490 1.1"，ath11k 归为 `WCN6855 hw2.1`） |
| 挂法 | **PCIe0**（`pcie@1c00000`），独立端点、自己的 AMSS/EE/BHI；没有 AHB/SNOC 路径 |
| 固件 | `amss.bin` 5,236,304 B md5 `341ec80bb5caa88867bbb5718322a652` crc32 `0xb4376a2a`（前缀 512 KiB crc32 `0xb163aa48`）；`amss20.bin` 5,197,824 B（major 2 用）；`m3.bin` 266,684 B（RDDM 用）；`regdb.bin` 24,278 B；`bdwlan.e01…e97` 共 147 个 |
| 固件真伪 | 与原厂 `/vendor/firmware_mnt/image/` 四个文件 **md5 全一致** ⇒ **"换个更好的固件"这条路已关闭** |
| 为什么用 `amss.bin` | 厂商规则 `cnss_pci_update_fw_name()`：`QCA6490` 且 `major==2` → `amss20.bin`，其余 → `amss.bin`；本机 major 1，真机 dmesg 也是 `amss.bin` |
| 参考实现 | 小米 11 Ultra（**star**，同 SM8350 + 同芯片）用**同一份固件**（size/crc 逐字节一致）跑通了 IPCR/WLFW/QMI ⇒ 卡点不在硬件 |
| 根端口供电 | `ldob6` 1.2 V、`ldob5` 0.88 V（RPMh 投票） |
| 无线电六路 | `smpb10` 1.8 V、`ldoe7` 2.7 V、`smpe2` 0.95 V、`smpb11` 0.95 V、`smpc1` 1.9 V、`smpb12` 1.35 V（全部 RPMh） |
| 引脚 | PERST# = TLMM **94**、WLAN_EN = **64**、CLKREQ = 95、BT_EN = 65、SW_CTRL = 153 |

---

## 3. 阶段总表

| 阶段 | 内容 | 状态 | 决定性证据 |
|---|---|---|---|
| **M0** | 上电、时钟、PHY 75 条序列、PERST/WLAN_EN、**链路训练**、ECAM 枚举 | ✅ 11-07 | `link UP: ELBI 0x08 = 0x00011401`、`LTSSM 0x00000111`（state 17）、Gen2、读到 `17cb:1103` |
| **M1** | SMMU（BDF→SID `0x1c01`）+ BAR0 + MHI 能力寄存器 | ✅ 11-08 | `gfsr 0` 无 fault；`MHICFG 0x00030880`、`CHDBOFF 0x300`、`ERDBOFF 0x700` |
| **M2** | BHI/BHIE 固件下载，设备进 `EE=2` | ✅ 11-08 | 10 个 512 KiB 向量覆盖全部 5,236,304 B；`bhie after 700 ms: status 0xbbd056f0 ee 0x00000002` |
| **M3** | MHI 初始化（上下文数组、命令/事件/通道环、门铃） | ✅ 11-08 | `CCABAP 0xa0200000`、`ECABAP 0xa0202000`、`CRCBAP 0xa0202400`；命令环 `+0x7000`、事件环 `+0x4000` |
| **M4** | M0 握手 + 事件环 device→host | ✅ 11-08 | `MHISTATUS 0x00000201`；er0 收到 `STATE_CHANGE(state 2)`、`EE_EVENT(ee 2)` |
| **M5** | 命令环 host→device（START_CHAN 回 SUCCESS） | ✅ 11-09 | 4 条 `CMD_COMPLETION(code 1)`，`dword0` 指向 `0xa0207000/7010/7020/7030`（p480） |
| **M6** | BW_REQ / bw-scale / 特殊通道 | ✅ 11-09 | er2 收到 `BW_REQ_EVENT(type 0x25)`，应答后 `bwdb 0` |
| **M7** | 控制面 + `0xb0` SOC reset / RDDM | ✅ 11-10 | 写 `0xb0=1` → 7–20 ms 进 `EE=3`，再写一次可**钉住** |
| **M8** | 数据面：TRE 取用 + 载荷 DMA + 完成事件 | ✅ 11-10（测试通道） | p431 `apply-390`：ch0 发出 16 B，ch1 缓冲区**原样收到**，er1 两个事件（ch0 TX_EVENT / ch1 完成） |
| **M9** | **IPCR（ch20/ch21）被固件消费** | ⛔ **当前卡点** | 见第 5 节 |

---

## 4. 已经打通的部分（每一格都能拿日志复现）

### 4.1 上电与链路

- 六路 rail 全部投票成功；`CLKREQ#`/`WLAN_EN`/`PERST#`/`BT_EN`/`SW_CTRL` 全部拉到位。
- PARF `DEVICE_TYPE=4`、`SYS_CTRL=0x365e`；PHY 75 条序列跑完、PLL 锁定（`the PCS status bit cleared at 3 x 200 us: 0x00000086`）。
- **注意**：写 `LTSSM` 要**置位** bit8 才启动训练；早期两次把它清零，白跑两轮。

### 4.2 固件下载

- BHI：`BHI_IMGADDR 0xa0004000`、`IMGSIZE 0x80000`，`BHI_STATUS = 0x80000001`（SUCCESS + READY）。
- BHIE：10 段 × 512 KiB，589 ms 传完，`TXVECSTATUS = 0xbbd056f0`（top2 = XFER_COMPL，seq 与我们写入的一致）。
- 之后 `EE: 1(SBL) → 2(AMSS)`，`MHISTATUS = 0x201`。

### 4.3 MHI 控制面与命令环

- `MHICFG 0x00030880`（NCH 128 / NHWCH 3 / NER 3 / NHWER 2）、`CHDBOFF 0x300`（通道门铃 `0x300+ch*8`，ch20 → `0x3a0`）、`ERDBOFF 0x700`、`BHIOFF 0x100`、`BHIEOFF 0x224`。
- **命令环在稳态是可用的**（这条曾经被误判为"只在启动窗口可用"）：
  p480 一次写 4 条 `START_CHAN` TRE（`00120000 01120000 14120000 15120000`）、把 cmd `wp` 直接推到 `0xa0207040`、**敲一次**命令门铃 → 事件环出现 **4 条 `CMD_COMPLETION`（`type 0x21`，`code 1 = SUCCESS`）**，ch20 变 `0x202`。
  ⇒ 单条 TRE + 逐步门铃不行、批量 + 单次门铃可以；差别在 wp 语义，不在环地址。
- 反过来把 cmd `wp` 往回拨会让设备 `0x0000ff05`（SYS_ERR）⇒ 命令面是活的且严格。

### 4.4 数据面（测试通道 LOOPBACK）

p431 / `apply-390` 完整走了一遍双向：

```
apply-390 b ch1: two buffers at 0xa03e0000/0xa03f0000 wp 0xa0209020, ringing 0x308
apply-390 d ch0: tre ptr 0xa03d0000 len 0x10 wp 0xa0208010, ringing 0x300
apply-390 f ECHO at 0 ms: a 534f494b 534f494c 534f494d 534f494e | b beef0000 beef0001 beef0002 beef0003
apply-390 h slot0 er1: a0208000 00000000 02000010 00220000   ← ch0 TX_EVENT
apply-390 h slot1 er1: a0209000 00000000 02000010 01220000   ← ch1 完成，低字节 = 通道号
```

⇒ **主机侧 TRE 取用、payload DMA、事件投递三件事全对**。这条正对照是后面一切判断的基准。

事件字段语义（实测）：`dword2` 高 16 = code/状态、低 16 = 长度；`dword3` bit16-23 = 类型、**低 8 位 = 通道号**。

### 4.5 通道上下文到底谁写

p468（`pcie_chanstart=0`，主机完全不发通道上下文）证明：**固件自己就把 ch0/ch1/ch20/ch21 建好了**，全是 `0x00000202`（RUNNING + brustmode 2），环基址 `0xa0208000/9000/c000/d000`。

而且**只有 `0x202` 能让 AMSS 启动**：

| 握手时发布的值 | 结果 |
|---|---|
| `0x202` | EE=2，AMSS 正常起来 |
| `0x201` | EE 恒 1，AMSS 永不启动 |
| `0x200`（chstate 0） | EE 恒 1，AMSS 永不启动 |

⇒ 固件在 SBL→AMSS 交接时**确实读这两条通道的上下文**，通道对象存在且被消费——只是它读完不干活。

### 4.6 RDDM

写 `MHI_SOC_RESET_REQ (0xb0) = 1` → 7–20 ms 进 `EE=3`（RDDM），**再写一次可以钉住不走**。
但 BHIE RX 无论"下载前武装"还是"启动后武装"都**一个字节也收不到** ⇒ 这条路拿不到固件 crash 文本。
（教训：RDDM 缓冲区不能放在镜像区，`0xa0220000 + 0x4fe650` 一直是有效镜像，落在里面的"转储"其实是自己的固件副本——差点当成成功。）

---

## 5. 当前卡点（三条，全部有正对照）

### 5.1 IPCR ch20/ch21：设备不消费

| 主机动作 | 结果 |
|---|---|
| 敲 ch20 通道门铃（`0x3a0`，值 = ring wp） | 无反应，`rp` 不动 |
| 先写 `ctx.wp` 再敲门铃（vendor 顺序） | 无反应 |
| ch21 预填 32 个 0x8000 buffer 再敲门铃 | `ch21 rp` 停在 `rbase`，设备不往里写 |
| **完全不碰上下文**、只用固件自己的环与 wp（p481） | `ch20 st 0x202 rp 0xa020c000 wp 0xa020c010`（10 s 采样）**`rp` 一格没动** |
| 只读观察 10 s / 100 ms 采样 | 零变化（不是"起得慢"） |

判据强度：同一套代码在 ch0 上立刻搬数据并回事件 ⇒ **主机机制没问题，缺的是固件里的消费者**。

### 5.2 早 M0（EE=1 写 M0）在 venus 上必 SYS_ERR

| 轮次 | 做法 | 结果 |
|---|---|---|
| p477 | `nom0=0 late0=0`，READY 时写 M0 | `apply-273 m0 fault check: fsr 0x400 far 0x… mh 0x0000ff05 ee 1` → 整轮崩 |
| p484 | 同上 + 通道预发布 `0x200` | 同样 `0xff05`，之后 MHI 恒 `0xff05`，START 全无 completion |
| p485 | READY 后**第一次看到 EE=1 的同一毫秒**写 M0 | 21 ms 后照样 `0xff05` ⇒ **不是时机问题** |
| p487 | 改 `pcie_novec=0`，走 BHIE 向量路径 | 照样 `0xff05` ⇒ **不是装载方式问题** |

而真机 Android 上 **vendor 就是在 `EE=1`（SBL）写 M0 的，而且不崩**（见 5.4 真机时序）。

⇒ **这是目前唯一还剩下的"主机侧结构差异"**。晚写 M0（EE=2 之后）一切健康，但 IPCR 客户端永远不 attach（p486：EE=2 后 1 ms 内写 M0，`mh 0x201`、命令环回 4 条 completion、数据环仍零消费）。

### 5.3 事件流在 EE=2 之后只剩 2 条

擦净实验（把 `0x4000..0x5000` 清零）后设备仍写回：

```
er[00] … 00200000  type 20 (STATE_CHANGE)
er[01] … 00400000  type 40 (EE_EVENT，均带 EE=2)
er[02..1f] 全 0
```

且**设备从不更新事件上下文的 `wp(+0x24)`**（擦净后 rp/wp 都还是基址）⇒ 主机只能扫 TRE 判断有无新事件。
`wp` 初值（`rb+0xff0` vs `rb`）与地址搬家（`0xa0200000` ↔ `0xa1c00000` A/B）都**与事件数无关**。

---

## 6. 已排除清单（**别再重复做**）

| # | 类别 | 怎么排除的 |
|---|---|---|
| 1 | 固件版本/来源 | 原厂 md5 全一致；`amss20` 起不来（major 不符） |
| 2 | 镜像完整性/装载方式 | BHIE 10 段全拉、XFER_COMPL、seq 匹配；push 窗口与 BHIE 拉取都成功 |
| 3 | SMMU | `gfsr 0`，无 fault |
| 4 | 通道上下文地址与内容 | p424 证明 `CCABAP` 就是我们写的块；p468 证明是固件自己写的 |
| 5 | 门铃地址/写序 | `0x300+ch*8`（ch20=0x3a0）；先写高 32 位再写低半，与 vendor `mhi_write_db()` 一致 |
| 6 | TRE 位域 | `dword1=0x00020200` 与 `MHI_TRE_DATA_DWORD1` 逐位一致；IEOT/IEB 各种组合、brst 0/2/3 都试过 |
| 7 | 环长度 | 32 vs 64 元素 |
| 8 | 事件环约定 | `rp=base/wp=base` 与 `rp=base/wp=base+len-16` 两种 |
| 9 | MSI / 向量数 | MME=0 只有 1 个向量 → 4 个向量、清 `BHI_INTVEC`，无效 |
| 10 | M2 请求 | 写 `MHICTRL=0x400`，通道全空闲也拒 |
| 11 | 电源/时钟/使能脚 | 六路 rail 逐条对上 DT supply phandle；三个使能脚全拉高无效；cnss 节点**没有 clocks 属性**，参考时钟来自 PCIe REFCLK |
| 12 | ICC 带宽投票 / `vrm.wlan` TCS | 唯一使用者在 BDF 下载**之后**才调，属 QMI 阶段 |
| 13 | `m3.bin` | 只是 RDDM/crash dump 缓冲，不是启动阶段 |
| 14 | RDDM 抓 dump | 两次武装 BHIE RX 都收不到 |
| 15 | 写 `MHICTRL` 的 SYS_ERR(0xff00) | 设备直接无视，MHISTATUS 恒 `0x101`（SBL） |
| 16 | star 的差异项 | BHIE 前发布 `chstate 0`（venus 上让 AMSS 起不来）、ER 空环约定（无效）、`smpc1` 2000/1900（非卡点） |
| 17 | 真机 trace / devmem | `available_tracers` 只有 `nop`、无 kprobe、kallsyms 全 0；`devmem` 读 BAR 会崩机（adb 掉 55 s） |
| 18 | 固件里有没有 IPCR | 有：`ipc_router_core_patch.c`、`IPCR_CORE_DEBUG`/`IPCR_MHI_TX_DEBUG`/`IPCR_MHI_RX_DEBUG`、`In ipc_router_xal_up xport->up=0x%x`、`1st message` |
| 19 | 纯静态反汇编定位 | 见第 8 节，硬边界 |

---

## 7. 被推翻的旧结论（如果你读过 11-10 的文档，请以本节为准）

| 旧结论 | 现在的结论 | 推翻它的轮次 |
|---|---|---|
| "设备从未碰过任何通道上下文" | **错**。固件自己建上下文（`0x202`）并把它当握手条件；`0x200` 直接让 AMSS 起不来 | p468 |
| "设备发过 CMD_COMPLETION 从未被真正证实" | **错**。p480 一次拿 4 条 `code 1`，`dword0` 指向我们写的那 4 条 TRE | p480 |
| "命令环只在 boot 窗口可用" | **错**。稳态可用；之前失败是 `nom0/late0` 把 M0 写晚 + 单条 TRE 逐步门铃的 wp 语义问题 | p480 / p486 |
| "`amss.bin` 是 ARM Thumb-2，可 `arm-none-eabi-objdump`" | **错**。它是 **Hexagon（Q6）DSP 固件**，`e_machine=40` 只是打包默认值；用 `llvm-objdump --triple=hexagon --mcpu=hexagonv66` 才能解 | 2026-11-11 |

---

## 8. 固件静态分析的边界（Hexagon / QURT）

- 把 ELF 头 offset `0x12` 的 `e_machine` 从 40 改成 **164（EM_HEXAGON）**，即可：
  `llvm-objdump -d --triple=hexagon --mcpu=hexagonv66`（795,208 行，零错误）。
  现成脚本：`scripts/re-hx-elf.sh`、`scripts/re-hx-dump.sh`。
- 已定位：
  - `0x15ede6c` = 打印 `In ipc_router_xal_up xport->up …` 的函数（读 `xport+0x2c` up / `+0x2d` hello_sent）；
  - `0x15edd6c` = IPCR debug flag 注册函数；
  - `mhi_channel_rw_multiple`（`0x15e96f0` 起）：channel 结构 state 在 `+0x10`，**open 状态 = 2**，`r18==0` → "wasn't opened"。
- **边界**：`0x15ede6c`（xal_up）在 5 MB 镜像里**零函数指针引用、零 direct call**，只被自己 tail-call；`0x8xxxxx` 那些地址（`0x839840`、`0x8559bc`）**不在任何 ELF 段内**，是 QURT 对外 stub。
  ⇒ **IPCR 的初始化/通道 open 调用方在 QURT 镜像里，不在 ELF 里**。继续啃 ELF 没有增量，要往前必须先把 QURT 的 stub 解析（符号表/ROM 镜像）拿下来。

---

## 9. 真机（原厂 Android）对照：它到底在哪一刻跑起来

从 `android/cnss-mhi-clean.log`（74 KB，UTF-16LE BOM + ASCII 正文）解出 31.5–32.2 s 这段：

1. `mhi_alloc_bhie_table … bytes:5236304 seg_size:524288 total_seg:11`（10 数据段 + 1 个 160 B 的 BHI 向量表段）。
2. 31.536 `Processing Event … → MHI state change event to state:M0`、`mhi_pm_m0_transition Entered With State:READY`，紧接 `EE received event:SBL`
   ⇒ **vendor 在 EE=1 就写 M0，而且不崩**。
3. 32.190 `device ee:AMSS dev_state:M0`；32.192 `mhi_prepare_channel … channel:20` → `mhi_send_cmd WP:0xa0108000 TRE: 0x14120000`（**单条** START_CHAN）
   → 32.194 `Chan:20 successfully moved to start state`。
4. 同一毫秒 `mhi_queue_skb chan:20 WP:0xa0c01000 TRE:0xa0c02a00 0x00000034 0x00020200`（**首发 52 B QMI**）；随后 ch21 START + 布 32 条 RX TRE。
5. 32.207 起事件环（`er_index:1`）立刻工作：ch20 `TX_EVENT`、ch21 完成事件，host 收一个补一个。
   ⇒ **START 完成到双向数据，真机是毫秒级**。
6. 地址布局：ctrl ≈ `0xa0100000`（命令环 `0xa0108000`）、data ≈ `0xa0c00000`（ch20 环 `0xa0c01000`、ch21 `0xa0c03000`、RX 缓冲 `0xa0c08000` 起）、固件 staging `0xa0700000`。
7. 另有一条旁证：`wlfw_start` 之后 `Server disconnect, err -2` 再重启一次 ⇒ AMSS 起来后确实有一段"服务未就绪"期。

---

## 10. 从"现在"到"能上网"还要过几道门

| 里程碑 | 内容 | 状态 / 估计 |
|---|---|---|
| M9 | IPCR ch20/ch21 起来（固件客户端 attach） | ⛔ 当前；1–3 天（若属配置）～1–2 周（若属时序/必要条件） |
| M10 | QRTR over MHI（`sq_family = AF_QIPCRTR`） | 3–7 天 |
| M11 | QMI / WLFW + `board-2.bin`（用芯片上报的 board id 拼 `bdwlan.*`） | 1–2 周 |
| M12 | ath11k CE/HTC/WMI（含 hw2.1 十行补丁），能扫描 | 2–3 周 |
| M13 | 关联 / 四次握手 / DHCP | 2–3 周 |
| M14 | Apple80211 / `wifid`：开关、列表、状态栏图标 | +1–2 周（Darwin 侧骨架已写好） |

**总体**：乐观 2–3 周，**现实 6–9 周**，悲观 3 个月以上。
风险已经从"移植工作量"挪到了"固件应用层到底为什么没起来"——这条不在我们的代码里。

**每轮实验成本**：冷启动 42 s + 打包 65 s + 跑 115 s + 取日志 15 s ≈ **5 分钟**，一天能跑 60–80 轮。

---

## 11. 通俗版（给不看寄存器的人）

- 手机里那颗 Wi-Fi 芯片是"外挂"的，插在 PCIe 总线上，跟一块小显卡差不多。
- iOS 内核要驱动它，第一步是**给它上电、把它叫醒**（M0）——**做到了**。
- 第二步是**把它的固件（`amss.bin`）塞进它自己的内存并让它跑起来**（M2）——**做到了**。
- 第三步是**和它建立"收件箱"和"发件箱"**（MHI 的环和门铃）——**做到了**，而且我们往发件箱里塞一个测试包裹，它确实收下并原样退回（LOOPBACK 通道）。
- 第四步，也是卡住的那步：**它应该主动打开"Wi-Fi 专用"的那两个收件箱**（IPCR ch20/ch21），然后我们才能跟它聊"扫到哪些热点""密码对不对"。
  它现在只回了开机时的两条通知，之后就**装死**。
- 我们这边能试的都试完了（换地址、换姿势、换敲门顺序、换时序、换固件装载方式……），**全部无效**；而在另一台同芯片的小米 11 Ultra 上，同一份固件是能跑通的。
- 所以现在的判断是：**要么它启动后缺一个我们还没给的前置条件（例如"必须先收到一条 QMI 消息它才开门"），要么它对我们的启动方式有隐含要求**（唯一的硬差异：Android 上厂商是在"固件刚起来、还没进入系统"那一刻就发"我准备好了"，而我们在那个时刻发，它会直接报错关机）。

---

## 12. 复现要点（不是"看一眼"就行的部分）

| 判据 | 必须看到什么才算数 |
|---|---|
| 这一轮真的生效了 | 日志里**没有** `WARNING: the kernel command line is TRUNCATED`，且 `strings hakios-kernel \| grep -c apply-NNN` = 1 |
| 读的是本轮日志 | 先按 `pcie_tag=pNNN` 切片，再取以 `the probe is done…(apply-169)` 结尾的最新时间戳组 |
| 设备还活着 | `MHISTATUS` 低 8 位 = `0x01`（READY），且没有 `0xff05`（SYS_ERR） |
| 通道被消费了 | 通道上下文 `rp` **前进**了（不是 `wp` 变了） |
