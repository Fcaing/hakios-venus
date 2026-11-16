# 实测可用功能清单

> 设备：小米 11（`M2011K2C` / 代号 **venus** / SM8350 Snapdragon 888）
> 系统：HakiOS 2.1.13（XNU `xnu-8796.121.2` / Darwin 22.5.0 / iOS 16.5 `20F66`）
> 基线：2026-11-11，最后一批实测轮次为 p416–p487
> 判定标准：**"可用"= 真机冷启动后亲自跑通，并有日志、屏幕或 sysctl 证据**；拿不到证据的一律不进本表。

---

## 1. 一页结论

这台手机现在是一台**能开机、能触摸、能显示、能装应用**的 iOS 16.5 设备，**还没有网络**。

| 分类 | 可用 | 不可用 |
|---|---|---|
| 底座 | 3 | 0 |
| 交互 | 4（音量键算 0.5） | 0 |
| 桌面与应用 | 3 | 1 |
| 网络 | 1（只有设置页面） | 3 |
| 媒体 | 0 | 3 |
| 调试通道 | 5 | 0 |

---

## 2. 底座

| 功能 | 状态 | 判据 / 证据 | 备注 |
|---|---|---|---|
| 双系统并存（Android `/ iOS`） | ✅ | `fastboot --set-active=a/b` 切槽；两套互不破坏 | Android 侧是 HyperOS + ReSukiSU root；iOS 在 `boot_b` |
| 冷启动直接进 iOS（不连电脑） | ✅ | `boot_b` 放 payload `img-final3.bin`（15,949 块 × 4096 = 65,327,104 B） | 前提是上一次正常关机，不是挂死 |
| 数据卷跨启动持久化 | ✅ | HFS+ 卷 `/dev/ufs_darwin_data`，位于 `darwin` 分区块 2042368 起、长 3,200,549 块（13,109,448,704 B）；`IconState.plist` 从 2,764 B 长到 3,728 B、`IconsCache/*.isdata` 逐次增多 | 写入路径确实通；Android 侧内核无 HFS+，取证只能 `dd` 12 GB |

分区布局（实测）：

| 分区 | 内容 |
|---|---|
| `boot_a` | Android（HyperOS + root） |
| `boot_b` | HakiOS payload（当前 `img-final3.bin`） |
| `darwin` | 约 20 GiB：root APFS（块 0–1374207）、cryptexes（1374208–2042367）、**数据卷**（2042368 起） |
| `logdump` | `/dev/block/sda24`，2 MB，loader 日志窗口 |

---

## 3. 交互

| 功能 | 状态 | 判据 / 证据 | 备注 |
|---|---|---|---|
| 显示 + GPU 加速（GLES） | ✅ | 引导日志 `gpu=1 gl=1`；Adreno 660 走 `drivers/gpu/hakios.adreno.c`；分辨率 `fbwidth=1440 fbheight=3200` | **Metal 未启用**；设备树必须声明 sRGB（曾错报 P3，导致 WebKit 要 10-bit 表面、页面全黑） |
| 触摸（单点 / 滑动） | ✅ | `touchscreen=1`，设备节点 `/dev/hakios-touch`；用户态 `rwtouch` 可 `tap/swipe/drag/hold/read/wait` | 跟手延迟偏高；移植了 2.3.4 的 16 ms 空闲轮询但手感无改善，怀疑瓶颈在 `rwtouch` 之上 |
| 电源键 | ✅ | `buttons=1` | 也是"挂死后唯一救命手段"（长按 15–20 s 断电） |
| 音量键 | ⚠️ 半可用 | 硬件可读，键值有 | 因为**没有音频路由**（设置›声音与触感会卡死），已主动放弃映射，实际不可用 |
| 电池百分比 / 充电状态 | ✅ | ADSP 电池管理器 `adsp=1 pmic=1`，能报容量/电压/电流/温度/循环次数；状态栏出百分比；USB `online 1` | **绝对不能加 `battery=1`**，加了就不走 DSP、没有百分比 |

---

## 4. 桌面与应用

| 功能 | 状态 | 判据 / 证据 | 备注 |
|---|---|---|---|
| 主屏图标（完整两页） | ✅ | 17 + 18 项 + Dock 4 项 | 原"只剩 3 个图标"的根因：32 个系统应用在 `private/var/staged_system_apps` 里只建了 APFS synthetic dir，LaunchServices 不认 |
| 设置 › 应用列表图标与名字 | ✅ | 逐项显示正常 | 原"黑色方块"= 图标缓存未热（`lsdidentifiers.plist` 停在 157 项、`IconsCache` 只有 86 个 `.isdata`）；把列表滚一遍后写入 89 个，跨启动保留 |
| 设置应用本体 | ✅ | 根页、通用、语言与地区、应用列表、电池页均正常 | 声音与触感页会卡死（音频路由缺失） |
| 第三方 `.app` 注册与启动 | ✅ | `hello.app` 放进系统镜像 `/Applications` → 品红图标出现在第 2 页 → 点按启动，日志 `Successfully spawned Tips[55] because launch job demand` | `/Applications` 共 174 项（173 个 `.app` + 1 plist），LS 每次启动重建数据库；内核**没有签名策略**（无 trust cache、无校验），未签名也能跑，但**拿不到 entitlement** |
| 端到端"点一下装好" | ❌ | — | 只有"镜像内置"和"离线侧载"两条路；侧载 union 到 `/Applications` 会把目录盖空，**已废弃回退** |

