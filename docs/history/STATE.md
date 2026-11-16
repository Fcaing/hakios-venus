# venus (小米 11, M2011K2C) iOS 16.5 — 当前状态

更新时间：2026-11-06 10:50

## 2026-11-06 14:05 ath11k hw1.0: the SteamOS-ARM SM8350 tree already solved it

The REDMAGIC 6 (Nubia NX669J) is SM8350 + the same QCA6490, and it runs mainline Linux 7.1.2
with ath11k. Two of its patches answer our open question:

    external-and-mods/kernel-sm8350/patches/0008-wifi-ath11k-pci-accept-QCA6490-1.1-as-WCN6855-hw2.1.patch

        +        case 1:
        +            /* QCA6490 1.1, as in SM8350 phones (REDMAGIC 6): the downstream driver
        +               runs it with the same firmware (WLAN.HSP.1.1, amss.bin) as WCN6855 2.1. */
        +            if (soc_hw_version_minor != 0x10)
        +                goto unsupported_wcn6855_soc;
        +            ab->hw_rev = ATH11K_HW_WCN6855_HW21;
        +            break;

- Our chip reads TCSR_SOC_HW_VERSION 0x400c0110, that is major 1, minor 0x10 -- exactly the
  case above. `ATH11K_HW_WCN6855_HW21` already exists in the source we have
  (`ath11k/pci.c:1056`, `ath11k/core.c:490`), so there is no HAL table to write: the whole
  "ath11k major 1" risk is a ten line patch.
- Their firmware layout, from scripts/extract-nx669j-firmware.sh: `ath11k/WCN6855/hw2.1/`
  holds `amss.bin` + `m3.bin` + `regdb.bin`; `hw2.0` takes `amss20.bin` renamed to amss.bin.
  That is the layout our `venus-recon/fw-wifi/` copies belong in.
- `board-2.bin` is "built on the device, it needs the chip's board id" -- it is made from the
  `bdwlan.*` files (we have 147 of them) and the board id the chip reports. So the board file is
  a runtime step, not a missing download.
- Two more of their patches are relevant: 0009 adds an `ath11k.mac_addr` module parameter (no
  calibration data needed to get an address), 0014 keeps the SM8350 PCIe GDSCs in retention
  during suspend.

Copies of all five files are in `venus-recon/ref-steamos/`.

## 2026-11-06 13:45 p63: RPMh votes work, the rails are the next step

The kernel voted the RSC for the first time, and every vote completed:

    pcie: 2:   the root's rails: ldob6 1200 mV, then ldob5 880 mV (RPMh)
    pcie: rsc: ldob6 1200 mV: done 1 idle 1 (address 0x00041900)
    pcie: rsc: ldob5  880 mV: done 1 idle 1 (address 0x00040d00)
    pcie: 2:   rails voted (ldob6 ok, ldob5 ok)
    pcie: 4:   smpb10 1800 mV: done 1 idle 1 (address 0x00040900)
    pcie: rsc: ldoe7: no RPMh address in the command DB (0x00000000)
    pcie: 4:   the radio's rails are not there: stopping here

- The cmd-db lookup works (ldob5/ldob6/smpb10 all resolved), the TCS transaction works
  (`done 1 idle 1`), and a vote the DB does not carry is the only thing that stopped the
  sequence.
- The rest of the chain is unchanged and green: GDSCR 0xf822f000, PARF ready, votes
  0x00ec0d7f/0x023c203f, clkref 1, aux 0x220, pipe mux 0, the PHY's PCS 0x86.
- fix88.py: `radio_rails()` now prints every rail's address and skips the ones the command DB
  does not carry (the antenna switch is often left out), and `cmddb_address()` bends the entry
  base correctly (`base + 144 + header_offset`, as `cmddb_dump()` did).
- The system booted normally throughout (init, the data volume, the battery, ADSP), so none of
  this is in the way of a working phone.

Next: build p64 with fix88 and run it; the six rails' addresses will be printed, then come
stage 12 (iATU/BAR), 13-15 (SMMU, BDF->SID 0x1c01), 17-19 (BHI, MHI, BHIE), 20-21 (IPCR, QMI).

## 交接（下一次开工先看这个）
- **新会话从这里开始：`venus-recon\NEXT-SESSION.md`**（一页启动包：现状、立即要做的第一步、环境、硬约束、数值速查、文件地图）
- 上一轮精确交接：`venus-recon\HANDOVER-2026-11-06.md`（PCIe RC 全绿、EP 缺电、cmd-db 已读出、第 1/2 步的精确做法、10 条坑、开发流程）
- 全景与工期：`venus-recon\PROGRESS-2026-11-06.md`
- 更早的一轮：`venus-recon\HANDOVER-2026-11-05.md`

下面这份 STATE.md 是更长的历史记录（p4–p64 的每次实验都在里面）。

## 每次开工必做
1. `powershell -NoProfile -ExecutionPolicy Bypass -File venus-recon\check-freeze.ps1` → 必须 `THAWED`；`FROZEN` 就停下告诉用户。
2. 读本文件。
3. 先确认手机在哪：`adb devices` / `fastboot getvar product`。
   - `product: venus` = ABL fastboot（可切槽、可 `fastboot boot`）
   - `product: xiaomi-venus` = U-Boot 的 fastboot
   - `product: xnuloader` = loader（可 `oem stop/stage/run/dump`，**不能切槽**）
   - adb 有设备 = Android（root 可用 `su -c`）；都没有 = iOS 在跑（内核对 USB 独占）

## 双系统
- `boot_a` = Android（HyperOS，ReSukiSU root，`su -c` 可用）
- `boot_b` = iOS 16.5（触摸可用、GPU 加速、电量显示、数据卷持久）
- 切换：ABL 里 `fastboot --set-active=a|b` 然后 `fastboot reboot`
- **loader 的 fastboot 不支持切槽**（会回 `Device does not support slots`）
- 2026-11-05 05:5x 起 `boot_b` = `img-ic12.bin`（U-Boot + payload，`root_apfs=ufs_darwin` + `var_hfs=ufs_darwin_data`，没有 `loader_return_after`），已 `--set-active=b` 并 `fastboot reboot` 冷启动过一次：150 s 后 adb / fastboot 都没有设备（= 内核接管了 USB，不是 Android）。要看屏幕得靠人眼；回到 Android 用 `fastboot --set-active=a`。

## 写 boot_b 的可靠方法（重要）
loader 的 `oem write` 现在会报 `FAILED (remote: 'length must be 1..the size staged')`（`loader.c:4094` 比较 `resident_rd_size`，在 `oem ramdisk`+`stage` 路径下它是 0）。
→ **改用 Android root dd**：
```
adb push img.bin /data/local/tmp/x.img
adb shell su -c 'dd if=/data/local/tmp/x.img of=/dev/block/by-name/boot_b bs=4096 conv=fsync'
adb reboot bootloader
fastboot --set-active=b            # 只能在 ABL 里
fastboot reboot
```

## 构建（WSL Ubuntu，`/root/hakios`）
- 内核：`cd /root/hakios && make kernel -j1`（**必须 -j1**，-j12 会 clang segfault；exit 2 是预期的 kext symbol-set 检查失败）
- 打完补丁要把 `drivers/**.c` 同步到 `xnu-src/xnu-8796.121.2/bsd/dev/`，否则编的是旧文件
- userland：`cd userland && DARWIN_JOBS="configd accountsd profiled installd mobileassetd secd trustd" ADSP=1 GL=1 CRYPTEXES=flash FLASHBOOT=1 bash build.sh`
- 镜像：`python3 xnuloader/mkpayload.py -o out/p.bin kernel=hakios-kernel ramdisk=userland/root.apfs resident=userland/flashboot.apfs --cmdline "..."` → `python3 tools/mkubootimg.py -d venus -u /root/hakios/build-venus-wr/u-boot.bin -p out/p.bin --install -o out/img.bin` → 补零到 4096 对齐
- 当前 boot_b 的 cmdline（`img-ic12.bin`）：`root_apfs=ufs_darwin ufs=2 ufs_native=1 ufs_write=1 var_hfs=ufs_darwin_data bootcpu=7 cpus=8 cpufreq=1 touchscreen=1 buttons=1 gpu=1 gl=1 sb_delay=45 fbwidth=1440 fbheight=3200 debug=0x8`
  （`loader_return_after=200` 只在抓日志的测试 payload 里加，常驻镜像不要带；`sb_delay=45` 让 lsctl 先注完册再让 SpringBoard 排版）

## 已打通
- 触摸（ST FingerTip / FTS，SPI 0xa8c000，IRQ GPIO23，reset GPIO22，AVDD GPIO132）
- GPU（`GPU_CHIP_ID` 必须报 `0x060600ff`（a660），否则 Mesa 按 a7xx 方言打包 → CP 卡死）
- 电量（DSP battmgr；必须去掉 `battery=1`，否则 `battmgr_start()` 提前返回）
- ADSP 固件跑通（`ADSP_MEMORY 0x87300000`, size 0x3900000, mdt 头允许 64 KB / 64 段）
- 数据卷持久化（HFS+，darwin block 2,042,368 起）

## 已解决：主屏只有 3 个图标（2026-11-05）
**根因**：32 个「首发 app」（Books / Calculator / FaceTime / Maps / Music / Notes / Weather …）在 `sysimage/rootfs/private/var/staged_system_apps` 里，`userland/src/init.c:210-248` 只为它们在 `/flash/Applications` 建 **APFS synthetic dir**（`kern.apfs_synthetic`，`/flash/Applications/Books.app=/flash/private/var/staged_system_apps/Books.app`）。内核层 lookup 能走通，但 **LaunchServices 不登记**它们：数据卷上 `/containers/Shared/SystemGroup/8CCE1BBB-…/Library/Caches/com.apple.lsdidentifiers.plist` 的 157 项与 `/Applications` 里的 140 个真 app 对得上，32 个 staged 全 0 命中 → SpringBoard 把默认布局裁到「已注册」的那些，只剩 3~6 个图标。
**修法**：`userland/build.sh:610-618` 构建时把这 32 个 app 直接 `mv` 进 `sysroot/Applications/`（174 项），只删 `staged_system_apps`、**保留空的 `/private/var`**（数据卷挂载点）；`userland/src/init.c` 的 staged 循环改成目录不存在时静默跳过（`bound == apps` 才 check）。改动脚本：`venus-recon\fix1.py`（两文件都有 `.bak`）。
**证据**（2026-11-05 05:1x，flash 根 + 数据卷，payload `p-ic10`，日志 `venus-recon\last-ic10.log`）：
- `[ ok ] mount the Darwin volume read only`、`/private/var: HFS Plus from /dev/ufs_darwin_data, kept between boots`、`[ ok ] create the directories of the data volume`、`=== 45 checks, 4 failed ===`
- 主屏两页完整：第一页 17 项（2 个 widget 堆 + FaceTime / Calendar / Photos / Mail / Notes / Reminders / Clock / News / TV / Podcasts / App Store / Maps / Health / Wallet / Settings），第二页 18 项（Weather … Utilities 文件夹 … Xcode Previews），Dock 4 个（Phone / Safari / Messages / **Music**）——与 `SpringBoard.app/DefaultIconState.plist` 完全一致
- 运行期写的确实是数据卷：`/mobile/Library/SpringBoard/IconState.plist` 2764 B → **3728 B**，卷内条目 6340 → 6538（`venus-recon\dv.img` 与 `dv2.img` 对比，脚本 `ls-reg.py` / `sb-layout.py`）
- 截图：`venus-recon\ic103.png`（第二页，flash 根）、`ic94.png`（第一页，RAM 根）

### 已知不致命的 4 个 FAIL（ic10 行 924-934）
- `synthetic directory /flash/redwood: File exists` → `[FAIL] a synthetic /redwood on it, for this image`：我们的镜像里本来就有 `/redwood`
- `/fw` 同样（`[FAIL] the firmware on /fw`）
- `the OS cryptex from /dev/ufs_darwin,c=1: Invalid argument`（c=2 同）：OS/App cryptex 是 Apple 容器的第 1、2 号卷，我们的单卷镜像没有
另：switch_root 之后第二次 init（行 1450 起）`mount /dev/ufs_darwin` 失败、且 `/private/var` 因 `Resource busy` 回退成 ramfs（`=== 37 checks, 1 failed ===`）——布局写盘证明第一次 init 的 HFS+ 挂载有效，图标问题不受影响，但这条要单独查。

