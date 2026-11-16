# 下一步该怎么做

> 写给接手的人：这份文档假设你已经读完 [`01-verified-features.md`](01-verified-features.md) 与 [`02-wifi-status.md`](02-wifi-status.md)。
> 结论先行：**不要再调主机侧的 TRE/门铃/上下文了**——那 434 轮已经把这条路走到没有信息量；剩下的收益全在"固件为什么没把 IPCR 客户端接上"和"绕开它"两个方向。

---

## 0. 先修地基：构建环境已经没了

重装系统后，真正的驱动源码树（`/root/hakios`，`hakios.pcie.c` 约 5,150 行）**不在了**。
本仓库能提供的替代物只有：

| 有 | 没有 |
|---|---|
| 43 KB 的驱动早期快照（`src/drivers/pcie/hakios.pcie.c`，停在 11-06 的 M0 之前） | 带 apply-001…434 的最终 5,150 行版本 |
| 307 份 `apply-NNN.py`（每份的锚点字符串 + 改编意图） | 它们赖以生效的那份中间状态 |
| 全部结论、寄存器表、判据、踩坑记录 | 可编译的完整内核树 |

所以第一件事是**把树重建出来**，三条路按成本排序：

| 路线 | 做法 | 成本 | 风险 |
|---|---|---|---|
| **0-A 重建基线（推荐）** | 克隆 HakiOS 2.1.13（`github.com/oosexgang/hakios-xnu-kernel`）→ 装工具链 → `bash tools/make-kernel.sh -j20` 先确认基线能编 | 半天 | 低。基线本来就能编，`exit 2` 只是 kext symbol-set 检查 |
| **0-B 从 patch 反推** | 用 `history/INDEX.md` 按编号把 307 个 `apply-NNN.py` 逐个跑一遍 | 1–2 天 | 中。锚点强依赖中间态，越往后越容易 `assert count==1` 失败；失败了就按 INDEX 的描述手写改动 |
| **0-C 抄 star 的结构** | 直接照 `lemonade_wifi.c`（小米 11 Ultra，同芯片，已跑通 IPCR/WLFW）重写我们的 `jpcie` 探针骨架，只保留结论表里那些已验证的寄存器值 | 2–3 天 | 中低。**这条路的天花板更高**：star 的写法本身就是"能跑通"的写法 |

> 建议：**0-A 打通编译 → 0-C 重写骨架**，0-B 只用来查"当时到底改了什么"。
> 理由：`hakios.pcie.c` 是一个 5,150 行的单函数实验探针，它已经完成了它的使命（把 M0–M8 钉死），继续在它上面堆补丁只会继承历史包袱。

---

## 1. 优先级总表

| 优先级 | 任务 | 为什么现在做 | 成本 |
|---|---|---|---|
| **P1** | 验证"AMSS 跑的是不是我们下载的镜像" | 一次 30 分钟的实验，能**一刀切开两种完全不同的解释** | 0.5 h |
| **P2** | 重开 RDDM，抓固件崩溃转储 | 唯一能直接看到设备侧异常 PC 的办法 | 2–4 h + 数轮 |
| **P3** | 拿一台 star（11 Ultra）的现场或 `MHI_VERB` 日志 | 同一份固件在它上面跑通；差异就是答案 | 取决于能否拿到设备 |
| **P4** | 解 QURT stub（`0x8xxxxx` 段） | 静态分析唯一的下一步；能定位 `ipc_router_xal_up` 的调用方 | 3–5 天，风险高 |
| **P5** | 上层并行：QRTR → QMI/WLFW → ath11k → Apple80211 | 不占设备时间，且 M9 一通就能立刻接上 | 2–3 周，可与 P1–P4 并行 |
| **P6** | 兜底：USB 网卡 / USB tether | 如果目标只是"这台机器能上网"，这条最省 | 2–4 周（要 XNU USB host 栈） |

---

## 2. P1：镜像真伪验证（先做这个）

