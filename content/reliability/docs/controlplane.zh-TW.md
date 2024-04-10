# EKS 控制平面

Amazon Elastic Kubernetes Service (EKS) 是一項受管理的 Kubernetes 服務,可讓您輕鬆在 AWS 上執行 Kubernetes,而無需安裝、操作和維護自己的 Kubernetes 控制平面或工作節點。它運行上游 Kubernetes 並獲得 Kubernetes 一致性認證。這種一致性確保 EKS 支持 Kubernetes API,就像您可以在 EC2 或內部部署的開源社區版本一樣。運行在上游 Kubernetes 上的現有應用程序與 Amazon EKS 兼容。

EKS 會自動管理 Kubernetes 控制平面節點的可用性和可擴展性,並自動替換不健康的控制平面節點。

## EKS 架構

EKS 架構旨在消除可能危及 Kubernetes 控制平面可用性和持久性的任何單點故障。

由 EKS 管理的 Kubernetes 控制平面運行在 EKS 管理的 VPC 內。EKS 控制平面包括 Kubernetes API 伺服器節點、etcd 集群。運行 API 伺服器、調度程序和 `kube-controller-manager` 等組件的 Kubernetes API 伺服器節點在自動擴展群組中運行。EKS 在 AWS 區域內的不同可用區域 (AZ) 中至少運行兩個 API 伺服器節點。同樣,為了持久性,etcd 伺服器節點也在跨越三個 AZ 的自動擴展群組中運行。EKS 在每個 AZ 中運行一個 NAT 網關,API 伺服器和 etcd 伺服器運行在私有子網路中。這種架構確保單個 AZ 中的事件不會影響 EKS 集群的可用性。

當您創建新集群時,Amazon EKS 會為受管理的 Kubernetes API 伺服器創建一個高可用性端點,您可以使用該端點與集群通信 (使用工具如 `kubectl`)。受管理的端點使用 NLB 來負載平衡 Kubernetes API 伺服器。EKS 還在不同的 AZ 中配置了兩個 [ENI](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-eni.html),以促進與工作節點的通信。

![EKS 數據平面網絡連接](./images/eks-data-plane-connectivity.jpeg)

