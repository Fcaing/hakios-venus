# HakiOS on Xiaomi 11（venus）功能总结

> 设备：小米 11（M2011K2C，代号 **venus**，SoC **SM8350 / Snapdragon 888**）
> 系统：HakiOS（XNU **xnu-8796.121.2**，Darwin **22.5.0**，iOS **16.5 / 20F66**）
> 文档更新：**2026-11-10 22:20**（本文件随每次实测更新；上一次更新为 11-06 22:00）
> 姊妹文档：`venus-recon/CONTINUE-2026-11-10.md`（**当前交接，最新**）、`HANDOVER-2026-11-10.md`（11-10 交接）、`venus-recon/section14.md`（M8 分析）、`venus-recon/STATE.md`（逐日状态）

---

## 1. 一页总览

| 能力 | 状态 | 备注 |
|---|---|---|
| 双系统并存（Android / iOS 16.5） | ✅ 可用 | 切槽即可，互不破坏 |
| 冷启动进 iOS（不依赖电脑） | ✅ 可用 | `boot_b` = `img-final3.bin` |
| 显示 / GPU 加速（GLES） | ✅ 可用 | Adreno 660，`gpu=1 gl=1` |
| 触摸 | ✅ 可用 | 单点与滑动；跟手延迟仍偏高 |
| 电源键 / 音量键 | ✅ 可用 | 音量键因无音频路由已放弃映射 |
| 电池百分比 / 充电状态 | ✅ 可用 | ADSP battmgr（`adsp=1 pmic=1`） |
| 主屏图标（完整两页） | ✅ 可用 | 原"只剩 3 个图标"已修 |
| 设置 › 应用列表图标/名字 | ✅ 可用 | 原"黑色方块"已修（预热图标缓存） |
| 第三方 `.app` 注册与启动 | ✅ 可用 | 放进系统镜像 `/Applications` 即被 LS 注册 |
| 数据卷跨启动持久化 | ✅ 可用 | HFS+，`/dev/ufs_darwin_data` |
| 设置 › Wi-Fi 页面能打开 | ✅ 可用 | 页面本身正常 |
| **Wi-Fi 开关能开 / 能扫描 / 能上网** | ❌ **不可用** | 内核侧已到"固件跑起来、MHI 数据面在 LOOPBACK 上双向打通"；卡在 AMSS 的 IPCR 客户端不注册 |
| 蜂窝 / 蓝牙 / 相机 / 音频输出 | ❌ 不可用 | 未移植 |
| 端到端"装第三方应用"（点一下装好） | ❌ 不可用 | 只有"镜像内置"与"离线侧载"两条路 |

**一句话**：这台手机现在是一台"能开机、能触摸、能显示、能装应用"的 iOS 16.5 设备，**还没有网络**。Wi-Fi 已从 11-06 的"芯片还没上电"推进到 **M8**：PCIe 链路训练、SMMU/BAR、BHI/BHIE 固件下载、MHI 初始化、事件环、命令环、SOC reset/RDDM 全部打通，**MHI 数据面已在 LOOPBACK（ch0→ch1）上端到端双向跑通**；唯一卡点是真实业务通道 **IPCR（ch20/ch21）在固件侧没有客户端**——引擎取 TRE、搬数据都正常，但 AMSS 的 IPCR 服务还没注册起来。

---

## 2. 设备与系统底座

### 2.1 分区与双系统

| 分区 | 内容 |
|---|---|
| `boot_a` | Android（HyperOS + ReSukiSU root） |
| `boot_b` | **HakiOS**（当前 `img-final3.bin`，15,949 块 × 4096 = 65,327,104 B） |
| `darwin` | 21,476,913,152 B（约 20 GiB），内含：root APFS（块 0–1374207）、cryptexes（1374208–2042367）、**数据卷**（从块 **2042368** 起，长 **3,200,549 块 = 13,109,448,704 B**） |
| `logdump` | `/dev/block/sda24`，loader 的日志分区（2 MB） |
| `dbg` | `/dev/block/sda3`，32,768 B（原准备做报告分区，因 loader 只放行数据卷而弃用） |

切槽：`fastboot --set-active=b` 进 iOS，`--set-active=a` 回 Android（在 Android 的 fastboot 里有效；在 HakiOS 的 loader 里不支持）。

### 2.2 启动链

```
ABL → boot_b 里的 U-Boot（img-wr2.bin，我们改过的）→ 加载 payload
   ├── 内核：hakios-kernel（XNU 15.2 MB 级）
   ├── ramdisk：root.apfs（我们的用户态根，6,500 块量级）
   └── 可选 resident：flashboot.apfs（4–21 MB）
→ 内核 init（/redwood/sbin/init）→ 挂数据卷 → 建 /private/var 骨架 → 起 Darwin launchd
```

- **RAM 路线（测试用，不动 flash）**：`fastboot boot img-wr2.bin` → `oem ramdisk` → stage 2.4 GB 系统镜像 → stage payload → `oem run` → 跑完自动回 Android。
- **flash 路线（日常用）**：系统镜像写在 `darwin` 块 0 起（`dd count=607327`），`boot_b` 放 payload。

### 2.3 版本与构建

- 本地树：`/root/hakios`（WSL Ubuntu），HakiOS 版本 **2.1.13**，`DARWIN=22.5.0`，`XNU=xnu-8796.121.2`。
- 上游参考：`/root/hakios-up`（HakiOS **2.3.4**，浅克隆，仅用于挑补丁）。
- 内核构建：`bash tools/make-kernel.sh -j20`（增量约 4 秒；退出码 2 只代表 kext symbol-set 检查失败，属正常）。
- 系统镜像：`SYSTEM=1 bash build.sh` → `system.apfs`（607,327 块 = 2,487,611,392 B）。
- payload：`mkpayload.py` + 可选 `mkubootimg.py -d venus`（XNU 引导镜像 65,314,816 B）。

