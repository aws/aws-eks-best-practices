# 多帳戶策略

AWS 建議使用 [多帳戶策略](https://docs.aws.amazon.com/whitepapers/latest/organizing-your-aws-environment/organizing-your-aws-environment.html)和 AWS 組織來幫助隔離和管理您的業務應用程式和資料。使用多帳戶策略有 [許多好處](https://docs.aws.amazon.com/whitepapers/latest/organizing-your-aws-environment/benefits-of-using-multiple-aws-accounts.html)：

- 增加 AWS API 服務配額。配額是應用於 AWS 帳戶的，為您的工作負載使用多個帳戶可增加工作負載可用的總體配額。
- 簡化身份和存取管理 (IAM) 政策。只授予工作負載和支援它們的操作員存取其自己的 AWS 帳戶的權限，這意味著較少時間需要精心製作細緻的 IAM 政策來實現最小權限原則。
- 改善 AWS 資源的隔離。根據設計，在一個帳戶中佈建的所有資源在邏輯上都與在其他帳戶中佈建的資源隔離。這個隔離界限為您提供了一種方式來限制應用程式相關問題、錯誤配置或惡意行為的風險。如果在一個帳戶中發生問題，對包含在其他帳戶中的工作負載的影響可能會減少或消除。
- 更多好處，如 [AWS 多帳戶策略白皮書](https://docs.aws.amazon.com/whitepapers/latest/organizing-your-aws-environment/benefits-of-using-multiple-aws-accounts.html#group-workloads-based-on-business-purpose-and-ownership)所述

以下幾節將解釋如何為您的 EKS 工作負載實現多帳戶策略，使用集中式或分散式 EKS 叢集方法。

## 為多租戶叢集規劃多工作負載帳戶策略

在多帳戶 AWS 策略中，屬於給定工作負載的資源（如 S3 儲存貯體、ElastiCache 叢集和 DynamoDB 資料表）都是在包含該工作負載所有資源的 AWS 帳戶中建立的。這些被稱為工作負載帳戶，而 EKS 叢集則部署在稱為叢集帳戶的帳戶中。叢集帳戶將在下一節中探討。將資源部署到專用的工作負載帳戶類似於將 kubernetes 資源部署到專用的命名空間。

如果適當的話，工作負載帳戶可以進一步根據軟體開發生命週期或其他需求進行細分。例如，給定的工作負載可以有一個生產帳戶、一個開發帳戶，或者是在特定區域托管該工作負載實例的帳戶。[更多資訊](https://docs.aws.amazon.com/whitepapers/latest/organizing-your-aws-environment/organizing-workload-oriented-ous.html)可在此 AWS 白皮書中找到。

在實施 EKS 多帳戶策略時，您可以採用以下方法：

## 集中式 EKS 叢集

在這種方法中，您的 EKS 叢集將部署在一個稱為 `叢集帳戶` 的單一 AWS 帳戶中。使用 [IAM 角色的服務帳戶 (IRSA)](https://docs.aws.amazon.com/eks/latest/userguide/iam-roles-for-service-accounts.html) 或 [EKS Pod Identities](https://docs.aws.amazon.com/eks/latest/userguide/pod-identities.html) 來提供臨時 AWS 憑證，以及 [AWS Resource Access Manager (RAM)](https://aws.amazon.com/ram/) 來簡化網路存取，您可以為多租戶 EKS 叢集採用多帳戶策略。叢集帳戶將包含 VPC、子網路、EKS 叢集、EC2/Fargate 計算資源（工作節點）以及運行 EKS 叢集所需的任何其他網路配置。

在多工作負載帳戶策略中，AWS 帳戶通常與 [kubernetes 命名空間](https://kubernetes.io/docs/concepts/overview/working-with-objects/namespaces/)一致，作為隔離資源組的機制。在實施多帳戶策略的多租戶 EKS 叢集時，仍應遵循 [租戶隔離的最佳實踐](/security/docs/multitenancy/)。

在您的 AWS 組織中可能有多個 `叢集帳戶`，而根據您的軟體開發生命週期需求，擁有多個 `叢集帳戶` 是最佳實踐。對於在非常大規模運作的工作負載，您可能需要多個 `叢集帳戶` 以確保所有工作負載都有足夠的 kubernetes 和 AWS 服務配額。

| ![multi-account-eks](./images/multi-account-eks.jpg) |
|:--:|
| 在上圖中，AWS RAM 用於將子網路從叢集帳戶共享到工作負載帳戶。然後在 EKS 吊舷上運行的工作負載使用 IRSA 或 EKS Pod Identities 和角色鏈接來假設工作負載帳戶中的角色，並存取其 AWS 資源。 |

### 為多租戶叢集實施多工作負載帳戶策略

#### 使用 AWS Resource Access Manager 共享子網路

[AWS Resource Access Manager](https://aws.amazon.com/ram/) (RAM) 允許您跨 AWS 帳戶共享資源。

如果為您的 AWS 組織 [啟用了 RAM](https://docs.aws.amazon.com/ram/latest/userguide/getting-started-sharing.html#getting-started-sharing-orgs)，您可以將叢集帳戶的 VPC 子網路共享到您的工作負載帳戶。這將允許您的工作負載帳戶擁有的 AWS 資源（如 [Amazon ElastiCache](https://aws.amazon.com/elasticache/) 叢集或 [Amazon Relational Database Service (RDS)](https://aws.amazon.com/rds/) 資料庫）部署到與您的 EKS 叢集相同的 VPC 中，並可由運行在您的 EKS 叢集上的工作負載使用。

要通過 RAM 共享資源，請在叢集帳戶的 AWS 控制台中打開 RAM，選擇"資源共享"和"建立資源共享"。為您的資源共享命名並選擇要共享的子網路。再次選擇"下一步"，輸入您希望與之共享子網路的工作負載帳戶的 12 位數帳戶 ID，再次選擇"下一步"，然後單擊"建立資源共享"完成。完成此步驟後，工作負載帳戶就可以在那些子網路中部署資源。

資源共享也可以通過程式化方式或使用基礎架構作為代碼來建立。

#### 在 EKS Pod Identities 和 IRSA 之間做出選擇

在 2023 年的 re:Invent 大會上，AWS 推出了 EKS Pod Identities，作為一種更簡單的方式為 EKS 上的吊舷提供臨時 AWS 憑證。IRSA 和 EKS Pod Identities 都是向 EKS 吊舷提供臨時 AWS 憑證的有效方法，並將繼續得到支持。您應該考慮哪種提供方法最能滿足您的需求。

在使用 EKS 叢集和多個 AWS 帳戶時，IRSA 可以直接假設除 EKS 叢集所在帳戶以外的其他 AWS 帳戶中的角色，而 EKS Pod identities 則需要您配置角色鏈接。請參閱 [EKS 文檔](https://docs.aws.amazon.com/eks/latest/userguide/service-accounts.html#service-accounts-iam) 以獲得深入比較。

##### 使用 IAM 角色的服務帳戶存取 AWS API 資源

[IAM 角色的服務帳戶 (IRSA)](https://docs.aws.amazon.com/eks/latest/userguide/iam-roles-for-service-accounts.html) 允許您將臨時 AWS 憑證傳遞給在 EKS 上運行的工作負載。IRSA 可用於從叢集帳戶獲取工作負載帳戶中 IAM 角色的臨時憑證。這允許在叢集帳戶中的 EKS 叢集上運行的工作負載無縫地使用 AWS API 資源（如託管在工作負載帳戶中的 S3 儲存貯體），並使用 IAM 驗證來存取 Amazon RDS 資料庫或 Amazon EFS 檔案系統等資源。

除非明確啟用了跨帳戶存取，否則工作負載帳戶中的 AWS API 資源和其他使用 IAM 驗證的資源只能由同一工作負載帳戶中 IAM 角色的憑證存取。

###### 啟用 IRSA 跨帳戶存取

要為叢集帳戶中的工作負載啟用存取工作負載帳戶中資源的 IRSA，您首先必須在工作負載帳戶中建立 IAM OIDC 身份提供者。這可以通過與設置 [IRSA](https://docs.aws.amazon.com/eks/latest/userguide/enable-iam-roles-for-service-accounts.html) 相同的程序來完成，只是身份提供者將在工作負載帳戶中建立。

然後，在為 EKS 上的工作負載配置 IRSA 時，您可以 [按照與文檔相同的步驟](https://docs.aws.amazon.com/eks/latest/userguide/associate-service-account-role.html)，但使用 [工作負載帳戶的 12 位數帳戶 ID](https://docs.aws.amazon.com/eks/latest/userguide/cross-account-access.html)，如"從另一個帳戶的叢集建立身份提供者"一節所述。

配置完成後，在 EKS 中運行的應用程式將能夠直接使用其服務帳戶來假設工作負載帳戶中的角色，並使用該帳戶中的資源。

##### 使用 EKS Pod Identities 存取 AWS API 資源

[EKS Pod Identities](https://docs.aws.amazon.com/eks/latest/userguide/pod-identities.html) 是一種新的方式，為在 EKS 上運行的工作負載提供 AWS 憑證。EKS pod identities 簡化了 AWS 資源的配置，因為您不再需要管理 OIDC 配置來為 EKS 上的吊舷提供 AWS 憑證。

###### 啟用 EKS Pod Identities 跨帳戶存取

與 IRSA 不同，EKS Pod Identities 只能用於直接授予與 EKS 叢集所在相同帳戶中角色的存取權限。要存取另一個 AWS 帳戶中的角色，使用 EKS Pod Identities 的吊舷必須執行 [角色鏈接](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_terms-and-concepts.html#iam-term-role-chaining)。

可以在應用程式的 aws 配置檔案中使用各種 AWS SDK 中可用的 [Process Credentials Provider](https://docs.aws.amazon.com/sdkref/latest/guide/feature-process-credentials.html) 來配置角色鏈接。在配置配置檔案時，`credential_process` 可以用作憑證源，例如：

```bash
# AWS 配置檔案的內容
[profile account_b_role] 
source_profile = account_a_role 
role_arn = arn:aws:iam::444455556666:role/account-b-role

[profile account_a_role] 
credential_process = /eks-credential-processrole.sh
```

credential_process 調用的腳本源：

```bash
#!/bin/bash
# eks-credential-processrole.sh 的內容
# 這將從 pod identities 代理檢索憑證，
# 並在引用配置檔案時將其返回給 AWS SDK
curl -H "Authorization: $(cat $AWS_CONTAINER_AUTHORIZATION_TOKEN_FILE)" $AWS_CONTAINER_CREDENTIALS_FULL_URI | jq -c '{AccessKeyId: .AccessKeyId, SecretAccessKey: .SecretAccessKey, SessionToken: .Token, Expiration: .Expiration, Version: 1}' 
```

您可以如上所示建立一個包含帳戶 A 和 B 角色的 aws 配置檔案，並在您的吊舷規格中指定 AWS_CONFIG_FILE 和 AWS_PROFILE 環境變數。如果環境變數已經存在於吊舷規格中，EKS Pod identity webhook 不會覆蓋它們。

```yaml
# 吊舷規格的片段
containers: 
  - name: container-name
    image: container-image:version
    env:
    - name: AWS_CONFIG_FILE
      value: path-to-customer-provided-aws-config-file
    - name: AWS_PROFILE
      value: account_b_role
```

在為角色鏈接配置 EKS pod identities 的角色信任政策時，您可以參考 [EKS 特定屬性](https://docs.aws.amazon.com/eks/latest/userguide/pod-id-abac.html)作為會話標籤，並使用基於屬性的存取控制 (ABAC) 來限制對您的 IAM 角色的存取，只允許特定的 EKS Pod identity 會話，例如吊舷所屬的 Kubernetes 服務帳戶。

請注意，這些屬性中的一些可能不是通用唯一的，例如兩個 EKS 叢集可能有相同的命名空間，而一個叢集可能在跨命名空間時具有相同名稱的服務帳戶。因此，在使用 EKS Pod Identities 和 ABAC 授予存取權時，最佳做法是始終考慮叢集 arn 和命名空間來授予對服務帳戶的存取權。

###### ABAC 和 EKS Pod Identities 的跨帳戶存取

在使用 EKS Pod Identities 作為多帳戶策略的一部分來假設其他帳戶中的角色（角色鏈接）時，您可以選擇為每個需要存取另一個帳戶的服務帳戶分配一個唯一的 IAM 角色，或者跨多個服務帳戶使用一個通用的 IAM 角色，並使用 ABAC 來控制它可以存取哪些帳戶。

要使用 ABAC 控制哪些服務帳戶可以通過角色鏈接假設另一個帳戶中的角色，您可以建立一個角色信任政策語句，只允許在存在預期值時才能假設該角色。以下角色信任政策將只允許來自 EKS 叢集帳戶（帳戶 ID 111122223333）的角色在 `kubernetes-service-account`、`eks-cluster-arn` 和 `kubernetes-namespace` 標籤都具有預期值時才能假設該角色。

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "AWS": "arn:aws:iam::111122223333:root"
            },
            "Action": "sts:AssumeRole",
            "Condition": {
                "StringEquals": {
                    "aws:PrincipalTag/kubernetes-service-account": "PayrollApplication",
                    "aws:PrincipalTag/eks-cluster-arn": "arn:aws:eks:us-east-1:111122223333:cluster/ProductionCluster",
                    "aws:PrincipalTag/kubernetes-namespace": "PayrollNamespace"
                }
            }
        }
    ]
}
```

在使用這種策略時，最佳做法是確保通用的 IAM 角色只有 `sts:AssumeRole` 權限，沒有其他 AWS 存取權限。

在使用 ABAC 時，重要的是要控制誰有能力為 IAM 角色和用戶設置標籤，只有那些確實需要這樣做的人才能這樣做。任何能夠在 IAM 角色或用戶上設置與 EKS Pod Identities 相同的標籤的人，都可能會提高他們的特權。您可以使用 IAM 政策或服務控制政策 (SCP) 來限制誰有權在 IAM 角色和用戶上設置 `kubernetes-` 和 `eks-` 標籤。

## 分散式 EKS 叢集

在這種方法中，EKS 叢集部署到各自的工作負載 AWS 帳戶中，並與其他 AWS 資源（如 Amazon S3 儲存貯體、VPC、Amazon DynamoDB 資料表等）一起存在。每個工作負載帳戶都是獨立的、自給自足的，並由各自的業務單位/應用程式團隊進行操作。這種模式允許為各種叢集功能（AI/ML 叢集、批處理、通用等）建立可重用的藍圖，並根據應用程式團隊的需求提供叢集。應用程式團隊和平台團隊都在各自的 [GitOps](https://www.weave.works/technologies/gitops/) 存儲庫中操作，以管理對工作負載叢集的部署。

|![分散式 EKS 叢集架構](./images/multi-account-eks-decentralized.png)|
|:--:|
| 在上圖中，Amazon EKS 叢集和其他 AWS 資源部署到各自的工作負載帳戶。然後在 EKS 吊舷上運行的工作負載使用 IRSA 或 EKS Pod Identities 來存取其 AWS 資源。 |

GitOps 是一種管理應用程式和基礎架構部署的方式，整個系統都是在 Git 存儲庫中以聲明式的方式描述的。它是一種操作模型，為您提供使用版本控制、不可變工件和自動化的最佳實踐來管理多個 Kubernetes 叢集狀態的能力。在這種多叢集模型中，每個工作負載叢集都使用多個 Git 存儲庫進行引導，允許每個團隊（應用程式、平台、安全性等）在叢集上部署各自的更改。

您可以在每個帳戶中使用 [IAM 角色的服務帳戶 (IRSA)](https://docs.aws.amazon.com/eks/latest/userguide/iam-roles-for-service-accounts.html) 或 [EKS Pod Identities](https://docs.aws.amazon.com/eks/latest/userguide/pod-identities.html)，以允許您的 EKS 工作負載獲取臨時 aws 憑證來安全地存取其他 AWS 資源。IAM 角色在各自的工作負載 AWS 帳戶中建立，並映射到 k8s 服務帳戶以提供臨時 IAM 存取。因此，在這種方法中不需要跨帳戶存取。請按照 [IAM 角色的服務帳戶](https://docs.aws.amazon.com/eks/latest/userguide/iam-roles-for-service-accounts.html)文檔中的說明在每個工作負載帳戶中為 IRSA 設置，以及 [EKS Pod Identities](https://docs.aws.amazon.com/eks/latest/userguide/pod-identities.html) 文檔中的說明在每個帳戶中設置 EKS pod identities。

### 集中式網路

您還可以使用 AWS RAM 將 VPC 子網路共享到工作負載帳戶，並在其中啟動 Amazon EKS 叢集和其他 AWS 資源。這實現了集中式網路管理/管理、簡化的網路連接性和分散式 EKS 叢集。請參閱此 [AWS 博客](https://aws.amazon.com/blogs/containers/use-shared-vpcs-in-amazon-eks/)以獲取此方法的詳細演練和注意事項。

|![使用共享子網路的分散式 EKS 叢集架構](./images/multi-account-eks-shared-subnets.png)|
|:--:|
| 在上圖中，AWS RAM 用於將子網路從中央網路帳戶共享到工作負載帳戶。然後在這些子網路中啟動 EKS 叢集和其他 AWS 資源。EKS 吊舷使用 IRSA 或 EKS Pod Identities 來存取其 AWS 資源。 |

## 集中式與分散式 EKS 叢集

決定運行集中式還是分散式將取決於您的需求。下表展示了每種策略的主要區別。

|# |集中式 EKS 叢集 | 分散式 EKS 叢集 |
|:--|:--|:--|
|叢集管理：  |管理單個 EKS 叢集比管理多個叢集更容易 | 需要有效的叢集管理自動化來減少管理多個 EKS 叢集的操作開銷|
|成本效率： | 允許重用 EKS 叢集和網路資源，從而提高成本效率 | 需要為每個工作負載設置網路和叢集，這需要額外的資源|
|彈性： | 集中式叢集出現故障可能會影響多個工作負載 | 如果一個叢集出現故障，損害僅限於在該叢集上運行的工作負載。所有其他工作負載不受影響 |
|隔離和安全性：|使用 k8s 原生構造（如 `Namespaces`）實現隔離/軟多租戶。工作負載可能共享底層資源（如 CPU、內存等）。AWS 資源被隔離到各自的工作負載帳戶中，默認情況下不能從其他 AWS 帳戶訪問。|在計算資源上實現更強的隔離，因為工作負載在單獨的叢集和節點上運行，不共享任何資源。AWS 資源被隔離到各自的工作負載帳戶中，默認情況下不能從其他 AWS 帳戶訪問。|
|性能和可擴展性：|隨著工作負載增長到非常大的規模，您可能會在叢集帳戶中遇到 kubernetes 和 AWS 服務配額。您可以部署額外的叢集帳戶以進一步擴展|隨著存在更多叢集和 VPC，每個工作負載都有更多可用的 k8s 和 AWS 服務配額|
|網路： | 每個叢集使用單個 VPC，允許該叢集上的應用程式進行更簡單的連接 | 必須在分散式 EKS 叢集 VPC 之間建立路由|
|Kubernetes 訪問管理： |需要在叢集中維護許多不同的角色和用戶，以為所有工作負載團隊提供訪問權限，並確保正確隔離 kubernetes 資源| 由於每個叢集都專用於一個工作負載/團隊，因此訪問管理更簡單|
|AWS 訪問管理： |AWS 資源部署到各自的帳戶中，默認情況下只能通過工作負載帳戶中的 IAM 角色訪問。工作負載帳戶中的 IAM 角色通過 IRSA 或 EKS Pod Identities 跨帳戶假設。|AWS 資源部署到各自的帳戶中，默認情況下只能通過工作負載帳戶中的 IAM 角色訪問。工作負載帳戶中的 IAM 角色直接通過 IRSA 或 EKS Pod Identities 傳遞給吊舷。|
