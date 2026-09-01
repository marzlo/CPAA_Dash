# CPAA Dashboard 自動化部署設定步驟

這個檔案包裡的東西,可以讓 GitHub 每天自動去 Jira 撈最新的 CPAA 票、重新產生
`dashboard.html`,並且發布到一個公開的 GitHub Pages 網址上,不需要你再手動匯出
CSV、上傳給 Claude。

**注意(資料公開性)**:GitHub Free 方案的 Pages 只能對「public repo」開啟。也就是說,
這個 repo 裡的原始碼 —— 包含 `scripts/build_data.py` 裡的 `TEAM_MAP`(同事姓名 →
所屬組織的對應表)—— 會是任何人都看得到、Google 也搜得到的公開內容,不只是最後產生的
`dashboard.html` 網頁而已。你先前確認過 dashboard 本身「有連結就能看,不設密碼」沒問題,
但如果連原始碼裡的人名對應表也公開會讓你在意,請在開始之前告訴我,我可以把 `TEAM_MAP`
改成從一個不進 git 版控的檔案讀取,或是改用 GitHub 的私有 Pages 方案(需要 GitHub Team
以上的付費方案,不算免費了)。

## 檔案結構

```
.github/workflows/refresh-dashboard.yml   # 排程 + 手動觸發的自動化流程
scripts/fetch_jira.py                      # 呼叫 Jira API,把票匯出成 CSV
scripts/build_data.py                      # CSV -> dashboard_data.json(跟你現在用的邏輯完全一樣)
scripts/gen_dashboard.py                   # dashboard_data.json -> dashboard.html
```

## 步驟 1:建立 GitHub repo

1. 到 GitHub 建立一個新的 **public** repo(例如叫 `cpaa-dashboard`)。
2. 把這個檔案包裡的所有檔案(含 `.github` 資料夾)上傳 / push 進這個 repo,
   保持原本的資料夾結構。

## 步驟 2:申請 Jira API Token

建議用一個大家共用的服務帳號(而不是你個人帳號)申請,方便以後交接、也比較好管控權限。
1. 用該帳號登入 https://id.atlassian.com/manage-profile/security/api-tokens
2. 建立一個新的 API token,複製起來(只會顯示一次)。
3. 記下這個帳號的登入 email。

## 步驟 3:在 GitHub repo 設定 Secrets

到 repo 的 **Settings → Secrets and variables → Actions → New repository secret**,新增兩個:

| Secret 名稱       | 值                                   |
|-------------------|--------------------------------------|
| `JIRA_EMAIL`      | 步驟 2 那個帳號的 email               |
| `JIRA_API_TOKEN`  | 步驟 2 產生的 API token               |

## 步驟 4:開啟 GitHub Pages

到 repo 的 **Settings → Pages**,「Build and deployment → Source」選擇
**GitHub Actions**(不要選 "Deploy from a branch")。

## 步驟 5:手動跑一次

到 repo 的 **Actions** 分頁,選左邊的 **Refresh CPAA Dashboard**,右上角按
**Run workflow** 手動觸發一次,確認整個流程(抓 Jira → 產生 dashboard_data.json →
產生 dashboard.html → 部署到 Pages)成功跑完,沒有紅色錯誤。

跑完之後,Settings → Pages 頁面上方會顯示你的公開網址,格式通常是:

```
https://<你的 GitHub 帳號>.github.io/<repo 名稱>/
```

## 之後

`.github/workflows/refresh-dashboard.yml` 裡設定的是每天 UTC 01:00(台北時間早上 9 點)
自動跑一次,一樣可以隨時到 Actions 分頁手動觸發。JQL 篩選條件目前寫死是
`filter=12399`(跟你現在手動匯出用的同一個 Jira Filter),如果之後篩選條件換了,
改 `.github/workflows/refresh-dashboard.yml` 裡 `JIRA_JQL` 那一行就好。

**這條自動化 pipeline 目前還沒有辦法自動判斷新出現、還沒對應到組織的 assignee**
(現在都是你回答我、我再手動加進 `TEAM_MAP`)。如果之後 Jira 上出現新同事、
新的 assignee,dashboard 上該同事的票會先被歸在「Unknown」,需要有人發現後手動修改
`scripts/build_data.py` 裡的 `TEAM_MAP` 再重新 push 一次,才會在下次跑的時候生效。