---

## 3. 已实现且实测可用的功能

### 3.1 显示与 GPU

- Adreno 660 走 `drivers/gpu/hakios.adreno.c`，GLES 可用（`gpu=1 gl=1`），Metal 未启用。
- 分辨率 `fbwidth=1440 fbheight=3200`，设备树声明 **sRGB**（曾因报 P3 导致 WebKit 要 10-bit 表面、页面全黑，已修）。
- 屏幕下半的 U-Boot 控制台文字是 loader 打的，属正常现象。

### 3.2 触摸

- 驱动：`drivers/input/hakios.goodix.c`（含 ST FTS 分支），`touchscreen=1`。
- 已移植 HakiOS 2.3.4 的"16 ms idle 轮询 + 手指在位判定"，但**手感提升不明显**（用户实测"跟之前差不多"），怀疑瓶颈在 `rwtouch`/驱动之外的上报路径，暂缓。
- 触摸设备是 `/dev/hakios-touch`，用户态 `rwtouch` 支持 `tap/swipe/drag/hold/zigzag/button home|lock|volup|voldown/read/notify/wait`，坐标用 0–1 比例。

### 3.3 电源与电池

- 电源键、音量键可用（`buttons=1`）。
- 电池：ADSP 电池管理器（`adsp=1 pmic=1`，**不能加 `battery=1`**），能报容量/电压/电流/温度/循环次数，状态栏显示百分比。
- 充电状态正常（USB online 1）。

### 3.4 桌面与图标

- 主屏两页默认布局齐全（17 + 18 项 + Dock 4 项）。
- **原"只有 3 个图标"**：根因是 32 个系统应用在 `private/var/staged_system_apps` 里只被建了 APFS synthetic dir，LaunchServices 不认；修法是构建时把它们 `mv` 进 `sysroot/Applications`（`build.sh:610-618`），并保留空 `/private/var` 当挂载点。
- **设置 › 应用列表"黑色方块"**：根因是图标缓存未热（`lsdidentifiers.plist` 停在 157 项、`IconsCache` 只有 86 个 `.isdata`）；把列表完整滚一遍后缓存写入 89 个，跨启动保留，问题消失。

### 3.5 应用与 LaunchServices

- `/Applications` 共 **174 项**（173 个 `.app` + 1 个 plist），LaunchServices 每次启动扫描该目录重建数据库。
- **第三方 `.app` 放进系统镜像 `/Applications` → LS 注册为 installed → 出现在主屏 → 点开可运行**（已用 `hello.app` 实测：品红图标出现在第 2 页；点按启动的验证日志 `Successfully spawned Tips[55] because launch job demand`）。
- 内核**没有签名策略**（`miniamfi.c`：没有 trust cache、没有签名校验），所以未签名的 app 也能跑，但**拿不到 entitlement**。

### 3.6 设置

- 设置应用完全可用（根页、通用、语言与地区、应用列表、电池等）。
- Wi-Fi 行可点开（页面渲染正常），但**开关无效**——见第 4 节。

### 3.7 数据卷

- HFS+ 卷，位于 `darwin` 块 2042368 起，跨启动保留；init 会建 111 个目录 + 16 个文件。
- 系统自己会往里写：`IconState.plist`（2,764 → 3,728 B）、`IconsCache/*.isdata`、`applicationState.db`、设置快照（JPEG）等——这证明**写入路径是通的**。
- Android 侧内核**没有 HFS+**，只能 `dd` 12 GB 再 `adb pull`（约 5 分钟）。

### 3.8 观察与调试（这是最近两天最重要的"功能"）

| 通道 | 用法 |
|---|---|
| loader 日志分区 | Android 上 `dd if=/dev/block/sda24 of=/data/local/tmp/ld.bin bs=4096 count=512` + `adb pull`；loader 内 `oem dump logdump 0 <hex长度>` |
| 只取最新一轮 | `python3 scripts/last-run.py ld-*.bin` |
| 驱动器内报告 | `sysctl kern.hakios.pcie`（init 打印 `hakios: the PCIe driver says: …`） |
| 命令库 | boot arg `cmddb=2` 转储 4 slave / 161 条资源 |
| 分步探针 | `pcie_step`、`pcie_only`、`pcie_go`、`pcie_pause`、`pcie_settle`、`pcie_delay`、`pcie_tag` |
| 截图 | `oem screenshot` + `get_staged`（18,432,000 B = 1440×3200×4） |

---

## 4. Wi-Fi 专项

### 4.1 硬件事实（设备树 + Android 运行态核实）

