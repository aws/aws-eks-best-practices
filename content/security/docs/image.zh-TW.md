# 映像安全性

您應該將容器映像視為防禦攻擊的第一道防線。不安全、構建不當的映像可能會允許攻擊者逃脫容器的界限並獲得對主機的訪問權限。一旦進入主機,攻擊者就可以訪問敏感信息或在集群或 AWS 帳戶內進行橫向移動。以下最佳實踐將有助於降低發生這種情況的風險。

## 建議

### 創建最小映像

首先從容器映像中刪除所有多餘的二進制文件。如果您正在使用來自 Dockerhub 的不熟悉的映像,請使用像 [Dive](https://github.com/wagoodman/dive) 這樣的應用程序檢查映像,它可以向您顯示容器每一層的內容。刪除所有帶有 SETUID 和 SETGID 位的二進制文件,因為它們可用於權限提升,並考慮刪除所有 shell 和實用程序,如 nc 和 curl,它們可用於不當目的。您可以使用以下命令找到帶有 SETUID 和 SETGID 位的文件:

```bash
find / -perm /6000 -type f -exec ls -ld {} \;
```

要從這些文件中刪除特殊權限,請在您的容器映像中添加以下指令:

```docker
RUN find / -xdev -perm /6000 -type f -exec chmod a-s {} \; || true
```

俗稱,這被稱為去除映像的牙齒。

### 使用多級構建

使用多級構建是創建最小映像的一種方式。通常,多級構建用於自動化持續集成週期的某些部分。例如,多級構建可用於 lint 您的源代碼或執行靜態代碼分析。這為開發人員提供了一個機會,可以獲得幾乎即時的反饋,而不是等待管道執行。從安全角度來看,多級構建很有吸引力,因為它們允許您最小化推送到容器註冊表的最終映像的大小。沒有構建工具和其他多餘二進制文件的容器映像可以通過減少映像的攻擊面來改善您的安全態勢。有關多級構建的更多信息,請參閱 [Docker 的多級構建文檔](https://docs.docker.com/develop/develop-images/multistage-build/)。

### 為您的容器映像創建軟件清單 (SBOM)

"軟件清單"(SBOM) 是構成您的容器映像的軟件工件的嵌套清單。
SBOM 是軟件安全和軟件供應鏈風險管理的關鍵組成部分。[生成、在中央存儲庫中存儲 SBOM 並掃描 SBOM 以查找漏洞](https://anchore.com/sbom/)有助於解決以下問題:

- **可見性**: 了解構成您的容器映像的組件。將其存儲在中央存儲庫中允許隨時審核和掃描 SBOM,甚至在部署後檢測和響應新的漏洞,如零日漏洞。
- **來源驗證**: 確保對工件及其隨附元數據的來源和生成方式的現有假設是真實的,並且工件或其隨附元數據在構建或交付過程中沒有被篡改。
- **可信度**: 確保給定的工件及其內容可以被信任,即可以做它所宣稱要做的事情,即適合某種用途。這涉及對代碼是否安全執行的判斷,並對執行代碼的風險做出明智決定。可信度通過創建經過認證的管道執行報告以及經過認證的 SBOM 和經過認證的 CVE 掃描報告來確保,以確保映像的消費者該映像實際上是通過安全方式(管道)使用安全組件創建的。
- **依賴信任驗證**: 對工件使用的依賴項樹的可信度和來源進行遞歸檢查。SBOM 中的偏差可以幫助檢測惡意活動,包括未經授權、不受信任的依賴項、入侵企圖。

以下工具可用於生成 SBOM:

- [Amazon Inspector](https://docs.aws.amazon.com/inspector) 可用於[創建和導出 SBOM](https://docs.aws.amazon.com/inspector/latest/user/sbom-export.html)。
- [Anchore 的 Syft](https://github.com/anchore/syft) 也可用於 SBOM 生成。為了更快地進行漏洞掃描,為容器映像生成的 SBOM 可用作輸入進行掃描。然後將 SBOM 和掃描報告[認證並附加](https://github.com/sigstore/cosign/blob/main/doc/cosign_attach_attestation.md)到映像上,然後將映像推送到中央 OCI 存儲庫(如 Amazon ECR)以供審查和審計。

通過查看 [CNCF 軟件供應鏈最佳實踐指南](https://project.linuxfoundation.org/hubfs/CNCF_SSCP_v1.pdf)瞭解有關保護您的軟件供應鏈的更多信息。

### 定期掃描映像以查找漏洞

與其虛擬機器對應物一樣,容器映像也可能包含有漏洞的二進制文件和應用程序庫,或者隨著時間的推移而產生漏洞。防止利用的最佳方式是使用映像掃描器定期掃描您的映像。存儲在 Amazon ECR 中的映像可以在推送時或按需掃描(在 24 小時內一次)。ECR 目前支持[兩種類型的掃描 - 基本和增強](https://docs.aws.amazon.com/AmazonECR/latest/userguide/image-scanning.html)。基本掃描利用開源映像掃描解決方案 [Clair](https://github.com/quay/clair) 免費。[增強掃描](https://docs.aws.amazon.com/AmazonECR/latest/userguide/image-scanning-enhanced.html)使用 Amazon Inspector 提供自動持續掃描[額外費用](https://aws.amazon.com/inspector/pricing/)。掃描映像後,結果將記錄到 EventBridge 中的 ECR 事件流。您也可以從 ECR 控制台查看掃描結果。具有高或關鍵漏洞的映像應該被刪除或重建。如果已部署的映像出現漏洞,應盡快更換。

知道具有漏洞的映像部署到哪裡對於保持環境安全至關重要。雖然您可以自己構建映像跟踪解決方案,但已經有幾種商業產品可以開箱即用地提供此功能和其他高級功能,包括:

- [Grype](https://github.com/anchore/grype)
- [Palo Alto - Prisma Cloud (twistcli)](https://docs.paloaltonetworks.com/prisma/prisma-cloud/prisma-cloud-admin-compute/tools/twistcli_scan_images)
- [Aqua](https://www.aquasec.com/)
- [Kubei](https://github.com/Portshift/kubei)
- [Trivy](https://github.com/aquasecurity/trivy)
- [Snyk](https://support.snyk.io/hc/en-us/articles/360003946917-Test-images-with-the-Snyk-Container-CLI)

Kubernetes 驗證 webhook 也可用於驗證映像沒有關鍵漏洞。驗證 webhook 在 Kubernetes API 之前被調用。它們通常用於拒絕不符合 webhook 中定義的驗證標準的請求。[這](https://aws.amazon.com/blogs/containers/building-serverless-admission-webhooks-for-kubernetes-with-aws-sam/)是一個無服務器 webhook 的示例,它調用 ECR describeImageScanFindings API 來確定 pod 是否正在拉取具有關鍵漏洞的映像。如果發現漏洞,pod 將被拒絕,並返回一條帶有 CVE 列表的事件消息。

### 使用認證來驗證工件完整性

認證是一個加密簽名的"聲明",聲明某些事情 - 一個"謂詞",例如管道運行或 SBOM 或漏洞掃描報告,關於另一件事 - 一個"主題"即容器映像是真實的。

認證幫助用戶驗證工件是否來自軟件供應鏈中的可信來源。例如,我們可能會使用容器映像而不知道該映像中包含的所有軟件組件或依賴項。但是,如果我們信任容器映像的生產者所說的關於存在哪些軟件的話,我們就可以使用生產者的認證來依賴該工件。這意味著我們可以安全地在工作流程中使用該工件,而不是自己進行分析。

- 可以使用 [AWS Signer](https://docs.aws.amazon.com/signer/latest/developerguide/Welcome.html) 或 [Sigstore cosign](https://github.com/sigstore/cosign/blob/main/doc/cosign_attest.md) 創建認證。
- Kubernetes 准入控制器,如 [Kyverno](https://kyverno.io/) 可用於[驗證認證](https://kyverno.io/docs/writing-policies/verify-images/sigstore/)。
- 參考此[工作坊](https://catalog.us-east-1.prod.workshops.aws/workshops/49343bb7-2cc5-4001-9d3b-f6a33b3c4442/en-US/0-introduction)瞭解有關在 AWS 上使用開源工具的軟件供應鏈管理最佳實踐的更多信息,包括為容器映像創建和附加認證的主題。

### 為 ECR 存儲庫創建 IAM 策略

如今,在共享 AWS 帳戶內有多個獨立運作的開發團隊並不罕見。如果這些團隊不需要共享資產,您可能希望創建一組 IAM 策略來限制每個團隊可以與之交互的存儲庫。實現這一點的一個好方法是使用 ECR [命名空間](https://docs.aws.amazon.com/AmazonECR/latest/userguide/Repositories.html#repository-concepts)。命名空間是將類似的存儲庫分組在一起的一種方式。例如,團隊 A 的所有註冊表可以使用 team-a/ 作為前綴,而團隊 B 的註冊表可以使用 team-b/ 前綴。限制訪問的策略可能如下所示:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowPushPull",
      "Effect": "Allow",
      "Action": [
        "ecr:GetDownloadUrlForLayer",
        "ecr:BatchGetImage",
        "ecr:BatchCheckLayerAvailability",
        "ecr:PutImage",
        "ecr:InitiateLayerUpload",
        "ecr:UploadLayerPart",
        "ecr:CompleteLayerUpload"
      ],
      "Resource": [
        "arn:aws:ecr:<region>:<account_id>:repository/team-a/*"
      ]
    }
  ]
}
```

### 考慮使用 ECR 私有端點

ECR API 有一個公共端點。因此,只要請求已通過 IAM 進行身份驗證和授權,就可以從互聯網訪問 ECR 註冊表。對於需要在沒有互聯網網關 (IGW) 的 VPC 中運行的人員,您可以為 ECR 配置私有端點。創建私有端點可以使您通過私有 IP 地址而不是通過互聯網路由流量來私密訪問 ECR API。有關此主題的更多信息,請參閱 [Amazon ECR 接口 VPC 端點](https://docs.aws.amazon.com/AmazonECR/latest/userguide/vpc-endpoints.html)。

### 為 ECR 實現端點策略

區域中的 ECR 的默認端點策略允許訪問所有 ECR 存儲庫。這可能會允許攻擊者/內部人員將數據打包為容器映像並將其推送到另一個 AWS 帳戶中的註冊表中,從而導致數據外洩。緩解此風險涉及創建一個端點策略,該策略限制對 ECR 存儲庫的 API 訪問。例如,以下策略允許您帳戶中的所有 AWS 主體對您自己的 ECR 存儲庫執行所有操作:

```json
{
  "Statement": [
    {
      "Sid": "LimitECRAccess",
      "Principal": "*",
      "Action": "*",
      "Effect": "Allow",
      "Resource": "arn:aws:ecr:<region>:<account_id>:repository/*"
    }
  ]
}
```

您可以通過設置使用新的 `PrincipalOrgID` 屬性的條件來增強此策略,這將防止不屬於您的 AWS 組織的 IAM 主體推送/拉取映像。請參閱 [aws:PrincipalOrgID](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_condition-keys.html#condition-keys-principalorgid) 以獲取更多詳細信息。
我們建議將相同的策略應用於 `com.amazonaws.<region>.ecr.dkr` 和 `com.amazonaws.<region>.ecr.api` 端點。
由於 EKS 從 ECR 為 kube-proxy、coredns 和 aws-node 拉取映像,因此您需要將註冊表的帳戶 ID(例如 `602401143452.dkr.ecr.us-west-2.amazonaws.com/*`)添加到端點策略中的資源列表中,或者修改策略以允許從"*"拉取並將推送限制為您的帳戶 ID。下表顯示了 EKS 映像供應商的 AWS 帳戶與集群區域之間的映射關係。

|帳號號碼 |區域 |
|--- |--- |
|602401143452 |除下面列出的區域外的所有商業區域 |
|--- |--- |
|800184023465 |ap-east-1 - 亞太地區(香港) |
|558608220178 |me-south-1 - 中東(巴林) |
|918309763551 |cn-north-1 - 中國(北京) |
|961992271922 |cn-northwest-1 - 中國(寧夏) |

有關使用端點策略的更多信息,請參閱[使用 VPC 端點策略控制對 Amazon ECR 的訪問](https://aws.amazon.com/blogs/containers/using-vpc-endpoint-policies-to-control-amazon-ecr-access/)。

### 為 ECR 實現生命週期策略

[NIST 應用程序容器安全指南](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-190.pdf)警告了"註冊表中陳舊映像"的風險,指出隨著時間的推移,應刪除具有易受攻擊、過時的軟件包的舊映像,以防止意外部署和暴露。
每個 ECR 存儲庫都可以有一個生命週期策略,用於設置映像過期的規則。[AWS 官方文檔](https://docs.aws.amazon.com/AmazonECR/latest/userguide/LifecyclePolicies.html)描述了如何設置測試規則、評估它們並將其應用。官方文檔中有幾個[生命週期策略示例](https://docs.aws.amazon.com/AmazonECR/latest/userguide/lifecycle_policy_examples.html),顯示了在存儲庫中過濾映像的不同方式:

- 按映像年齡或計數過濾
- 按帶標籤或無標籤映像過濾
- 按映像標籤過濾,無論是在多個規則中還是單個規則中

???+ warning
    如果長期運行的應用程序的映像從 ECR 中被刪除,則在重新部署或水平擴展應用程序時可能會導致映像拉取錯誤。使用映像生命週期策略時,請確保您有良好的 CI/CD 實踐來保持部署和它們引用的映像的最新狀態,並始終創建考慮到您的發佈/部署頻率的[映像]過期規則。

### 創建一組精選映像

與其允許開發人員創建自己的映像,不如為組織中的不同應用程序棧創建一組經過審查的映像。這樣做,開發人員就可以避免學習如何編寫 Dockerfile,而專注於編寫代碼。隨著更改合併到主分支,CI/CD 管道可以自動編譯資產、將其存儲在工件存儲庫中,並將工件複製到適當的映像中,然後將其推送到 Docker 註冊表(如 ECR)。至少,您應該為開發人員創建一組基礎映像,以便他們創建自己的 Dockerfile。理想情況下,您要避免從 Dockerhub 拉取映像,因為 1/ 您不總是知道映像中包含什麼,2/ 大約[五分之一](https://www.kennasecurity.com/blog/one-fifth-of-the-most-used-docker-containers-have-at-least-one-critical-vulnerability/)的前 1000 個映像存在漏洞。這些映像及其漏洞的列表可以在[這裡](https://vulnerablecontainers.org/)找到。

### 在您的 Dockerfile 中添加 USER 指令以作為非 root 用戶運行

正如在 pod 安全性部分中提到的,您應該避免以 root 用戶身份運行容器。雖然您可以將其配置為 podSpec 的一部分,但在 Dockerfile 中使用 `USER` 指令是一個良好的習慣。`USER` 指令設置在 USER 指令之後出現的 `RUN`、`ENTRYPOINT` 或 `CMD` 指令時要使用的 UID。

### Lint 您的 Dockerfile

Lint 可用於驗證您的 Dockerfile 是否符合創建安全映像的一組預定義準則,例如包含 `USER` 指令或要求所有映像都被標記。[dockerfile_lint](https://github.com/projectatomic/dockerfile_lint) 是 RedHat 的一個開源項目,它驗證常見的最佳實踐,並包含一個規則引擎,您可以使用它來構建自己的 Dockerfile lint 規則。它可以併入 CI 管道中,因此違反規則的構建 Dockerfile 將自動失敗。

### 從 Scratch 構建映像

減少容器映像的攻擊面應該是構建映像時的主要目標。實現這一點的理想方式是創建最小的映像,這些映像不包含可用於利用漏洞的二進制文件。幸運的是,Docker 有一種機制可以從 [`scratch`](https://docs.docker.com/develop/develop-images/baseimages/#create-a-simple-parent-image-using-scratch) 創建映像。對於像 Go 這樣的語言,您可以創建一個靜態鏈接的二進制文件,並在您的 Dockerfile 中引用它,如下例所示:

```docker
############################
# 步驟 1 構建可執行二進制文件
############################
FROM golang:alpine AS builder# 安裝 git。
# 獲取依賴項需要 Git。
RUN apk update && apk add --no-cache gitWORKDIR $GOPATH/src/mypackage/myapp/COPY . . # 獲取依賴項。
# 使用 go get。
RUN go get -d -v# 構建二進制文件。
RUN go build -o /go/bin/hello

############################
# 步驟 2 構建小型映像
############################
FROM scratch# 複製我們的靜態可執行文件。
COPY --from=builder /go/bin/hello /go/bin/hello# 運行 hello 二進制文件。
ENTRYPOINT ["/go/bin/hello"]
```

這將創建一個僅包含您的應用程序的容器映像,使其非常安全。

### 使用 ECR 的不可變標籤

[不可變標籤](https://aws.amazon.com/about-aws/whats-new/2019/07/amazon-ecr-now-supports-immutable-image-tags/)強制您在每次推送到映像存儲庫時更新映像標籤。這可以阻止攻擊者在不更改映像標籤的情況下用惡意版本覆蓋映像。此外,它為您提供了一種輕鬆且唯一地識別映像的方式。

### 為您的映像、SBOM、管道運行和漏洞報告簽名

當 Docker 剛推出時,沒有加密模型來驗證容器映像。在 v2 中,Docker 為映像清單添加了摘要。這允許對映像配置進行哈希運算,並使用哈希為映像生成 ID。啟用映像簽名後,Docker 引擎將驗證清單的簽名,確保內容是從可信來源生成的,並且沒有發生篡改。下載每一層後,引擎將驗證該層的摘要,確保內容與清單中指定的內容匹配。映像簽名實際上允許您創建一個安全的供應鏈,通過驗證與映像關聯的數字簽名。

我們可以使用 [AWS Signer](https://docs.aws.amazon.com/signer/latest/developerguide/Welcome.html) 或 [Sigstore Cosign](https://github.com/sigstore/cosign) 為容器映像、SBOM、漏洞掃描報告和管道運行報告簽名並創建認證。這些認證確保了映像的可信度和完整性,確實是由可信管道創建的,沒有任何干擾或篡改,並且只包含映像發佈者驗證和信任的軟件組件(在 SBOM 中記錄)。這些認證可以附加到容器映像上並推送到存儲庫。

在下一節中,我們將看到如何使用經過認證的工件進行審計和准入控制器驗證。

### 使用 Kubernetes 准入控制器進行映像完整性驗證

我們可以使用[動態准入控制器](https://kubernetes.io/blog/2019/03/21/a-guide-to-kubernetes-admission-controllers/)在自動化方式下部署映像到目標 Kubernetes 集群之前驗證映像簽名、經過認證的工件,並且只有在工件的安全元數據符合准入控制器策略時才允許部署。

例如,我們可以編寫一個策略來加密驗證映像的簽名、經過認證的 SBOM、經過認證的管道運行報告或經過認證的 CVE 掃描報告。我們可以在策略中編寫條件來檢查報告中的數據,例如 CVE 掃描不應該有任何關鍵 CVE。只有滿足這些條件的映像才允許部署,所有其他部署都將被准入控制器拒絕。

准入控制器示例包括:

- [Kyverno](https://kyverno.io/)
- [OPA Gatekeeper](https://github.com/open-policy-agent/gatekeeper)
- [Portieris](https://github.com/IBM/portieris)
- [Ratify](https://github.com/deislabs/ratify)
- [Kritis](https://github.com/grafeas/kritis)
- [Grafeas 教程](https://github.com/kelseyhightower/grafeas-tutorial)
- [Voucher](https://github.com/Shopify/voucher)

### 更新您的容器映像中的包

您應該在您的 Dockerfile 中包含 RUN `apt-get update && apt-get upgrade` 以升級映像中的包。雖然升級需要以 root 身份運行,但這是在映像構建階段發生的。應用程序不需要以 root 身份運行。您可以安裝更新,然後切換到其他用戶使用 USER 指令。如果您的基礎映像以非 root 用戶身份運行,請切換到 root 並返回;不要僅依賴基礎映像的維護者來安裝最新的安全更新。

運行 `apt-get clean` 以從 `/var/cache/apt/archives/` 中刪除安裝程序文件。安裝包後,您還可以運行 `rm -rf /var/lib/apt/lists/*`。這將刪除可安裝包的索引文件或列表。請注意,對於每個包管理器,這些命令可能會有所不同。例如:

```docker
RUN apt-get update && apt-get install -y \
    curl \
    git \
    libsqlite3-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*
```

## 工具和資源

- [Amazon EKS 安全沉浸式工作坊 - 映像安全性](https://catalog.workshops.aws/eks-security-immersionday/en-US/12-image-security)
- [docker-slim](https://github.com/docker-slim/docker-slim) 構建安全的最小映像
- [dockle](https://github.com/goodwithtech/dockle) 驗證您的 Dockerfile 是否符合創建安全映像的最佳實踐
- [dockerfile-lint](https://github.com/projectatomic/dockerfile_lint) Dockerfile 的基於規則的 linter
- [hadolint](https://github.com/hadolint/hadolint) 一個智能 dockerfile linter
- [Gatekeeper 和 OPA](https://github.com/open-policy-agent/gatekeeper) 基於策略的准入控制器
- [Kyverno](https://kyverno.io/) 一個原生 Kubernetes 策略引擎
- [in-toto](https://in-toto.io/) 允許用戶驗證供應鏈中的步驟是否有意執行,以及步驟是否由正確的參與者執行
- [Notary](https://github.com/theupdateframework/notary) 一個用於簽名容器映像的項目
- [Notary v2](https://github.com/notaryproject/nv2)
- [Grafeas](https://grafeas.io/) 一個開放的工件元數據 API,用於審計和管理您的軟件供應鏈
- [SUSE 的 NeuVector](https://www.suse.com/neuvector/) 開源、零信任容器安全平台,提供容器、映像和註冊表掃描以查找漏洞、密碼和合規性。
