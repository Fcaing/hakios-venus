# 一轮实验的固定流程与踩坑清单

> 每轮 ≈ 5 分钟：冷启动 42 s + 打包 65 s + 跑 115 s + 取日志 15 s。一天能跑 60–80 轮。
> 这份清单里的每一条都**真的废掉过一整轮**。

---

## 1. 固定流程

### 1.1 构建（WSL / 构建机）

```bash
# 打补丁 + 编内核
wsl -e bash /mnt/c/.../venus-recon/buildNNN.sh
# 判据：errors=0；且 strings hakios-kernel | grep -c apply-NNN == 1
# 注意：make-kernel.sh 退出码 2 = kext symbol-set 检查失败，不代表编译失败
```

```bash
# 打包 payload（cmdline 预算 514 字符，超出静默截断）
RET=200 bash mk-pcie2.sh pNNN 'pcie=1 pcie_step=5 ...'
```

### 1.2 上机（Windows）

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force   # 每个新 pwsh 会话都要
$fb = 'C:\...\tools\platform-tools\fastboot.exe'
& $fb reboot bootloader                     # 必须冷启动；等设备号 4f9baecb（6–24 s）
.\run-p104.ps1 -Payload p-pNNN.bin -Tag pNNN -RunSeconds 115
& $fb oem dump logdump 0 40000              # 立刻返回 OKAY
Start-Sleep 5
& $fb get_staged "C:\...\venus-recon\cur-pNNN.bin"     # 262,144 B，这才是本轮日志
.\extract-log.ps1 -File "C:\...\cur-pNNN.bin" -Out "C:\...\pNNN.txt"
```

### 1.3 判读

1. 先按 `pcie_tag=pNNN` 切片（`logdump` 里保留着历史启动）。
2. 只取以 `the probe is done…(apply-169)` 结尾的**最新**时间戳组。
3. 没有 `WARNING: the kernel command line is TRUNCATED` 才算有效轮次。

---

## 2. 十三条硬规矩

| # | 坑 | 症状 | 规矩 |
|---|---|---|---|
| 1 | **cmdline 只有 514 字符** | 新加的 boot-arg 静默失效，整轮结论无效 | loader 前缀占 93 字符；payload 只装 514，超了从尾部截断。日志里必须**没有** `TRUNCATED` |
| 2 | `pcie_tag` 重复 | 白费 14 字符 | `mk-pcie2.sh` 自己会追加 `pcie_tag=$TAG`，别再写进 `$EXTRA` |
| 3 | 热启动 | 链路 down（LTSSM 3/5）或状态脏 | **每一轮都要冷启动**；从 Android 侧 `adb reboot bootloader` 会掉 USB 数分钟，脚本要等 ≥180 s |
| 4 | 日志串轮 | 读到上一轮的 `apply-*` 行 | 先按 tag 切片，再取最新时间戳组 |
| 5 | 64 位指针存进 `uint32_t` | 探针在第一条读之后就"静默结束"，看起来像设备没反应 | 偏移量用 `uint32_t`，用时现加：`rd(pcie_dma_extra + off)`。这个错犯过三次 |
| 6 | TRE 的 CPU 地址算错 | 把 ch20 的 TRE 写进 ch21 的上下文 | 必须 `pcie_dma_extra + (iova - PCIE_EXTRA_IOVA)` |
| 7 | 通道上下文偏移 | 读到一片零，误判"设备不写上下文" | 通道在 `ch*0x2c`（ch20 → `0x370`），**没有** `+0x2000`；事件才是 `+0x2000 + er*0x2c`，命令是 `+0x2400` |
| 8 | "界外指针"用错值 | 以为验证了"不取环" | MHI 窗是 `0xa0000000..0xb0000000`，`0xa0100000` 仍**在窗内**；界外要用 `0x80000000` |
| 9 | `.ps1` 被策略拦住 | 脚本静默不跑 | 每个新 pwsh 会话先 `Set-ExecutionPolicy -Scope Process Bypass -Force` |
| 10 | `Set-Content -Encoding UTF8` | WSL 里 `#!/bin/bash` 报"文件不存在"（BOM + CRLF） | `.sh` 用写文件工具生成，或 `sed -i 's/\r$//'` |
| 11 | `wsl -e bash -c "…"` | 引号/花括号被 PowerShell 吃掉，甚至跑到 Windows 侧的 grep | 命令写进 `.sh`，用 `wsl -e bash /mnt/c/.../x.sh` 执行 |
| 12 | boot-arg 解析块共用变量 | 传 `pcie_chanstart=0` 把整个 MHI 初始化块清零，四轮"稳定"全是空转 | 每个 boot-arg 用**独立变量**解析，且解析前先清零；每加一个补丁就 `strings \| grep apply-` 核对 |
| 13 | `run-p104.ps1` 的假警报 | `giving up on seeing the loader go away`、`back in the loader after 30 s` | 忽略它；只有 `cur-pNNN.bin` 是真的 |