| 项 | 值 |
|---|---|
| 芯片 | **QCA6490**（WCN6855 家族） |
| PCIe 地址 | 根端口 `17cb:010c`（`00:00.0`）→ 端点 **`17cb:1103`**（`01:00.0`） |
| 硬件版本 | `TCSR_SOC_HW_VERSION = 0x400c0110` → **major 1 / minor 0x10**（"QCA6490 1.1"） |
| 挂法 | **PCIe0**（`pcie@1c00000`），不是 AHB/SNOC |
| 固件 | `amss.bin` 5,236,304 B（md5 `341ec80bb5caa88867bbb5718322a652`）、`amss20.bin` 5,197,824 B（md5 `5bfd3402260cf1ac089c89113b9b05d4`）、`m3.bin` 266,684 B、`regdb.bin` 24,278 B、`bdwlan.e01…e27` **147 个** |
| 固件出处（11-10 核实） | 与原厂 `/vendor/firmware_mnt/image/` 下的四个文件 **md5 全部一致** ⇒ 我们用的就是出厂固件，无"更好版本"可换 |
| 缺的固件 | `board-2.bin`（需用 `bdwlan.*` + 芯片上报的 board id 在运行时生成） |
| 供电 | 根端口：`ldob6` 1.2 V、`ldob5` 0.88 V；无线电六路：`smpb10` 1.8 V、`ldoe7` 2.7 V、`smpe2` 0.95 V、`smpb11` 0.95 V、`smpc1` 1.9 V、`smpb12` 1.35 V（**全部 RPMh**） |
| 引脚 | PERST# = TLMM **94**、WLAN_EN = TLMM **64**、CLKREQ = 95、BT_EN = 65 |

### 4.2 已打通（每一项有日志证据）

#### 4.2.1 上电与链路（11-06 → 11-07，M0）

| 阶段 | 结果 | 证据行 |
|---|---|---|
| 读 GCC 常开寄存器 | ✅ 安全 | `0x52000=0x00e0057f`、`GDSCR=0x0022f001`、`clkref=0x80000000` |
| 电源域上电 | ✅ | `GDSCR 0x0022f001 -> 0xf822f000`、`came up after 1 polls of 100 us` |
| 时钟投票 | ✅ | `votes 0x52000=0x00ec0d7f, 0x52008=0x023c203f` |
| 参考时钟 / RCG / pipe mux | ✅ | `clkref=1`、`aux 0x00000220`、`pipe mux 0 (the phy)` |
| PARF 配置 | ✅ | `DEVICE_TYPE=4`、`SYS_CTRL=0x365e`、`DBI=0`、`SLV=0x4000000`、`AXI halted` |
| PHY 75 条序列 + PLL | ✅ | `the PCS status bit cleared at 3 x 200 us: 0x00000086` |
| DBI 识别 | ✅ | `DBI ID 0x010c17cb` |
| RPMh 投票（RSC TCS） | ✅ | `ldob6 done 1 idle 1`、`ldob5 done 1 idle 1`、`smpb10 done 1 idle 1` |
| 六路无线电 rail | ✅ | `smpb10 1800 / ldoe7 2800 / smpe2 1012 / smpb11 1012 / smpc1 1900 / smpb12 1350` 全部 `done 1 idle 1` |
| PERST# / WLAN_EN / CLKREQ | ✅ | `PERST# high: IO 0x00000003`、`WLAN_EN (pin 64) driven high`、`CLKREQ# alt1 pull-up CFG 0x3 -> 0x7` |
| **链路训练成功（M0）** | ✅ | `link UP: ELBI 0x08 = 0x00011401`、`LTSSM 0x00000111`（state 17）、Gen2 |
| ECAM 枚举 | ✅ | 根端口 `17cb:010c` → 端点 **`17cb:1103`**，`TCSR_SOC_HW_VERSION 0x400c0110` |

#### 4.2.2 MHI 控制面与数据面（11-07 → 11-10，M1–M8）

| 阶段 | 结果 | 证据行 / 数值 |
|---|---|---|
| SMMU 配置（BDF→SID `0x1c01`） | ✅ | `scr/idr0/idr1` 读通，`gfsr 0`（无 fault） |
| BAR0 映射 + MHI 能力 | ✅ | `MHICFG 0x00030880`（NCH 0x80、NHWCH 0x08、NER 0x02、NHWER 0x03）、`CHDBOFF 0x300`、`ERDBOFF 0x700` |
| **BHI/BHIE 固件下载（M2）** | ✅ | 10 个 512 KiB 向量覆盖整个 5,236,304 B 的 `amss.bin`；`TXVECSTATUS` 完成，设备进入 **EE=2（AMSS）** |
| MHI 初始化（M3） | ✅ | 上下文数组：`CCABAP 0xa0200000`、`ECABAP 0xa0202000`、`CRCBAP 0xa0202400`；命令环 `0xa0207000`、事件环 `0xa0204000`/`0xa0205000`、通道环 `ch*0x1000+0xc000` |
| **M0 握手（M4）** | ✅ | `MHISTATUS 0x00000201`（READY+M0）；`MHICTRL 0x00000200` |
| 事件环 device→host | ✅ | er0 收到 `STATE_CHANGE(state 2)`、`EE_EVENT(ee 2)`、4 条 `CMD_COMPLETION(code 1 = SUCCESS)` |
| BW 请求 / bw-scale | ✅ | er2 收到 `BW_REQ_EVENT`（type 0x25），应答后 `bwdb 0` |
| 命令环 host→device | ✅ | 4 条 START_CHAN 全部被取、被校验、回 SUCCESS；把 cmd wp 往回拨会让设备 `0x0000ff05`（SYS_ERR）⇒ 命令面是活的且严格 |
| SOC reset / RDDM | ✅ | 写 `0xb0=1` → `t=7~20 ms` 进 **EE=3（RDDM）**；EE=3 时再写一次可**钉住**不走 |
| **数据面（M8，LOOPBACK）** | ✅ **双向跑通** | ch0 发 16 B `4b494f53…`，ch1 的 RX buffer 里原样收到；er1 上收到 `TX_EVENT(type 0x22, ch0)` + `ch1 完成事件(dword3 低字节=1)` |
| 数据面（IPCR ch20/ch21） | ❌ 无客户端 | 判据有正对照：同一套代码给 ch20 投"载荷指针在 MHI 窗外"的 TRE，ch0 立刻 `st 0x5`(ERROR)，ch20 纹丝不动 |

