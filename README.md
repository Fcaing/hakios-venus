# hakios-venus

**在小米 11（venus / SM8350）上跑 iOS 16.5 的内核移植工作台 —— 以及一块卡住的 Wi-Fi。**

A bring-up workbench for iOS 16.5 (XNU 8796.121.2) on the Xiaomi 11 (`venus`, SM8350), plus the
PCIe/MHI experiment log for its external QCA6490 (WCN6855) Wi-Fi chip, which is where it currently
stops: the firmware boots, the host side is proven correct on a test channel pair, and the
firmware never attaches its IPCR client.

---

## 现状

| 能力 | 状态 |
|---|---|
| 双系统并存 / 冷启动进 iOS | ✅ |
| 显示 + GLES（Adreno 660） | ✅ |
| 触摸、电源键、电池百分比、充电状态 | ✅ |
| 主屏两页图标、设置、第三方 `.app`（镜像内置） | ✅ |
| 数据卷跨启动持久化（HFS+） | ✅ |
| 设置 › Wi-Fi 页面能打开 | ✅ |
| **Wi-Fi 开关 / 扫描 / 上网** | ❌ 固件侧卡点（见下） |
| 蜂窝 / 蓝牙 / 相机 / 音频输出 / Metal | ❌ 未移植 |
| 端到端"点一下装应用" | ❌ 未实现 |

**Wi-Fi 进度条**

```
上电 ✅ → 链路 Gen2 ✅ → BHI/BHIE 固件下载 ✅ → MHI 控制面 ✅
        → 命令环（START_CHAN 回 SUCCESS）✅
        → 数据面 测试通道 LOOPBACK 双向通 ✅
        → 数据面 业务通道 IPCR ch20/ch21 ❌ ← 这里
```

一句话：主机侧已经逐条与厂商驱动对齐、并且在**固件确实提供**的 LOOPBACK 通道上把 TRE 取用、payload DMA、
完成事件全跑通了；但 AMSS 固件起来之后**不认领 IPCR 那对通道**，而 Wi-Fi 的 QMI 只走 IPCR。
详细证据与已排除的 19 类假设见 [`docs/02-wifi-status.md`](docs/02-wifi-status.md)。

---

## 文档

| 文件 | 内容 |
|---|---|
| [`docs/01-verified-features.md`](docs/01-verified-features.md) | **实测可用功能清单**（含判据、复验命令、平台缺陷） |
| [`docs/02-wifi-status.md`](docs/02-wifi-status.md) | **Wi-Fi 进度**：硬件事实、M0–M9、已排除清单、被推翻的旧结论、固件逆向边界 |
| [`docs/03-next-steps.md`](docs/03-next-steps.md) | **下一步**：先修环境，再按 P1–P6 排序（含验收标准与两周排期） |
| [`docs/04-experiment-rules.md`](docs/04-experiment-rules.md) | 一轮实验的固定流程 + 13 条硬规矩 + 领域坑 |
| [`docs/05-register-map.md`](docs/05-register-map.md) | 寄存器 / 上下文 / TRE / 内存布局速查（**venus 实测值**） |
| [`docs/06-milestones.md`](docs/06-milestones.md) | 时间线、两条技术路线的取舍、复盘（哪些判断错了） |
| [`docs/history/`](docs/history/) | 原始交接与逐轮证据（`HANDOVER-2026-11-11.md`、`CONTINUE-2026-11-10.md`、`VENDOR-MHI-AUDIT.md` …） |

---

## 仓库结构

```
docs/                  上述文档 + history/（原始交接与逐轮证据）
src/                   移植相关的源码（早期快照，见下）
  drivers/pcie/        hakios.pcie.c（43 KB 实验驱动）、venus.pcie.h（从设备树生成的 75 条 PHY 序列）
  drivers/{input,power,storage}/
  devices/venus/       venus 的配置与自检清单
  userland/src/        驱动报告的 sysctl 另一半
history/
  INDEX.md             307 份 apply-NNN.py 的一句话索引
  patches/             全部实验补丁（按编号）
scripts/               构建 / 打包 / 上机 / 取日志 / 固件分析
evidence/              两段可核对的关键日志摘录（LOOPBACK 回环、通道上下文归属）
```

### 关于 `src/` 的重要说明

