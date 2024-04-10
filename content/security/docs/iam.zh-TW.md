# 身份和存取管理

[身份和存取管理](https://docs.aws.amazon.com/IAM/latest/UserGuide/introduction.html) (IAM) 是一項 AWS 服務，執行兩項基本功能：驗證和授權。驗證涉及驗證身份，而授權則管理可對 AWS 資源執行的動作。在 AWS 中，資源可以是另一個 AWS 服務，例如 EC2，或 AWS [主體](https://docs.aws.amazon.com/IAM/latest/UserGuide/intro-structure.html#intro-structure-principal)，例如 [IAM 使用者](https://docs.aws.amazon.com/IAM/latest/UserGuide/id.html#id_iam-users)或[角色](https://docs.aws.amazon.com/IAM/latest/UserGuide/id.html#id_iam-roles)。允許資源執行動作的規則以 [IAM 政策](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies.html)的形式表示。

## 控制對 EKS 叢集的存取

Kubernetes 專案支援各種不同的策略來驗證對 kube-apiserver 服務的請求，例如 Bearer Token、X.509 憑證、OIDC 等。EKS 目前原生支援 [webhook token 驗證](https://kubernetes.io/docs/reference/access-authn-authz/authentication/#webhook-token-authentication)、[服務帳戶 token](https://kubernetes.io/docs/reference/access-authn-authz/authentication/#service-account-tokens)，以及自 2021 年 2 月 21 日起支援 OIDC 驗證。

webhook 驗證策略會呼叫一個 webhook 來驗證 bearer token。在 EKS 上，這些 bearer token 是由 AWS CLI 或 [aws-iam-authenticator](https://github.com/kubernetes-sigs/aws-iam-authenticator) 用戶端在執行 `kubectl` 命令時產生的。當您執行命令時，token 會傳遞給 kube-apiserver，kube-apiserver 會將它轉發給驗證 webhook。如果請求格式正確，webhook 會呼叫 token 主體中內嵌的預先簽名 URL。此 URL 會驗證請求的簽名，並將有關使用者的資訊（例如使用者的帳戶、Arn 和 UserId）傳回給 kube-apiserver。

要在終端機視窗中手動產生驗證 token，請輸入以下命令：

```bash
aws eks get-token --cluster-name <cluster_name>
```

您也可以以程式設計方式取得 token。以下是用 Go 撰寫的範例：

```golang
package main

import (
  "fmt"
  "log"
  "sigs.k8s.io/aws-iam-authenticator/pkg/token"
)

func main()  {
  g, _ := token.NewGenerator(false, false)
  tk, err := g.Get("<cluster_name>")
  if err != nil {
    log.Fatal(err)
  }
  fmt.Println(tk)
}
```

輸出應類似於：

```json
{
  "kind": "ExecCredential",
  "apiVersion": "client.authentication.k8s.io/v1alpha1",
  "spec": {},
  "status": {
    "expirationTimestamp": "2020-02-19T16:08:27Z",
    "token": "k8s-aws-v1.aHR0cHM6Ly9zdHMuYW1hem9uYXdzLmNvbS8_QWN0aW9uPUdldENhbGxlcklkZW50aXR5JlZlcnNpb249MjAxMS0wNi0xNSZYLUFtei1BbGdvcml0aG09QVdTNC1ITUFDLVNIQTI1NiZYLUFtei1DcmVkZW50aWFsPUFLSUFKTkdSSUxLTlNSQzJXNVFBJTJGMjAyMDAyMTklMkZ1cy1lYXN0LTElMkZzdHMlMkZhd3M0X3JlcXVlc3QmWC1BbXotRGF0ZT0yMDIwMDIxOVQxNTU0MjdaJlgtQW16LUV4cGlyZXM9NjAmWC1BbXotU2lnbmVkSGVhZGVycz1ob3N0JTNCeC1rOHMtYXdzLWlkJlgtQW16LVNpZ25hdHVyZT0yMjBmOGYzNTg1ZTMyMGRkYjVlNjgzYTVjOWE0MDUzMDFhZDc2NTQ2ZjI0ZjI4MTExZmRhZDA5Y2Y2NDhhMzkz"
  }
}
```

每個 token 都以 `k8s-aws-v1.` 開頭，後面接著一個 base64 編碼的字串。解碼該字串後，應類似於：

```bash
https://sts.amazonaws.com/?Action=GetCallerIdentity&Version=2011-06-15&X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=XXXXJPFRILKNSRC2W5QA%2F20200219%2Fus-xxxx-1%2Fsts%2Faws4_request&X-Amz-Date=20200219T155427Z&X-Amz-Expires=60&X-Amz-SignedHeaders=host%3Bx-k8s-aws-id&X-Amz-Signature=XXXf8f3285e320ddb5e683a5c9a405301ad76546f24f28111fdad09cf648a393
```

該 token 包含一個預先簽名的 URL，其中包含 Amazon 憑證和簽名。如需詳細資訊，請參閱 [https://docs.aws.amazon.com/STS/latest/APIReference/API_GetCallerIdentity.html](https://docs.aws.amazon.com/STS/latest/APIReference/API_GetCallerIdentity.html)。

該 token 的生存時間 (TTL) 為 15 分鐘，之後需要產生新的 token。當您使用像 `kubectl` 這樣的用戶端時，這會自動處理，但是，如果您使用 Kubernetes 儀表板，每次 token 過期時，您都需要產生新的 token 並重新驗證。

一旦使用者的身份已由 AWS IAM 服務驗證，kube-apiserver 就會讀取 `kube-system` 命名空間中的 `aws-auth` ConfigMap，以確定要與使用者關聯的 RBAC 群組。`aws-auth` ConfigMap 用於在 IAM 主體（即 IAM 使用者和角色）與 Kubernetes RBAC 群組之間建立靜態對應。RBAC 群組可以在 Kubernetes RoleBinding 或 ClusterRoleBinding 中參考。它們類似於 IAM 角色，因為它們定義了可對一組 Kubernetes 資源（物件）執行的一組動作（動詞）。

### 叢集存取管理員

叢集存取管理員現在是管理 AWS IAM 主體對 Amazon EKS 叢集存取權限的首選方式，是 EKS v1.23 及更新版本叢集（新建或現有）的一項 AWS API 功能和選用功能。它簡化了 AWS IAM 與 Kubernetes RBAC 之間的身份對應，消除了在 AWS 和 Kubernetes API 之間切換或編輯 `aws-auth` ConfigMap 進行存取管理的需求，降低了操作開銷，並有助於解決錯誤配置的問題。該工具還可讓叢集管理員自動撤銷或精簡自動授予用於建立叢集的 AWS IAM 主體的 `cluster-admin` 權限。

此 API 依賴於兩個概念：

- **存取項目：**直接與允許驗證到 Amazon EKS 叢集的 AWS IAM 主體（使用者或角色）相關聯的叢集身份。
- **存取政策：**是 Amazon EKS 特定的政策，為存取項目提供在 Amazon EKS 叢集中執行動作的授權。

> 在推出時，Amazon EKS 僅支援預先定義和 AWS 管理的政策。存取政策不是 IAM 實體，而是由 Amazon EKS 定義和管理。

叢集存取管理員允許將上游 RBAC 與支援允許和通過（但不拒絕）Kubernetes AuthZ 決策的存取政策相結合。如果上游 RBAC 和 Amazon EKS 授權者都無法確定請求評估的結果，則會發生拒絕決策。

使用此功能，Amazon EKS 支援三種驗證模式：

1. `CONFIG_MAP` 繼續專門使用 `aws-auth` configMap。
2. `API_AND_CONFIG_MAP` 從 EKS 存取項目 API 和 `aws-auth` configMap 獲取已驗證的 IAM 主體，並優先考慮存取項目。理想的是將現有的 `aws-auth` 權限遷移到存取項目。
3. `API` 專門依賴 EKS 存取項目 API。這是新的 **建議方法**。

要開始使用，叢集管理員可以建立或更新 Amazon EKS 叢集，將首選驗證方法設定為 `API_AND_CONFIG_MAP` 或 `API`，並定義存取項目以授予所需的 AWS IAM 主體存取權限。

```bash
$ aws eks create-cluster \
    --name <CLUSTER_NAME> \
    --role-arn <CLUSTER_ROLE_ARN> \
    --resources-vpc-config subnetIds=<value>,endpointPublicAccess=true,endpointPrivateAccess=true \
    --logging '{"clusterLogging":[{"types":["api","audit","authenticator","controllerManager","scheduler"],"enabled":true}]}' \
    --access-config authenticationMode=API_AND_CONFIG_MAP,bootstrapClusterCreatorAdminPermissions=false
```

上面的命令是一個範例，用於建立一個已經沒有叢集建立者管理員權限的 Amazon EKS 叢集。

您可以使用 `update-cluster-config` 命令更新 Amazon EKS 叢集配置以啟用 `API` authenticationMode，對於使用 `CONFIG_MAP` 的現有叢集，您必須先更新為 `API_AND_CONFIG_MAP`，然後再更新為 `API`。**這些操作無法還原**，這意味著無法從 `API` 切換到 `API_AND_CONFIG_MAP` 或 `CONFIG_MAP`，也無法從 `API_AND_CONFIG_MAP` 切換到 `CONFIG_MAP`。

```bash
$ aws eks update-cluster-config \
    --name <CLUSTER_NAME> \
    --access-config authenticationMode=API
```

該 API 支援命令來新增和撤銷對叢集的存取權限，以及驗證指定叢集的現有存取政策和存取項目。預設政策是根據 Kubernets RBAC 建立的，如下所示。

| EKS 存取政策 | Kubernetes RBAC |
|--|--|
| AmazonEKSClusterAdminPolicy | cluster-admin |
| AmazonEKSAdminPolicy | admin |
| AmazonEKSEditPolicy | edit |
| AmazonEKSViewPolicy | view |

```bash
$ aws eks list-access-policies
{
    "accessPolicies": [
        {
            "name": "AmazonEKSAdminPolicy",
            "arn": "arn:aws:eks::aws:cluster-access-policy/AmazonEKSAdminPolicy"
        },
        {
            "name": "AmazonEKSClusterAdminPolicy",
            "arn": "arn:aws:eks::aws:cluster-access-policy/AmazonEKSClusterAdminPolicy"
        },
        {
            "name": "AmazonEKSEditPolicy",
            "arn": "arn:aws:eks::aws:cluster-access-policy/AmazonEKSEditPolicy"
        },
        {
            "name": "AmazonEKSViewPolicy",
            "arn": "arn:aws:eks::aws:cluster-access-policy/AmazonEKSViewPolicy"
        }
    ]
}

$ aws eks list-access-entries --cluster-name <CLUSTER_NAME>

{
    "accessEntries": []
}
```

> 當叢集在不授予叢集建立者管理員權限的情況下建立時，不會有任何存取項目，這是預設建立的唯一項目。

### `aws-auth` ConfigMap _(已棄用)_

與 AWS 驗證整合的一種方式是透過 `aws-auth` ConfigMap，它位於 `kube-system` 命名空間中。它負責將 AWS IAM 身份（使用者、群組和角色）驗證對應到 Kubernetes 角色型存取控制 (RBAC) 授權。在您的 Amazon EKS 叢集佈建階段會自動在其中建立 `aws-auth` ConfigMap。它最初是為了允許節點加入您的叢集而建立的，但如前所述，您也可以使用此 ConfigMap 為 IAM 主體新增 RBAC 存取權限。

要檢查您叢集的 `aws-auth` ConfigMap，您可以使用以下命令。

```bash
kubectl -n kube-system get configmap aws-auth -o yaml
```

這是預設 `aws-auth` ConfigMap 配置的範例。

```yaml
apiVersion: v1
data:
  mapRoles: |
    - groups:
      - system:bootstrappers
      - system:nodes
      - system:node-proxier
      rolearn: arn:aws:iam::<AWS_ACCOUNT_ID>:role/kube-system-<SELF_GENERATED_UUID>
      username: system:node:{{SessionName}}
kind: ConfigMap
metadata:
  creationTimestamp: "2023-10-22T18:19:30Z"
  name: aws-auth
  namespace: kube-system
```

此 ConfigMap 的主要部分在於 `data` 下的 `mapRoles` 區塊，基本上由 3 個參數組成。

- **groups：**要將 IAM 角色對應到的 Kubernetes 群組。這可以是預設群組或在 `clusterrolebinding` 或 `rolebinding` 中指定的自訂群組。在上面的範例中，我們只聲明了系統群組。
- **rolearn：**要對應到 Kubernetes 群組的 AWS IAM 角色的 ARN，使用以下格式 `arn:<PARTITION>:iam::<AWS_ACCOUNT_ID>:role/role-name`。
- **username：**要在 Kubernetes 中對應到 AWS IAM 角色的使用者名稱。這可以是任何自訂名稱。

> 您也可以透過在 `aws-auth` ConfigMap 的 `data` 下定義新的 `mapUsers` 配置區塊來對應 AWS IAM 使用者的權限，但 **最佳實踐** 是始終使用 `mapRoles`。

要管理權限，您可以編輯 `aws-auth` ConfigMap 來新增或移除對 Amazon EKS 叢集的存取權限。雖然您可以手動編輯 `aws-auth` ConfigMap，但建議使用像 `eksctl` 這樣的工具，因為這是一個非常敏感的配置，不正確的配置可能會讓您無法存取您的 Amazon EKS 叢集。如需詳細資訊，請參閱下面的 [使用工具對 aws-auth ConfigMap 進行更改](https://aws.github.io/aws-eks-best-practices/security/docs/iam/#use-tools-to-make-changes-to-the-aws-auth-configmap)小節。

## 叢集存取建議

### 將 EKS 叢集端點設為私有

預設情況下，當您佈建 EKS 叢集時，API 叢集端點會設定為公開，即可從網際網路存取。儘管可從網際網路存取，但端點仍然被視為安全，因為它要求所有 API 請求都必須由 IAM 驗證，然後由 Kubernetes RBAC 授權。儘管如此，如果您的公司安全政策要求您限制從網際網路存取 API 或防止您的流量離開叢集 VPC，您可以：

- 將 EKS 叢集端點配置為私有。如需進一步資訊，請參閱 [修改叢集端點存取](https://docs.aws.amazon.com/eks/latest/userguide/cluster-endpoint.html)。
- 保持叢集端點公開，並指定哪些 CIDR 區塊可以與叢集端點通訊。這些區塊實際上是允許存取叢集端點的一組公開 IP 位址的白名單。
- 配置公開存取和一組允許的 CIDR 區塊，並將私有端點存取設定為已啟用。這將允許從特定範圍的公開 IP 進行公開存取，同時強制 kubelet（工作節點）與 Kubernetes API 之間的所有網路流量通過在佈建控制平面時佈建到叢集 VPC 中的跨帳戶 ENI。

### 不要使用服務帳戶 token 進行驗證

服務帳戶 token 是長期存在的靜態憑證。如果它被入侵、遺失或被盜，攻擊者可能能夠執行與該 token 相關聯的所有動作，直到該服務帳戶被刪除為止。有時，您可能需要為必須從叢集外部消耗 Kubernetes API 的應用程式授予例外，例如 CI/CD 管線應用程式。如果這類應用程式在 AWS 基礎架構（如 EC2 執行個體）上執行，請考慮使用執行個體設定檔並將其對應到 Kubernetes RBAC 角色。

### 對 AWS 資源採用最小權限存取

IAM 使用者不需要被指派 AWS 資源的權限就可以存取 Kubernetes API。如果您需要授予 IAM 使用者存取 EKS 叢集的權限，請在 `aws-auth` ConfigMap 中為該使用者建立一個項目，將其對應到特定的 Kubernetes RBAC 群組。

### 從叢集建立者主體移除 cluster-admin 權限

預設情況下，Amazon EKS 叢集在建立時會將永久的 `cluster-admin` 權限系結到叢集建立者主體。使用叢集存取管理員 API，您可以在建立叢集時透過將 `--access-config bootstrapClusterCreatorAdminPermissions` 設定為 `false` 來建立不具有此權限的叢集，並使用 `API_AND_CONFIG_MAP` 或 `API` 驗證模式。撤銷此存取權被視為最佳實踐，以避免對叢集配置進行任何不需要的更改。撤銷此存取權的程序與撤銷對叢集的任何其他存取權的程序相同。

該 API 讓您只能將 IAM 主體與存取政策解除關聯，在這種情況下是 `AmazonEKSClusterAdminPolicy`。

```bash
$ aws eks list-associated-access-policies \
    --cluster-name <CLUSTER_NAME> \
    --principal-arn <IAM_PRINCIPAL_ARN>

$ aws eks disassociate-access-policy --cluster-name <CLUSTER_NAME> \
    --principal-arn <IAM_PRINCIPAL_ARN. \
    --policy-arn arn:aws:eks::aws:cluster-access-policy/AmazonEKSClusterAdminPolicy
```

或完全移除與 `cluster-admin` 權限相關聯的存取項目。

```bash
$ aws eks list-access-entries --cluster-name <CLUSTER_NAME>

{
    "accessEntries": []
}

$ aws eks delete-access-entry --cluster-name <CLUSTER_NAME> \
  --principal-arn <IAM_PRINCIPAL_ARN>
```

> 在發生事故、緊急情況或無法存取叢集的情況下，可以再次授予此存取權。

如果叢集仍使用 `CONFIG_MAP` 驗證方法，所有其他使用者都應透過 `aws-auth` ConfigMap 獲得對叢集的存取權限，並且在配置 `aws-auth` ConfigMap 之後，可以刪除指派給建立叢集的實體的角色，並且只在發生事故、緊急情況或無法存取叢集的情況下重新建立，或者在 `aws-auth` ConfigMap 損毀且無法存取叢集的情況下重新建立。這在生產叢集中特別有用。

### 當多個使用者需要相同的叢集存取權限時，請使用 IAM 角色

與為每個個別 IAM 使用者建立項目相比，允許這些使用者承擔 IAM 角色並將該角色對應到 Kubernetes RBAC 群組會更容易維護，尤其是在需要存取的使用者數量增加時。

!!! attention
    當使用由 `aws-auth` ConfigMap 對應的 IAM 實體存取 EKS 叢集時，描述的使用者名稱會記錄在 Kubernetes 審計日誌的使用者欄位中。如果您使用 IAM 角色，則實際承擔該角色的使用者無法記錄和審計。

如果仍在使用 `aws-auth` configMap 作為驗證方法，當為 IAM 角色指派 K8s RBAC 權限時，您應在使用者名稱中包含 {{SessionName}}。這樣，審計日誌就會記錄會話名稱，因此您可以追蹤誰是實際承擔此角色的使用者，以及 CloudTrail 日誌。

```yaml
- rolearn: arn:aws:iam::XXXXXXXXXXXX:role/testRole
  username: testRole:{{SessionName}}
  groups:
    - system:masters
```

> 在 Kubernetes 1.20 及更高版本中，不再需要進行此更改，因為已新增 ```user.extra.sessionName.0``` 到 Kubernetes 審計日誌中。

### 在建立 RoleBinding 和 ClusterRoleBinding 時採用最小權限存取

與前面關於授予對 AWS 資源的存取權限的要點一樣，RoleBinding 和 ClusterRoleBinding 應該只包含執行特定功能所需的權限集。除非絕對必要，否則請避免在您的角色和叢集角色中使用 `["*"]`。如果您不確定要指派哪些權限，請考慮使用像 [audit2rbac](https://github.com/liggitt/audit2rbac) 這樣的工具，根據 Kubernetes 審計日誌中觀察到的 API 呼叫自動產生角色和系結。

### 使用自動化程序建立叢集

如前面的步驟所示，在建立 Amazon EKS 叢集時，如果不使用 `API_AND_CONFIG_MAP` 或 `API` 驗證模式，並且不選擇不將 `cluster-admin` 權限委派給叢集建立者，則建立叢集的 IAM 實體使用者或角色（例如聯合使用者）會自動在叢集的 RBAC 配置中獲得 `system:masters` 權限。即使將移除此權限被視為 [這裡](Rremove-the-cluster-admin-permissions-from-the-cluster-creator-principal) 所述的最佳實踐，但如果使用 `CONFIG_MAP` 驗證方法，依賴 `aws-auth` ConfigMap，則無法撤銷此存取權。因此，最好使用與專用 IAM 角色相關聯的基礎架構自動化管線來建立叢集，該角色沒有可供其他使用者或實體承擔的權限，並定期審計此角色的權限、政策和誰可以觸發管線。此外，該角色不應用於對叢集執行例行操作，而應僅用於通過 SCM 程式碼變更等方式觸發管線的叢集層級操作。

### 使用專用 IAM 角色建立叢集

當您建立 Amazon EKS 叢集時，建立叢集的 IAM 實體使用者或角色（例如聯合使用者）會自動在叢集的 RBAC 配置中獲得 `system:masters` 權限。無法移除此存取權，也不會通過 `aws-auth` ConfigMap 進行管理。因此，最好使用專用 IAM 角色建立叢集，並定期審計誰可以承擔此角色。此角色不應用於對叢集執行例行操作，而是應通過 `aws-auth` ConfigMap 為此目的授予其他使用者對叢集的存取權限。在配置 `aws-auth` ConfigMap 之後，應保護該角色，並且只在臨時提升權限模式/無法存取叢集的情況下使用。這在不允許直接使用者存取的叢集中特別有用。

### 定期審計對叢集的存取

隨著時間的推移，需要存取的人員可能會發生變化。請計劃定期審計 `aws-auth` ConfigMap，查看誰被授予了存取權限以及他們被指派的權限。您還可以使用像 [kubectl-who-can](https://github.com/aquasecurity/kubectl-who-can) 或 [rbac-lookup](https://github.com/FairwindsOps/rbac-lookup) 這樣的開源工具來檢查系結到特定服務帳戶、使用者或群組的角色。我們將在 [審計](detective.md) 一節中進一步探討這個主題。NCC Group 在這篇 [文章](https://www.nccgroup.trust/us/about-us/newsroom-and-events/blog/2019/august/tools-and-methods-for-auditing-kubernetes-rbac-policies/?mkt_tok=eyJpIjoiWWpGa056SXlNV1E0WWpRNSIsInQiOiJBT1hyUTRHYkg1TGxBV0hTZnRibDAyRUZ0VzBxbndnRzNGbTAxZzI0WmFHckJJbWlKdE5WWDdUQlBrYVZpMnNuTFJ1R3hacVYrRCsxYWQ2RTRcL2pMN1BtRVA1ZFZcL0NtaEtIUDdZV3pENzNLcE1zWGVwUndEXC9Pb2tmSERcL1pUaGUifQ%3D%3D) 中也提供了其他想法。

### 如果依賴 `aws-auth` configMap，請使用工具對其進行更改

不正確格式化的 aws-auth ConfigMap 可能會導致您無法存取叢集。如果您需要對 ConfigMap 進行更改，請使用工具。

**eksctl**
`eksctl` CLI 包括一個命令，用於將身份對應新增到 aws-auth ConfigMap。

查看 CLI 說明：

```bash
$ eksctl create iamidentitymapping --help
...
```

檢查對應到您 Amazon EKS 叢集的身份。

```bash
$ eksctl get iamidentitymapping --cluster $CLUSTER_NAME --region $AWS_REGION
ARN                                                                   USERNAME                        GROUPS                                                  ACCOUNT
arn:aws:iam::788355785855:role/kube-system-<SELF_GENERATED_UUID>      system:node:{{SessionName}}     system:bootstrappers,system:nodes,system:node-proxier  
```

使 IAM 角色成為叢集管理員：

```bash
$ eksctl create iamidentitymapping --cluster  <CLUSTER_NAME> --region=<region> --arn arn:aws:iam::123456:role/testing --group system:masters --username admin
...
```

如需更多資訊，請查看 [`eksctl` 文件](https://eksctl.io/usage/iam-identity-mappings/)

**[aws-auth](https://github.com/keikoproj/aws-auth) 由 keikoproj 提供**

keikoproj 的 `aws-auth` 包括 CLI 和 Go 程式庫。

下載並查看 CLI 說明：

```bash
$ go get github.com/keikoproj/aws-auth
...
$ aws-auth help
...
```

或者，使用 [krew 插件管理器](https://krew.sigs.k8s.io) 為 kubectl 安裝 `aws-auth`。

```bash
$ kubectl krew install aws-auth
...
$ kubectl aws-auth
...
```

[在 GitHub 上查看 aws-auth 文件](https://github.com/keikoproj/aws-auth/blob/master/README.md)以獲取更多資訊，包括 Go 程式庫。

**[AWS IAM Authenticator CLI](https://github.com/kubernetes-sigs/aws-iam-authenticator/tree/master/cmd/aws-iam-authenticator)**

`aws-iam-authenticator` 專案包括一個用於更新 ConfigMap 的 CLI。

在 GitHub 上 [下載發行版](https://github.com/kubernetes-sigs/aws-iam-authenticator/releases)。

為 IAM 角色新增叢集權限：

```bash
$ ./aws-iam-authenticator add role --rolearn arn:aws:iam::185309785115:role/lil-dev-role-cluster --username lil-dev-user --groups system:masters --kubeconfig ~/.kube/config
...
```

### 驗證和存取管理的替代方法

雖然 IAM 是需要存取 EKS 叢集的使用者進行驗證的首選方式，但也可以使用 OIDC 身份提供者（例如 GitHub）搭配驗證 Proxy 和 Kubernetes [模擬](https://kubernetes.io/docs/reference/access-authn-authz/authentication/#user-impersonation)。AWS Open Source 部落格已發表了兩種此類解決方案的文章：

- [使用 GitHub 憑證對 EKS 進行驗證的 Teleport](https://aws.amazon.com/blogs/opensource/authenticating-eks-github-credentials-teleport/)
- [使用 kube-oidc-proxy 跨多個 EKS 叢集實現一致的 OIDC 驗證](https://aws.amazon.com/blogs/opensource/consistent-oidc-authentication-across-multiple-eks-clusters-using-kube-oidc-proxy/)

!!! attention
    EKS 原生支援不使用 Proxy 的 OIDC 驗證。如需進一步資訊，請閱讀發佈部落格 [為 Amazon EKS 引入 OIDC 身份提供者驗證](https://aws.amazon.com/blogs/containers/introducing-oidc-identity-provider-authentication-amazon-eks/)。如需使用 Dex（一種支援各種不同驗證方法的熱門開源 OIDC 提供者）與 EKS 配置的範例，請參閱 [使用 Dex 和 dex-k8s-authenticator 對 Amazon EKS 進行驗證](https://aws.amazon.com/blogs/containers/using-dex-dex-k8s-authenticator-to-authenticate-to-amazon-eks/)。如部落格所述，由 OIDC 提供者驗證的使用者的使用者名稱/群組將出現在 Kubernetes 審計日誌中。

您還可以使用 [AWS SSO](https://docs.aws.amazon.com/singlesignon/latest/userguide/what-is.html) 將 AWS 與外部身份提供者（例如 Azure AD）聯合。如果您決定使用此方法，AWS CLI v2.0 包括一個選項，可以建立命名設定檔，輕鬆將 SSO 會話與您目前的 CLI 會話相關聯並承擔 IAM 角色。請注意，您必須在運行 `kubectl` 之前承擔角色，因為 IAM 角色用於確定使用者的 Kubernetes RBAC 群組。

## EKS Pod 的身份和憑證

某些在 Kubernetes 叢集內運行的應用程式需要權限來呼叫 Kubernetes API 才能正常運作。例如，[AWS Load Balancer Controller](https://github.com/kubernetes-sigs/aws-load-balancer-controller) 需要能夠列出服務的端點。控制器還需要能夠調用 AWS API 來佈建和配置 ALB。在本節中，我們將探討為 Pod 指派權限和特權的最佳實踐。

### Kubernetes 服務帳戶

服務帳戶是一種特殊類型的物件，允許您將 Kubernetes RBAC 角色指派給 Pod。在叢集中的每個命名空間中，都會自動建立一個預設服務帳戶。當您在命名空間中部署 Pod 而不參考特定服務帳戶時，該命名空間的預設服務帳戶將自動指派給該 Pod，並且該服務帳戶（JWT）token 的 Secret 將作為磁碟區掛載到 Pod 的 `/var/run/secrets/kubernetes.io/serviceaccount`。解碼該目錄中的服務帳戶 token 將顯示以下元資料：

```json
{
  "iss": "kubernetes/serviceaccount",
  "kubernetes.io/serviceaccount/namespace": "default",
  "kubernetes.io/serviceaccount/secret.name": "default-token-5pv4z",
  "kubernetes.io/serviceaccount/service-account.name": "default",
  "kubernetes.io/serviceaccount/service-account.uid": "3b36ddb5-438c-11ea-9438-063a49b60fba",
  "sub": "system:serviceaccount:default:default"
}
```

預設服務帳戶對 Kubernetes API 具有以下權限。

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  annotations:
    rbac.authorization.kubernetes.io/autoupdate: "true"
  creationTimestamp: "2020-01-30T18:13:25Z"
  labels:
    kubernetes.io/bootstrapping: rbac-defaults
  name: system:discovery
  resourceVersion: "43"
  selfLink: /apis/rbac.authorization.k8s.io/v1/clusterroles/system%3Adiscovery
  uid: 350d2ab8-438c-11ea-9438-063a49b60fba
rules:
- nonResourceURLs:
  - /api
  - /api/*
  - /apis
  - /apis/*
  - /healthz
  - /openapi
  - /openapi/*
  - /version
  - /version/
  verbs:
  - get
```

此角色授權未驗證和已驗證的使用者讀取 API 資訊，並被視為可公開存取。

當在 Pod 內運行的應用程式呼叫 Kubernetes API 時，需要為該 Pod 指派一個明確授予它呼叫這些 API 的權限的服務帳戶。與使用者存取權限的指導原則類似，系結到服務帳戶的角色或叢集角色應限制為應用程式運作所需的 API 資源和方法，而不應超出範圍。要使用非預設服務帳戶，只需將 Pod 的 `spec.serviceAccountName` 欄位設定為您要使用的服務帳戶名稱。如需建立服務帳戶的其他資訊，請參閱 [https://kubernetes.io/docs/reference/access-authn-authz/rbac/#service-account-permissions](https://kubernetes.io/docs/reference/access-authn-authz/rbac/#service-account-permissions)。

!!! note
    在 Kubernetes 1.24 之前，Kubernetes 會自動為每個服務帳戶建立一個 Secret。此 Secret 會掛載到 Pod 的 /var/run/secrets/kubernetes.io/serviceaccount，並由 Pod 用於對 Kubernetes API 伺服器進行驗證。在 Kubernetes 1.24 中，服務帳戶 token 會在 Pod 運行時動態產生，並且預設只有效 1 小時。不會建立服務帳戶的 Secret。如果您有一個需要從叢集外部驗證到 Kubernetes API 的應用程式（例如 Jenkins），您將需要建立一個類型為 `kubernetes.io/service-account-token` 的 Secret，以及一個參考服務帳戶的註解，例如 `metadata.annotations.kubernetes.io/service-account.name: <SERVICE_ACCOUNT_NAME>`。以這種方式建立的 Secret 不會過期。

### IAM 角色的服務帳戶 (IRSA)

IRSA 是一項功能，允許您將 IAM 角色指派給 Kubernetes 服務帳戶。它利用了一個名為 [服務帳戶 Token 磁碟區投射](https://kubernetes.io/docs/tasks/configure-pod-container/configure-service-account/#serviceaccount-token-volume-projection)的 Kubernetes 功能。當 Pod 配置為參考 IAM 角色的服務帳戶時，Kubernetes API 伺服器會在啟動時呼叫叢集的公開 OIDC 探索端點。該端點會對 Kubernetes 發出的 OIDC token 進行加密簽名，並將產生的 token 掛載為磁碟區。此簽名 token 允許 Pod 呼叫與 IAM 角色相關聯的 AWS API。當調用 AWS API 時，AWS SDK 會呼叫 `sts:AssumeRoleWithWebIdentity`。在驗證 token 簽名後，IAM 會將 Kubernetes 發出的 token 交換為臨時 AWS 角色憑證。

使用 IRSA 時，[重用 AWS SDK 會話](#reuse-aws-sdk-sessions-with-irsa)很重要，以避免對 AWS STS 進行不必要的呼叫。

解碼 IRSA 的 (JWT) token 將產生類似於下面範例的輸出：

```json
{
  "aud": [
    "sts.amazonaws.com"
  ],
  "exp": 1582306514,
  "iat": 1582220114,
  "iss": "https://oidc.eks.us-west-2.amazonaws.com/id/D43CF17C27A865933144EA99A26FB128",
  "kubernetes.io": {
    "namespace": "default",
    "pod": {
      "name": "alpine-57b5664646-rf966",
      "uid": "5a20f883-5407-11ea-a85c-0e62b7a4a436"
    },
    "serviceaccount": {
      "name": "s3-read-only",
      "uid": "a720ba5c-5406-11ea-9438-063a49b60fba"
    }
  },
  "nbf": 1582220114,
  "sub": "system:serviceaccount:default:s3-read-only"
}
```

此特定 token 授予 Pod 對 S3 的唯讀權限，方式是承擔 IAM 角色。當應用程式嘗試讀取 S3 時，該 token 會被交換為類似以下的臨時 IAM 憑證：

```json
{
    "AssumedRoleUser": {
        "AssumedRoleId": "AROA36C6WWEJULFUYMPB6:abc",
        "Arn": "arn:aws:sts::123456789012:assumed-role/eksctl-winterfell-addon-iamserviceaccount-de-Role1-1D61LT75JH3MB/abc"
    },
    "Audience": "sts.amazonaws.com",
    "Provider": "arn:aws:iam::123456789012:oidc-provider/oidc.eks.us-west-2.amazonaws.com/id/D43CF17C27A865933144EA99A26FB128",
    "SubjectFromWebIdentityToken": "system:serviceaccount:default:s3-read-only",
    "Credentials": {
        "SecretAccessKey": "ORJ+8Adk+wW+nU8FETq7+mOqeA8Z6jlPihnV8hX1",
        "SessionToken": "FwoGZXIvYXdzEGMaDMLxAZkuLpmSwYXShiL9A1S0X87VBC1mHCrRe/pB2oes+l1eXxUYnPJyC9ayOoXMvqXQsomq0xs6OqZ3vaa5Iw1HIyA4Cv1suLaOCoU3hNvOIJ6C94H1vU0siQYk7DIq9Av5RZe+uE2FnOctNBvYLd3i0IZo1ajjc00yRK3v24VRq9nQpoPLuqyH2jzlhCEjXuPScPbi5KEVs9fNcOTtgzbVf7IG2gNiwNs5aCpN4Bv/Zv2A6zp5xGz9cWj2f0aD9v66vX4bexOs5t/YYhwuwAvkkJPSIGvxja0xRThnceHyFHKtj0H+bi/PWAtlI8YJcDX69cM30JAHDdQH+ltm/4scFptW1hlvMaP+WReCAaCrsHrAT+yka7ttw5YlUyvZ8EPog+j6fwHlxmrXM9h1BqdikomyJU00gm1++FJelfP+1zAwcyrxCnbRl3ARFrAt8hIlrT6Vyu8WvWtLxcI8KcLcJQb/LgkW+sCTGlYcY8z3zkigJMbYn07ewTL5Ss7LazTJJa758I7PZan/v3xQHd5DEc5WBneiV3iOznDFgup0VAMkIviVjVCkszaPSVEdK2NU7jtrh6Jfm7bU/3P6ZG+CkyDLIa8MBn9KPXeJd/y+jTk5Ii+fIwO/+mDpGNUribg6TPxhzZ8b/XdZO1kS1gVgqjXyVC+M+BRBh6C4H21w/eMzjCtDIpoxt5rGKL6Nu/IFMipoC4fgx6LIIHwtGYMG7SWQi7OsMAkiwZRg0n68/RqWgLzBt/4pfjSRYuk=",
        "Expiration": "2020-02-20T18:49:50Z",
        "AccessKeyId": "XXXX36C6WWEJUMHA3L7Z"
    }
}
```

EKS 控制平面作為一部分運行的變更 Webhook 會將 AWS 角色 ARN 和指向 Web 身份 token 檔案的路徑注入到 Pod 中作為環境變數。這些值也可以手動提供。

```bash
AWS_ROLE_ARN=arn:aws:iam::AWS_ACCOUNT_ID:role/IAM_ROLE_NAME
AWS_WEB_IDENTITY_TOKEN_FILE=/var/run/secrets/eks.amazonaws.com/serviceaccount/token
```

當投射的 token 的年齡超過其總 TTL 的 80% 或 24 小時後，kubelet 會自動輪換該 token。AWS SDK 負責在 token 輪換時重新載入它。如需有關 IRSA 的更多資訊，請參閱 [https://docs.aws.amazon.com/eks/latest/userguide/iam-roles-for-service-accounts-technical-overview.html](https://docs.aws.amazon.com/eks/latest/userguide/iam-roles-for-service-accounts-technical-overview.html)。

### EKS Pod 身份

[EKS Pod 身份](https://docs.aws.amazon.com/eks/latest/userguide/pod-identities.html)是在 2023 年 re:Invent 上推出的一項功能，允許您將 IAM 角色指派給 kubernetes 服務帳戶，而無需為您的 AWS 帳戶中的每個叢集配置開放 ID 連接 (OIDC) 身份提供者 (IDP)。要使用 EKS Pod 身份，您必須部署一個代理程式，該代理程式作為 DaemonSet Pod 在每個合格的工作節點上運行。此代理程式作為 EKS 附加元件提供給您，是使用 EKS Pod 身份功能的先決條件。您的應用程式必須使用 [支援的 AWS SDK 版本](https://docs.aws.amazon.com/eks/latest/userguide/pod-id-minimum-sdk.html) 才能使用此功能。

當為 Pod 配置 EKS Pod 身份時，EKS 將掛載並刷新位於 `/var/run/secrets/pods.eks.amazonaws.com/serviceaccount/eks-pod-identity-token` 的 Pod 身份 token。AWS SDK 將使用此 token 與 EKS Pod 身份代理程式通訊，代理程式使用 Pod 身份 token 和代理程式的 IAM 角色來通過呼叫 [AssumeRoleForPodIdentity API](https://docs.aws.amazon.com/eks/latest/APIReference/API_auth_AssumeRoleForPodIdentity.html) 為您的 Pod 建立臨時憑證。傳遞給您的 Pod 的 Pod 身份 token 是從您的 EKS 叢集發出的 JWT，經過加密簽名，並包含適用於 EKS Pod 身份的適當 JWT 聲明。

要了解有關 EKS Pod 身份的更多資訊，請參閱 [此部落格](https://aws.amazon.com/blogs/containers/amazon-eks-pod-identity-a-new-way-for-applications-on-eks-to-obtain-iam-credentials/)。

您不需要修改應用程式程式碼即可使用 EKS Pod 身份。支援的 AWS SDK 版本將自動透過 [憑證提供者鏈](https://docs.aws.amazon.com/sdkref/latest/guide/standardized-credentials.html) 探索使用 EKS Pod 身份提供的憑證。與 IRSA 一樣，EKS Pod 身份在您的 Pod 中設定變數，以指示它們如何找到 AWS 憑證。

#### 使用 EKS Pod 身份的 IAM 角色

- EKS Pod 身份只能直接承擔屬於與 EKS 叢集相同 AWS 帳戶的 IAM 角色。要存取另一個 AWS 帳戶中的 IAM 角色，您必須 [在您的 SDK 配置中配置設定檔](https://docs.aws.amazon.com/sdkref/latest/guide/feature-assume-role-credentials.html)或 [在您的應用程式程式碼中](https://docs.aws.amazon.com/IAM/latest/UserGuide/sts_example_sts_AssumeRole_section.html) 承擔該角色。
- 在為服務帳戶配置 EKS Pod 身份時，配置 Pod 身份關聯的人員或程序必須對該角色具有 `iam:PassRole` 權限。
- 每個服務帳戶只能通過 EKS Pod 身份與一個 IAM 角色關聯，但您可以將相同的 IAM 角色與多個服務帳戶關聯。
- 與 EKS Pod 身份一起使用的 IAM 角色必須允許 `pods.eks.amazonaws.com` 服務主體承擔它們，_並且_ 設定會話標籤。以下是一個允許 EKS Pod 身份使用 IAM 角色的角色信任政策範例：

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "pods.eks.amazonaws.com"
      },
      "Action": [
        "sts:AssumeRole",
        "sts:TagSession"
      ],
      "Condition": {
        "StringEquals": {
          "aws:SourceOrgId": "${aws:ResourceOrgId}"
        }
      }
    }
  ]
}
```

AWS 建議使用 `aws:SourceOrgId` 等條件金鑰來幫助防止 [跨服務混淆代理問題](https://docs.aws.amazon.com/IAM/latest/UserGuide/confused-deputy.html#cross-service-confused-deputy-prevention)。在上面的角色信任政策範例中，`ResourceOrgId` 是一個變數，等於 AWS 帳戶所屬的 AWS Organizations 組織的組織 ID。EKS 在使用 EKS Pod 身份承擔角色時，將傳遞一個等於該組織 ID 的 `aws:SourceOrgId` 值。

#### ABAC 和 EKS Pod 身份

當 EKS Pod 身份承擔 IAM 角色時，它會設定以下會話標籤：

|EKS Pod 身份會話標籤 | 值 |
|:--|:--|
|kubernetes-namespace | 與 EKS Pod 身份相關聯的 Pod 所在的命名空間。|
|kubernetes-service-account | 與 EKS Pod 身份相關聯的 kubernetes 服務帳戶名稱。|
|eks-cluster-arn | EKS 叢集的 ARN，例如 `arn:${Partition}:eks:${Region}:${Account}:cluster/${ClusterName}`。叢集 ARN 是唯一的，但如果在同一 AWS 帳戶、同一區域中使用相同名稱刪除並重新建立叢集，它將具有相同的 ARN。|
|eks-cluster-name | EKS 叢集的名稱。請注意，您的 AWS 帳戶中的 EKS 叢集名稱可能相同，而其他 AWS 帳戶中的 EKS 叢集也可能相同。|
|kubernetes-pod-name | EKS 中的 Pod 名稱。|
|kubernetes-pod-uid | EKS 中的 Pod UID。|

這些會話標籤允許您使用 [屬性型存取控制 (ABAC)](https://docs.aws.amazon.com/IAM/latest/UserGuide/introduction_attribute-based-access-control.html) 僅授予特定 kubernetes 服務帳戶存取您的 AWS 資源的權限。這樣做時，非常重要的是要了解 kubernetes 服務帳戶只在命名空間內是唯一的，而 kubernetes 命名空間只在 EKS 叢集內是唯一的。這些會話標籤可以在 AWS 政策中使用全域條件金鑰 `aws:PrincipalTag/<tag-key>` 來存取，例如 `aws:PrincipalTag/eks-cluster-arn`

例如，如果您只想授予特定服務帳戶存取您帳戶中的 AWS 資源的權限，您將需要檢查 `eks-cluster-arn` 和 `kubernetes-namespace` 標籤以及 `kubernetes-service-account`，以確保只有來自預期叢集的該服務帳戶才能存取該資源，因為其他叢集可能具有相同的 `kubernetes-service-accounts` 和 `kubernetes-namespaces`。

此 S3 Bucket 政策範例僅在 `kubernetes-service-account`、`kubernetes-namespace` 和 `eks-cluster-arn` 都符合其預期值時，才允許存取附加到該 S3 Bucket 的物件，其中 EKS 叢集託管在 AWS 帳戶 `111122223333` 中。

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "AWS": "arn:aws:iam::111122223333:root"
            },
            "Action": "s3:*",
            "Resource":            [
                "arn:aws:s3:::ExampleBucket/*"
            ],
            "Condition": {
                "StringEquals": {
                    "aws:PrincipalTag/kubernetes-service-account": "s3objectservice",
                    "aws:PrincipalTag/eks-cluster-arn": "arn:aws:eks:us-west-2:111122223333:cluster/ProductionCluster",
                    "aws:PrincipalTag/kubernetes-namespace": "s3datanamespace"
                }
            }
        }
    ]
}
```

### EKS Pod 身份與 IRSA 的比較

EKS Pod 身份和 IRSA 都是向 EKS Pod 傳遞臨時 AWS 憑證的首選方式。除非您有特定的 IRSA 使用案例，否則我們建議您在使用 EKS 時使用 EKS Pod 身份。此表有助於比較這兩個功能。

|# |EKS Pod 身份 | IRSA |
|:--|:--|:--|
|需要在您的 AWS 帳戶中建立 OIDC IDP 的權限？|否|是|
|需要為每個叢集設定唯一的 IDP？|否|是|
|設定與 ABAC 相關的會話標籤？|是|否|
|需要 iam:PassRole 檢查？|是|否|
|使用您的 AWS 帳戶的 AWS STS 配額？|否|是|
|可以存取其他 AWS 帳戶？|間接通過角色鏈|直接使用 sts:AssumeRoleWithWebIdentity|
|與 AWS SDK 相容？|是|是|
|需要在節點上部署 Pod 身份代理程式 DaemonSet？|是|否|

## EKS Pod 的身份和憑證建議

### 更新 aws-node daemonset 以使用 IRSA

目前，aws-node daemonset 配置為使用指派給 EC2 執行個體的角色來為 Pod 指派 IP。此角色包括多個 AWS 受管理政策，例如 AmazonEKS_CNI_Policy 和 EC2ContainerRegistryReadOnly，這實際上允許在節點上運行的 **所有** Pod 附加/分離 ENI、指派/取消指派 IP 位址或從 ECR 提取映像。由於這會對您的叢集帶來風險，因此建議您更新 aws-node daemonset 以使用 IRSA。可以在本指南的 [存放庫](https://github.com/aws/aws-eks-best-practices/tree/master/projects/enable-irsa/src) 中找到執行此操作的腳本。

aws-node daemonset 目前不支援 EKS Pod 身份。

### 限制對指派給工作節點的執行個體設定檔的存取

當您使用 IRSA 或 EKS Pod 身份時，它會更新 Pod 的憑證鏈以優先使用 IRSA 或 EKS Pod 身份，但是 Pod _仍然可以繼承指派給工作節點的執行個體設定檔的權限_。使用 IRSA 或 EKS Pod 身份時，**強烈** 建議您阻止存取 [執行個體元資料](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/configuring-instance-metadata-service.html)，以幫助確保您的應用程式只具有所需的權限，而不是其節點的權限。

!!! caution
    阻止存取執行個體元資料將防止不使用 IRSA 或 EKS Pod 身份的 Pod 繼承指派給工作節點的角色。

您可以要求執行個體只使用 IMDSv2 並更新跳數為 1 來阻止存取執行個體元資料，如下例所示。您也可以在節點群組的啟動範本中包含這些設定。請 **不要** 停用執行個體元資料，因為這將防止依賴執行個體元資料的組件（如節點終止處理程式等）正常運作。

```bash
$ aws ec2 modify-instance-metadata-options --instance-id <value> --http-tokens required --http-put-response-hop-limit 1
...
```

如果您使用 Terraform 為受管節點群組建立啟動範本，請在 metadata 區塊中新增配置跳數，如此程式碼片段所示：

``` tf hl_lines="7"
resource "aws_launch_template" "foo" {
  name = "foo"
  ...
    metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required"
    http_put_response_hop_limit = 1
    instance_metadata_tags      = "enabled"
  }
  ...
```

您也可以透過操作節點上的 iptables 來阻止 Pod 存取 EC2 元資料。如需此方法的更多資訊，請參閱 [限制存取執行個體元資料服務](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/instancedata-data-retrieval.html#instance-metadata-limiting-access)。

如果您有一個使用舊版 AWS SDK 的應用程式，該版本不支援 IRSA 或 EKS Pod 身份，您應更新 SDK 版本。

### 將 IRSA 角色的信任政策範圍縮小到服務帳戶名稱、命名空間和叢集

信任政策可以縮小到命名空間或命名空間內的特定服務帳戶。使用 IRSA 時，最好將角色信任政策設定得盡可能明確，包括服務帳戶名稱。這將有效防止同一命名空間內的其他 Pod 承擔該角色。CLI `eksctl` 在您使用它建立服務帳戶/IAM 角色時會自動執行此操作。如需進一步資訊，請參閱 [https://eksctl.io/usage/iamserviceaccounts/](https://eksctl.io/usage/iamserviceaccounts/)。

直接使用 IAM 時，這是在角色的信任政策中新增條件，使用條件來確保 `:sub` 聲明是您預期的命名空間和服務帳戶。例如，在我們之前有一個 IRSA token，其 sub 聲明為 "system:serviceaccount:default:s3-read-only"。這是 `default` 命名空間，服務帳戶是 `s3-read-only`。您將使用如下條件來確保只有您的叢集中給定命名空間中的該服務帳戶才能承擔該角色：

```json
  "Condition": {
      "StringEquals": {
          "oidc.eks.us-west-2.amazonaws.com/id/D43CF17C27A865933144EA99A26FB128:aud": "sts.amazonaws.com",
          "oidc.eks.us-west-2.amazonaws.com/id/D43CF17C27A865933144EA99A26FB128:sub": "system:serviceaccount:default:s3-read-only"
      }
  }
```

### 為每個應用程式使用一個 IAM 角色

使用 IRSA 和 EKS Pod 身份時，最佳實踐是為每個應用程式提供自己的 IAM 角色。這可以為您提供更好的隔離，因為您可以修改一個應用程式而不影響另一個應用程式，並允許您應用最小權限原則，只為應用程式授予它所需的權限。

使用 EKS Pod 身份的 ABAC 時，您可以跨多個服務帳戶使用通用 IAM 角色，並依賴其會話屬性進行存取控制。在大規模運營時，這尤其有用，因為 ABAC 允許您使用較少的 IAM 角色進行運營。

### 當您的應用程式需要存取 IMDS 時，請使用 IMDSv2 並將 EC2 執行個體的跳數增加到 2

[IMDSv2](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/configuring-instance-metadata-service.html) 要求您使用 PUT 請求來獲取會話 token。初始 PUT 請求必須包含會話 token 的 TTL。較新版本的 AWS SDK 將自動處理這一點以及該 token 的續期。還需要注意的是，EC2 執行個體上的預設跳數有意設定為 1，以防止 IP 轉發。因此，在 EC2 執行個體上運行並請求會話 token 的 Pod 最終可能會超時並回退到使用 IMDSv1 資料流。EKS 通過 _啟用_ v1 和 v2 並將跳數更改為 2 來支援 IMDSv2，這適用於由 eksctl 或使用官方 CloudFormation 範本佈建的節點。

### 停用自動掛載服務帳戶 token

如果您的應用程式不需要呼叫 Kubernetes API，請將 PodSpec 中的 `automountServiceAccountToken` 屬性設定為 `false`，或修補每個命名空間中的預設服務帳戶，使其不再自動掛載到 Pod。例如：

```bash
kubectl patch serviceaccount default -p $'automountServiceAccountToken: false'
```

### 為每個應用程式使用專用服務帳戶

每個應用程式都應該有自己的專用服務帳戶。這適用於 Kubernetes API 的服務帳戶以及 IRSA 和 EKS Pod 身份。

!!! attention
    如果您在使用 IRSA 時採用藍/綠色方法進行叢集升級而不是執行就地叢集升級，您將需要使用新叢集的 OIDC 端點更新每個 IRSA IAM 角色的信任政策。藍/綠色叢集升級是指在舊叢集旁建立一個運行較新版本 Kubernetes 的叢集，並使用負載平衡器或服務網格將服務從舊叢集無縫地移至新叢集。
    使用藍/綠色叢集升級與 EKS Pod 身份時，您將在新叢集中為 IAM 角色和服務帳戶建立 Pod 身份關聯。如果您有 `sourceArn` 條件，請更新 IAM 角色信任政策。

### 以非根使用者身份運行應用程式

容器預設以 root 身份運行。雖然這允許它們讀取 Web 身份 token 檔案，但以 root 身份運行容器不被視為最佳實踐。作為替代方案，請考慮在 PodSpec 中新增 `spec.securityContext.runAsUser` 屬性。`runAsUser` 的值是任意值。

在以下範例中，Pod 內的所有程序都將以 `runAsUser` 欄位中指定的使用者 ID 運行。

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: security-context-demo
spec:
  securityContext:
    runAsUser: 1000
    runAsGroup: 3000
  containers:
  - name: sec-ctx-demo
    image: busybox
    command: [ "sh", "-c", "sleep 1h" ]
```

當您以非根使用者身份運行容器時，它會防止容器讀取 IRSA 服務帳戶 token，因為該 token 預設會被指派 0600 [root] 權限。如果您更新容器的 securityContext 以包含 fsgroup=65534 [Nobody]，它將允許容器讀取該 token。

```yaml
spec:
  securityContext:
    fsGroup: 65534
```

在 Kubernetes 1.19 及更高版本中，不再需要進行此更改，應用程式可以在不將它們新增到 Nobody 群組的情況下讀取 IRSA 服務帳戶 token。

### 為應用程式授予最小權限存取

[Action Hero](https://github.com/princespaghetti/actionhero) 是一個工具，您可以將其與您的應用程式一起運行，以識別您的應用程式正常運作所需的 AWS API 呼叫和相應的 IAM 權限。它類似於 [IAM Access Advisor](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_access-advisor.html)，可以幫助您逐步限制指派給應用程式的 IAM 角色的範圍。請參閱有關授予 [最小權限存取](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html#grant-least-privilege) AWS 資源的文件，以獲取更多資訊。

請考慮為與 IRSA 和 Pod 身份一起使用的 IAM 角色設定 [權限範圍](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_boundaries.html)。您可以使用權限範圍來確保 IRSA 或 Pod 身份使用的角色無法超過最大權限級別。如需開始使用權限範圍和權限範圍政策範例的指南，請參閱此 [github 存放庫](https://github.com/aws-samples/example-permissions-boundary)。

### 檢閱並撤銷對您的 EKS 叢集的不必要的匿名存取權限

理想情況下，應該為所有 API 動作停用匿名存取。通過為 Kubernetes 內建使用者 system:anonymous 建立 RoleBinding 或 ClusterRoleBinding 來授予匿名存取權限。您可以使用 [rbac-lookup](https://github.com/FairwindsOps/rbac-lookup) 工具來識別 system:anonymous 使用者在您的叢集上擁有的權限：

```bash
./rbac-lookup | grep -P 'system:(anonymous)|(unauthenticated)'
system:anonymous               cluster-wide        ClusterRole/system:discovery
system:unauthenticated         cluster-wide        ClusterRole/system:discovery
system:unauthenticated         cluster-wide        ClusterRole/system:public-info-viewer
```

除了 system:public-info-viewer 之外，不應將任何角色或叢集角色系結到 system:anonymous 使用者或 system:unauthenticated 群組。

在某些情況下，為特定 API 啟用匿名存取可能是合理的。如果是這種情況，請確保只有那些特定 API 可以在不進行驗證的情況下被匿名使用者存取，並且這樣做不會使您的叢集面臨風險。

在 Kubernetes/EKS 1.14 版之前，system:unauthenticated 群組預設與 system:discovery 和 system:basic-user ClusterRole 相關聯。請注意，即使您已將叢集更新到 1.14 或更高版本，這些權限也可能仍在您的叢集上啟用，因為叢集更新不會撤銷這些權限。
要檢查除 system:public-info-viewer 之外哪些 ClusterRole 具有 "system:unauthenticated"，您可以運行以下命令（需要 jq 工具）：

```bash
kubectl get ClusterRoleBinding -o json | jq -r '.items[] | select(.subjects[]?.name =="system:unauthenticated") | select(.metadata.name != "system:public-info-viewer") | .metadata.name'
```

並且可以使用以下命令從除 "system:public-info-viewer" 之外的所有角色中移除 "system:unauthenticated"：

```bash
kubectl get ClusterRoleBinding -o json | jq -r '.items[] | select(.subjects[]?.name =="system:unauthenticated") | select(.metadata.name != "system:public-info-viewer") | del(.subjects[] | select(.name =="system:unauthenticated"))' | kubectl apply -f -
```

或者，您可以使用 kubectl describe 和 kubectl edit 手動檢查和移除。要檢查 system:unauthenticated 群組是否在您的叢集上具有 system:discovery 權限，請運行以下命令：

```bash
kubectl describe clusterrolebindings system:discovery

Name:         system:discovery
Labels:       kubernetes.io/bootstrapping=rbac-defaults
Annotations:  rbac.authorization.kubernetes.io/autoupdate: true
Role:
  Kind:  ClusterRole
  Name:  system:discovery
Subjects:
  Kind   Name                    Namespace
  ----   ----                    ---------
  Group  system:authenticated
  Group  system:unauthenticated
```

要檢查 system:unauthenticated 群組是否在您的叢集上具有 system:basic-user 權限，請運行以下命令：

```bash
kubectl describe clusterrolebindings system:basic-user

Name:         system:basic-user
Labels:       kubernetes.io/bootstrapping=rbac-defaults
Annotations:  rbac.authorization.kubernetes.io/autoupdate: true
Role:
  Kind:  ClusterRole
  Name:  system:basic-user
Subjects:
  Kind   Name                    Namespace
  ----   ----                    ---------
  Group  system:authenticated
  Group  system:unauthenticated
```

如果 system:unauthenticated 群組在您的叢集上系結到 system:discovery 和/或 system:basic-user ClusterRole，您應該將這些角色與 system:unauthenticated 群組解除關聯。使用以下命令編輯 system:discovery ClusterRoleBinding：

```bash
kubectl edit clusterrolebindings system:discovery
```

上述命令將在編輯器中打開 system:discovery ClusterRoleBinding 的當前定義，如下所示：

```yaml
# Please edit the object below. Lines beginning with a '#' will be ignored,
# and an empty file will abort the edit. If an error occurs while saving this file will be
# reopened with the relevant failures.
#
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  annotations:
    rbac.authorization.kubernetes.io/autoupdate: "true"
  creationTimestamp: "2021-06-17T20:50:49Z"
  labels:
    kubernetes.io/bootstrapping: rbac-defaults
  name: system:discovery
  resourceVersion: "24502985"
  selfLink: /apis/rbac.authorization.k8s.io/v1/clusterrolebindings/system%3Adiscovery
  uid: b7936268-5043-431a-a0e1-171a423abeb6
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: system:discovery
subjects:
- apiGroup: rbac.authorization.k8s.io
  kind: Group
  name: system:authenticated
- apiGroup: rbac.authorization.k8s.io
  kind: Group
  name: system:unauthenticated
```

從上面的編輯器畫面中的 "subjects" 部分刪除 system:unauthenticated 群組的項目。

對 system:basic-user ClusterRoleBinding 重複相同的步驟。

### 使用 IRSA 時重用 AWS SDK 會話

使用 IRSA 時，使用 AWS SDK 編寫的應用程式會使用傳遞給您的 Pod 的 token 呼叫 `sts:AssumeRoleWithWebIdentity` 來產生臨時 AWS 憑證。這與其他 AWS 計算服務不同，在其他 AWS 計算服務中，計算服務會直接將臨時 AWS 憑證傳遞給 AWS 計算資源（例如 Lambda 函數）。這意味著每次初始化 AWS SDK 會話時，都會進行一次對 `AssumeRoleWithWebIdentity` 的呼叫到 AWS STS。如果您的應用程式快速擴展並初始化許多 AWS SDK 會話，您可能會遇到來自 AWS STS 的節流，因為您的程式碼將進行許多對 `AssumeRoleWithWebIdentity` 的呼叫。

為了避免這種情況，我們建議在您的應用程式中重用 AWS SDK 會話，以免對 `AssumeRoleWithWebIdentity` 進行不必要的呼叫。

在以下範例程式碼中，使用 boto3 python SDK 建立會話，並使用相同的會話建立用戶端並與 Amazon S3 和 Amazon SQS 互動。`AssumeRoleWithWebIdentity` 只呼叫一次，AWS SDK 將在憑證過期時自動重新載入 `my_session` 的憑證。

```py hl_lines="4 7 8"  
import boto3

# 建立您自己的會話
my_session = boto3.session.Session()

# 現在我們可以從我們的會話建立低層級用戶端
sqs = my_session.client('sqs')
s3 = my_session.client('s3')

s3response = s3.list_buckets()
sqsresponse = sqs.list_queues()


#列印來自 S3 和 SQS API 的回應
print("s3 response:")
print(s3response)
print("---")
print("sqs response:")
print(sqsresponse)
```

如果您正在將應用程式從其他 AWS 計算服務（如 EC2）遷移到使用 IRSA 的 EKS，這一點尤其重要。在其他計算服務上，初始化 AWS SDK 會話不會呼叫 AWS STS，除非您指示它這樣做。

### 替代方法

雖然 IRSA 和 EKS Pod 身份是為 Pod 指派 AWS 身份的 _首選方式_，但它們需要您在應用程式中包含最新版本的 AWS SDK。有關目前支援 IRSA 的 SDK 的完整列表，請參閱 [https://docs.aws.amazon.com/eks/latest/userguide/iam-roles-for-service-accounts-minimum-sdk.html](https://docs.aws.amazon.com/eks/latest/userguide/iam-roles-for-service-accounts-minimum-sdk.html)，對於 EKS Pod 身份，請參閱 [https://docs.aws.amazon.com/eks/latest/userguide/pod-id-minimum-sdk.html](https://docs.aws.amazon.com/eks/latest/userguide/pod-id-minimum-sdk.html)。如果您有一個暫時無法使用相容 SDK 更新的應用程式，社區提供了一些為 Kubernetes Pod 指派 IAM 角色的解決方案，包括 [kube2iam](https://github.com/jtblin/kube2iam) 和 [kiam](https://github.com/uswitch/kiam)。雖然 AWS 不認可、支持或支援使用這些解決方案，但它們經常被大眾社區使用以實現與 IRSA 和 EKS Pod 身份類似的結果。

如果您需要使用這些非 AWS 提供的解決方案之一，請謹慎行事並確保您了解這樣做的安全性影響。

## 工具和資源

- [Amazon EKS 安全沉浸式研討會 - 身份和存取管理](https://catalog.workshops.aws/eks-security-immersionday/en-US/2-identity-and-access-management)
- [Terraform EKS Blueprints Pattern - 完全私有 Amazon EKS 叢集](https://github.com/aws-ia/terraform-aws-eks-blueprints/tree/main/patterns/fully-private-cluster)
- [Terraform EKS Blueprints Pattern - Amazon EKS 叢集的 IAM Identity Center 單一登入](https://github.com/aws-ia/terraform-aws-eks-blueprints/tree/main/patterns/sso-iam-identity-center)
- [Terraform EKS Blueprints Pattern - Amazon EKS 叢集的 Okta 單一登入](https://github.com/aws-ia/terraform-aws-eks-blueprints/tree/main/patterns/sso-okta)
- [audit2rbac](https://github.com/liggitt/audit2rbac)
- [rbac.dev](https://github.com/mhausenblas/rbac.dev) 包含部落格和工具在內的其他 Kubernetes RBAC 資源列表
- [Action Hero](https://github.com/princespaghetti/actionhero)
- [kube2iam](https://github.com/jtblin/kube2iam)
- [kiam](https://github.com/uswitch/kiam)