**M8 已被排除的原因**（全部有实验）：通道上下文地址/内容（`+ch*0x2c`，CCABAP 与设备读到的一致）、门铃地址（`0x300+ch*8`，与 vendor `mhi_init.c:1003` 完全一致）、门铃写序（高 32 位先）、唤醒门铃 `0x6f8`、TRE 合法性与类型、载荷可映射性、环长度 32 vs 64、事件环 er1、电源/时钟/GPIO、MSI 向量数、SOC 复位与 RDDM。

### 4.3 还没打通

| 项 | 现状 | 缺什么 |
|---|---|---|
| **IPCR（ch20/ch21）** | 上下文由固件写成 RUNNING，但 nobody fetches | AMSS 的 IPCR 客户端没注册。**我们这边已无可怀疑**（见 4.2 末） |
| RDDM dump（固件自己的 panic 记录） | `0xb0` 能进 RDDM 并钉住，BHIE RX 按 vendor 武装后 `delivered 0x0` | BHI/BHIE 只在下载期有效，拿不到固件 crash 文本 |
| QRTR over MHI | 未开始 | IPCR 起来后用 ch20/ch21 收发 QRTR 报文（`sq_family = AF_QIPCRTR`） |
| QMI / WLFW | 未开始 | `wlan_firmware_service_v01.{c,h}` 已在树里；要 host 端 QMI 客户端 |
| board-2.bin / regdb | `regdb.bin` 有，`bdwlan.e01…e27` 147 个 | 用芯片上报的 board id 在运行时拼 `board-2.bin` |
| ath11k（真驱动） | 未接 | hw2.1 十行补丁 + 固件布局；本地已能编出 `ath11k.o`（`tools/mk-ath11k.sh`） |
| Apple80211 / wifid | **骨架已写好** | `bsd/dev/hakios.apple80211.c`（29 KB，ioctl `0x802869c8/0xc02869c9`）+ `iokit/Kernel/hakios.wlan.cpp`（发 `IO80211Controller`/`IO80211InterfaceRole`）+ `bsd/sys/hakios.sta.h`（`hakios_sta_ops`）；缺的是把真实 802.11 挂到 `hakios_sta_ops` 上 |
| configd / DHCP / DNS | 未开始 | 现成组件，缺接口与网络栈对接 |
| 设置里的 Wi-Fi 开关 | 按下无反应 | `wifid` 报 `PPM Error:No matching driver found`——没有驱动认领接口 |

### 4.4 关键寄存器速查

| 名称 | 地址 |
|---|---|
| PARF | `0x1c00000`（+0x3000） |
| PHY（QMP v5） | `0x1c06000`（+0x2000） |
| DBI | `0x60000000` |
| ELBI（状态 +0x08，bit10 = LINK_UP） | `0x60000f20` |
| ECAM（1 MB） | `0x60100000` |
| TLMM | `0xf100000`（`GPIO_CFG(n)=+0x1000*n`，`GPIO_IO=+4`，bit1 = 输出电平） |
| 命令库 | `0x80860000`（+0x20000） |
| RSC/TCS | `0x18220000`（+0x10000），`tcs-offset 0xd00`，`drv-id 2` |
| GCC 投票 | `0x52000` / `0x52008`（mask `0x004c0c00` / `0x3f`） |
| GDSCR | `0x6b004` |
| clkref | `0x8c004` bit0 |
| PARF LTSSM | `0x1b0`（**置位** bit8 启动训练） |
| PHY PCS 状态 | `0x214` bit6（**清零** = 锁相成功） |
| PHY power-down / start | `0x240`（先写 3）/ `0x244`（bits 0|1） |
| TZ 保护 | `0x152128`——**读就 panic，禁止访问** |

**MHI（BAR0 内偏移，venus 实测值）**