**假设**：设备可能在跑**自己 flash 里的 AMSS**，而不是我们用 BHI/BHIE 推过去的镜像。若成立，那"IPCR 客户端不 attach"的解释就要从"我们的镜像里没起来"改成"设备侧配置问题"。

**做法**（三种，任选其一，越靠前越干净）：

1. **截断镜像**：把 `userland/root/fw/amss.bin` 截到 1 MB（`truncate -s 1048576`），重打 `root.apfs`（`scripts/fwswap.sh`），冷启动跑一轮。
2. **改一个字节**：在镜像头部某个无意义位置翻一位（保留 crc 长度字段不变更稳妥），同上。
3. **换错版本**：直接用 `amss20.bin` 改名成 `amss.bin`（已知 major 不符，正常应停在 EE=1）。

**判据**：

| 现象 | 说明 |
|---|---|
| 截断后**照常出现 EE=2**、`MHISTATUS=0x201` | 设备跑的不是我们推的镜像 ⇒ **立刻改打法**：问题在 flash 侧配置/NV/board data，不在镜像内容 |
| 截断后停在 EE=1 或 SYS_ERR | 镜像确实被它执行了 ⇒ 继续 P2 |

**注意**：`amss20.bin` 那条实验历史上做过（停在 EE=1），所以它同时也是 P1 的第 3 个对照——如果"截断"也停在 EE=1，就与"换错版本"同构，可信度高。

---

## 3. P2：把 RDDM 重新打开，抓崩溃转储

现状：`0xb0` 能把设备打进 `EE=3` 并钉住，但 **BHIE RX 收不到任何字节**，因为 `apply-345` 把 RDDM 块编译掉了。

**要做的事**：

1. 恢复 `apply-345` 之前那版 RDDM 代码（参考厂商 `drivers/bus/mhi/core/mhi_boot.c` 的 `mhi_rddm_prepare()` / `mhi_force_rddm_mode()`；本仓库 `history/patches/` 里有对应的脚本）。
2. 缓冲区必须放在**镜像区之外**：镜像整份副本在 `0xa0220000` 起 5 MB（结束约 `0xa071fa50`），表放 `0xa0990000`、5 段从 `0xa0720000` 起（这是 p351/p352 试过的位置）。
3. 按 vendor 顺序：先清零 BHIE RX 寄存器（上电值未定义）→ 写向量表 → 触发。
4. 读回后**先核对"这是不是我们自己写进去的"**（p349 就差点把固件副本当成转储）。

**判据**：`RXVECSTATUS` 低位的序号等于我们写入的值（历史上我们写 `0x3320`，读回却不是）→ 表被设备确认了；之后 `seg0 nz > 0` 才算真的拿到 dump。

---

## 4. P3：拿 star 的现场

star（小米 11 Ultra，同 SM8350 + 同 QCA6490 + **同一份固件**）是唯一已知的成功样本。要的是它 **MHI 初始化 0–600 ms** 那一段的完整日志。

两条取法：

| 取法 | 前提 | 能拿到什么 |
|---|---|---|
| 借一台 star，开 `MHI_VERB` 的内核跑一遍 | 需要设备 | 完整逐帧时间线，可直接 diff |
| 让 star 的用户提供现成 dmesg | 需要人 | 同上，但可能被裁剪 |

**diff 的维度**（按可疑度，不是按寄存器值）：

1. **EE=1 写 M0 为什么会成功**（我们必 `0xff05`）。这是唯一还剩下的主机侧结构差异。
2. **BHI→BHIE 之间主机还做了什么"与 MHI 无关"的动作**（QMI 预置、board data、时钟/电源的第二次切换）。
3. **IOVA 布局**：真机 ctrl `0xa0100000` / data `0xa0c00000` / staging `0xa0700000`；我们一直是 `0xa0200000` 起 8 MB。历史上验证过"搬家不是原因"，但没验证过"范围与对齐不是原因"。

> 如果拿不到 star，P3 就跳过，直接 P4/P5，不要空转。

---

## 5. P4：解 QURT stub，把静态分析推进一步

