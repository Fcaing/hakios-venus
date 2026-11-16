# scripts

一轮实验的五个动作：**改代码 → 编内核 → 打 payload → 上机 → 取日志**，外加固件分析工具。

> ⚠️ **所有脚本里的路径都是 2026-11 那台机器的**：
> `/root/hakios`（WSL 里的构建树）与 `/mnt/c/Users/Administrator/Documents/deepseek-harness/default-workspace/venus-recon`（Windows 工作区）。
> 换机器后先改路径，最省事：
> ```bash
> sed -i 's#/root/hakios#/root/hakios#; s#/mnt/c/Users/Administrator/Documents/deepseek-harness/default-workspace/venus-recon#/mnt/c/Users/<you>/<path>/venus-recon#' scripts/*.sh
> ```
> 或者把两个路径提成环境变量 `HAKIOS=/root/hakios` 与 `W=/mnt/c/.../venus-recon`，再全局替换。

---

## 1. 构建与打包

| 脚本 | 作用 | 用法 |
|---|---|---|
| `build434.sh` | 打一个补丁（`apply434.py`）→ 编内核 → 打印 `errors=` 与 `apply_tags=` | 照抄改编号：`buildNNN.sh`。**`errors` 必须是 0**；`make-kernel.sh` 退出码 2 只是 kext symbol-set 检查失败 |
| `mk-pcie2.sh` | 用当前内核 + `root.apfs` 打一个 payload，打印 sha256 与完整 cmdline | `RET=200 bash mk-pcie2.sh pNNN '<EXTRA boot-args>'`。**故意不带 `gpu=1 gl=1`**：Adreno 起来时会刷几千行，把 PCIe 探针的日志挤出 logdump |
| `mk434.sh` | 一轮的 payload 参数模板（Wi-Fi 探针全套） | 换编号与 `pcie_mhi_data=NN` 即可 |
| `prebuild.sh` | 环境自检（编译链、内核、root.apfs 是否就位） | `bash prebuild.sh` |

`mk-pcie2.sh` 里两个容易踩的点：

1. `RET` 是内核跑多少秒后自己回 loader（默认 200；测试通常 `RunSeconds=115` + `RET=200` 留余量）；
2. cmdline 由 loader 前缀（93 字符）+ 这些参数组成，**payload 只装 514 字符**，超了从尾部静默截断。

## 2. 上机与取证

| 脚本 | 作用 | 用法 |
|---|---|---|
| `run-p104.ps1` | 把 payload 送进设备、跑指定秒数、收日志 | `.\run-p104.ps1 -Payload p-pNNN.bin -Tag pNNN -RunSeconds 115` |
| `extract-log.ps1` | 从 `cur-pNNN.bin`（262,144 B）抽 ASCII 行 | `.\extract-log.ps1 -File cur-pNNN.bin -Out pNNN.txt` |
| `extract-log.py` | 同上，Python 版（跨平台） | `python extract-log.py cur-pNNN.bin pNNN.txt` |
| `last-run.py` | 从 `ld-*.bin` 里只挑最新一轮（loader 分区保留多次启动） | `python last-run.py ld-pNNN.bin` |

**只认 `cur-pNNN.bin`**：`run-p104.ps1` 顺手抓的 `ld-pNNN.bin` 是历史分区内容，常被 GPU 日志刷屏；
它打印的 `back in the loader after 30 s` 也是假警报（loader 的 fastboot gadget 在内核运行时照样应答）。

## 3. 固件与静态分析

| 脚本 | 作用 |
|---|---|
| `re-hx-elf.sh` | 把 `amss.bin` 的 `e_machine` 改成 164（EM_HEXAGON）→ `llvm-objdump --triple=hexagon --mcpu=hexagonv66` 全量反汇编 → 按常量（字符串地址）grep 引用。用法 `re-hx-elf.sh 160bb` |
| `re-hx-dump.sh` | 按 vaddr 区间从反汇编结果里导出代码 |
| `crc-amss.py` | 算固件的 size / crc32 / 前缀 512 KiB crc32（与 star 板级表对账用） |
| `fwswap.sh` | 换 `userland/root/fw/amss.bin` 并重打 `root.apfs`（做"镜像真伪"实验用，见 `docs/03-next-steps.md` P1） |

反汇编的前置：LLVM ≥ 15 且注册了 hexagon target（`llvm-objdump --triple=hexagon` 不报 unknown target）。
验证方式：`llvm-objdump -d --triple=hexagon` 一个 5 MB 镜像应该产出 ~795k 行且 stderr 为空。

## 4. 这些脚本**不**负责的事

- 不负责装工具链（见 HakiOS 上游的 `xnu-deps/setup.sh`）
- 不负责把镜像刷进 `boot_b`（那是 `fastboot flash boot_b` + `--set-active=b`）
- 不负责设备救砖（长按电源 20 s 是唯一手段）