| 名称 | 偏移 / 值 | 说明 |
|---|---|---|
| `MHIREG`(0x00) / `MHIVER`(0x08) | `0x00000100` / `0xdeadbeef` | 版本读出来是垃圾，别用 |
| `MHICFG`(0x10) | `0x00030880` | NCH 0x80、NHWCH 0x08、NER 0x02、NHWER 0x03 |
| `CHDBOFF`(0x18) / `ERDBOFF`(0x20) | `0x300` / `0x700` | 通道门铃 `0x300+ch*8`（ch20 → **0x3a0**）；事件门铃 `0x700+er*8` |
| `BHIOFF`(0x28) / `BHIEOFF`(0x2c) | `0x100` / `0x224` | |
| `MHICTRL`(0x38) / `MHISTATUS`(0x48) | `M0=0x200` / `0x201` | 低 8 位 = 状态，bit0 READY、bit2 SYSERR |
| `MHICTRLBASE/LIMIT` | `0xa0000000`..`0xb0000000` | MHI 窗口 |
| EE 寄存器 | `0x128` | 0 PBL / 1 SBL / **2 AMSS** / 3 RDDM |
| **`MHI_SOC_RESET_REQ`** | **`0xb0`，写 1** | EE=3 时**再写一次可钉住 RDDM** |
| BHI 块（`0x224` 起） | `IMGSIZE 0x10`、`IMGTXDB 0x18`、`INTVEC 0x20`、`EXECENV 0x28`、`STATUS 0x2c`、`ERRCODE 0x30` | AMSS 起来后除 `MSMSOCID` 外全是总线噪声 |
| BHIE TX/RX | `TXVECADDR 0x2c/0x30`、`TXVECSIZE 0x34`、`TXVECDB 0x3c`、`TXVECSTATUS 0x44`；`RXVECADDR 0x60/0x64`、`RXVECSIZE 0x68`、`RXVECDB 0x70`、`RXVECSTATUS 0x78` | 向量 16 B/条，512 KiB 一块 |
| 通道上下文 | `pcie_dma_extra + ch*0x2c` | `0x00` chstate/brst/poll、`0x04` chtype、`0x08` erindex、`0x0c` rbase、`0x14` rlen、`0x1c` rp、`0x24` wp |
| 事件上下文 | `pcie_dma_extra + 0x2000 + er*0x2c` | |
| 命令上下文 | `pcie_dma_extra + 0x2400` | |
| 环 | 事件 `+0x4000`、命令 `+0x7000`、通道 `ch*0x1000+0xc000` | 每条 TRE 16 B |
| TRE 字段 | `dword2` 高 16 = code/长度；`dword3` bit16-23 = 类型、**低 8 位 = 通道号** | 类型：`0x12` START_CHAN、`0x20` STATE_CHANGE、`0x21` CMD_COMPLETION、`0x22` TX_EVENT、`0x40` EE_EVENT、`0x50` BW_REQ |
| 门铃写法 | 先写 `db+4`（高 32 位）再写 `db`（低 32 位），值是 ring 的 wp IOVA | 与 vendor `mhi_write_db()` 一致 |

### 4.5 参考源码

| 树 | 价值 |
|---|---|
| **star（小米 11 Ultra）** `ref-star/` | 同 SoC + 同芯片；`lemonade_wifi.c` 89 KB 覆盖 stage 2–22（含 MHI/IPCR/QMI），已实测到"WLFW 能力查询成功" |
| **SteamOS-ARM SM8350**（REDMAGIC 6）`ref-steamos/` | 同 SoC + 同芯片跑 mainline + ath11k；`0008` 补丁把 major 1 / minor 0x10 映射到 `ATH11K_HW_WCN6855_HW21`（十行，直接解决 hw1.0 问题）；`0009` 提供 `mac_addr` 参数；`0014` 是 PCIe GDSC retention |
| **Xiaomi venus 内核源码** | 厂商 `pci-msm.c`/`cnss2/`（PARF、link-train、BDF→SID、噪声/供电顺序、`wlan_firmware_service_v01` QMI 定义） |
| Linux 7.0.14 ath11k | `ath11k/pci.c`、`hw.h`、`core.c`；MHI 在 `drivers/bus/mhi/host/`（约 7,900 行） |

### 4.6 时间表（按当前进度）

| 里程碑 | 内容 | 状态 / 预计 |
|---|---|---|
| M0 | 链路训练成功，ECAM 读到 `17cb:1103` | ✅ **11-07 完成** |
| M1 | SMMU + BAR + MHI 能力寄存器 | ✅ 11-08 |
| M2 | BHI/BHIE 全镜像下载，设备进 EE=2 | ✅ 11-08 |
| M3 | MHI 初始化（上下文数组、环、门铃） | ✅ 11-08 |
| M4 | M0 握手 + 事件环 device→host | ✅ 11-08 |
| M5 | 命令环 host→device（START_CHAN 回 SUCCESS） | ✅ 11-09 |
| M6 | BW_REQ / bw-scale / 特殊通道 | ✅ 11-09 |
| M7 | M0/M2/RESET 控制面 + `0xb0` SOC reset / RDDM | ✅ 11-10 |
| **M8** | **数据面：TRE 取用 + 载荷 DMA + 完成事件** | ✅ **11-10 在 LOOPBACK（ch0→ch1）双向跑通** |
| M9 | **IPCR（ch20/ch21）起来** —— 固件客户端注册 | ⏳ **当前卡点**，1–3 天（若属镜像/预装）～1–2 周（若属时序） |
| M10 | QRTR over MHI | 3–7 天 |
| M11 | QMI / WLFW + board data | 1–2 周 |
| M12 | ath11k CE/HTC/WMI 起来，能扫描 | 2–3 周 |
| M13 | 关联 / 四次握手 / DHCP | 2–3 周 |
| M14 | Apple80211/wifid：开关、列表、状态栏图标 | +1–2 周（骨架已有） |

**总体估计**：乐观 2–3 周、**现实 6–9 周**、悲观 3 个月以上（比 11-06 版的 3–6 周更保守，因为风险已从"移植工作量"挪到"固件应用层起没起来"）。

**每轮实验成本**：冷启动 42 s + 打包 65 s + 跑 115 s + 取日志 15 s ≈ **5 分钟**；一天能跑 60–80 轮。`0xb0` 双写钉住 RDDM 之后，可以把"同一固件内重放 BHI→BHIE→AMSS"压到 ~10 秒/轮，是后面最大的提速杠杆。

### 4.7 M8 卡点：IPCR 为什么不动（证据汇总）