已到边界：`ipc_router_xal_up`（`0x15ede6c`）零引用，`0x8xxxxx` 是 QURT 对外 stub，不在任何 ELF 段内。

**要的东西**：QURT 的符号表或 ROM 镜像（`0x8xxxxx` 段的实际内容）。可能的来源：

1. 同一份 `amss.bin` 里是否还有第二个 ELF/段表被漏掉（`readelf -l` 全量对一遍 program header，不只 PT_LOAD）。
2. 其它 QCA6490 机型（一加 9、REDMAGIC 6）的 `amss.bin` 做二进制 diff：相同区 = MHI 核心，差异区 = 机型相关。
3. Qualcomm 公开的 QURT 文档/开源片段（QuRT 是闭源的，但 stub 调用约定有社区总结）。

**目标问题**：**谁创建 `xport`？创建条件是什么？**
如果答案是"主机发来第一条 MHI 消息"，那就是死锁 ⇒ 必须从上层先发（见 P5）；
如果答案是"通道 open 完成回调"，那说明 open 根本没发生 ⇒ 回去查设备为什么不开。

**成本**：3–5 天，且不保证有结论。**在 P1/P2 之前不要开这条。**

---

## 6. P5：上层并行（不占设备时间，收益确定）

这一层**不依赖 M9**，可以先写完、先单测，等 IPCR 一通立刻接上：

| 模块 | 现状 | 要做的 |
|---|---|---|
| QRTR over MHI | `bsd/sys/hakios.qrtr.h`、`hakios.qmi.h` 已有结构与 `AF_QIPCRTR` 助手 | 把传输层指向 MHI 的 ch20/ch21；写一个 hello（`{2, {0}}` 到 `QRTR_CONTROL_PORT 0xffffffff`） |
| QMI / WLFW | 树里已有 `wlan_firmware_service_v01.{c,h}`（厂商定义） | host 端 QMI 客户端：`WLFW_GET_CAPABILITIES`、`WLFW_BDF_DOWNLOAD`（用芯片上报的 board id 拼 `board-2.bin`） |
| `board-2.bin` 生成 | `bdwlan.e01…e97` 147 个 + `regdb.bin` | 按 board id 拼装的脚本（参考 SteamOS-ARM 的 `extract-nx669j-firmware.sh`） |
| ath11k | `tools/mk-ath11k.sh` 能编出 `ath11k.o`；hw2.1 只需十行补丁 | CE/HTC/WMI 起来，能 `scan` |
| Apple80211 / IO80211 | `hakios.apple80211.c`（ioctl `0x802869c8/0xc02869c9`）、`hakios.wlan.cpp`（发 `IO80211Controller`）、`hakios.sta.h`（`hakios_sta_ops{scan,heard,join,state,channels}`） | 一旦底层能扫到 AP，把 802.11 实现挂到 `hakios_sta_ops` |
| configd / DHCP / DNS | 现成组件 | 接口与网络栈对接 |

排序建议：**QRTR hello → WLFW 能力查询 → board data → ath11k scan → 关联 → DHCP → Apple80211**。
这条链上每一步都有 star 的日志可以对照（`docs/history/` 与 `references/01-star-wifi-source`）。

---

## 7. P6：如果目标只是"这台机器能上网"

| 方案 | 代价 | 可行性 |
|---|---|---|
| USB 以太网/Wi-Fi 网卡 | 需要 XNU 的 USB host 栈 + 对应驱动（`hakios.net.h` 有骨架） | 中，2–4 周 |
| USB tethering（Android 手机共享） | 同上，但驱动更简单（CDC-ECM/RNDIS） | 中低 |
| 蓝牙 tether | 需要蓝牙协议栈，比 USB 更远 | 低 |

**建议**：这条只在"Wi-Fi 明确要搁置几个月"时启用。它会让这台设备**能上网**，但不会让 iOS 的 Wi-Fi 界面变可用——`wifid` 仍然没有驱动认领接口。

---

## 8. 每条路线的验收标准（写死，避免自我安慰）

