# 合規性

合規性是 AWS 與其服務消費者之間的共同責任。一般而言,AWS 負責「雲端的安全性」,而其用戶則負責「雲端中的安全性」。AWS 和其用戶負責的界線因服務而異。例如,對於 Fargate 而言,AWS 負責管理其數據中心的實體安全性、硬件、虛擬基礎設施 (Amazon EC2) 和容器運行時 (Docker)。Fargate 的用戶則負責確保容器映像和應用程序的安全性。了解誰負責什麼是在運行必須遵守合規標準的工作負載時的一個重要考慮因素。

下表顯示了不同容器服務符合的合規性程序。

| 合規性程序 | Amazon ECS 編排器 | Amazon EKS 編排器| ECS Fargate | Amazon ECR |
| ------------------ |:----------:|:----------:|:-----------:|:----------:|
| PCI DSS 第 1 級 | 1 | 1 | 1 | 1 |
| HIPAA 合格 | 1 | 1 | 1 | 1 |
| SOC I | 1 | 1 | 1 | 1 |
| SOC II | 1 | 1 | 1 | 1 |
| SOC III | 1 | 1 | 1 | 1 |
| ISO 27001:2013 | 1 | 1 | 1 | 1 |
| ISO 9001:2015 | 1 | 1 | 1 | 1 |
| ISO 27017:2015 | 1 | 1 | 1 | 1 |
| ISO 27018:2019 | 1 | 1 | 1 | 1 |
| IRAP | 1 | 1 | 1 | 1 |
| FedRAMP Moderate (東/西) | 1 | 1 | 0 | 1 |
| FedRAMP High (GovCloud) | 1 | 1 | 0 | 1 |
| DOD CC SRG | 1 | DISA 審查 (IL5) | 0 | 1 |
| HIPAA BAA | 1 | 1 | 1 | 1 |
| MTCS | 1 | 1 | 0 | 1 |
| C5 | 1 | 1 | 0 | 1 |
| K-ISMS | 1 | 1 | 0 | 1 |
| ENS High | 1 | 1 | 0 | 1 |
| OSPAR | 1 | 1 | 0 | 1 |
| HITRUST CSF | 1 | 1 | 1 | 1 |

合規性狀態會隨時間而變化。有關最新狀態,請始終參考 [https://aws.amazon.com/compliance/services-in-scope/](https://aws.amazon.com/compliance/services-in-scope/)。

有關雲端認證模型和最佳實踐的更多資訊,請參閱 AWS 白皮書 [Accreditation Models for Secure Cloud Adoption](https://d1.awsstatic.com/whitepapers/accreditation-models-for-secure-cloud-adoption.pdf)

## 左移

左移的概念是在軟件開發生命週期的較早階段捕獲政策違規和錯誤。從安全角度來看,這可能會很有益。例如,開發人員可以在將其應用程序部署到集群之前修復其配置中的問題。提早發現這樣的錯誤將有助於防止違反您的政策的配置被部署。

### 政策即代碼

政策可以被視為管理行為的一組規則,即允許或禁止的行為。例如,您可能有一個政策規定所有 Dockerfile 都應包含一個 USER 指令,該指令會導致容器以非 root 用戶身份運行。作為一個文件,這樣的政策可能很難被發現和執行。隨著您的要求發生變化,它也可能過時。通過政策即代碼 (PaC) 解決方案,您可以自動化安全性、合規性和隱私控制,以檢測、預防、減少和抵禦已知和持續的威脅。此外,它們為您提供了一種機制來編碼您的政策並像管理其他代碼工件一樣管理它們。這種方法的好處是您可以重用您的 DevOps 和 GitOps 策略來管理和一致地應用於整個 Kubernetes 集群。有關 PaC 選項和 PSP 的未來的資訊,請參閱 [Pod Security](https://aws.github.io/aws-eks-best-practices/security/docs/pods/#pod-security)。

### 在管道中使用政策即代碼工具來檢測部署前的違規行為

- [OPA](https://www.openpolicyagent.org/) 是一個開源政策引擎,是 CNCF 的一部分。它用於做出政策決策,可以以多種不同的方式運行,例如作為語言庫或服務。OPA 政策是用一種名為 Rego 的領域特定語言 (DSL) 編寫的。雖然它通常作為 [Gatekeeper](https://github.com/open-policy-agent/gatekeeper) 項目的一部分運行在 Kubernetes 動態准入控制器中,但 OPA 也可以被納入您的 CI/CD 管道。這允許開發人員在發佈週期的較早階段獲得有關其配置的反饋,從而隨後可以幫助他們在進入生產環境之前解決問題。一組常見的 OPA 政策可以在本項目的 GitHub [repository](https://github.com/aws/aws-eks-best-practices/tree/master/policies/opa) 中找到。
- [Conftest](https://github.com/open-policy-agent/conftest) 建立在 OPA 之上,它為測試 Kubernetes 配置提供了一個面向開發人員的體驗。
- [Kyverno](https://kyverno.io/) 是一個為 Kubernetes 設計的政策引擎。通過 Kyverno,政策被管理為 Kubernetes 資源,無需學習新的語言即可編寫政策。這允許使用熟悉的工具,如 kubectl、git 和 kustomize 來管理政策。Kyverno 政策可以驗證、變更和生成 Kubernetes 資源,並確保 OCI 映像供應鏈安全。[Kyverno CLI](https://kyverno.io/docs/kyverno-cli/) 可以用於在 CI/CD 管道中測試政策和驗證資源。所有 Kyverno 社區政策都可以在 [Kyverno 網站](https://kyverno.io/policies/)上找到,有關在管道中使用 Kyverno CLI 編寫測試的示例,請參閱 [policies repository](https://github.com/kyverno/policies)。

## 工具和資源

- [Amazon EKS Security Immersion Workshop - Regulatory Compliance](https://catalog.workshops.aws/eks-security-immersionday/en-US/10-regulatory-compliance)
- [kube-bench](https://github.com/aquasecurity/kube-bench)
- [docker-bench-security](https://github.com/docker/docker-bench-security)
- [AWS Inspector](https://aws.amazon.com/inspector/)
- [Kubernetes Security Review](https://github.com/kubernetes/community/blob/master/sig-security/security-audit-2019/findings/Kubernetes%20Final%20Report.pdf) Kubernetes 1.13.4 (2019) 的第三方安全評估
- [NeuVector by SUSE](https://www.suse.com/neuvector/) 開源、零信任容器安全平台,提供合規性報告和自定義合規性檢查