- **固件是真的**：与原厂 `/vendor/firmware_mnt/image/amss.bin` **md5 完全一致**（`341ec80bb5caa88867bbb5718322a652`），`amss20.bin`/`m3.bin`/`regdb.bin` 也全部一致 ⇒ 不是固件版本问题。
- **固件里有 IPCR**：字符串里有 `IPCR_CORE_DEBUG`、`IPCR_MHI_RX_DEBUG`、`IPCR_MHI_TX_DEBUG`、`ipcr_debug_hello_sent_ts_cntr`、`wls_wlansvc_WLAN`。
- **Wi-Fi 真正要的就是这两个通道**：ath11k qca6390 的通道表只有 ch20/ch21，名字都叫 **"IPCR"**，`ee_mask 0x4`（AMSS）、`num_elements 64`、`event_ring 1`；`qmi.c` 的 `sq_family = AF_QIPCRTR` ⇒ QMI 走 QRTR，而 QRTR 的 MHI 传输就是这一对通道。
- **引擎是活的，客户端不在**：ch0（LOOPBACK）同一套代码能取 TRE、能 DMA、能回 TX_EVENT，IPCR 通道则连"取一条 TRE"都没有（用 MHI 窗外的载荷指针做正对照，ch0 立刻 ERROR、ch20 纹丝不动）。
- **我们这边已排除的**：上下文地址与内容、门铃地址与写序、唤醒门铃、TRE 格式、载荷映射、环长度、事件环、电源/时钟/GPIO、MSI 向量数、SOC reset 时序。
- **结论**：AMSS 应用层（IPCR 服务）没注册。下一步只能从"固件内部为什么没起来"和"真实驱动还多做了一步什么"两个方向逼近。

---

## 5. 第三方应用安装专项

| 路径 | 状态 | 说明 |
|---|---|---|
| 把 `.app` 放进系统镜像 `/Applications` | ✅ 已验证 | 重新构建 + 刷镜像；LS 注册、图标出现、点开可运行 |
| 离线侧载到数据卷再 union 到 `/Applications` | ❌ 已废弃 | `mount(bindfs, MNT_UNION)` 在本内核把 `/Applications` 盖成空目录（图标全消失），已回退 |
| TrollStore / Sileo / 巨魔 | ⏸ 不可行 | 都需要网络（venus 现在无网）；TrollStore 还需要 entitlement |
| 爱思助手 / `.ipa` 直装 | ⏸ 未实现 | 需要 installd/MobileInstallation 接口 + 签名/entitlement 方案 |
| 抖音 IPA（已放在桌面） | ⏳ 待装 | 可用"放进镜像"的方式安装（`mk-install.sh` 入口已写好） |

**结论**：现在唯一可靠的是"镜像内置"。要做到"点一下装"，至少要 Wi-Fi 或一条侧载通道。

---

## 6. 平台级已知缺陷（与 Wi-Fi 无关但会拖慢一切）

| 问题 | 表现 | 影响 |
|---|---|---|
| guest 时钟快 2.4–8 倍 | `rwtouch wait` 不可靠，脚本要按事件顺序判断 | 自动化测试难写 |
| `mobileactivationd` 每 10 s 崩溃 | `SIGTRAP | sent by exc handler` | 刷日志，不影响使用 |
| 每次挂死要手动断电 | 长按电源 15 秒 → 音量下+电源 进 fastboot | 最大的时间成本 |
| loader 日志窗口只有 24 秒 | 之后的日志写不进 `logdump` | 只能用 sysctl/落盘通道 |
| Android 内核无 HFS+ | 数据卷只能 dd 12 GB | 每次取证 5 分钟 |
| 设置 › 声音与触感卡死 | 音频路由未完成 | 已放弃音量键 |
| 触摸延迟偏高 | 2.3.4 的 16 ms 修复无效 | 待查 |

---

## 7. 工程结构与脚本地图

```
/root/hakios/                     WSL Ubuntu 里的源码树
├── drivers/
│   ├── pcie/hakios.pcie.c        ~5,150 行 / 200 KB 级：PCIe RC 实验驱动（step 1–5、RSC 投票、PHY、PERST、链路、SMMU、BHI/BHIE、MHI、IPCR 探针），内含 apply-001…apply-398 的逐条补丁与日志标记
│   ├── pcie/venus.pcie.h         从设备树生成的基址/引脚/75 条 PHY 序列
│   ├── storage/hakios.ufs.c      报告分区写路径（ufs_report_part）
│   ├── power/hakios.pmic.c       SPMI 写 + pmic_poke + LDO dump
│   ├── input/hakios.input.c      启动钩子顺序（pcie 在 wifi 之后、adsp 之前）
│   ├── wifi/                     wifi.conf、hakios.wifi.c、hakios.apple80211.c 等（待用）
│   └── map                       新驱动必须在这里登记
├── devices/venus/                设备配置（configs/venus.config：CONFIG_HAKIOS_PCIE=y）
├── userland/                     mini 用户态（init、stage0、root.apfs）
├── xnu-src/xnu-8796.121.2/       XNU 本体
├── tools/                        make-kernel.sh、hakios-config.py、apfs 工具、mk-ath11k.sh
└── xnuloader/loader.c            loader（日志、stage、oem 命令）

C:\...\venus-recon\               工作区（脚本、日志、文档、参考源码）
├── STATE.md / HANDOVER-*.md / PROGRESS-2026-11-06.md / REVIEW-*.md / NEXT-SESSION.md
├── PCIe-试验记录-人工.md         每次实验的手写记录与教训
├── VENDOR-PCIE-NOTES.md          厂商源码摘录（带行号）
├── WIFI-hakios-venus-2026-11-06.zip   全部成果打包（源码/补丁/脚本/文档/证据/参考/固件）
├── ref-star/                     小米 11 Ultra Wi-Fi 源码包
├── ref-steamos/                  SteamOS-ARM SM8350 补丁与脚本
├── fw-wifi/                      amss/amss20/m3/regdb + 147 个 bdwlan
├── **当前实验工作流**（一轮 = 5 分钟，见 `CONTINUE-2026-11-10.md` 的"固定流程"）：
│     applyNNN.py        用 python 改 hakios.pcie.c（每处 replace 都 assert count==1，
│                        并在 `pcie_mhi_data` 的两处 gate 上追加自己的编号）
│     buildNNN.sh        applyNNN.py → tools/make-kernel.sh，打印 errors= / apply_tags=
│                         （退出码 2 是已知的 kext symbol-set 检查失败，看 errors: 是否为 0）
│     mkNNN.sh           RET=200 bash mk-pcie2.sh pNNN '<EXTRA>'，打包当前 hakios-kernel
│     run-p104.ps1       -Payload p-pNNN.bin -Tag pNNN -RunSeconds 115（注意它的
│                        "back in the loader after 30 s" 与 ld-pNNN.bin 都是假数据）
│     extract-log.ps1    fastboot oem dump logdump → get_staged cur-pNNN.bin → 抽 ASCII 行
│     fwswap.sh          换 userland/root/fw/amss.bin 并重打 root.apfs
├── scripts: mk-pcie2.sh、prebuild.sh/prebuild2.sh、dtbchan.sh、q-*.sh（厂商源码速查）…
└── patches: fix*.py（95 个）+ apply*.py（apply-001…apply-398，按序号记录每一次改动）
```

