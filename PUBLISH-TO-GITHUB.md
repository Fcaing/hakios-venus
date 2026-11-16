# 发布到 GitHub

仓库已经在桌面：`C:\Users\Administrator\Desktop\hakios-venus`。
下面三步即可上线（这台机器**没有装 git**，先看第 0 步）。

---

## 0. 装 git（任选其一）

| 方式 | 命令 / 操作 |
|---|---|
| winget（最快） | `winget install --id Git.Git -e --source winget` |
| 官网安装包 | <https://git-scm.com/download/win> |
| GitHub Desktop | <https://desktop.github.com>（图形化，适合不想碰命令行） |

装完新开一个 PowerShell 窗口，`git --version` 能出版本号就算成功。

---

## 1. 首次提交

```powershell
cd C:\Users\Administrator\Desktop\hakios-venus

git init -b main
git config user.name  "你的名字"
git config user.email "你的邮箱"

git add .
git status --short          # 先看一眼：不该有 .bin/.apfs/amss.bin/大日志
git commit -m "venus: iOS 16.5 bring-up docs, PCIe/MHI experiment record, tooling"
```

`.gitignore` 已经把 `*.bin`、`*.apfs`、`*.img`、`amss*.bin`、`bdwlan.*`、`p[0-9][0-9][0-9].txt`、`*.log`、`tools/platform-tools/` 全部排除了。
提交前务必确认 `git status` 里**没有**几十 MB 的文件——一旦推上去，历史里就删不掉了。

---

## 2. 建远程仓库并推上去

### 方式 A：用 GitHub CLI（推荐）

```powershell
winget install --id GitHub.cli -e --source winget      # 若未安装
gh auth login                                          # 浏览器授权一次
gh repo create hakios-venus --public --source=. --remote=origin --push
```

### 方式 B：网页建仓 + 手动推

1. 打开 <https://github.com/new>，仓库名 **`hakios-venus`**，**不要**勾选 "Add a README / .gitignore / license"（本地都有了）。
2. 复制页面给的地址，然后：

```powershell
git remote add origin https://github.com/<你的用户名>/hakios-venus.git
git push -u origin main
```

第一次 `push` 会要求认证：用 **Personal Access Token**（Settings → Developer settings → Personal access tokens → Fine-grained，权限选 `Contents: Read and write`）当密码，**不要**用账号密码。

---

## 3. 建议的仓库设置

| 项 | 建议值 |
|---|---|
| Description | `iOS 16.5 (HakiOS/XNU) bring-up on Xiaomi 11 (venus/SM8350) + QCA6490 Wi-Fi PCIe/MHI experiment log` |
| Topics | `ios` `xnu` `hakios` `xiaomi-11` `sm8350` `qca6490` `wcn6855` `mhi` `pcie` `kernel` |
| License | 选 **View license**（仓库自带 `LICENSE` 与 `LICENSE-APSL-2.0.txt`，不要在网页上再生成一个） |
| Default branch | `main` |
| Releases | **不要**上传 payload/镜像；本项目不发布可刷二进制 |

---

## 4. 把下一步变成 Issue（可选，但很有用）

`docs/03-next-steps.md` 里的 P1–P6 直接可以当六个 issue，标题建议：

```
P1  验证 AMSS 跑的是不是我们下载的镜像（截断 / 改字节 / amss20 三连）
P2  重开 RDDM，抓固件崩溃转储（缓冲区必须落在镜像区之外）
P3  star（11 Ultra）MHI 日志对齐：EE=1 写 M0 为什么在它上面不崩
P4  QURT stub 解析：定位 ipc_router_xal_up 的调用方
P5  QRTR-over-MHI → WLFW QMI → board-2.bin → ath11k 扫描（不占设备）
P6  兜底：USB 网卡 / USB tether
```

每个 issue 的验收标准照 `docs/03-next-steps.md` 第 8 节写死，避免"看起来设备收到了"这类自我安慰。

---

## 5. 发布前自查（30 秒）

```powershell
# 1) 仓库体积（健康值 < 3 MB）
(Get-ChildItem -Recurse -File | Measure-Object Length -Sum).Sum / 1MB

# 2) 有没有混进二进制 / 固件
Get-ChildItem -Recurse -File | Where-Object { $_.Extension -in '.bin','.apfs','.img','.efi','.ipsw','.ipa' }

# 3) 链接是否都能点开（README 里的相对路径）
Get-Content README.md | Select-String '\]\(.*\.md\)'
```

三项都干净再推。

---

## 6. 别做的事

- **别**把 `references/`、`phone-dump/`、`Xiaomi_Kernel_OpenSource-venus-r-oss/` 一起提交（后者 919 MB）。
- **别**为了保证"能跑"而把 `amss.bin` 传上来——它会让仓库直接变成"厂商固件分发站"。
- **别**加 `--force` 推，尤其在你之后又提交了别的东西时。
- 如果已经误推了大文件，用 `git filter-repo` 重写历史，别指望 `git rm` 能解决。