您可以 [配置您的 Kubernetes 集群的 API 伺服器](https://docs.aws.amazon.com/eks/latest/userguide/cluster-endpoint.html) 是否可從公共互聯網 (使用公共端點) 或通過您的 VPC (使用 EKS 管理的 ENI) 或兩者都可訪問。

無論用戶和工作節點是使用公共端點還是 EKS 管理的 ENI 連接到 API 伺服器,都有冗餘的連接路徑。

## 建議

## 監控控制平面指標

監控 Kubernetes API 指標可以讓您深入了解控制平面性能並識別問題。不健康的控制平面可能會危及集群內運行的工作負載的可用性。例如,編寫不當的控制器可能會使 API 伺服器過載,從而影響您的應用程序可用性。

Kubernetes 在 `/metrics` 端點公開控制平面指標。

您可以使用 `kubectl` 查看公開的指標:

```shell
kubectl get --raw /metrics
```

這些指標以 [Prometheus 文本格式](https://github.com/prometheus/docs/blob/master/content/docs/instrumenting/exposition_formats.md) 表示。

您可以使用 Prometheus 收集和存儲這些指標。2020 年 5 月,CloudWatch 增加了在 CloudWatch Container Insights 中監控 Prometheus 指標的支持。因此,您也可以使用 Amazon CloudWatch 來監控 EKS 控制平面。您可以使用 [教程:添加新的 Prometheus 抓取目標:Prometheus KPI 伺服器指標](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/ContainerInsights-Prometheus-Setup-configure.html#ContainerInsights-Prometheus-Setup-new-exporters) 來收集指標並創建 CloudWatch 儀表板來監控您的集群的控制平面。

您可以在 [這裡](https://github.com/kubernetes/apiserver/blob/master/pkg/endpoints/metrics/metrics.go) 找到 Kubernetes API 伺服器指標。例如,`apiserver_request_duration_seconds` 可以顯示 API 請求運行所需的時間。

考慮監控以下控制平面指標:

### API 伺服器

| 指標 | 描述  |
|:--|:--|
| `apiserver_request_total` | 按動詞、乾運行值、組、版本、資源、範圍、組件和 HTTP 響應代碼劃分的 apiserver 請求計數器。 |
| `apiserver_request_duration_seconds*`  | 按動詞、乾運行值、組、版本、資源、子資源、範圍和組件劃分的以秒為單位的響應延遲分佈。 |
| `apiserver_admission_controller_admission_duration_seconds` | 以秒為單位的準入控制器延遲直方圖,按名稱識別並按每個操作和 API 資源和類型 (驗證或准入) 劃分。 |
| `apiserver_admission_webhook_rejection_count` | 準入 webhook 拒絕計數。按名稱、操作、拒絕代碼、類型 (驗證或准入)、錯誤類型 (調用 webhook 錯誤、apiserver 內部錯誤、無錯誤) 識別。 |
| `rest_client_request_duration_seconds` | 以秒為單位的請求延遲。按動詞和 URL 劃分。 |
| `rest_client_requests_total`  | HTTP 請求數,按狀態代碼、方法和主機劃分。 |

### etcd

| 指標                                                                                                                                                                                    | 描述  
|:------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:--|
| `etcd_request_duration_seconds`                                                                                                                                                           | 以秒為單位的 etcd 請求延遲,按每個操作和對象類型劃分。 |
| `etcd_db_total_size_in_bytes` 或 <br />`apiserver_storage_db_total_size_in_bytes` (從 EKS v1.26 開始) 或 <br />`apiserver_storage_size_bytes` (從 EKS v1.28 開始) | Etcd 數據庫大小。 |

考慮使用 [Kubernetes 監控概述儀表板](https://grafana.com/grafana/dashboards/14623) 來可視化和監控 Kubernetes API 伺服器請求和延遲以及 etcd 延遲指標。

以下 Prometheus 查詢可用於監控 etcd 的當前大小。該查詢假設有一個名為 `kube-apiserver` 的作業用於從 API 指標端點抓取指標,且 EKS 版本低於 v1.26。

```text
max(etcd_db_total_size_in_bytes{job="kube-apiserver"} / (8 * 1024 * 1024 * 1024))
```

!!! 注意
    當數據庫大小超過限制時,etcd 會發出空間不足警報並停止接受進一步的寫入請求。換句話說,集群變為只讀,所有對像創建新 Pod、擴展部署等的變更請求都將被集群的 API 伺服器拒絕。

## 集群身份驗證

EKS 目前支持兩種類型的身份驗證: [持有者/服務帳戶令牌](https://kubernetes.io/docs/reference/access-authn-authz/authentication/#service-account-tokens) 和使用 [webhook 令牌身份驗證](https://kubernetes.io/docs/reference/access-authn-authz/authentication/#webhook-token-authentication) 的 IAM 身份驗證。當用戶調用 Kubernetes API 時,webhook 會將請求中包含的身份驗證令牌傳遞給 IAM。該令牌是由 AWS 命令行界面 ([AWS CLI](https://aws.amazon.com/cli/)) 生成的基於 64 位簽名的 URL。

創建 EKS 集群的 IAM 用戶或角色會自動獲得對集群的完全訪問權限。您可以通過編輯 [`aws-auth` configmap](https://docs.aws.amazon.com/eks/latest/userguide/add-user-role.html) 來管理對 EKS 集群的訪問。

如果您錯誤配置了 `aws-auth` configmap 並失去了對集群的訪問權限,您仍然可以使用集群創建者的用戶或角色來訪問您的 EKS 集群。

在不太可能無法在 AWS 區域中使用 IAM 服務的情況下,您還可以使用 Kubernetes 服務帳戶的持有者令牌來管理集群。

創建一個允許在集群中執行所有操作的"超級管理員"帳戶:

```
kubectl -n kube-system create serviceaccount super-admin
```

創建一個角色綁定,將 cluster-admin 角色授予 super-admin:

```
kubectl create clusterrolebinding super-admin-rb --clusterrole=cluster-admin --serviceaccount=kube-system:super-admin
```

獲取服務帳戶的密鑰:

```
SECRET_NAME=`kubectl -n kube-system get serviceaccount/super-admin -o jsonpath='{.secrets[0].name}'`
```

獲取與密鑰關聯的令牌:

```
TOKEN=`kubectl -n kube-system get secret $SECRET_NAME -o jsonpath='{.data.token}'| base64 --decode`
```

將服務帳戶和令牌添加到 `kubeconfig`:

```
kubectl config set-credentials super-admin --token=$TOKEN
```

將 `kubeconfig` 中的 current-context 設置為使用 super-admin 帳戶:

```
kubectl config set-context --current --user=super-admin
```

最終的 `kubeconfig` 應該如下所示:

```
apiVersion: v1
clusters:
- cluster:
    certificate-authority-data:<REDACTED>
    server: https://<CLUSTER>.gr7.us-west-2.eks.amazonaws.com
  name: arn:aws:eks:us-west-2:<account number>:cluster/<cluster name>
contexts:
- context:
    cluster: arn:aws:eks:us-west-2:<account number>:cluster/<cluster name>
    user: super-admin
  name: arn:aws:eks:us-west-2:<account number>:cluster/<cluster name>
current-context: arn:aws:eks:us-west-2:<account number>:cluster/<cluster name>
kind: Config
preferences: {}
users:
#- name: arn:aws:eks:us-west-2:<account number>:cluster/<cluster name>
#  user:
#    exec:
#      apiVersion: client.authentication.k8s.io/v1alpha1
#      args:
#      - --region
#      - us-west-2
#      - eks
#      - get-token
#      - --cluster-name
#      - <<cluster name>>
#      command: aws
#      env: null
- name: super-admin
  user:
    token: <<super-admin sa's secret>>
```

## 準入 Webhooks

Kubernetes 有兩種類型的準入 Webhooks: [驗證準入 Webhooks 和變更準入 Webhooks](https://kubernetes.io/docs/reference/access-authn-authz/extensible-admission-controllers)。這些允許用戶擴展 kubernetes API,並在對象被 API 接受之前驗證或變更對象。這些 Webhooks 的配置不當可能會通過阻止集群關鍵操作來破壞 EKS 控制平面的穩定性。

為了避免影響集群關鍵操作,請避免設置"全捕獲"Webhooks,如以下所示:

```
- name: "pod-policy.example.com"
  rules:
  - apiGroups:   ["*"]
    apiVersions: ["*"]
    operations:  ["*"]
    resources:   ["*"]
    scope: "*"
```

或者確保 Webhook 具有失效開啟策略,超時時間短於 30 秒,以確保如果您的 Webhook 不可用,它不會損害集群關鍵工作負載。

### 阻止使用不安全 `sysctls` 的 Pod

`Sysctl` 是一個 Linux 實用程序,允許用戶在運行時修改內核參數。這些內核參數控制操作系統行為的各個方面,如網絡、文件系統、虛擬內存和進程管理。

Kubernetes 允許為 Pod 分配 `sysctl` 配置文件。Kubernetes 將 `sysctl` 分為安全和不安全兩種。安全的 `sysctl` 在容器或 Pod 中是命名空間的,設置它們不會影響節點上的其他 Pod 或節點本身。相反,不安全的 sysctl 默認情況下是禁用的,因為它們可能會擾亂其他 Pod 或使節點不穩定。

由於不安全的 `sysctl` 默認情況下是禁用的,kubelet 將不會創建具有不安全 `sysctl` 配置文件的 Pod。如果您創建這樣的 Pod,調度程序將反復將此類 Pod 分配給節點,而節點將無法啟動它。這個無限循環最終會給集群控制平面帶來壓力,使集群不穩定。

考慮使用 [OPA Gatekeeper](https://github.com/open-policy-agent/gatekeeper-library/blob/377cb915dba2db10702c25ef1ee374b4aa8d347a/src/pod-security-policy/forbidden-sysctls/constraint.tmpl) 或 [Kyverno](https://kyverno.io/policies/pod-security/baseline/restrict-sysctls/restrict-sysctls/) 來拒絕具有不安全 `sysctl` 的 Pod。



## 處理集群升級
自 2021 年 4 月起,Kubernetes 發佈週期已從一年四次 (每季度一次) 更改為一年三次。新的次要版本 (如 1.**21** 或 1.**22**) 大約每 [十五週](https://kubernetes.io/blog/2021/07/20/new-kubernetes-release-cadence/#what-s-changing-and-when) 發佈一次。從 Kubernetes 1.19 開始,每個次要版本在首次發佈後大約支持十二個月。隨著 Kubernetes v1.28 的推出,控制平面和工作節點之間的兼容性偏差已從 n-2 次次要版本擴展到 n-3 次次要版本。要了解更多信息,請參閱 [集群升級最佳實踐](../../upgrades/index.md)。

## 運行大型集群

EKS 會主動監控控制平面實例上的負載,並自動對它們進行擴展以確保高性能。但是,在運行大型集群時,您應該考慮 Kubernetes 內部的潛在性能問題和限制以及 AWS 服務中的配額。

- 根據 ProjectCalico 團隊 [進行的測試](https://www.projectcalico.org/comparing-kube-proxy-modes-iptables-or-ipvs/),擁有超過 1000 個服務的集群在使用 `iptables` 模式的 `kube-proxy` 時可能會遇到網絡延遲。解決方案是切換到 [以 `ipvs` 模式運行 `kube-proxy`](https://medium.com/@jeremy.i.cowan/the-problem-with-kube-proxy-enabling-ipvs-on-eks-169ac22e237e)。
- 如果 CNI 需要為 Pod 請求 IP 地址或您需要頻繁創建新的 EC2 實例,您也可能會遇到 [EC2 API 請求節流](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/throttling.html)。您可以通過配置 CNI 來緩存 IP 地址來減少對 EC2 API 的調用。您可以使用更大的 EC2 實例類型來減少 EC2 擴展事件。


## 其他資源:

- [揭秘 Amazon EKS 工作節點的集群網絡](https://aws.amazon.com/blogs/containers/de-mystifying-cluster-networking-for-amazon-eks-worker-nodes/)
- [Amazon EKS 集群端點訪問控制](https://docs.aws.amazon.com/eks/latest/userguide/cluster-endpoint.html)
- [AWS re:Invent 2019: Amazon EKS 內部原理 (CON421-R1)](https://www.youtube.com/watch?v=7vxDWDD2YnM)