---

## 8. 关键参数速查

### 8.1 日常启动 cmdline（`boot_b`）

```
root_apfs=ufs_darwin ufs=2 ufs_native=1 ufs_write=1 var_hfs=ufs_darwin_data
adsp=1 pmic=1 bootcpu=7 cpus=8 cpufreq=1 touchscreen=1 buttons=1 gpu=1 gl=1
sb_delay=45 fbwidth=1440 fbheight=3200 debug=0x8
```

（`battery=1` **绝对不能加**，否则电池管理器不走 DSP、没有百分比。）

### 8.2 测试 payload（RAM 根）

```
ufs=2 ufs_native=1 ufs_write=1 var_hfs=ufs_darwin_data adsp=1 pmic=1 bootcpu=7 cpus=8
cpufreq=1 touchscreen=1 buttons=1 sb_delay=45 loader_return_after=<秒>
[pcie=1 pcie_step=N pcie_power=1 pcie_tag=NAME …]
```

### 8.3 常用命令

```sh
# 内核
bash tools/make-kernel.sh -j20

# payload（当前 M8 全套参数；pcie_mhi_data 决定跑哪一段探针）
RET=200 bash mk-pcie2.sh pNNN 'pcie=1 pcie_step=5 pcie_power=1 pcie_delay=0 pcie_settle=100 \
  pcie_bar=21 pcie_watch=0 pcie_star_mask=31 pcie_bhi_addr=0xa0004000 pcie_bhi_size=0x80000 \
  pcie_novec=1 pcie_msi_test=1 pcie_mhi_nom0=1 pcie_chanstart=1 pcie_mhi_late0=1 \
  pcie_mhi_data=NN pcie_bw_db=1 pcie_bw_rp=1 pcie_gen=2'

# 冷启动（fastboot 不在 PATH，必须写全路径）
C:\...\default-workspace\tools\platform-tools\fastboot.exe reboot bootloader

# 上机
.\run-p104.ps1 -Payload p-pNNN.bin -Tag pNNN -RunSeconds 115

# 取日志
fastboot oem dump logdump 0 40000        # 立刻返回 OKAY
Start-Sleep 5
fastboot get_staged <绝对路径>\cur-pNNN.bin
.\extract-log.ps1 -File <绝对路径>\cur-pNNN.bin -Out <绝对路径>\pNNN.txt
```

### 8.4 踩过的坑（每一条都真的浪费过一整轮）

| 坑 | 症状 | 规矩 |
|---|---|---|
| **cmdline 只有 514 字符** | 新加的 boot-arg 静默失效，整轮结论无效 | loader 自己的前缀占 93 字符（`debug=0x8 rd=md0 ufs_shared_pa=… hakios_kver=…`），payload cmdline 只装得下 **514**；超了从尾部截断。日志里必须**没有** `WARNING: the kernel command line is TRUNCATED` 才算有效轮次 |
| **`pcie_tag` 会重复** | 浪费 14 字符 | `mk-pcie2.sh` 自己会追加 `pcie_tag=$TAG`，别再写进 `$EXTRA` |
| **热启动** | 链路 down（LTSSM 3/5）或状态脏 | **每一轮都要冷启动** |
| **日志串轮** | 读到上一轮的 `apply-*` 行 | 先按 `pcie_tag=pNNN` 切片，再取以"probe is done"结尾的最新时间戳组 |
| **64 位指针存进 `uint32_t`** | 探针打在第一条读之后就"静默结束"，看起来像设备没反应 | 偏移量用 `uint32_t`，用时现加（`rd(pcie_dma_extra + off)`） |
| **TRE 的 CPU 地址算错** | 把 ch20 的 TRE 写进了 ch21 的上下文 | 必须 `pcie_dma_extra + (iova - PCIE_EXTRA_IOVA)` |
| **通道上下文偏移** | 读到一片零，误判"设备不写上下文" | 通道在 `ch*0x2c`（ch20 → `0x370`），**没有** `+0x2000`；事件才是 `+0x2000+er*0x2c` |
| **`0xa0100000` 不算界外** | 以为"界外指针"验证了不取环 | MHI 窗是 `0xa0000000..0xb0000000`，界外要用 `0x80000000` |
| **`.ps1` 被执行策略拦住** | 脚本静默不跑 | 每个新 pwsh 会话先 `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force` |
| **`Set-Content -Encoding UTF8`** | WSL 里 `#!/bin/bash` 报"文件不存在"（BOM+CRLF） | `.sh` 一律用写文件工具生成，或在 WSL 里 `sed -i 's/\r$//'` |
| **`wsl -e bash -c "…"`** | 引号/花括号被 PowerShell 吃掉（甚至跑到 Windows 侧的 grep） | 命令写进 `venus-recon/*.sh`，用 `wsl -e bash /mnt/c/.../x.sh` 执行 |