## 已解决：设置 › 应用列表里的黑块（2026-11-05）
**现象**：设置根页滚到底的「应用列表」里，一部分行画成纯黑圆角块（左边图标方块 + 右边名字长条），滚一下就恢复。
**不是字体**：设置根页其它文字全正常（数据卷里 SplashBoard 快照 `snap-prefs-00/01.jpg` 可证）；镜像里 `/System/Library/Fonts` 完整（AppFonts 37 / Core 59 / CoreAddition 22 / CoreUI 26 / LanguageSupport 1 / UnicodeSupport 105 / Watch 6，258 MB），正文是 `CoreUI/SFUI.ttf`，SF Symbols 的 `CoreGlyphs.bundle`（`Assets.car` 178,049,760 B）也在。
**根因**：这些行是「图标 + 名字」的占位（redacted/skeleton）。图标要 iconservicesagent 现生成；真机上它们在安装时由 installd / MobileInstallation 生成好，我们这套系统从没"安装"过这些 app，所以只有 SpringBoard 画过的那些在缓存里。缓存落在数据卷：`/containers/Shared/SystemGroup/systemgroup.com.apple.lsd.iconscache/Library/Caches/com.apple.IconsCache/`，每个 `.isdata` = 24 B 头 + 192×192 BGRA（147,488 B）；2026-11-05 06:0x 时只有 **86 个**（app 约 173 个）。
**修法（已验证）**：把列表完整显示一遍，让图标生成并落盘——缓存跨启动保留，之后一直正常。06:34 用户确认「黑块不在了」。
- 现成 payload：`venus-recon\img-icwarm.bin`（65,314,816 B，sha256 `25675173c4ec3303afcf444f831a74e042bde1a5f85181c1b4201b3ad39a28ff`）。它内置一次性 job `com.hakios.uitest`：等 SpringBoard 起来 → 解锁 → 点设置 → 滚到列表底部 → 回顶部 → 回主屏；`loader_return_after=420`。
- 跑法：`fastboot oem stop`（内核若在跑）→ `powershell -NoProfile -ExecutionPolicy Bypass -File venus-recon\run-ic.ps1 -Tag icwarm -Shots 1 -WaitSeconds 460`。
- 什么时候需要再跑：数据卷被重建/清空（缓存没了）之后；平时用户滚动一次也能补齐。
**排查工具链**（都留在 `venus-recon\`）：`mk-uitest.py` 生成 job plist、`mk-ic.sh TAG "STEPS"` 一步出 payload、`run-ic.ps1` 跑一轮并抓日志与截图（fastboot 会把文件下到进程 cwd，脚本已 `Set-Location $PSScriptRoot`）。
**顺带发现的两个平台问题**（与本次无关）：
- guest 时钟比真实快 2.4–8 倍：同样约 210 s 的真实运行，内核日志末尾时间从 511 s（ic16）到 1652 s（ic20）不等 → `rwtouch wait` 的对准很难，定时器/看门狗也受影响。
- `com.apple.mobileactivationd` 每 10 s 崩一次（`exited due to SIGTRAP | sent by exc handler`，最多连续 20 次），一直刷日志。
**复现证据**：`venus-recon\ic17-3.png`（应用列表原样复现）、`ic18-retry.png`（同页顶部正常）、`crop-a/b/c.png`（用户照片放大，占位是实心圆角块）。
## 写系统镜像到 darwin 根卷（flash 路线）
- flash 上的根卷 = Apple 原版 `rootfs.apfs`，占 darwin 块 0..1374207（5,628,755,968 B）；`tools/darwin-write.py` 的 `PROTECTED = 1374208` 就是保护这一段
- 换根：`adb push userland/system.apfs /data/local/tmp/sys.apfs` → `adb shell su -c 'dd if=/data/local/tmp/sys.apfs of=/dev/block/by-name/darwin bs=4096 count=607327 conv=fsync'`（607327 = 镜像块数；实测 775 M/s、3 s）→ 回读 `dd … count=607327 | sha256sum` 比对
- 回滚：`dd if=work/rootfs.apfs of=/dev/block/by-name/darwin bs=4096 count=1374208 conv=fsync`
- 现状：flash 根 = 修好图标问题后的 `system.apfs`（2,487,611,392 B，sha256 `3c66d01db85d7b8145d13f03c7b912868f2f3ee3aac7eb252aacd6bc7d9a9d81`）；boot_b = `img-ic12.bin`（65,314,816 B，sha256 `ac9fb8350b8d64b150589c015cf411fd3a36cf3c8538ed4ce9bf8e4ef5680a73`，写于 05:5x，`dd count=15946` + 回读校验通过，`fastboot --set-active=b` 已切到 b）

## WiFi 与第三方应用安装（2026-11-05 下午）

### WiFi：现状与结论
- **venus 的内核里没有 WiFi 驱动**：`devices/venus/configs/venus.config:16` `# CONFIG_HAKIOS_QMI is not set`、`:24` `# CONFIG_HAKIOS_WIFI is not set`（`configs/common_defconfig` 里这两个是 `=y`，那是 redwood 的）。`devices/venus/README.md:48` 也把 Wi-Fi 留成未勾选项。
- `drivers/wifi`（`hakios.wifi.c` 193 KB + `wifi/lx/` 的 lx 层 + `hakios.wlan.cpp`）是给 **WCN6750**（POCO X5 Pro / redwood）写的，`requires QMI`，help 里写着 "Needs fw-wifi/ from the phone"，而 **`/root/hakios/fw-wifi/` 不存在**。venus 是 SM8350 + **WCN6855**（ath11k 家族），要另做驱动 + 本机 NV，不是"打开一个开关"。
- 参考包（桌面 `红米k20pro\`，raphael / SM8150 + WCN3990）能做到 WiFi/蜂窝，做法：内核里是 **ath10k 移植**（strings 有 `wifi/lx/ath10k/host.c`、`ath10k/WCN3990/hw1.0/{board,firmware-5}.bin`、`/soc/wifi@18800000`），并在**首次安装时于临时 recovery 里读本机 `modemst1/modemst2/fsg/fsc`** 生成"这台手机专用的无线资源"（`config.json` 的 `wireless_inputs`、`wifi_nv_device_specific: true`、`nv_failure_policy`），资源打在 darwin 的 3 GiB 偏移处（`ios-boot-resources.bin`，magic 是 `RAPHIOS1`；`data_first_block 2042368` / `minimum_darwin_blocks 5242875` 跟我们完全一样，同源工程）。驱动不能直接搬，但"资源容器 + 本机 NV + lx 层移植 ath 驱动"这条路可以照。
- **"设置 › Wi-Fi 打不开"的直接原因还没钉死**：点中该行只高亮、不推入（`icwifi2-3.png`），日志里没有 `WiFiSettings` / `PreferenceBundles` / `MobileWiFi` 字样；`wifid` 每次都 `WiFiManagerCreate: entering` → `exiting`（1–5 s）→ **`PPM Error:No matching driver found`**；`configd` 默认不在 job 列表（见下），已把它带起来仍不推入。`WiFiSettings.bundle` 与 `MobileWiFi.framework` 在镜像里都在。
- `build.sh:101` 的旋钮是 **`JOBS=`**（`DARWIN_JOBS=${JOBS-默认}`），不是 `DARWIN_JOBS=`；默认 21 个 label 里**没有** `com.apple.configd` 与 `com.apple.mobile.installd`。

### 第三方应用安装：已验证到哪一步
- **内核不校验签名**（`xnu/files/libkern/amfi/miniamfi.c` 头注释："no signature policy … a program without a signature holds none"）→ 把 .app 放进镜像的 `/Applications` 就会被 LaunchServices 注册。**已实测**：自编的最小 UIKit 应用 `hello.app`（品红图标）出现在 LS 里：`<LSApplicationProxy … com.hakios.example.hello file:///Applications/hello.app/ <… <installed>>>` ✓
- **程序化启动还没成功**：这个 LaunchServices **没有** `openApplication:withOptions:`（`--list` 打出的 155 个方法里只有 `openURL:`、`installApplication:withOptions:`、`applicationIsInstalled:` 等），SpringBoardServices 的 `SBSLaunchApplicationWithIdentifier` 返回 **11**（解锁后仍是 11）。下一步试"直接点图标"或 `installApplication:withOptions:`。
- App Store / 爱思 / Sileo / 巨魔**全都要网络**（爱思那条是 `127.0.0.1:27015` 的 usbmux，K20 Pro 包里 `computer_link.py` 的做法），venus 现在无网 → 现实路径是**离线侧载**（.app 进 `/Applications`，或把 .ipa 塞进 payload 再解包）。
- 现成工具：`userland/build.sh` 的 `APPBUNDLE=` 钩子（把 .app 拷进 `sysroot/Applications`）、`venus-recon\mk-ram.sh TAG "PROGRAM ARGS"`（造 RAM 根 payload）、`venus-recon\mk-job.py`（一次性 job，stdout/stderr → `/dev/console`）、`venus-recon\openprefs.m`（dlopen CoreServices/SpringBoardServices 后调 LS/SBS；`--list` 列方法）。

### 跑测试的硬约束（血泪）
- payload 里**不能带 `resident=`**：否则 loader 把 flashboot.apfs 当根（md0），`oem ramdisk` 后 stage 的 2.4 GB 系统镜像被忽略，10 s 就 `returned 128376`、`/sbin/launchd.darwin: No such file or directory`。
- guest 时钟比真实快 2.4–8 倍，`rwtouch wait` 不可靠；截屏里控制台字会盖住下半屏。
- `userland/src/rwtouch.c` 已改为**首次发事件才开** `/dev/hakios-touch`（否则 backboardd 晚开设备时点击全丢）。
- **构建进行中不要改 build.sh**（bash 边读边执行，会报 `line 659: has: command not found`）。
- 图标缓存：设置列表首次滚动会现生成图标（`.isdata`，24 B 头 + 192×192 BGRA），存在数据卷 `containers/Shared/SystemGroup/systemgroup.com.apple.lsd.iconscache/.../IconsCache/` 里，跨启动保留；没热过的列表会出现黑块（已解决，见上节）。

## 2026-11-05 09:05 boot_b 刷入的版本（今天实测可用的全部）

`venus-recon\img-final.bin`，65,327,104 B = 15,949 块，
sha256 `12e93768c0b80fab5091b7e91c7d63c100c7e59399c148d6d5936b8b79b2e031`，
用 `fastboot flash boot_b img-final.bin` 写入（slot 已是 b）。**已被 09:25 的 img-final2.bin、再被 09:35 的 img-final3.bin（= final2 + `adsp=1 pmic=1`）取代。**

cmdline：

```
root_apfs=ufs_darwin ufs=2 ufs_native=1 ufs_write=1 var_hfs=ufs_darwin_data bootcpu=7 cpus=8
cpufreq=1 touchscreen=1 buttons=1 gpu=1 gl=1 sb_delay=45 fbwidth=1440 fbheight=3200 debug=0x8
```

（不带宽 `loader_return_after`：这是给真开机用的，不是抓日志的。）

里面包含、且今天在设备上实测可用的：

- 触摸：`rwtouch` 改成第一次发事件时才开 `/dev/hakios-touch`（原来开机就开会撞上 backboardd 还没开设备，点击全丢）；主屏点图标能启动 app。
- GPU：`gpu=1 gl=1`，adreno 起得来、SpringBoard 能画（今天所有截图都是它画的）。
- 电源按键：`buttons=1`，长按锁屏/唤醒可用。
- 电量百分比：状态栏与设置里的电量显示正常（`battery` 相关驱动 + `BatteryCenter` 的 QG 读数）。
- 图标：32 个 staged app 现在都在 `/Applications`（`system.apfs` 里 174 项），主屏是完整的两页默认布局；图标缓存已经预热进数据卷（`IconsCache` 89 个 `.isdata`）。
- daemon：默认 21 个 job + `com.apple.configd` + `com.apple.mobile.installd`（这两个之前一直缺，日志里 `failed lookup` 里最常见的就是它们）。
- 第三方应用：`/Applications` 的 union 挂载 + `init` 的 `/install` 安装器（见下节）；数据卷里已经装了一个测试用的 `hello2.app`（青色图标，`com.hakios.example.hello2`）。

