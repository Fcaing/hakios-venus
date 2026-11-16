# 第三方与许可说明

本仓库**不含**任何厂商固件、Apple 版权内容或第三方参考实现。以下是它的依赖与来源。

---

## 1. 直接依赖

| 项目 | 许可 | 在本仓库里的角色 |
|---|---|---|
| [HakiOS](https://github.com/oosexgang/hakios-xnu-kernel)（`xnu-8796.121.2` / Darwin 22.5） | 内核与 `drivers/`、`xnu/files/`：APSL 2.0；其余按其 `LICENSE` | 本仓库的 `src/` 是它的移植增量；构建必须基于它 |
| [UniXNU](https://github.com/UniXNU/UniXNU) | 见上游 | 只作为 iOS 26 路线的架构参考，代码未引入 |

## 2. `src/` 里各文件的来源

| 文件 | 性质 |
|---|---|
| `drivers/pcie/hakios.pcie.c` | 我们为 venus 写的 PCIe/MHI 实验驱动（XNU 衍生作品 → APSL 2.0）。**是 2026-11-06 的早期快照** |
| `drivers/pcie/venus.pcie.h` | 从 venus 自己的设备树生成的基址/引脚/75 条 PHY 序列 |
| `drivers/input/hakios.input.c` | 启动钩子（`hakios_pcie_init()` 从这里调用），改动自 HakiOS |
| `drivers/power/hakios.pmic.c` | SPMI 写路径 + `pmic_poke` + LDO dump |
| `drivers/storage/hakios.ufs.c` | 报告分区写路径（`ufs_report_part`） |
| `devices/venus/**`、`tools/map`、`xnu-files/**`、`userland/src/pcie_report.c` | HakiOS 设备层与工具层的 venus 增量 |

## 3. 未包含、但复现时需要的第三方材料

| 材料 | 从哪来 | 为什么不放进来 |
|---|---|---|
| `amss.bin`（5,236,304 B, md5 `341ec80bb5caa88867bbb5718322a652`） | 你自己设备的 `/vendor/firmware_mnt/image/` | Qualcomm 专有固件 |
| `amss20.bin` / `m3.bin` / `regdb.bin` / `bdwlan.e01…e97` | 同上 | 同上 |
| iOS 16.5 IPSW、kernelcache、系统 app | Apple | 版权内容 |
| `root.apfs` / `system.apfs` / payload 镜像 | 由上面两类打出来 | 体积 + 内含上面两类 |
| 小米 11 Ultra（star）的 `lemonade_wifi.c` 等 | 第三方提供 | 第三方代码，不转售 |
| SteamOS-ARM SM8350 补丁（`0008-qca6490-hw21.patch` 等） | 上游开源项目 | 按其自身许可使用，不在本仓库分发 |
| Xiaomi 内核源码（`venus-r-oss`） | 小米开源发布 | 体积 900+ MB；按其发布条款使用 |
| `platform-tools`（adb/fastboot） | Google | 二进制工具链 |

## 4. 引用与引用方式

本项目在文档里引用寄存器值、时序与代码行号，均来自：

- 本机实测日志（`pNNN.txt` / `cur-pNNN.bin`，未分发）
- 真机 Android 运行态（`/sys/firmware/fdt` 反编译、`cnss2` dmesg）
- 厂商内核源码（`drivers/bus/mhi/core/*`、`drivers/net/wireless/cnss2/*`、`pci-msm.c`）
- 上游 Linux `ath11k` 与 `drivers/bus/mhi/host`

如果转发本仓库的文档，请一并保留这些来源说明。

## 5. 安全与合规

- 本仓库不含任何签名材料、trust cache、密钥或绕过 AMFI/签名校验的方法。
- 所有实验只在本机自有设备上进行，通过设备自身的 fastboot/loader 通道加载自建镜像。
- 不提供刷机包，不提供"一键安装"，不承诺任何设备的可用性。