---

## 3. 领域知识的坑（不看就会重犯）

| 坑 | 正确做法 |
|---|---|
| `LTSSM` 要**置位** bit8 才启动训练 | vendor 的 `write_mask(addr, clear, set)` 是 `(read & ~clear) \| set`，所以 `write_mask(LTSSM, 0, BIT(8))` 是**置位**。早期两次当成清零，白跑 |
| 写 GDSCR 前必须先投 rail | 否则整个 SoC 挂住 |
| 读 `0x152128`（vendor 的 collapse-vote）会 panic | TZ 保护，**禁止访问** |
| RDDM 缓冲区不能放在镜像区 | `0xa0220000 + 0x4fe650` 一直是有效镜像，落在其中的任何"转储"都是自己的固件副本 |
| 写 `MHICTRL` 的 SYS_ERR(0xff00) 不会强制 RDDM | 设备会按非法主机行为处理（`MHISTATUS` 置 `0xff05`） |
| 事件环 `wp` 设备从不更新 | 主机只能扫 TRE 判断有无新事件，不能等 wp |
| 设备在 `EE=2` 之后事件流只剩 2 条 | 不要用"最近没有新事件"当作"设备没反应"的证据 |
| `fastboot stage` 2.4 GB 系统镜像 | 必须先 `oem ramdisk`，否则 `bad size` |
| loader 里 `--set-active` 不可用 | `Device does not support slots` |
| loader 日志只在 UEFI 还持有存储时能写 | 内核接管 UFS 之后写不进去（`log: NOT WRITTEN to logdump`） |
| `oem stop` 要发两次 | 一次停不下来 |
| iOS 桌面运行时 USB 完全不枚举 | 与"卡死"无法从主机区分 ⇒ **每轮必须问屏幕状态** |

---

## 4. 别再做的事（一句话清单）

- 别写 `MHICTRL` 的 M0，除了 `M2 → M0` 这一条合法路径；
- 别在 `EE=1` 时打事件环门铃；
- 别用 `ld-pNNN.bin` 判读；
- 别信 `run-p104.ps1` 的 `back in the loader`；
- 别从 xnuloader 里重跑（热启动）；
- 别给 `wsl` 命令接 `| head` / `| tail` / `| Select-Object`；
- 别用 `.ps1` 之外的壳去跑 `.sh`（`bash -c` 的引号会被吃掉）；
- 别拿"寄存器读回来是我们在里面写的值"当作"设备收到了"（必须有正对照）。

---

## 5. 取证命令速查

```powershell
# 冷启动
& $fb reboot bootloader

# 上机一轮
.\run-p104.ps1 -Payload p-pNNN.bin -Tag pNNN -RunSeconds 115

# 取日志（loader 内）
& $fb oem dump logdump 0 40000        # 立刻返回 OKAY
Start-Sleep 5
& $fb get_staged "C:\...\cur-pNNN.bin"

# 从 Android 侧取（设备已回 Android）
adb shell su -c "dd if=/dev/block/sda24 of=/data/local/tmp/ld.bin bs=4096 count=512"
adb pull /data/local/tmp/ld.bin ld-pNNN.bin
python scripts/last-run.py ld-pNNN.bin     # 只打最新一轮

# 截图
& $fb oem screenshot ; & $fb get_staged "C:\...\shot.bin"   # 18,432,000 B

# 设备救回
# 卡死（USB 全灭）→ 长按电源 20 s；panic 进 Android → adb reboot bootloader（12–20 s 自恢复）
# adb 掉线 → pnputil /restart-device "USB\VID_18D1&PID_4EE7\4F9BAECB" + adb kill-server/start-server
```

---

## 6. 环境自检（`scripts/prebuild.sh`）

编译前先确认这四件事，能省掉一半"为什么没有日志"：

1. `strings hakios-kernel | grep -c apply-NNN` 是否等于期望值；
2. payload 的 cmdline 长度（`payload entry 'cmdline' size` 的十六进制，换算 < 514）；
3. `img-wr2.bin`（loader）与内核是否同一次构建；
4. `root.apfs` 里的 `fw/amss.bin` md5 是否还是原厂那份。