### 离线侧载（今天跑通，等 IPA 进来用）

- `venus-recon\mk-install.sh TAG <ipa 或 .app>`：解包 `Payload/*.app` → 构建 root.apfs（app 放进 `/install`）→ 出 `p-TAG.bin`。
- 跑一次 `ic9-run.ps1 -Tag TAG -Payload p-TAG.bin -Ramdisk system-hello.apfs`：init 会把 `/install` 里的 app 复制到 `/private/var/Applications`，再 union 到只读的 `/Applications`，LaunchServices 开机扫描时注册 → 图标出现在主屏，点开即用；装过的 app 留在数据卷里，跨启动保留。
- 实测证据（`last-install2.log`）：`  installed hello2.app, 4 files` / ` 1 application installed from the payload` / `[ ok ] the installed applications over the system's own` / `=== 37 checks, 0 failed ===`。
- 待装：`C:\Users\Administrator\Desktop\抖音_41.0.0（正版）.ipa`（用户放的）——下次开工先 `bash mk-install.sh douyin "/mnt/c/Users/Administrator/Desktop/抖音_41.0.0（正版）.ipa"`，再刷 boot_b 并开机一次即可。

## 2026-11-05 09:25 事故与回退：**不要在 /Applications 上用 bindfs union**

- 09:05 刷进 boot_b 的 `img-final.bin` 里带了「离线侧载」的第二半：init 在挂好数据卷之后
  `mount("bindfs", "/Applications", MNT_RDONLY | MNT_UNION, "/private/var/Applications")`，
  想把数据卷里装的 app 叠到只读的 /Applications 上。
- **后果：开机后主屏一个图标都没有**（/Applications 在被挂空目录覆盖后对 LaunchServices 就是空的）。
  这条 union 路径以前从没在本机跑过（`/jb-bin` 的 union 只在带 jb 的构建里才走），是未验证代码。
- 处理：`init.c` 回退到 `init.c.bak6`（`install_apps` 与 union 挂载全部撤掉，`grep -c install_apps` = 0），
  重建 root.apfs（6500 块）→ `mk-slot.sh final2` → **`venus-recon\img-final2.bin`，65,327,104 B = 15,949 块，
  sha256 `f85012f0b9c4dd1f52d6aa2b26bcc15a0f6025948c7b50886f0677ec734bf2d1`**，刷入 boot_b 并开机 → 图标恢复 ✓。
- 结论：**离线侧载的「装到数据卷 + union 展示」这条路在本内核上不可用**（至少现在）。
  已验证可用的只有：把 .app 直接放进系统镜像的 /Applications（`APPBUNDLE` 钩子），LS 会注册、主屏有图标、点开能启动。
  要恢复「运行时装 app」，得换机制（例如逐个 app 建 synthetic dir 到数据卷，或把 union 先在 RAM 启动里验证清楚再上真机）。
- **电量百分比的回归也查清了：是我的 cmdline 漏了 `adsp=1`。** 电池读数来自 ADSP 上的电池管理器
  （`hakios.adsp.c` 的 `battmgr_start()`，由 ADSP 启动路径在 `:3249` 调用），没有 `adsp=1` 时 DSP 不启动，
  `battmgr` 不跑，`hakios_battery_report()` 就没人喂 → 状态栏没有百分比。`battery=1` 一定不能加：
  它把电池交给 loader 的 UEFI charger 驱动，DSP 那条路反而关掉。
  `venus-recon\mk-slot.sh` 的 cmdline 已固定成 `… var_hfs=ufs_darwin_data adsp=1 pmic=1 …`（并写了注释）。
- 修好后的镜像：**`venus-recon\img-final3.bin`，65,327,104 B = 15,949 块，
  sha256 `c9b6126806c82395aae7be6dd3853ba477ddfc12efe2c9ff7fb6cf3fad84acc0`**，
  `fastboot flash boot_b` 写入并开机 → 图标、电量百分比都正常（用户确认）。
  它 = `img-final2.bin` + cmdline 里的 `adsp=1 pmic=1`，其余内容（触摸修复、GPU、电源键、configd/installd job）不变。

### ath11k 预编译的进度（2026-11-05 09:20 用户叫停）

- ash tools/mk-ath11k.sh 停在**解包阶段**（用户取消）：两个源码包已缓存在 xnu-deps/build/ath11k/
  （linux-7.0.14.tar.xz 157 MB、reebsd-15.1-src.txz 92.7 MB），src/ 已建，**0 个 .o**。
- 重跑不会重新下载，直接进编译；真正开工时应先做 PCIe 阶段 1（读完 config space 再谈 ath11k 的传输层）。

## 当前卡点/下一步

- 现在：实验暂停，boot_b 已是 `img-final.bin`（上一节），手机在 iOS 里。
- 第三方应用：离线侧载链路已通，只剩把用户的 IPA 装进去（`mk-install.sh douyin ...` → 跑一次 payload）。
- WiFi：真无线只有 PCIe 一条路——QCA6490（WCN6855）挂在 `pcie@1c00000`（ECAM 1 MB @ 0x60100000，PHY 序列在 DT 里约 120 条写），
  而内核里一个 PCIe 都没有。阶段 1 是写最小 PCIe RC（时钟/复位/供电/PHY 序列/链路训练 → 读到 config space 的 vendor/device），
  2–4 天可以判定成败；阶段 2 才轮到 `ath11k_pci`（`tools/mk-ath11k.sh` 已经把 Linux 7.0.14 的 ath11k 与 FreeBSD 的 LinuxKPI 拉下来编）；
  阶段 3 是把 `wlan` 接口交给 wifid/configd（`drivers/net/hakios.net.c` 的 en0 已就位，缺的是链路）。
- 设置 › Wi-Fi 页面打不开：不是缺文件（`WiFiSettings.bundle` 与 `MobileWiFi.framework` 都在），是面板在等没有的驱动/服务；WiFi 起来后自然好。
- 平台小毛病：guest 时钟比真实快 2.4–8 倍（`rwtouch wait` 不可靠）；`mobileactivationd` 每 10 s SIGTRAP 一次（不致命）。
- 回滚：`work/rootfs.apfs`（5,628,755,968 B）写回 darwin 块 0..1374207 就回到 Apple 的根卷；boot_b 回到任意旧镜像用 `fastboot flash boot_b`。

## 其它待办
音量键（HID 路线系统不认、AVSystemController 会崩 SpringBoard）、CS35L41 扬声器、蓝牙、WiFi（WCN6855 vs 驱动 WCN6750）、蜂窝数据、应用安装。