| 任务 | 成功必须看到 | 失败就是失败，不要说"看起来设备收到了" |
|---|---|---|
| P1 镜像真伪 | 截断镜像后 `EE` 与 `MHISTATUS` 的变化（或不变） | 不能用"没有变化"解释成"设备很稳" |
| P2 RDDM | `RXVECSTATUS` 序号 == 写入值，且 `seg0 nz > 0` | 读到非零但落在镜像区 = 假数据 |
| P3 star diff | 逐字段 diff 表（时间、寄存器、动作），至少一条差异被实验证实 | "star 也是这么做的"不算结论 |
| P5 QRTR | IPCR 通道 `rp` 前进 + 收到 `hello` 应答 | 门铃写进去回读一致 ≠ 设备收到 |
| 任何一轮 | 日志无 `TRUNCATED`、`apply-NNN` 命中、`pcie_tag` 对得上 | 三条缺一条，这一轮结论作废 |

---

## 9. 时间表（诚实版）

| 里程碑 | 乐观 | 现实 | 悲观 |
|---|---|---|---|
| 环境重建 + 能编能跑 | 1 天 | 2–3 天 | 1 周（若 patch 反推失败） |
| P1 镜像真伪 | 半天 | 1 天 | 2 天 |
| P2 RDDM 拿到 dump | 2 天 | 1 周 | —（可能永远拿不到，取决于固件是否愿意吐） |
| M9 IPCR attach | 3 天 | 2 周 | 1 个月+ |
| M10–M14 到能上网 | 3 周 | 6–9 周 | 3 个月+ |

**结论**：如果 P1 证明"设备跑的是 flash 里的 AMSS"，整个 M9 的性质会变（从"主机/镜像问题"变成"设备侧配置问题"），时间表要重估——这是为什么 P1 排第一。

---

## 10. 不要做的事（每一条都真的浪费过一整轮）

1. 不要在 `EE=1` 写 `MHICTRL` 的 M0（除 M2→M0 这一条合法路径）——venus 上必 `0xff05`。
2. 不要在 `EE=1` 时打事件环门铃（设备直接丢弃）。
3. 不要用 `ld-pNNN.bin` 判读（历史分区内容），只认 `cur-pNNN.bin`。
4. 不要相信 `run-p104.ps1` 的 `back in the loader after 30 s`（假警报）。
5. 不要从 xnuloader 里重跑（热启动，链路必 down）。
6. 不要给 `wsl` 命令接 `| head` / `| tail`（PowerShell 会当本地命令，payload 直接不生成）。
7. 不要用 `Set-Content -Encoding UTF8` 写 `.sh`（BOM + CRLF，WSL 里 `#!/bin/bash` 会报"文件不存在"）。
8. 不要为了消除障碍去破坏性绕过：挂死就断电重来，不要试图"跳过"校验/复位。

---

## 11. 两周内的工作顺序（可以直接照抄）

```
第 1 天   克隆 HakiOS 2.1.13 → 装工具链 → make-kernel.sh 出基线内核 → 刷进 boot_b 确认还能起
第 2 天   按 0-C 重写 jpcie 骨架（只保留结论表里的寄存器值），先只跑到 M0（链路 + ECAM）
第 3 天   接上 BHI/BHIE + MHI 控制面，跑一轮拿到 STATE_CHANGE / EE_EVENT
第 4 天   P1 镜像真伪三连（截断 / 改字节 / amss20），三个结论写进 docs/02
第 5–7 天 P2 RDDM 恢复 + 抓 dump（每轮 5 分钟，一天 60 轮）
第 8 天   据 dump 结论决定：进 P4（解 QURT）还是转 P5（上层先做）
第 9–14 天 P5 QRTR/QMI/WLFW 骨架 + board-2.bin 生成脚本（不占设备）
```

---

## 12. 一句话

**主机侧已经没有可试的了。先用半小时验证"它跑的到底是不是我们的镜像"，再决定是继续挖固件还是先把上层写完。**
