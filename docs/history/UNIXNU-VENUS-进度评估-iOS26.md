# UniXNU on 小米 11（venus / SM8350）—— 到 iOS 26.5.2 主屏幕的差距评估

> 评估时间：2026-11-07
> 目标：Xiaomi Mi 11（venus, M2011K2C, SM8350），iOS 26.5.2（23F84）iPhone18,2 用户态
> 当前产物：`build-out/venus-arm64-boot.img`（43,921,408 B），内核 arm64 22,092,208 B

---

## 一、现在真实站在哪一步（已验证的事实，不含推测）

| 环节 | 状态 | 证据 |
|---|---|---|
| UEFI 固件（Mu-Silicium + venusPkg）启动 | ✅ | 菜单、USB PHY、充电、按键均正常 |
| payload 卷（FAT32 40 MiB）被发现 | ✅ | 菜单出现 `Mi 11 XNU platform bring-up (xnu)` |
| trustcache 裸 v2 module（3,692 条） | ✅ | `DbMark` 全过，`ValidTrustCaches` 不再返回 Compromised Data |
| owned 窗口 512 MiB | ✅ | `AllocateWindow` 成功，不再 Out of Resources |
| ADT 解析 | ✅ | `DbMark(4)` 通过 |
| 内核镜像读入 / ParseKernel / 拷贝到窗口 | ✅ | `DbMark(1..7)` 全亮 |
| `ExitBootServices` | ✅ | ExBS 后的 C 代码能跑、能 PSCI 复位 |
| 进入内核入口 `0xFFFFFFF007513488` | ✅ | 入口放复位 cave，手机确实重启 |
| `_start_first_cpu` 之后 | ⚠️ | 卡在 `_arm_vm_init` 极早期，第二条指令都未必到达 |
| 开启 MMU（`msr sctlr_el1`） | ❌ | 从未到达 |
| `pmap_bootstrap` / `_early_random` | ❌ | 从未到达 |
| IOKit 匹配、根设备、UFS 读写 | ❌ | 未开始 |
| launchd / 用户态 | ❌ | 未开始 |

**一句话结论**：内核"能加载、能跳进去、能在 EL1 跑几条指令"，但**离内核自己站起来还差整个 `arm_vm_init` 之后的初始化链**。

---

## 二、到"内核完整启动"还缺什么（M1）

这是最近的里程碑，也是当前唯一在啃的东西。

### 2.1 卡点本身
- 位置：`_arm_vm_init`（`0xFFFFFFF007509A68`）序言之后、`bl _phystokv` 之前。
- 现象：不触发异常（3 秒复位向量没响）、也没走到后续站点 → 更像是**某条指令把 CPU 挂住**（访问了 stage-2 未映射的物理页，abort 被 Gunyah 吞掉，或进入 WFI/WFE 死等）。
- 已排除：PAC（arm64 无 PAC 也崩）、CNTP_CTL_EL0 写入、帧缓冲（已改成完全不碰内存的探测）。

### 2.2 内核侧还要补的子系统（按启动顺序）
1. **异常向量与早期调试输出**：现在 VBAR 指向 DarwinBoot 的向量，内核自己的 fake vectors 还没生效；没有串口就只能拍照。
2. **GICv3**：Distributor `0x17A00000`、Redistributor `0x17A60000`（stride `0x20000`），中断分发、IPI。
3. **定时器**：`CNTVCT/CNTV_CTL` 可用（19.2 MHz），`CNTP_CTL` 被 Gunyah trap —— 已按 zeta 的做法绕过，但需要在 `machine_routines` 里彻底走通。
4. **PSCI**：`CPU_ON` 拉起 secondary core；`SYSTEM_RESET` 已可用。
5. **PMGR / RPMh / GDSC / regulator**：时钟与电源域。HakiOS 在 venus 上已经证明这块能通（否则屏幕都点不亮），但那是另一套代码，需要移植。
6. **平台专家 `PE_init_platform`**：ADT 解析、CPU 拓扑、`gVirtBase`、`machine_startup` 的板级回调。
7. **UART / 串口日志**：venus 的 GENI UART 在 Gunyah 下能否直接用未知；zeta 用 **USB CDC（`ZetaUsbSerialDxe`，VID:PID `0525:a4a7`）** 做日志，这是我们必须补的基础设施 —— 没有它，每一轮调试都要人肉拍照，效率差一个数量级。
8. **panic 输出**：`--panic-screen` 目前关着（cave 空间不够），需要单独规划一块 framebuffer 或串口。

**M1 时间估计：2 周（若卡点是个配置/单点问题）～ 2 个月（若牵出 Gunyah trap 或缺失的板级初始化）。**

---

## 三、到"能挂载 iOS 根卷"还缺什么（M2）

| 需求 | 现状 | 差距 |
|---|---|---|
| UFS 控制器 | ShengUfs 只读探针（`native-ufs-probe=3`，接管固件初始化过的控制器，不 reset 链路） | 需要完整的 DMA、SMMU 映射、中断、错误恢复；读分区够用，写要先解决 ICE |
| SMMU / IOMMU | 无 | UFS、USB、PCIe 全都要 |
| ICE（内联加密引擎） | 无 | iOS 数据卷是加密的，没有 ICE 只能读未加密分区 |
| APFS | 内核侧无 | zeta 同 SoC 已验证可行，可复用其补丁 |
| 分区表解析 | 无 | GPT + Apple 分区类型 |
| 根卷 seal / snapshot | 无 | iOS 26 根卷是 sealed snapshot，需要 `apfs` 支持 seal 校验 |