## 设备备份
`venus-recon\backup-venus\` 58 个分区（857 MiB，FNV 全对），可回退。

## PCIe / WiFi 移植：第一次上机（2026-11-05 傍晚）

Wi-Fi 是 QCA6490（=WCN6855），挂在 PCIe0 上：Android 侧 `0000:00:00.0` 是根端口（17cb:010c，class 0x060400），`0000:01:00.0` 是 Wi-Fi（**17cb:1103**，即 ath11k_pci 的 id）。venus 的 DT 也这么写（`soc/qcom,cnss-qca6490@b0000000`、`pcie@1c00000/pcie0_rp/cnss_pci`）。

驱动：`drivers/pcie/hakios.pcie.c`（`CONFIG_HAKIOS_PCIE=y`，入口 `hakios_pcie_init()` 在 `drivers/input/hakios.input.c` 的启动序列里），boot-arg `pcie=1`、`pcie_step=N`、`pcie_fine=1`（每次访问前停一下）、`pcie_pause=MS`、`pcie_watch=S`。生成的头 `drivers/pcie/venus.pcie.h` 里有厂商的 75 条 PHY 序列（由 `venus-recon/pcie-phy-seq.py` 从设备树生成，别手改）。

两次事故，都已定位：

1. GCC 映射只给了 0x20000，而 PCIe 的分支时钟在 0x6b028 —— 越界读 → panic（日志里有 stackshot）。改成 0x1f0000（整个 clock controller）。
2. 映射对了之后，**读 CBCR 直接挂死**：读取它时 GDSC（`0x6b004`，PCIe 的电源域开关）还是 collapsed，那个电源域里的寄存器不答。挂死后 SoC 复位，ABL 从 b 槽启动 iOS。因此步骤顺序改成：**先只读 GCC 常开寄存器，再开电源域，最后才读控制器**。

关键数值（都来自 gcc-sm8350.c / pcie-qcom.c / phy-qcom-qmp-pcie.c / 厂商 DT）：

| 用途 | 寄存器 | 值 |
|---|---|---|
| 电源域开关 | GCC `0x6b004` | 清 bit0 = 开，轮询 bit31 = 已开（预算 2 ms） |
| 分支时钟投票 0 | GCC `0x52000` | bits 11 aggre1、12 aggre0、18 tbu、19 ddrss_sf_tbu、22 phy_rchng |
| 分支时钟投票 1 | GCC `0x52008` | bits 0 slv_axi、1 mstr_axi、2 cfg_ahb、3 aux、5 slv_q2a |
| 参考时钟 | GCC `0x8c004` | bit0 |
| 控制器复位 | GCC `0x6b000` | 置位 = assert，清 = 释放；Linux 各等 1–1.5 ms |
| PHY 复位 | GCC `0x6c01c` | 同上 |
| 链路状态 | PARF `0x1b0` | LTSSM，state 0x1e = L0 |
| PHY 状态 | PHY `0x214` | bit6 **清零** = PLL 起来（Linux 就是这么等） |
| PHY 电源/启动 | PHY `0x240` / `0x244` | 厂商序列已含这两处写，别叠加两套序列 |
| PERST# | TLMM pin 94 | 高 = 放行 |

固件已备好：`venus-recon\fw-wifi\`（`amss.bin` 5,236,304 B、`m3.bin` 266,684 B、`regdb.bin` 24,278 B、`bdwlan.e01…e27` 147 个，来自手机的 `/vendor/firmware_mnt/image`）。ath11k 要的 **`board-2.bin` 不在里面**（Android 的 cnss 用 bdwlan.eXX），到时候要从这些板文件合成。ath11k 的 Linux 源码对象可用 `tools/mk-ath11k.sh` 编（上次被叫停，停在解包）。

下一步：`p-p2.bin`（step 1：只读常开寄存器）、`p-p3.bin`（step 2：开电源域/时钟/复位并读控制器）都已生成；手机回到 fastboot 后先跑 p2，确认 GDSCR 的值和投票寄存器的值，再跑 p3。成功判据：`pcie: 2: ID 0x000 = 0x00001103`（或至少 LTSSM 有非零状态、config space 不是 0xffffffff）。

## PCIe 阶梯实验（2026-11-05 傍晚，p4–p9）

`drivers/pcie/hakios.pcie.c` 的 step 2 现在是一把六级的梯子（boot arg `pcie_go=N`）：

| 级 | 做什么 | 结果 |
|----|--------|------|
| 1 | 只读 GCC 常开寄存器（投票 0x52000/0x52008、GDSCR 0x6b004、clkref 0x8c004、CBCR 0x6b028） | 安全，p4 已跑通 |
| 2 | 投票九个分支时钟（0x52008 \|= 0x0000002f，0x52000 \|= 0x004c0c00） | 安全（p6/p9） |
| 3 | 打开参考时钟 gcc_pcie_0_clkref_en（0x8c004 bit0） | 安全，**值能读回 0x00000001**（p6 日志） |
| 4 | 端口复位 GCC_PCIE_0_BCR 0x6b000 / PHY_BCR 0x6c01c | **危险**：p6（含写）整颗 SoC 挂死；p9 只读时在内核里 data abort 并 panic |
| 5 | 放开 collapse vote（0x152128）并合上 GDSCR | 未试 |
| 6 | 读控制器自己的寄存器（PARF/PHY/DBI） | 未试 |

已经确认的寄存器状态（OS 交过来时）：

- `GDSCR 0x6b004 = 0x0022f001`：bit0=1（SW_COLLAPSE，域是关的）、bit31=0（没电）。投票与 clkref 之后**仍然是 0x0022f001**。
- `0x52000 = 0x00e0057f`、`0x52008 = 0x023c2000`：PCIe 的九个分支一个都没投。
- `0x8c004 = 0x80000000`（bit0=0 未使能）；写入 bit0 后读回 `0x00000001`。
- CBCR：slv_axi/mstr_axi/aux `0x80000220`、cfg_ahb `0x80000000`、slv_q2a `0x80000000`、phy_rchng `0x00000000`、aggre0 `0x80000000`、aggre1 `0x00000000`、tbu `0x80004220`、ddrss_sf_tbu `0x00100000`（bit31=1 表示"关"）。

今天得到的两条关键教训：

1. **写 GCC 里与 PCIe 端口有关的寄存器（复位/电源开关），在供电没起来之前会把整颗 SoC 拖死**——p6 只写到第 4 级就再没有日志，loader 连 `THE KERNEL HUNG` 都来不及打。
2. **`0x152128`（厂商 DT 的 `qcom,collapse-vote`）读一下就 data abort**（p9 panic，`fault_code=0x10`，寄存器 x9 = 0x152128）→ 这个寄存器在正常世界里是 TrustZone 管的，不能直接碰。

推论与下一步：电源域要合上，得先有供电（厂商 DT 的 `vreg-0p9` = PM8350 LDO5 `ldob5` 0.88 V、`vreg-1p8` = LDO6 `ldob6` 1.2 V、`vreg-cx` = CX rail，另外 cnss 还有 PMR735A LDO7 2.8 V）。Linux 是通过 RPMh 投票；本内核没有 RPMh，但**有 SPMI/PMIC arbiter**（p9 日志里 `pmic: PMIC arbiter version 0x50020000, 512 channels` 就是它在说话），所以可以考虑直接写 PMIC 的 LDO 寄存器把这三路电拉起来，再回头合 GDSC。

另外：`logdump` 分区现在是唯一可靠的取证手段（`venus-recon\read-logdump.ps1 -BootLoader`，长度按十六进制传）；`getvar result` 收不到并不代表内核挂了（p4/p5 都正常起完了）。

### ????PCIe ????? ??????

1. **??????**???? Android ??
   `su -c 'cat /sys/kernel/debug/regulator/regulator_summary'`?
   `su -c 'ls /sys/bus/pci/devices/0000:01:00.0'`?
   `su -c 'cat /sys/bus/pci/devices/0000:01:00.0/power/runtime_status'`?
   ? PCIe ??? regulator?`vdda`?`vddpe-3v3`?`vdda-phy`?`vdda-pll`?cx ? corner???????enable ?????????"???????????"????
2. ??????? OS ????????**??**?????
   a. ???? SPMI ?????`spmi_write()`?core ?? `0x0c440000 + 0x10000*apid`?`CMD 0x00` / `STATUS 0x08` / `WDATA0 0x10`?v5 ? `pmic_arb_fmt_cmd_v1` ??????? v5 ???? apid ? write-EE ???????
   b. ? loader?U-Boot?????? RPMh regulator?`CONFIG_DM_REGULATOR_QCOM_RPMH=y`?`CONFIG_CMD_REGULATOR=y`???? `oem rails` ?????????????????? RPMh ???
3. ?????????GDSCR ?? ? ?????`0x6b000`/`0x6c01c`?**???????**?? PHY 75 ??? ? PERST?TLMM pin 94?? ? config space ? `17cb:1103`?

### ?????? PMIC ??????2026-11-05 19:30????????

`drivers/power/hakios.pmic.c` ???????????? observer ??????? core ????

- core ?? `0x0c440000`??? apid ?? `0x10000 * apid`?`CMD +0x00`?`STATUS +0x08`?`WDATA0 +0x10`?`WDATA1 +0x14`
  ??? Linux `pmic_arb_write_cmd_unlocked()` ? `pmic_arb_offset_v5()` ? `PMIC_ARB_CHANNEL_RW` ????
- ???? `pmic_arb_fmt_cmd_v1()`?`(0x40 << 27) | (reg << 4) | (count - 1)`?????????????
- ?????boot args????????????`pmic=1 pmic_poke=1 pmic_slave=N pmic_usid=0xNN pmic_reg=0xNN pmic_value=0xNN`
  ? ?????????????? `pmic: poke: slave ? register ? <- ?` / `before` / `after`?
- ?????????????????**?????**???????? type ??? 0x04????????????
  ????? v5 ? write-EE ?????? `denied`?`spmi_write()` ?????????

??????Android ???? regulator ?????/??/enable ???? ? poke ?? PM8350 LDO5/LDO6 ? CX
? ?? PCIe ??? level 5?GDSCR???? level 6?? 17cb:1103 ? config space??

## PCIe 供电域已打通（2026-11-05 20:30 之后）

- **关键一步**：清 `GCC GDSCR 0x6b004` 的 bit0（SW_COLLAPSE）后，**一次 100 µs 轮询**就等到 bit31=1：
  `GDSCR 0x0022f001 -> 0xf822f000（域已上电）`。所以不需要 TrustZone 帮忙，也不需要 `0x152128` 那个
  collapse-vote（它受 TZ 保护，读会 data abort——p9 就是这么 panic 的，别碰）。
- **寄存器读数**（`pcie=1 pcie_step=2 pcie_power=1 pcie_after=1`，域上电后）：
  `PARF SYS_CTRL 0x00 = 0x2000361c`、`PHY_CTRL 0x40 = 0x00000900`、`REFCLK 0x4c = 0x00001019`、
  `CONFIG_BITS 0x50 = 0`、`DEVICE_TYPE 0x1000 = 0`。
- **教训：顺序**。GDSC 折叠时去读域内寄存器（BCR 0x6b000 / 0x6c01c）会挂住整颗 SoC（p6）；
  正确顺序是「清 SW_COLLAPSE → 轮询 bit31 → 投票分支时钟 → 开 clkref → 再碰 PARF/PHY/DBI」。
- **PMIC**：PM8350 的 LDO5 = usid `0x8c00`、LDO6 = `0x8d00`（SPMI slave 1）。开机时这两个
  LDO 的使能位（寄存器 0x46 bit7）**已经是 1**（ABL/Android 留下），电压寄存器 0x41 读回 0
  （电压由 RPMh/RSC 走另一条路径设定，SPMI 本地视图看不到）。CX 是 `pm8350c_s6_level`，只由
  RPMh corner 控制。
- **观测手段**：
  - 内核运行期间 loader 仍可能响应 fastboot：`getvar result` → `running`，`oem log` + `get_staged`
    取当前内核环形日志，`oem stop` 提前结束。
  - loader 只在**开机头 24 秒**每 2 秒把日志写进 `logdump` 分区（`NOTE_SECONDS`）；正常返回时还会
    再写一次（要求存储控制器已交还）。所以阶梯实验必须把要看的输出压进 24 秒内——
    `pcie_no1=1` 可跳过 step 1 的五次慢读（省 22 秒）。
  - `logdump` 分区在 Android 上是 `/dev/block/sda24`，`su -c dd` 即可读；但**有时会被清成全零**（原因未明），
    读不到内容不代表没跑。
- **驱动当前状态**（`drivers/pcie/hakios.pcie.c`）：boot args `pcie=`、`pcie_step=`、`pcie_power=1`
  （只上电）、`pcie_after=1`（上电+投票+clkref 后读控制器/PHY/DBI）、`pcie_reset=1`（才写 BCR）、
  `pcie_vote=1`（才写 0x152128，危险）、`pcie_no1=1`、`pcie_fine=`/`pcie_pause=`。
- 下一步：把 PARF/PHY/DBI 的读数拿到（p14），然后 step 3 的 75 条厂商 PHY 序列 → PCS 状态轮询
  → PERST(pin 94) → 读 ECAM 期待 `17cb:1103`。


### 更正（用户 21:06）
「设置 › Wi-Fi」页面**本来就能打开**（我之前把"行高亮但没推入"当成了页面打不开，那是 icwifi2 那一轮的时序问题）。
真正的症状是：页面打开、显示 Wi-Fi **关闭**，**点开关毫无反应**。

原因（按已有日志推断）：开关走 MobileWiFi → 与 wifid 的 XPC → wifid 再要求驱动（Apple80211）给一个接口；
而我们没有任何 wlan 接口对象，wifid 在 `WiFiManagerCreate: entering → exiting`（1.3 s）后就以
`PPM Error:No matching driver found` 收场，于是 set-power 找不到执行者，开关点了等于没点。

两条路：
- **A（快，但无实用价值）**：写一个「假驱动」——发布一个 Apple80211 接口对象，能报"已开机、扫描为空"。
  开关就会动，页面显示"Wi-Fi 已打开、没有网络"，真驱动以后替换它。代价：要猜 wifid 期望的属性集，约半天到一天。
- **B（真正的路）**：PCIe → MHI → ath11k_pci → 固件 → wifid 看到真接口。按现有记录推进，周期以周计。

## 2026-11-05 22:25 本轮收尾（p21–p23、sysctl 报告链、交接）

- **PCIe 阶梯的实测结论**（详见 HANDOVER §2.5）：step 1 读 GCC 安全；写 GDSCR（清 bit0）→ 域上电 ✅；
  写 votes/clkref → 时钟在跑 ✅；**写 BCR（0x6b000/0x6c01c）会整颗 SoC 死**；**读 `0x152128` 会 data abort（TZ）**；
  `pcie_after=1`（先投票再读 PARF）不崩（36 checks 0 failed）；DBI(0x60000000)/ECAM(0x60100000)/PHY 读在链路 down 时可疑。
- **内核日志这条路走不通**：loader 只在前 24 秒、每 2 秒把日志写进 logdump 分区，且需要 UEFI 还持有存储；
  ring 只留最新 ~1 MB。p17–p20 的四种办法都只拿到 stale 的两行。
- **改为 sysctl + 用户态**：驱动里 `pcie_note()` 填 `pcie_report[768]`，`SYSCTL_STRING(_kern_hakios, OID_AUTO, pcie, …)`
  暴露成 `kern.hakios.pcie`；`userland/src/pcie_report.c` → `/redwood/bin/pcie_report` 读它、打 console、
  写 `/private/var/pcie-ran.txt`（marker）与 `/private/var/pcie.txt`；job 用 `mk-ram.sh rpt2 '/redwood/bin/pcie_report'` 生成。
  **这条链还没验证过**（p21/p22 都因 SoC 在 ~4 s 死掉而没跑到用户态）。
- **p21/p22 的死因线索**：logdump 里 loader 的进度记录显示 4 s 时内核最后一行是 `pcie: 2: GDSCR … clear bit 0`，
  之后没有任何心跳 → 整颗 SoC 停（loader 也没来得及写 hung 判据）→ 复位回 Android。
  可疑点：`pcie_watch` 循环里的 DBI/PHY 读，或「提前到启动最前面执行」的时序。
- **p23 已就绪未跑**：`venus-recon\p-p23.bin`（`pcie=1 pcie_step=2 pcie_power=1 pcie_no1=1`，只上电 + 4 条 note，
  不带 after/watch），用来验证报告链。命令：
  `ic9-run.ps1 -Tag p23 -Payload p-p23.bin -Ramdisk system-hello.apfs -Shots 1 -WaitSeconds 120`，
  跑完回 Android 后 `su -c dd … skip=2042368 count=3200549` → `adb pull` → `hfs-ls.py cat /pcie.txt`。
- **MHI/ath11k_pci 的设计**：子代理产出 `/root/hakios/docs/venus-wifi/mhi-plan.md`（652 行，含 BAR0/iATU、
  BHI/BHIE 固件两段式、m3.bin 走 QMI 0x003C、QRTR-over-MHI 通道 20/21、环形几何）。最大风险是 PCIe SMMU 状态。
- **固件**：`venus-recon\fw-wifi\` 已有 amss.bin / m3.bin / regdb.bin / bdwlan.e01..e27（缺 board-2.bin）。
- **手机收尾状态**：在 Android（a 槽），adb 可见；boot_b = `img-final3.bin`；没有后台任务。

### 2026-11-06 08:10 p57-p59: the PHY is up, PERST works, the link still does not train

- p57/p58 completed the vendor's PARF configuration (DEVICE_TYPE=4, PHY_CTRL bit0 clear, SYS_CTRL=0x365E,
  DBI=0, SLV=0x4000000, AXI halt). They also showed that reading ELBI (0x60000f20+0x08) before `need(&elbi)`
  maps it reads address 0x8 and hangs the SoC -- the mapping call has to come first.
- The PHY comes up: the 75 writes of the vendor sequence run, `the PCS status bit cleared at 3 x 200 us`,
  `PHY 0x00000086`.
- PERST was written wrong twice: "output high" on a TLMM pin is bit 1 (write 2), not bit 0. With that fixed,
  `PERST# high: IO 0x00000003` (bit 0 the level read back, bit 1 the output), so pin 94 really is driven.