---

## 9. 里程碑时间线（回顾）

| 日期 | 事件 |
|---|---|
| 11-03 | 双系统跑通，RAM 启动可用 |
| 11-04 | 数据卷落地；设置黑块问题首次出现 |
| 11-05 | 主屏 3 图标修复；boot_b 首次刷入；电量/触摸/GPU 验证；离线侧载链路首次跑通 |
| 11-06 上午 | 触摸 16 ms 修复移植；`img-final3.bin` 定稿（含 `adsp=1 pmic=1`） |
| 11-06 下午 | PCIe：电源域、时钟、PHY、PERST、WLAN_EN、命令库、RPMh 投票全部打通（p4–p63） |
| 11-06 晚 | star 与 SteamOS-ARM 两份参考源码到手；ath11k hw1.0 问题降级为十行补丁 |
| 11-07 | **M0**：六路 rail 齐、PERST、LTSSM `0x111`、ECAM 读到 `17cb:1103`、Gen2 |
| 11-08 | SMMU/BAR → BHI/BHIE 下载 `amss.bin` → 设备进 **EE=2**；MHI 初始化、M0 握手、事件环收到 STATE_CHANGE/EE_EVENT |
| 11-09 | 命令环：START_CHAN 全被取用并回 SUCCESS；BW_REQ 与 bw-scale 通道确认；发现"cmd rp 是主机维护的"这一关键更正 |
| 11-10 上午 | 发现 `uint32` 截断 64 位指针的自伤 bug（白跑两轮）；修正后 ch20 保持 RUNNING，`0xb0` SOC reset 进 RDDM 并可钉住 |
| 11-10 下午 | **M8**：LOOPBACK ch0→ch1 双向跑通（TRE 取用 + 载荷 DMA + TX_EVENT）；用 MHI 窗外的载荷指针做正对照，证明 ch20/ch4 **没有任何固件客户端** |
| 11-10 晚 | 原厂 Android 比对固件 md5（完全一致，排除"换固件"这条路）；从本地 ath11k 源码确认 WiFi 只要 ch20/ch21 这对 "IPCR" |

---

## 10. 下一步（按优先级）

1. **M9：让 IPCR 起来**（当前唯一卡点）。已排除完我们自己这边的所有错，现在按 A→B→C 三条线推进：
   - **A（已关闭）**：固件来源——原厂 `amss.bin` 与我们手上**md5 一致**，没有更好的版本可换。
   - **B（进行中）**：把 MSI 从"只使能 1 个向量"改成使能全部向量、清 `BHI_INTVEC`，再用"载荷指针在 MHI 窗外"的正对照看 ch20 是否终于取 TRE（`apply398.py` / p443）。
   - **C（未开始）**：拿 star / lemonade 的成功时间线逐字段 diff——重点不在寄存器值，而在**下载 BHI 之后到 M0 之间主机还做了哪些"与 MHI 无关"的动作**（QMI 预置、board data、时钟/电源的第二次切换）。
2. **快循环**：`0xb0` 双写钉住 RDDM（已实测可行），把"一轮 5 分钟"压到"10 秒"，用来抓 AMSS 启动最初几毫秒的行为。
3. **并行（不占设备时间）**：ath11k 的 hw2.1 补丁、`board-2.bin` 生成脚本、QMI/WLFW 的 host 端客户端（`wlan_firmware_service_v01.{c,h}` 已在树里）。
4. **UI 侧已就绪**：`hakios.apple80211.c` + `hakios.wlan.cpp` + `hakios.sta.h` 已实现开关/扫描/关联的 Darwin 接口，只等底层能扫到 AP 就能接上。
5. **可选**：把 `img-final3.bin` 之后的新构建（含触摸修复、configd/installd job）重新刷进 `boot_b`。

---

## 11. 参考资料

- 本地：**`venus-recon/CONTINUE-2026-11-10.md`（最新交接，含固定流程与全部 M8 证据）**、`HANDOVER-2026-11-10.md`、`venus-recon/section14.md`、`venus-recon/STATE.md`、`PROGRESS-2026-11-06.md`、`PCIe-试验记录-人工.md`、`VENDOR-PCIE-NOTES.md`
- 本地 ath11k（已编好）：`/root/hakios/xnu-deps/build/ath11k/src/ath11k/`（`mhi.c` 的 qca6390 通道表、`qmi.c` 的 `AF_QIPCRTR`）、`tools/mk-ath11k.sh` → `out/ath11k.o`
- 参考源码：`ref-star/`（小米 11 Ultra）、`ref-steamos/`（REDMAGIC 6 / SteamOS-ARM）、`Xiaomi_Kernel_OpenSource-venus-r-oss/`（厂商）
- 上游：Linux 7.0.14 `drivers/net/wireless/ath/ath11k`、`drivers/bus/mhi/host`、`drivers/pci/controller/dwc/pcie-qcom.c`
- UniXNU（架构参考，不迁移）：https://github.com/UniXNU/UniXNU