`src/drivers/pcie/hakios.pcie.c` 是 **2026-11-06 的早期快照（43 KB）**，停在 M0 之前。
真正跑到 M8 的那版是约 5,150 行的单函数探针，**随机器重装丢失了**。
`history/patches/` 里 307 份 `apply-NNN.py` 是它的实验记录：每份都会断言自己的锚点字符串在文件里只出现一次，然后改一处。
**这些补丁不能干净地打到本仓库的 43 KB 快照上**——它们是"实验日志"，不是可复现的 patch series。
重建方法见 [`docs/03-next-steps.md`](docs/03-next-steps.md) 第 0 节。

---

## 复现一轮实验（前提：自己搭好构建树）

```bash
# 1) 构建机（Ubuntu/WSL，HakiOS 2.1.13）
git clone https://github.com/oosexgang/hakios-xnu-kernel.git hakios && cd hakios
# 把 src/ 里的驱动同步进树，然后
bash tools/make-kernel.sh -j20        # 退出码 2 = 仅 kext symbol-set 检查失败，看 errors 计数
# 2) 打包 payload（cmdline 预算 514 字符，超出静默截断）
RET=200 bash mk-pcie2.sh pNNN 'pcie=1 pcie_step=5 pcie_power=1 ...'
```

```powershell
# 3) 上机（必须冷启动；fastboot 不在 PATH）
& $FB reboot bootloader
.\run-p104.ps1 -Payload p-pNNN.bin -Tag pNNN -RunSeconds 115
& $FB oem dump logdump 0 40000 ; Start-Sleep 5
& $FB get_staged ".\cur-pNNN.bin"
```

三条判据缺一条这一轮就作废：日志里没有 `TRUNCATED`、`strings hakios-kernel | grep -c apply-NNN == 1`、
按 `pcie_tag=pNNN` 切片后能找到以 `the probe is done…(apply-169)` 结尾的最新一组。

---

## 本仓库**不包含**的东西

这是有意为之，不是遗漏：

| 不含 | 原因 |
|---|---|
| `amss.bin` / `amss20.bin` / `m3.bin` / `regdb.bin` / `bdwlan.*` | Qualcomm 专有固件，从设备 `/vendor/firmware_mnt/image` 取出；**请自己从自己的设备提取** |
| iOS IPSW / kernelcache / 系统应用 | Apple 版权内容 |
| `root.apfs` / `system.apfs` / payload 二进制 | 体积（GB 级）+ 内含上面两类内容 |
| 完整 XNU / HakiOS 内核树 | 上游有，见下；本仓库只放移植增量 |
| 参考实现（小米 11 Ultra `lemonade_wifi.c`、SteamOS-ARM 补丁） | 第三方代码，不转售 |
| Trust cache、签名材料、任何密钥 | 安全 |

---

## 许可

- `docs/`、`scripts/`、`history/`：**MIT**（见 [`LICENSE`](LICENSE)）
- `src/`：作为 XNU 衍生作品，**Apple Public Source License 2.0**（全文见 [`LICENSE-APSL-2.0.txt`](LICENSE-APSL-2.0.txt)）
- 第三方与固件的说明见 [`THIRD_PARTY.md`](THIRD_PARTY.md)

---

## 上游与致谢

- **HakiOS** — <https://github.com/oosexgang/hakios-xnu-kernel>（本项目的一切基础；没有它就没有"能开机的 iOS"）
- **UniXNU** — <https://github.com/UniXNU/UniXNU>（iOS 26 那条路的架构参考，已停，见 `docs/06-milestones.md`）
- **SteamOS-ARM SM8350**（REDMAGIC 6）：`hw2.1` 十行补丁与 `board-2.bin` 生成方法
- 小米 11 Ultra（star）的 Wi-Fi 实现：同 SoC + 同芯片 + 同一份固件的成功样本

---

## 想参与？

最有价值的三个切入点（都不需要这台手机）：

1. **star 的 MHI 日志**：一台跑通的 11 Ultra（开 `MHI_VERB` 的内核）在 0–600 ms 的完整时序，能直接 diff 出我们还差哪一步。
2. **QURT stub 解析**：`amss.bin` 里 `0x8xxxxx` 段不在任何 ELF 段内，是 QuRT 的对外 stub；能解析它，`ipc_router_xal_up` 的调用方就能追下去。
3. **上层先行**：QRTR-over-MHI / WLFW QMI / `board-2.bin` 拼装 / ath11k `hw2.1` —— 这些不占设备时间，IPCR 一通就能立刻接上。

> 本项目只做**自有设备上的移植实验**，不提供刷机包、不提供绕过签名的方法、不包含任何厂商固件。