- The link still does not train: `LTSSM 0x1b0 = 0`, `ELBI 0x08 = 0x00000001` (link down, state 0),
  `DBI 0x72c = 0x08200000`, and ECAM `00:00.0`/`01:00.0` read all 0xffffffff.
- What is missing is the vendor's DBI GEN3 configuration from `msm_pcie_link_train()` (GEN3_GEN2_CTRL,
  GEN3_EQ_CONTROL, GEN3_SPCIE_CAP, the LNKCTL2 target speed, DEVICE_CONTROL_STATUS 0x7000), and the right
  definition of the PARF LTSSM bit-8 clear. Next: take those macros and offsets out of `pci-msm.c` into step 4.

### 2026-11-06 08:30 p60: the DBI's link-training configuration, ported from the vendor

- The vendor's `msm_pcie_link_train()` writes the root complex's DBI before it asks the link to train:
  `GEN3_GEN2_CTRL (0x080c)` field 0x1f00 = 1, `GEN3_EQ_CONTROL (0x08a8)` bit 5, `GEN3_RELATED (0x0890)` bit 0 = 0,
  `GEN3_MISC_CONTROL (0x08bc)` bit 0 = 1, `SPCIE_CAP (0x0154)` = the preset, bit 0 = 0 again,
  `DEVICE_CONTROL_STATUS (0x0078)` field 0x7000 = the max TLP read size. Only then does it clear LTSSM bit 8
  and poll `ELBI + 0x08` for `XMLH_LINK_UP (0x400)`.
- p60 carries that sequence (new `link_train_config()` in `drivers/pcie/hakios.pcie.c`, called just before
  `link_train_start()`), built as `p-p60.bin` 41,871,888 B sha256 4d3031f743b471d8a44e59e0de871113d1feb7ef507b779215622a9d753eeba7.
- p60 ran (loader, ramdisk, system image, payload; 70 s); the phone did not come back to adb afterwards, so the
  dump has not been read yet. Next: get it to Android or fastboot, `read-logdump.ps1`, and look at
  `the DBI is configured`, LTSSM, ELBI 0x08 and the ECAM ids.

### 2026-11-06 08:40 p60-p62: the root complex is ready, the radio has no power

Every part of the root complex now works, and the log proves each step:

- power domain up (`GDSCR 0x6b004 = 0xf822f000`), the clock votes `0x52000 = 0x00ed0d7f`,
  `0x52008 = 0x023c203f` (bit 4, the pipe clock, now included), `clkref 0x8c004 = 1`,
  `pipe mux 0x6b054 = 0` (the PHY drives it)
- the PHY's 75 vendor writes, then `the PCS status bit cleared at 3 x 200 us`, `PHY = 0x00000086`
- `WLAN_EN (pin 64) driven high: CFG 0x00000200, IO 0x00000003`
- `PERST# (pin 94) high: IO 0x00000003` (bit 1 is the level driven, the mistake of the two earlier runs)
- the DBI's GEN3 configuration written (`GEN3_GEN2_CTRL = 0x00020190`, `EQ_CONTROL = 0x04059f60`)
- `LTSSM 0x1b0 -> set bit 8` reads back as `0x00000100` (the vendor's `write_mask(0, BIT(8))` sets it;
  we had cleared it in p60)

And the link still does not train: `LTSSM ... (state 0)` = DETECT_QUIET, `ELBI 0x08 = 0x00000001`
(link down), `DBI 0x72c = 0x08200000`, ECAM `00:00.0`/`01:00.0` all 0xffffffff.

The reason is the other end: the radio is not powered. `drivers/net/wireless/cnss2/power.c` lists the rails
Android enables for it -- vdd-wlan-core 1.3 V, vdd-wlan-io 1.8 V, vdd-wlan-xtal 1.8 V, vdd-wlan-aon 0.95 V,
vdd-wlan-dig 0.95 V, vdd-wlan-rfa1 1.9 V, vdd-wlan-rfa2 1.35 V, vdd-wlan-sp2t 2.7 V -- and they are RPMh
regulators, which this kernel has no driver for. `WLAN_ENABLE_DELAY` in that file is 1000 ms, so the pin
alone is not enough either.

Two ways forward:

1. the loader (U-Boot) already has `CONFIG_QCOM_RPMH` and `CONFIG_DM_REGULATOR_QCOM_RPMH`, so it can turn
   those rails on through its own regulator framework before it starts the kernel (a small function in
   `xnuloader/loader.c`, plus the rail nodes from the device tree). A day or two.
2. a minimal RPMh driver in the kernel (RSC + cmd DB) that votes the same rails. Three to five days.

### 2026-11-06 10:55 what the radio needs, and why the loader cannot give it yet

The device tree names the rails the radio sits on, and they resolve to these regulators:

| property | regulator | voltage |
|---|---|---|
| `vdd-wlan-io-supply` | `pm8350_s10` (SMPS, PM8350) | 1.80 V |
| `vdd-wlan-aon-supply` | `pmr735a_s2` (SMPS, PMR735A) | 0.95 V (0.50-1.02) |
| `vdd-wlan-dig-supply` | `pm8350_s11` (SMPS) | 0.95 V (0.752-1.012) |
| `vdd-wlan-rfa1-supply` | `pm8350c_s1` (SMPS) | 1.90 V (1.80-1.952) |
| `vdd-wlan-rfa2-supply` | `pm8350_s12` (SMPS, hfsmps) | 1.35 V (1.224-1.36) |

All five are RPMh regulators (the nodes live under `soc/rsc@18200000/rpmh-regulator-*`), and none of them
has an owner in this kernel: no RPMh driver, so no vote, so no power. `cnss2/power.c` also waits
`WLAN_ENABLE_DELAY` = 1000 ms after `wlan-en` before it touches the bus.

The loader detour does not work as it stands: U-Boot's `drivers/power/regulator/qcom-rpmh-regulator.c`
binds only PMIC containers whose `compatible` is one of `qcom,pm8550ve-rpmh-regulators`,
`qcom,pm8550vs-rpmh-regulators`, `qcom,pmc8380-rpmh-regulators`, `qcom,pmm8654au-rpmh-regulators`, and its
`rpmh_regulators_bind()` insists on `qcom,pmic-id` plus the driver's own `rpmh_vreg_init_data` table. There is
no entry for the PM8350 / PM8350C / PMR735A set that venus uses, so even with the DT nodes copied in it would
not probe without adding that table to U-Boot.

So the next real step is to write the RPMh vote itself, in the kernel:

1. read the command DB (`cmd-db`, the soc/rsc@18200000/cmd-db@1e00000 node) to get each resource's address;
2. send an active-only vote through the RSC's TCS (the same registers `rpmh-rsc.c` drives on Linux), with the
   voltage levels the DT already states;
3. then `wlan-en` high, 1 s, `PERST#` release, LTSSM bit 8, and the link should train.

That is the day or two the estimate said. Everything up to it is done and proven by logdump.

### 2026-11-06 12:15 the command DB is readable, and the five rails have names

A read-only probe (`cmddb=2` boot arg, `cmddb_dump()` at the top of `drivers/pcie/hakios.pcie.c`)
mapped `memory@80860000` (128 KB, `no-map` in the device tree) and read the RPMh command DB:

```
cmddb: magic db 30 03 0c, version 1
cmddb: slave 3: 24 entries, header +0, data +576      (cx.lvl, mx.lvl, mmcx.lvl, qphy.lvl, ...)
cmddb: slave 3: 12 entries, header +960               (the .mol entries)
cmddb: slave 5: 46 entries, header +1272              (MC0..MC2, SH0..SH7, MM0..MM5, SN0..SN14, QUP0..2, ...)
cmddb: slave 4: 79 entries, header +2744              (the regulators)
```

What matters is the fourth slave: the resource names are **flat short names**, not the
`pm8350_s10` style used by the kernel's regulator driver.  The five supplies the radio needs map
like this:

| rail | device tree regulator | command DB name |
|---|---|---|
| `vdd-wlan-io` | `pm8350_s10` | **`smpb10`** |
| `vdd-wlan-aon` | `pmr735a_s2` | **`smpe2`** |
| `vdd-wlan-dig` | `pm8350_s11` | **`smpb11`** |
| `vdd-wlan-rfa1` | `pm8350c_s1` | **`smpc1`** |
| `vdd-wlan-rfa2` | `pm8350_s12` | **`smpb12`** |

The DB also lists `vrm.aoss 0x00046000`, `vrm.soc`, `vrm.wlan 0x00046008`, `vrm.qlnk 0x00040d00`,
`vrm.mmcx 0x00042300` — so addresses are 8 bytes apart per resource and the vote address is the
entry's own `addr`.

**One bug, already understood:** the probe printed the 8-byte id with `%c%c%c%c%c%c%c%c`, and a
name shorter than eight characters carries NUL padding.  `say()` runs `vsnprintf` and then emits
the result as a C string, so it stops at the first NUL: entries with short names lost their
address.  Fix for the next run: copy the eight bytes into a local buffer, terminate at the first
zero, print with `%s`.  Then the five addresses above come out, and the TCS vote can be written.

How it was read back (the working method): run with `cmddb=2 pcie_tag=<tag> loader_return_after=60`,
wait for the phone to fall back to Android, then
`adb shell su -c "dd if=/dev/block/sda24 of=/data/local/tmp/ld.bin bs=4096 count=512"`,
`adb pull`, and `strings -a ld.bin | grep 'cmddb:'`.

## 2026-11-06 22:05 所有进度汇总文档

用户要求把全部进度写进一份对外可读的文档，已完成：

- `C:\Users\Administrator\Documents\deepseek-harness\default-workspace\HAKIOS-VENUS-功能总结.md`（工作区根）
- 内容：一页总览（可用/不可用）、设备与底座（分区、启动链、构建）、已实现功能（GPU/触摸/电源电池/图标与黑块/LaunchServices/设置/数据卷/观察通道）、Wi-Fi 专项（硬件表、已打通 13 项带证据、未打通表、寄存器速查、三份参考源码、M0–M6 时间表）、第三方应用安装（5 条路径）、平台级缺陷、工程与脚本地图、关键参数速查、里程碑时间线、下一步。

本轮状态（截至 22:05）：boot_b = `img-final3.bin`；内核 = fix88 之后（15,259,856 B），**p64 还没跑**；下一步仍是 p64（六路 rail + 链路训练）。
## 2026-11-07 06:46 p65: THE LINK IS UP (L0)