---

## 5. 网络与媒体

| 功能 | 状态 | 判据 / 证据 | 备注 |
|---|---|---|---|
| 设置 › Wi-Fi 页面能打开 | ✅ | 页面渲染正常、行可点 | 页面是系统自带的，与驱动无关 |
| Wi-Fi 开关 / 扫描 / 上网 | ❌ | 按下无反应；`wifid` 报 `PPM Error:No matching driver found`（没有驱动认领接口） | 详见 [`02-wifi-status.md`](02-wifi-status.md) |
| 蜂窝 | ❌ | — | 未移植（无 modem/QMI 上层） |
| 蓝牙 | ❌ | — | 未移植（`BT_EN` 引脚能拉，但无协议栈） |
| 相机 | ❌ | — | 未移植 |
| 音频输出 | ❌ | 设置›声音与触感卡死 | 未移植，连带音量键一起弃用 |
| Metal | ❌ | — | 只有 GLES；Adreno 上的 Metal 后端起不来 |

---

## 6. 调试通道（这部分其实是最有价值的"功能"）

| 通道 | 用法 | 实测状态 |
|---|---|---|
| loader 日志分区 | Android 侧 `dd if=/dev/block/sda24 of=/data/local/tmp/ld.bin bs=4096 count=512` + `adb pull`；loader 内 `oem dump logdump 0 <hex长度>` + `get_staged` | ✅，但**窗口只有 24 秒**，之后写不进 `logdump` |
| 驱动器内报告 | `sysctl kern.hakios.pcie`（init 会打印 `hakios: the PCIe driver says: …`） | ✅ |
| 命令库转储 | boot-arg `cmddb=2` → 4 个 slave / 161 条资源 | ✅ |
| 分步探针 | `pcie_step`、`pcie_only`、`pcie_go`、`pcie_pause`、`pcie_settle`、`pcie_delay`、`pcie_tag` | ✅ |
| 截图 | `oem screenshot` + `get_staged`（18,432,000 B = 1440×3200×4） | ✅ |
| 触摸脚本控制 | `rwtouch tap/swipe/drag/hold/zigzag/button home\|lock/read/notify/wait`，坐标用 0–1 比例 | ✅（但 guest 时钟快 2.4–8 倍，`wait` 不可靠） |
| 真机硬件取证 | 本机 Android 只读采集：`/sys/firmware/fdt` 803,915 B → `dtc` 反编译 34,151 行 | ✅（`phone-dump/venus-hw/`） |

---

## 7. 已知平台缺陷（不修就会一直拖慢你）

| 问题 | 表现 | 影响 |
|---|---|---|
| guest 时钟快 2.4–8 倍 | `rwtouch wait` 不可靠 | 自动化脚本必须按**事件顺序**判断，不能按秒 |
| `mobileactivationd` 每 10 s 崩溃 | `SIGTRAP \| sent by exc handler` | 刷日志，不影响使用 |
| 每次挂死要手动断电 | 长按电源 15 秒 → 音量下 + 电源 进 fastboot | 最大的时间成本 |
| loader 日志窗口 24 秒 | 之后的日志写不进 `logdump` | 只能用 sysctl / 落盘通道补 |
| Android 内核无 HFS+ | 数据卷只能 `dd` 12 GB 再 `adb pull`（约 5 分钟） | 每次取证 5 分钟 |
| 设置 › 声音与触感卡死 | 音频路由未完成 | 已连带放弃音量键 |
| 触摸延迟偏高 | 2.3.4 的 16 ms 修复无效 | 待查，瓶颈疑在 `rwtouch` |
| iOS 桌面运行时 USB 完全不枚举 | 与"卡死"无法从主机区分 | **每轮实验都必须问屏幕状态** |

---

## 8. 怎么自己复验（最短路径）

```powershell
# 0) 每次新 pwsh 会话
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force

# 1) 进 iOS（Android 的 fastboot 里切槽有效，HakiOS 的 loader 里不支持）
& $FB --set-active=b ; & $FB reboot

# 2) 看它到底起没起来
& $FB oem screenshot ; & $FB get_staged ".\shot.bin"     # 18,432,000 B = 一帧
& $FB oem dump logdump 0 40000 ; Start-Sleep 5 ; & $FB get_staged ".\cur.bin"

# 3) 回 Android
& $FB --set-active=a ; & $FB reboot
```

`$FB` = `tools\platform-tools\fastboot.exe` 的绝对路径（**不在 PATH 里**）。

三项最省事的判据：

| 想确认 | 一句话判据 |
|---|---|
| 内核起来了 | 日志里有 `bsd_init: calling loopattach`，且屏幕是桌面而不是 Apple logo |
| GPU 在跑 | 日志有 `gpu=1 gl=1`，且设置界面能滑动不撕裂 |
| 触摸在跑 | `rwtouch tap 0.5 0.5` 能让桌面图标响应 |

---

## 9. 一句话

**底座和交互这一层已经"能用"了**（这是 HakiOS 上游本身的功劳，venus 只是被接了上去）；
**应用这一层只做到"镜像内置"**；**网络和媒体整块是空的**——Wi-Fi 卡在固件侧，见下一份文档。