**M2 时间估计：1–2 个月（zeta 的成果可直接借，同 SoC 是关键优势）。**

---

## 四、到"launchd 跑起来"还缺什么（M3，zeta 卡在这一步）

| 需求 | 现状 | 差距 |
|---|---|---|
| trustcache 运行时加载 | 静态 bundle 已能进 payload | 运行时 AMFI 路径未做 |
| AMFI / 签名策略 | `libVenusOwner.a` 有公钥 anchor 与 `verified_root.c` | iOS 26 的 AMFI 更复杂，需要真实策略表 |
| dyld 共享缓存 | 无 | **arm64e 二进制 + 无 PAC 硬件 = 必须离线重写全部 PAC 指令**（zeta 已做：29.6M 个 PAC 字降低、每文件 4 KiB 页重签名） |
| libSystem / XPC / bootstrap | 无 | launchd 依赖的整条用户态链 |
| 页大小 | XNU 4 KiB | iOS 用户态假设 16 KiB，PTR_AUTH 相关指针布局会错位（zeta 的 launchd 就死在"4 KiB 内核未 slide 的指针"上） |
| SEP / keybag | 无 SEP 硬件 | iOS 26 大量依赖 SEP 做 keybag、生物识别、DRM；**这是架构级缺失** |

**M3 时间估计：3–6 个月，且成功率不确定**（zeta 用了一年多到 Stage 6 仍未过 launchd）。

---

## 五、到"SpringBoard 主屏幕"：这里有两个硬阻塞（M4）

### 5.1 GPU
- iOS 的图形栈是 **AGX（Apple GPU）+ Metal**。
- 小米 11 是 **Adreno 660**，没有、也不会有 Metal 驱动；写一个 Adreno 的 Metal 后端等于从零实现一个图形栈，工作量以**年**计，且没有可行性保证。
- 没有 GPU，SpringBoard 无法合成界面 —— 这一条就足以判定"进 iOS 主屏幕"在 venus 上**不可行**。

### 5.2 SEP
- iOS 26 的 keybag、数据保护、生物识别、部分 DRM 全在 SEP 里。
- 新硬件没有 SEP。可以仿（zeta/checkra1n 路线有 mock），但要做到 SpringBoard 级别完整，等于重实现安全隔区。

**M4 结论：不可行，不是"还要多久"的问题。**

---

## 六、时间总表（诚实版）

| 里程碑 | 乐观 | 现实 | 说明 |
|---|---|---|---|
| M0 越过 `_arm_vm_init` | 3 天 | 3 周 | 正在做 |
| M1 内核完整启动（IOKit 匹配完成） | 2 周 | 2 个月 | 含 GIC/PMGR/PE/UART |
| M2 读 UFS + 挂 APFS 根卷 | 1 个月 | 2 个月 | 复用 zeta |
| M3 launchd 在 EL0 跑起来 | 3 个月 | 6–12 个月 | zeta 仍未过 |
| M4 SpringBoard 主屏幕 | — | **不可行** | GPU/SEP 硬阻塞 |

**所以"进到 iOS 26.5.2 主屏幕"：在小米 11 上不是一个可达目标。**
现实里能做到的上限，参考 zeta（Surface Duo 2，同 SM8350）——**内核 + APFS + 改写后的 launchd 首进程**，那已经是社区最好水平，且花了约一年。

---

## 七、如果继续推进，最该先做的三件事

1. **补串口日志**（USB CDC，参照 zeta 的 `ZetaUsbSerialDxe`）。现在每轮调试 = 改代码 + 构建 + 人工烧写 + 拍照 + 猜，成本极高；有串口后内核 printk 直接可见，`_arm_vm_init` 这种卡点几分钟就能定位。
2. **解决 `_arm_vm_init` 卡点**：优先怀疑 stage-2 未映射（owned 窗口 512 MiB 与实际 DRAM 边界不匹配）、`boot_args+1144` 越界、以及 `gVirtBase` 相关全局写入。
3. **与 zeta 对齐**：把 `ios26` 分支的 `build-xnu-12377.sh`（未公开）与 Stage 5/6 补丁拿到，避免重复踩坑。

---

## 八、附：当前可交付物清单

| 文件 | 说明 |
|---|---|
| `build-out/venus-arm64-boot.img` | 43,921,408 B，可启动到内核 hand-off |
| `build-out/venus-ios26-kernel-arm64e.macho` | arm64e 版（23,407,816 B） |
| `out/venus/…iphone182arm64/venus/kernel/kernel.macho` | 当前 arm64 内核（22,092,208 B） |
| `phone-dump/venus-hw/live.dtb` | 真机设备树 803,915 B |
| `/root/unixnu-work/venus-trust-bundle.bin` | 裸 v2 trustcache，88,640 B，3,692 条 |
| `HAKIOS-VENUS-功能总结.md` | HakiOS 侧 9 项可用 / 9 项未完成 |
| `UNIXNU-VENUS-构建状态.md` | 构建流程与踩坑记录 |