第一次真正训练成功。关键日志（`venus-recon/ld-p65.bin` 最新运行）：

    pcie: 2:   rails voted (ldob6 ok, ldob5 ok)
    pcie: 2:   GDSCR 0x6b004 = 0xf822f000 (the domain is on)
    pcie: 4:   smpb11/smpc1/smpb12 voted; the radio's rails are voted
    pcie: 4:   WLAN_EN (pin 64) driven high: CFG 0x00000200, IO 0x00000003
    pcie: 4:   PERST# (pin 94) low: IO 0x00000000 / high: IO 0x00000003
    pcie: 4:   Gen1: 0xa0 0x00010003 -> 0x00010001, 0x80 0x10110008 -> 0x10110008
    pcie: 4:   LTSSM 0x1b0 = 0x00000000 -> set bit 8 (the vendor's write_mask(0, BIT(8)) sets it)
    pcie: 4:   link UP: ELBI 0x08 = 0x00011401, DBI 0x80 = 0x30110008, LTSSM 0x00000111
    pcie: 4: after PERST# and the training start: LTSSM 0x00000111 (state 17), PHY 0x00000084, DBI 0x72c 0x08000010, ELBI 0x08 0x00011401 (link up, state 17)

解读：ELBI 0x08 bit10（`XMLH_LINK_UP`）= 1；LTSSM 状态 17 = **L0**；PHY 状态 0x84 稳定。
=> **M0（链路训练）完成**，PCIe 物理链路与数据链路都起来了。

下一步（唯一剩下的第一段）：**config space 读不到设备** —— `pcie: 5: 00:00.0 / 01:00.0` 仍是 `0xffffffff`，
说明 ECAM 窗口还没配对（需要 iATU 出站区域 0 映射 configuration 空间，或设置 PARF 的 config 模式）。
弄好之后应当能读到 `17cb:1103`（QCA6490）。

Open objectives: ①WiFi（B 方案）：配 iATU/config 窗口 → 枚举 17cb:1103 → SMMU/BAR → BHI/MHI → IPCR/QMI → ath11k；②第三方应用安装；③boot_b = img-final3.bin。
## 2026-11-07 08:26 p76: THE ENDPOINT ANSWERS (17cb:1103)

    pcie: 5:   viewport at dbi + 0x900 = 0xffffffff (unrolled, no viewport)
    pcie: 5:   region 0 at 0xfe635000, the layout the vendor uses when the regions are unrolled
    pcie: 5:     set : ctrl1 0x00000004 ctrl2 0x00000000 lbar 0x60100000 lar 0x60100fff ltar 0x01000000
    pcie: 5:     the region answered after 1 polls of 100 us
    pcie: 5:     after: ctrl1 0x00000004 ctrl2 0x80000000 lbar 0x60100000 lar 0x60100fff
    pcie: 5: 01:00.0 id 0x110317cb (vendor 0x17cb device 0x1103) class 0x028000 rev 0x01
    pcie: 5:   cmd/status 0x00100000, header 0x00000000, BAR0 0x00000004

The WCN6855 is on the bus and its configuration space reads. Three things had to be right, and
each one was a trap of its own:

1. The power domain has to be up *before* anything inside it is touched. p69-p72 all died at
   the first register access after "clear SW_COLLAPSE" because GDSCR stayed at 0x0022f001; the
   whole gcc 0x6b0xx block, parf, and the core all hang the AXI bus if read while collapsed.
   fix96 polls 1000 x 10 us and returns instead of going on.
2. The iATU is in the unrolled layout (dbi+0x900 reads 0xffffffff, which is designware's marker
   for it), so the regions live in the window the device tree gives them, 0x60001000, at
   0x200 per region. Read that window before the domain is up and the machine hangs - which is
   what p68 saw.
3. The iATU speaks bus addresses. LBAR/LAR take the physical conf base (0x60100000), not the
   kvirtual address ml_io_map handed back; and the region address itself has to be a
   vm_offset_t, because a uint32_t there truncates the KVA (p74 panicked exactly there:
   "Kernel data abort ... far 0x00000000c30d1004, esr 0x96000045", a level 1 translation fault
   on a store - the low half of the address).

Next: the BARs (BAR0 reads 0x4: a 64-bit memory BAR, currently unmapped because memory space is
off), then SMMU, then BHI/MHI.

## 2026-11-07 09:24 the dbi header is not a bridge: 0x18 kills the machine

p80 (the whole BAR sequence), p81 (writing 0x18) and p82 (reading nine DBI
words) each killed the machine outright: the screen froze on the HAKIOS
screen, adb and fastboot both went away, and the dump was empty because the
loader cannot reach the UFS once the AXI bus is stuck.

p83, the same kernel with `pcie=0` and no probe at all, booted all the way to
the iOS home screen. The kernel is fine. The probe is the problem.

p84x0 then read one single word, `dbi + 0x18`, and killed the machine again.
That is the mine: 0x18.

In a type 1 header 0x18 is the primary bus number, and `dw_pcie_setup_rc()`
writes 0x00ff0100 there. But our DBI answers 0x10 (BAR0, read many times) and
dies on 0x18, so the RC is not presenting a bridge header at all. It does not
matter: we reach the endpoint through iATU region 0 (CFG0, with the bus in
ltar), not through host bridge forwarding, so 0x18/0x20/0x24 are all skipped
from here on.

fix108 rewrote the staircase with no DBI header access at all:

    pcie_bar=0  write the endpoint BAR0 = 0x60300000|4, no read back
    pcie_bar=1  read it back
    pcie_bar=2  add iATU region 1, the 2 MB identity window
    pcie_bar=3  add the root complex memory decode (dbi+0x04, safe)
    pcie_bar=4  add the endpoint memory decode (conf+0x04)
    pcie_bar=5  read the first words of bar0 plus BHI/BHIE/TCSR

Payloads p-p85x0 .. p-p85x5 are built and waiting on the phone.

## 2026-11-07 09:32 write the route first, then move the bar

p85x0 wrote the endpoint BAR0 = 0x60300000|4 and did nothing else, and the
machine died again. p78 had already written to the same register, but with
0xffffffff first and then the original zero back, and that was safe. So the
write itself is not the problem: the value is. 0xffffffff is not an address
that gets decoded, while 0x60300000 is. The moment the bar is written the
endpoint starts decoding 0x60300000..0x605fffff, but nothing on the host side
routes that window to the endpoint yet, so the first access that lands there
goes into the endpoint and comes back around, and the AXI bus locks up.

The order has to be the other way around: pave first, then move the bar.

fix109 therefore:

  1. moves bar0 to 0x60400000 (the address star uses as well),
  2. configures iATU region 1 as a 2 MB identity window 0x60400000 ->
     0x60400000 first, so the host side already has a route,
  3. only then writes the endpoint BAR0 = 0x60400000|4.

The new staircase (payloads p-p86x0 .. p-p86x5):

    pcie_bar=0  configure iATU region 1 only, do not touch the bar
    pcie_bar=1  then write BAR0 = 0x60400000|4
    pcie_bar=2  then read it back
    pcie_bar=3  then switch on the root complex memory decode (dbi+0x04)
    pcie_bar=4  then switch on the endpoint memory decode (conf+0x04)
    pcie_bar=5  then read the first words of bar0 plus BHI/BHIE/TCSR
## 2026-11-07 10:00 the bar write is what kills it

- p85x0 wrote `0x60300000 | 4` into the endpoint BAR0 and froze the phone.  p89x0 wrote
  `0x60400004` and froze it as well.  p78 wrote `0xffffffff` into the same register and was fine.
  So the value matters: anything the endpoint will decode.
- p84x0 read `dbi + 0x18` and froze the phone: the rc dbi header is not a type 1 bridge, and
  `0x18` is a hole there.  `0x10` reads fine.
- p86x0 configured iATU region 1 and froze.  p88 read `iatu + 0x200` and froze.  Only region 0
  exists on this controller; `0x200` onwards is a hole.
- p90 set `PARF_SLV_ADDR_SPACE_SIZE (0x358)` to `0x4000000` (the dts value, 64 MB) before the bar
  write and still froze.  The slave window size is not the missing piece.
- p91 turns `PARF_SYS_CTRL (0x00)` bit 29 on and reads the config window without any atu region,
  to test whether the config path is ecam rather than atu forwarded.  It writes no bar.

## 2026-11-07 11:00 p99/p100: the window, the bar, and the hardware inside it

- **p98**: `wr(dbi 0x20, 0x60506040)` alone is safe; the watch ran to 19 of 20 s.
  This is the bridge memory window android shows as `60400000-605fffff : PCI Bus 0000:01`.
- **p99**: the window first, then `wr(conf 0x10, 0x60400004)`; safe, the machine
  booted all the way to `/private/var`.  This closes the "a valid bar address
  kills the machine" question that cost p84x0..p89x0: the endpoint's bar needs
  the bridge memory window to have a route before it is written.
- **p100**: reading the bar at 0x60400000:
  `length 0x00000100, version 0xdeadbeef, status 0x00000000`,
  `bhi 0x00000100, bhie 0x00000224, tcsr 0x400c0110`.
  The last line matches star's `bhi_request` preconditions exactly
  (`tcsr == 0x400c0110`, `bhi == 0x100`), so the hardware agrees with the
  reference driver.
- **next**: SMMU route (`parf + 0x2000 + 4*hash = 0x01000100`, crc-8 poly 0x07
  over requester id 0x0100), a dma buffer, then the BHI upload of
  `amss.bin` (5,236,304 B), then MHI, IPCR/QMI and ath11k.

## 2026-11-07 11:24 p102: the mhi clock, and the registers behind it

- star's stage 6 writes `parf 0x174 |= (1 << 4)` before any DBI access.  p101
  read `bar+0x108..0x130` with that bit clear and the machine died; p102 set
  only that bit and the same window became readable:
  `parf 0x174 = 0x00000003 -> 0x00000013`,
  `ee 0x00000000 status 0x00000000 error 0x00000000`.
  So `PCIE20_PARF_MHI_CLOCK_RESET_CTRL` bit 4 is what gates the MHI block.
- the probe then panicked in `kmem_alloc(..., 16384, 0x100021)` with error 3
  (`KERN_NO_SPACE`) -- ours, not the hardware's: the block map of bar0 asks
  for 2 MB and the kernel is short of memory by the time it runs.  Next round
  maps only 4 KB of bar0.
- star's full parf order, for the next step:
  `0x1000=4`, `0x40 &= ~1`, `0x350=0`, `0x00=0x365e`, `0x174 |= 1<<4`,
  `0x358=0x4000000`, `0x1a8 |= 1<<31`.

## 2026-11-07 12:00 p104: the SMMU knows the endpoint (M3 done)

What the dump of p104 (pcie_bar=20, pcie_delay=15) shows, in order:

    pcie: 5:   20: rc command 0x00100000, ep command 0x00100002
    pcie: 5:   20: requester 0x0100 hashes to 21 (parf+0x2054)
    pcie: 5:   20: sid cfg 0x00000001 before
    pcie: 5:   20: entry 21 = 0x01000100, sid cfg 0x00000000
    pcie: 5:   20: 0 of 256 entries disagree; sid cfg bit0 0

So: the SID table was cleared, BDF 01:00.0 was placed at entry 21
(requester_hash(0x0100) = 21, CRC-8 poly 0x07), BDF_TO_SID_CFG's bit 0 was
cleared, and all 256 entries read back exactly as written.  No PARF 0x358 was
needed -- p104 did not set it and worked (p105 has fix127 that sets it; it is
now belt and braces, not a prerequisite).

And the system did not die: the same dump ends with launchd and SpringBoard
lines (com.apple.xpc.launchd ... SpringBoard[7]), i.e. iOS got all the way to
its user space.  The screen was still on the apple logo when the user looked;
that is the boot being slow, not the machine being dead.

That closes M3.  The next stage is M4: moving amss.bin into the radio with BHI.
It needs, in this order:
  1. a physically contiguous DMA buffer the SMMU can see (star's dma_prepare():
     it builds its own stage-1 tables, IOVAs from 0xa0004000, WIFI_MHI_IOVA
     0xa0200000, WIFI_DATA_IOVA 0xa1000000);
  2. amss.bin (5,236,304 bytes, crc32 0xb4376a2a) reachable from the kernel --
     it has to go into the system image, or be read from /private/var;
  3. star's bhi_request(): write bar+0x10c = addr >> 32, bar+0x108 = addr,
     bar+0x110 = size, bar+0x118 = 1, then poll bar+0x12c.

## 2026-11-07 13:30 handing over -- read HANDOVER-2026-11-07.md first

The session is being moved to a new window.  `C:\Users\Administrator\Documents\deepseek-harness\default-workspace\HANDOVER-2026-11-07.md`
has the whole picture: what works (GPU, touch, power, data volume, springboard, app
registration), how far WiFi got (M0 link L0 -> M1 17cb:1103 -> M2 bridge window + BAR0 +
MHI registers 0x100/0x224/0x400c0110 -> M2.5 MHI clock -> M3 SMMU SID routing), and the
two things to act on next:

1. loader.c's NOTE_SECONDS must stay 24.  build-loader-log.sh had raised it to 150 and
   that is what hung p119..p122 (the loader keeps writing logdump while the kernel owns
   UFS).  fix141.sh put it back and rebuilt loader.efi at 13:28.
2. hakios.pcie.c maps its registers with ml_io_map; star (and our own ufs/adsp/mpss/camera
   drivers) use ml_io_map_unmappable(phys, size, VM_WIMG_IO).  That plus star's clock gate
   (0x6b000 bit0, 0x6b014/0x6b01c/0x6b024 bit31) is the next experiment -- it may well be
   the root cause of every "reading this register hangs the machine" since p84.

p123 (pcie=0, rebuilt loader, sha256 9eb76b56...) is built and waiting for the phone to
come back to fastboot: it verifies that the boot path is healthy again before touching PCIe.


## 2026-11-07 night -- the p122/p123 hang was the small root, not the loader

Three findings, all from file evidence rather than from the phone:

1. build-loader-log.sh writes img-wr3.bin, and img-wr3.bin still has mtime 2026-11-06
   05:37:55 and loader crc32 0x2adbe9da, exactly like img-wr2.bin.  The script never
   finished today (it tries to pack the corrupt 1,041,788,928-byte flashboot.apfs), so
   p119..p122 ran the same 0x2adbe9da loader as p104..p118.  NOTE_SECONDS=150 is not what
   hung them.  img-wr2.bin is back to that original loader.

2. From p-p106.bin on, every payload's ramdisk was the 7,516,160-byte redwood-only root
   built at 11:58 by userland/build.sh, not the 26,628,096-byte full root that p105 and
   earlier used.  p122 and p123 set pcie=0 and still went black, so the small root -- not
   PCIe -- was the hang.  userland/root.apfs has been restored from p-p104.bin
   (offset 0x00e91a38, 26,628,096 bytes); the small one is kept as root.small7m.apfs.

3. p124 (pcie=0, full root) booted to the iOS desktop.  The base system is healthy, and the
   26.6 MB root is what every experiment from here on must use.

p125 was then pcie=1 pcie_step=5 pcie_bar=21 with apply-142 (need() now maps with
ml_io_map_unmappable(phys, size, VM_WIMG_IO)) and apply-143 (bar 21 tries both
kmem_alloc_contig forms -- star's mask 0 and the old PAGE_MASK one -- printing kvtophys for
each, plus the five GCC gate registers).  It stopped at the Apple logo: the kernel got far
enough to draw, never reached SpringBoard, never reached loader_return_after=90, and the
loader did not answer the dump.  p104 (bar 20, same SMMU work) reached the desktop, so the
difference is inside the bar 21 branch: reading amss.bin through hakios_image_file, or the
two kmem_alloc_contig calls.

Next (p126/p127): split those two.  pcie_bar 25 = GCC registers plus hakios_image_file only,
no allocation; pcie_bar 26 = both allocations only, no file read.  Whichever stops at the
logo tells us which half to fix.

Also new: star's source tree is the real reference.  docs/WIFI-LEMONADE.md records a full
QCA6490 bring-up on lemonade (same SM8350, same card) down to DHCP and HTTP, and
xnu/files/bsd/dev/lemonade_wifi.c has bhi_request() and firmware_probe() we can port almost
verbatim.  The BHI success signature there is BHI=0x80000001, EE=1 (SBL), MHISTATUS=0x101,
FSR=0x400 (translation format bit, not a fault), global=0, error=0.

handover for tomorrow: HANDOVER-2026-11-08.md

## 2026-11-07 21:10 -- p131 hangs in step 5, but the allocation before UFS is innocent

p131 (apply-147: `hakios_pcie_dma_init()` takes a page with `kmem_alloc_contig()` before
`hakios_ufs_init()`, stores its pa, and `pcie_bar == 24` still does the old 4 KB
`kmem_alloc()`) does not answer the loader, and the phone shows the apple logo with USB
gone -- it did **not** reboot into Android the way p130 did.

That difference is the useful part: p130 panicked inside `hakios_pcie_dma_init()` because
it called `ml_io_map()` there, and `io_submap` does not exist yet that early (it is built
by `io_map_init()`).  p131 removed that call, kept the allocation, and did not panic --
so **`kmem_alloc_contig()` before UFS is fine**.  What hangs p131 is the 4 KB
`kmem_alloc()` in step 5, at `hakios_pcie_init()` time.

So the picture is now:

  * before UFS: allocation works (p130's panic was the map, not the alloc);
  * at `hakios_pcie_init()`: any allocation hangs (p127 contig, p131 plain);
  * `ml_io_map_unmappable()` at step 5 works (p104, p105, and every `need()` since
    apply-142).

apply-148 therefore rebuilds `pcie_bar == 21` around that: the page comes from
`hakios_pcie_dma_init()` at the head of the boot path, step 5 only maps it with
`ml_io_map_unmappable()` and does a write/read (`0x41414141`) as self-test.  Nothing is
allocated and `amss.bin` is not read yet.

p132 is that build.  Waiting for the phone to come back to fastboot.

## Known answer to "why does allocation hang there"
Not known yet.  The candidates are: the page queues are drained by adreno/wifi by then
(and `cpm_allocate` cannot find a contiguous run), or `kmem_alloc` takes a lock that is
held.  `KMA_NOPAGEWAIT` did not change it (p111), which points away from "waiting for
pages" and towards "waits on a lock".  Not worth chasing while the pre-UFS page works.

## 2026-11-07 21:22 -- at hakios_pcie_init() time the kernel may touch MMIO and nothing else

Six runs pinned it down.  What works and what hangs, at `hakios_pcie_init()`:

| operation on memory | where | result |
| mmio physical address -> `ml_io_map_unmappable()` | step 5 | works (`need()`, p104) |
| loader page -> `ml_io_map()` | before UFS | panic (p130), `io_submap` not built yet |
| ram physical address -> `ml_io_map_unmappable()` | step 5 | hangs (p133) |
| `kmem_alloc_contig()` | before UFS | works (p130, p131, p133 all got past it) |
| `kmem_alloc_contig()` / `kmem_alloc()` | step 5 | hangs (p127, p131) |
| five gcc reads + `hakios_image_file("fw","amss.bin")` | step 5 | hangs (p126) -- the file read allocates |

So the rule is not "allocation is broken", it is "**memory management is not usable at
that point, but MMIO is**".  The only thing proven to touch RAM there is `need()`'s own
`ml_io_map_unmappable()` of the register windows, and those are device addresses.

apply-150 therefore stops mapping at all: the page that `hakios_pcie_dma_init()` took
before UFS already has a kernel VA, and the DMA buffer is written through **that** VA
while the physical address is what goes into the BHI registers.  That is the shape the
BHI upload wants anyway -- `memcpy()` the firmware into the page, then point the
endpoint at its physical address.

p134 is that build (`pcie_bar == 21` writes 0x41414141 through the VA and reads it back).

Not yet answered: whether the VA itself is safe at step 5.  If p134 hangs too, the
fallback is to copy `amss.bin` into the page before UFS and have step 5 touch no memory
at all, only the BHI registers.


## 2026-11-08 00:50 -- the link trains only on the first run of a cold loader session

p169 (first probe after `fastboot boot img-wr2.bin`) had the link UP:
`ELBI 0x08 = 0x00011401, DBI 0x80 = 0x30110008, LTSSM 0x00000111` (state 17),
`01:00.0 id 0x110317cb`, and the whole SMMU group (`0 of 256 entries disagree`,
`sid cfg bit0 0`).  Step 1 through step 5 all passed.

p170, p171, p172 and p173 (same payload, run again inside the same loader
session or after another `oem run`) all stop at `LTSSM 0x00000905` (state 5,
Configuration.Linkwidth.Start): `ELBI 0x08 = 0x00005101`,
`DBI 0x80 = 0x10110008` (or `0x38110008` when it is read before gen1_config),
`PHY 0x00000086`, `DBI 0x72c 0x08200000`; `01:00.0` reads `0xffffffff`.

Tried and did not help:
- PERST# timing 20/10/20 ms -> 100/100/100 ms (apply-171)
- `pcie_reset=1` (GCC_PCIE_BCR and GCC_PCIE_PHY_BCR assert/release in step 2)
- `pcie_power_cycle=1` (apply-172: set GDSCR bit 0 for 20 ms, then power up)

So the endpoint, the PHY or the controller keeps a state across kernels that
only a cold loader start clears.  Every PCIe experiment has to start with
`fastboot boot img-wr2.bin` and has to be the first `oem run` of that loader
session.  `fastboot reboot-bootloader` from xnuloader does not come back (the
phone lost USB completely), so recovery is a 20 s power cycle and
volume-down + power into ABL fastboot.


## 2026-11-08 01:15 -- p175: the dma page and the firmware staging work, bar0 reads 0xffffffff

p175 (`pcie=1 pcie_step=5 pcie_power=1 pcie_power_cycle=1 pcie_delay=0 pcie_settle=100
pcie_bar=21 pcie_watch=0`) on a cold loader start:

- `pcie: dma init: page at 0xfffffff4826d0000, pa 0x192728000, 0x80000 bytes` -- the
  512 KiB contiguous page is taken before UFS, the same call `hakios.ufshc.c:1273` makes.
- `pcie: stage: copied 524288 bytes of 0x4fe650 from amss.bin to 0x... first word
  0x464c457f` -- apply-173 reads the firmware after UFS and before hakios_pcie_init().
  Reading it before UFS panicked (p140/p142/p143): hakios_image_file() walks md0, which
  lives on the UFS volume, and the UFS driver has not started at that point.
- link UP (LTSSM 0x111), `01:00.0 id 0x110317cb`, and the bar 21 branch ran:
  `wrote 0x41414141, read back 0x41414141` -- the dma page is writable at step 5.
- `bar0 at 0x60400000 -> 0xfffffff482f2c000`, but
  `bhi before: soc 0xffffffff ee 0xffffffff mhi 0xffffffff status 0xffffffff err 0xffffffff`
  and `bhi after: status 0xffffffff (top 3, ee 255)`.

The step 5 dump says why: `bars 00000004 ...` and `bars after enable 00000004 ...` --
the endpoint's BAR0 still holds the unassigned value 4.  The memory window and BAR0 are
written only in the `pcie_bar == 17` branch (`wr(dbi.base + 0x20, 0x60506040);
wr(conf.base + 0x10, 0x60400004)`), so every other bar branch reads all ones.

apply-174 writes both in branches 21/22/23 before they touch bar0; p176 tests it.


## 2026-11-08 01:20 -- p176: bar0 answers, soc 0x400c0110, ee 0x100

apply-174 (`wr(dbi 0x20, 0x60506040)` + `wr(conf 0x10, 0x60400004)` before the bar
branches) worked.  p176 on a cold start:

    pcie: 5:   bar0 window: dbi 0x20 = 0x60506040, BAR0 = 0x60400004
    pcie: 5:   21: bhi before: soc 0x400c0110 ee 0x00000100 mhi 0x00000002 status 0x00000000 err 0x00000000
    pcie: 5:   21: bhi after:  status 0x00000000 (top 0, ee 0) mhi 0x00000002 err 0x00000000

The MHI/BHI block is readable: TCSR 0x400c0110 (the same value star and the vendor
see), the execution environment register 0x100 (SBL), MHI version 0x2, status 0, no
error.  The BHI request itself never started: the status stays 0 after the trigger
write because the endpoint's bus master bit was never set -- step 5 only turned on
memory space (`command 0x00100002`).  star's bhi_request() writes 0x6 into both the
RC's and the endpoint's command register.

apply-175 does that, and prints bar0 0x128 (star wants it to be 0), before the BHI
writes.  p177 tests it.


## 2026-11-08 01:30 -- p177: bus master and 0x128 are right, the BHI still does not start

p177 (apply-175) on a cold start:

    pcie: 5:   21: bhi before: soc 0x400c0110 ee 0x00000100 mhi 0x00000002 status 0x00000000 err 0x00000000
    pcie: 5:   21: bus master on: dbi 0x4 = 0x00100006, conf 0x4 = 0x00100006
    pcie: 5:   21: bar0 0x128 = 0x00000000 (star wants 0)
    pcie: 5:   21: bhi after: status 0x00000000 (top 0, ee 0) mhi 0x00000002 err 0x00000000

Every register the sequence touches reads back what star expects, but the status stays
0 after the trigger write.

star's bhi_request() (lemonade_wifi.c:719) refuses to write at all unless
`dma_space.owned` is set, which means the SMMU context is owned by the driver and
`dma_space.cb` points at that context bank (it also checks that context bank's FSR and
the global FSR before touching BHI).  The image it hands to PBL is `WIFI_DMA_IOVA`
(0xa0004000), an IOVA in the SMMU page table, never a physical address.

We hand the endpoint the physical address 0x192524000 with no SMMU context set up, so
the endpoint side cannot fetch it.  M5 therefore starts with the SMMU: SMR/S2CR for
stream 0x1c01, a context bank with the 4 KiB page table over the dma page,
CBAR/CBA2R, and then bhi_request with the IOVA.


## 2026-11-08 01:30 -- apply-176: the SMMU is in the driver

star's SMMU setup lives in lemonade_wifi.c:592 (dma_prepare).  The driver now
does the same thing, in pcie_smmu_setup():

  - maps 0x15000000 (1 MB) as the SMMU and checks SCR/IDR0/IDR1/GFSR
  - allocates three pages (L1, L2, L3) from kernel_map
  - fills L1[IOVA>>30] -> L2, L2[(IOVA>>21)&511] -> L3, and one 4 KiB leaf per
    page of the 512 KiB dma page (attrs 3|1<<6|2<<8|1<<10|1<<11|1<<53|1<<54)
  - resets the PARF BDF table, puts BDF 0x0100 at requester_hash(0x0100) as
    0x01000100 and clears bit 0 of parf+0x2c00 (vendor msm_pcie_config_sid)
  - claims the first free SMR and the first free context bank, and writes the
    CBAR/CBA2R/TCR/TTBR/SCTLR sequence star writes
  - reads everything back and walks every leaf against kvtophys()

BHI is now handed PCIE_SMMU_IOVA (0xa0004000) instead of pcie_dma_pa, and the
SMMU is set up before the bus master goes on (star's bhi_request refuses to run
until the context is owned and bus master was off).

p178 waits for a cold start; link training only succeeds on the first run after
fastboot boot img-wr2.bin (p169, p174, p175, p176, p177 all did).


## 2026-11-08 01:45 -- `fastboot reboot` from xnuloader is not a way out

Tried it so the cold start would not need a power button: `fastboot reboot`
answers OKAY [0.000s] and the device drops off the fastboot list, but nothing
comes back -- no adb, no fastboot, no Android VID in the PnP tree (only the
generic composite device).  Same as `fastboot reboot-bootloader`.

The only way out of xnuloader is the power button: hold 20 s, then volume down
+ power for ABL fastboot.  Do not spend a run on `fastboot reboot`.


## 2026-11-08 05:25 -- p178: the SMMU comes up, BHI still stays 0

p178 (apply-176, cold start) -- the SMMU part is green:

    pcie: smmu: scr 0x00200406 idr0 0x4c017e59 idr1 0x6000004b (89 matches, 75 contexts, 0 stage 2) gfsr 0x00000000
    pcie: smmu: tables at 0x1931e0000, iova 0xa0004000 -> pa 0x192528000, 128 pages
    pcie: smmu: parf sid table: bdf 0x0100 -> hash 21, 0x2000[21] = 0x01000100, 0x2c00 = 0x00000000
    pcie: smmu: claim match 8 context 0 for stream 0x1c01 (cbar 0x0001f000 cba2r 0x00000001)
    pcie: smmu: tlbi ack 0x7f4 = 0x00000001
    pcie: smmu: readback smr 0x80001c01 s2cr 0x00000000 sctlr 0x00000127 tcr 0x00803519 ttbr 0x00000001:931e0000 root 0x1931e0000
    pcie: smmu: 128 pages walk from iova 0xa0004000 to the dma page
    pcie: 5:   21: smmu state 1

Every check passed: SMR 0x80001c01 (the stream star uses), S2CR 0 (TYPE_TRANS,
CBNDX 0 -- vendor arm-smmu.h:116 puts TYPE at bits 17:16 and CBNDX at 7:0, so
star's plain `context` write is right), SCTLR 0x127 (M|TRE|AFE|CFRE; our 0x1127
loses bit 12 on readback), TTBR pointing at the tables, and all 128 leaves
walking to the dma page.

And the BHI still reads status 0x00000000, top 0, ee 0.  So the endpoint either
never fetched, or fetched and stopped.

New clue: context 0 read back cbar 0x0001f000 before we wrote it, i.e. the ABL
or Linux had already configured that context bank.  We overwrote it, which may
have collided with an existing translation.

apply-177 does two things:

  - only claims a context whose CBAR is still zero (nobody's)
  - after the trigger, prints the context bank's FSR (cb+0x58), FAR (cb+0x50),
    the global GFSR (mmio+0x48) and SCR

If the endpoint did issue a DMA, the FSR names the reason.  If FSR stays 0, the
endpoint never issued anything and the problem is above the SMMU (the trigger
write itself, or the SID reaching the SMMU at all).

Note: this dump came back as 118,995 bytes with `oem dump` answering
`FAILED (remote: 'read failed')`, not the usual 1,048,576; `get_staged` still
returned real content, so read it with grep rather than assuming the size.

## 2026-11-08 11:00 (Asia/Shanghai) -- M4: the BHI doorbell is ignored by venus' PBL (the whole trail)

The hardware path is all green since p169: power domain (GDSCR 0x0022f001 -> 0xf822f000),
clocks, PHY (75 writes), PERST#, link training (ELBI 0x08 = 0x00011401, DBI 0x80 = 0x30110008,
LTSSM 0x111 = L0), BAR0 window (DBI 0x20 = 0x60506040 -> BAR0 = 0x60400004), iATU region 0
for config space, endpoint 01:00.0 = 17cb:1103, and the SMMU path (SMR 0x80001c01 for the
stream 0x1c01, one free context bank, 4 KiB page tables, 0xa0004000..0xa0083fff 512 KiB).

What fails: neither BHI (bar+0x100, doorbell +0x118) nor BHIE (bar+0x224, TXVECDB +0x3c)
makes the PBL do anything.  Evidence:

- BHI window readback after the write: IMGADDR 0xa0000000, IMGSIZE 0x80000,
  IMGTXDB 0x02dc6454, EXECENV 0, STATUS 0, ERRCODE 0.
- ERRDBG1 (0x134) stays 0xa0084000 and ERRDBG3 (0x13c) stays 0x1000 -- the values ABL left
  behind.  They never change for us, so the PBL never even records a failed attempt.
- The guard test (ask the PBL to read an unmapped IOVA 0xa0084000 and require a translation
  fault) never produces one: FSR stays 0x400 (the read-only page-table format bit), FAR
  stays garbage.  star's own guard test did produce FSR 0x80000402, FAR 0xa0084000,
  SID 0x1c01, so their PBL does fetch.
- p201 proved BHI_STATUS and MHICTRL are plain writable registers: write 0x80000000 and read
  0x80000000 back, write 0 and read 0 back.  Nothing in the endpoint polls or clears them.
  So the PBL is not running a BHI state machine at all.
- BHI identity registers are real: version 1.2, serial 0x81efa74f, hwid 0x0012d0e1,
  segs 1 -- the PBL is alive, it simply does not serve BHI.

Ruled out (each with a run): the SMMU configuration (p180/p185, eight candidate stream ids
all silent), the inbound iATU window (p198: 0xa0000000-0xa007ffff -> 0x192528000, readback
correct, no effect), the doorbell sequence number, both the BHI and the BHIE protocol, the
MHI reset pulse (p182/p184), and the radio rail voltages.

The rail voltages were wrong until p202 -- the driver carried the lemonade table
{1800, 2700, 950, 950, 1900, 1350} while venus' device tree asks for
{io 1800, ant-switch 2800, aon 1012, dig 1012, rfa1 1900, rfa2 1350}.  apply-206 fixed
ldoe7 2700->2800, smpe2 950->1012, smpb11 950->1012 and p202 confirmed all six rails are now
voted at the dtb voltages.  The headroom is real but was not the cause.

Next candidates, in the order I would try them:
1. Print star's 23 GCC clock registers (inspect() in lemonade_wifi.c:273-282) plus the six
   GPIOs {64, 65, 94, 95, 96, 153}; venus' cnss node has qcom,sw-ctrl-gpio = GPIO 153 which
   we have never driven.
2. Try driving GPIO 153 (sw-ctrl) high before the doorbell.
3. Check whether the endpoint wants MSI configured first: the vendor's
   mhi_async_power_up() refuses to run with msi_allocated < total_ev_rings, and venus'
   config space advertises 32 MSI vectors against 0xa0000040 (the GIC ITS doorbell).
4. Re-read whether venus' BHI window is really at bar+0x100 (BHIOFF = 0x28 reads 0x100,
   BHIEOFF = 0x2c reads 0x224), or whether the 2 MB BAR0 has another BHI copy.

Recovery and dump recipes are unchanged: cold boot only (fastboot boot img-wr2.bin from ABL,
one oem run per boot); oem dump logdump 0 100000 then get_staged ld-<Tag>.bin (1,048,576 B);
grep -a -o "pcie: 5:   21: [^"]\{0,190\}" ld-*.bin.  A hung phone needs a 20 s power hold.

## 2026-11-08 evening -- the BHI transfer finally works, and stops at the SBL

The iATU inbound window was eating the SMMU translation.  p196 showed both
inbound windows empty; apply-199 then programmed inbound 0 as
0xa0000000-0xa007ffff -> pcie_dma_pa, and every BHI fetch since then carried
FAR equal to the iATU's own output (0x192528000, 0x19252c000, ...).  apply-214
removed that window, and p210 finally got BHI_STATUS = 0x82dc6454: top two bits
10 (SUCCESS), low 30 bits our doorbell sequence, ERRCODE 0, no SMMU fault.  It
reproduces on every cold boot, at the fourth 100 ms poll.

What still does not happen is the SBL taking over: EXECENV (bar+0x128) stays 0
(PBL) and MHISTATUS.READY stays 0 for the whole 15 s window.  star's PBL flips
EXECENV to 1 (SBL) at exactly this point, so the difference is real.

Things ruled out with an experiment each: SMMU page tables (128-page walk, l3[4]
matches kvtophys), CBAR/CBA2R/TCR/SCTLR, iATU outbound and inbound, doorbell
sequence, the six radio rails (corrected to the dtb's 1800/2800/1012/1012/1900/1350),
VOTE_0_MASK bit 12 (the PCIe0 aggre-noc AXI clock; without it the PBL's DMA never
reached the SMMU at all), the MHI context bases at 0x58/0x60/0x68 (apply-219,
ineffective as expected because vendor writes them only after READY), and the
512 KiB window (amss.bin is a plain ELF32 with 18 program headers; its entry
0x01439500 sits inside the first segment at file offset 0x2000, so 512 KiB
carries the whole SBL).

apply-220 enables MSI on the endpoint (conf+0x50, enable bit only, address left
at 0xa0000040) and p216 is built.  If that changes nothing, the remaining
difference is on the PBL's side, and the next experiment should be a deliberately
corrupt image: feed it garbage (or half an image) and watch ERRCODE/ERRDBG1-3.
Different errors mean PBL is parsing the image; identical SUCCESS plus no jump
means it never gets that far.

Also worth remembering for the log: during the 15 s wait the `buttons` line
prints once a second, and the 1 MB log ring is small enough that earlier lines
(including a `bar0 0x128` print) were overwritten in p215.  Put any diagnostic
that matters at the very end of the run, or shorten the wait.
