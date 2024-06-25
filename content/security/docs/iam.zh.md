# 身份和访问管理

[身份和访问管理](https://docs.aws.amazon.com/IAM/latest/UserGuide/introduction.html) (IAM) 是一项 AWS 服务，执行两个基本功能：身份验证和授权。身份验证涉及身份验证，而授权管理 AWS 资源可执行的操作。在 AWS 中，资源可以是另一个 AWS 服务，例如 EC2，或者是 AWS [主体](https://docs.aws.amazon.com/IAM/latest/UserGuide/intro-structure.html#intro-structure-principal)，如 [IAM 用户](https://docs.aws.amazon.com/IAM/latest/UserGuide/id.html#id_iam-users)或[角色](https://docs.aws.amazon.com/IAM/latest/UserGuide/id.html#id_iam-roles)。规定资源可执行操作的规则表示为 [IAM 策略](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies.html)。

## 控制对 EKS 集群的访问

Kubernetes 项目支持各种不同的策略来对 kube-apiserver 服务的请求进行身份验证，例如 Bearer 令牌、X.509 证书、OIDC 等。EKS 目前支持 [webhook 令牌身份验证](https://kubernetes.io/docs/reference/access-authn-authz/authentication/#webhook-token-authentication)、[服务账户令牌](https://kubernetes.io/docs/reference/access-authn-authz/authentication/#service-account-tokens)，以及从 2021 年 2 月 21 日起支持 OIDC 身份验证。

webhook 身份验证策略调用一个 webhook 来验证 bearer 令牌。在 EKS 上，这些 bearer 令牌是由 AWS CLI 或 [aws-iam-authenticator](https://github.com/kubernetes-sigs/aws-iam-authenticator) 客户端在您运行 `kubectl` 命令时生成的。当您执行命令时，令牌会传递给 kube-apiserver，然后 kube-apiserver 会将其转发给身份验证 webhook。如果请求格式正确，webhook 会调用令牌正文中嵌入的预签名 URL。该 URL 验证请求的签名并将有关用户的信息（例如用户的账户、Arn 和 UserId）返回给 kube-apiserver。

要在终端窗口中手动生成身份验证令牌，请键入以下命令：

```bash
aws eks get-token --cluster-name <cluster_name>
```

您也可以以编程方式获取令牌。下面是一个用 Go 编写的示例：

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

输出应该类似于这样：

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

每个令牌以 `k8s-aws-v1.` 开头，后跟一个 base64 编码的字符串。解码后的字符串应该类似于这样：

```bash
https://sts.amazonaws.com/?Action=GetCallerIdentity&Version=2011-06-15&X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=XXXXJPFRILKNSRC2W5QA%2F20200219%2Fus-xxxx-1%2Fsts%2Faws4_request&X-Amz-Date=20200219T155427Z&X-Amz-Expires=60&X-Amz-SignedHeaders=host%3Bx-k8s-aws-id&X-Amz-Signature=XXXf8f3285e320ddb5e683a5c9a405301ad76546f24f28111fdad09cf648a393
```

该令牌由一个预签名 URL 组成，其中包含一个 Amazon 凭证和签名。有关更多详细信息，请参阅 [https://docs.aws.amazon.com/STS/latest/APIReference/API_GetCallerIdentity.html](https://docs.aws.amazon.com/STS/latest/APIReference/API_GetCallerIdentity.html)。

该令牌的生存时间 (TTL) 为 15 分钟，之后需要生成新的令牌。当您使用 `kubectl` 等客户端时，这是自动处理的，但是，如果您使用 Kubernetes 仪表板，每次令牌过期时您都需要生成新的令牌并重新进行身份验证。

一旦用户的身份通过 AWS IAM 服务进行了身份验证，kube-apiserver 就会读取 `kube-system` 命名空间中的 `aws-auth` ConfigMap，以确定与用户关联的 RBAC 组。`aws-auth` ConfigMap 用于在 IAM 主体（即 IAM 用户和角色）与 Kubernetes RBAC 组之间创建静态映射。RBAC 组可以在 Kubernetes RoleBindings 或 ClusterRoleBindings 中引用。它们类似于 IAM 角色，因为它们定义了可以对 Kubernetes 资源（对象）集合执行的一组操作（动词）。

### 集群访问管理器

集群访问管理器现在是管理 AWS IAM 主体对 Amazon EKS 集群访问的首选方式，它是 EKS v1.23 及更高版本集群（新集群或现有集群）的一项可选功能。它简化了 AWS IAM 和 Kubernetes RBAC 之间的身份映射，消除了在 AWS 和 Kubernetes API 之间切换或编辑 `aws-auth` ConfigMap 进行访问管理的需要，从而减少了操作开销，并有助于解决错误配置问题。该工具还允许集群管理员自动撤销或细化为创建集群的 AWS IAM 主体自动授予的 `cluster-admin` 权限。

该 API 依赖于两个概念：

- **访问条目：**直接链接到允许对 Amazon EKS 集群进行身份验证的 AWS IAM 主体（用户或角色）的集群身份。
- **访问策略：**是 Amazon EKS 特定的策略，为访问条目提供在 Amazon EKS 集群中执行操作的授权。

> 在发布时，Amazon EKS 仅支持预定义和 AWS 管理的策略。访问策略不是 IAM 实体，由 Amazon EKS 定义和管理。

集群访问管理器允许将上游 RBAC 与支持允许和传递（但不是拒绝）Kubernetes AuthZ 决策的访问策略相结合。如果上游 RBAC 和 Amazon EKS 授权者都无法确定请求评估的结果，则会发生拒绝决策。

使用此功能，Amazon EKS 支持三种身份验证模式：

1. `CONFIG_MAP` 继续专门使用 `aws-auth` configMap。
2. `API_AND_CONFIG_MAP` 从 EKS 访问条目 API 和 `aws-auth` configMap 获取经过身份验证的 IAM 主体，优先考虑访问条目。理想的是将现有的 `aws-auth` 权限迁移到访问条目。
3. `API` 专门依赖 EKS 访问条目 API。这是新的**推荐方法**。

要开始使用，集群管理员可以创建或更新 Amazon EKS 集群，将首选身份验证设置为 `API_AND_CONFIG_MAP` 或 `API` 方法，并为所需的 AWS IAM 主体定义访问条目。

```bash
$ aws eks create-cluster \
    --name <CLUSTER_NAME> \
    --role-arn <CLUSTER_ROLE_ARN> \
    --resources-vpc-config subnetIds=<value>,endpointPublicAccess=true,endpointPrivateAccess=true \
    --logging '{"clusterLogging":[{"types":["api","audit","authenticator","controllerManager","scheduler"],"enabled":true}]}' \
    --access-config authenticationMode=API_AND_CONFIG_MAP,bootstrapClusterCreatorAdminPermissions=false
```

上面的命令是一个示例，用于创建一个没有集群创建者管理员权限的 Amazon EKS 集群。

可以使用 `update-cluster-config` 命令更新 Amazon EKS 集群配置以启用 `API` authenticationMode，对于使用 `CONFIG_MAP` 的现有集群，您必须先更新到 `API_AND_CONFIG_MAP`，然后再更新到 `API`。**这些操作无法撤消**，这意味着无法从 `API` 切换到 `API_AND_CONFIG_MAP` 或 `CONFIG_MAP`，也无法从 `API_AND_CONFIG_MAP` 切换到 `CONFIG_MAP`。

```bash
$ aws eks update-cluster-config \
    --name <CLUSTER_NAME> \
    --access-config authenticationMode=API
```

该 API 支持命令来添加和撤销对集群的访问权限，以及验证指定集群的现有访问策略和访问条目。默认策略是按照以下方式创建的，以匹配 Kubernets RBAC：

| EKS 访问策略 | Kubernetes RBAC |
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

> 当集群在没有集群创建者管理员权限的情况下创建时，不会有可用的访问条目，这是默认情况下创建的唯一条目。

### `aws-auth` ConfigMap _(已弃用)_

Kubernetes 与 AWS 身份验证集成的一种方式是通过 `aws-auth` ConfigMap，它位于 `kube-system` 命名空间中。它负责将 AWS IAM 身份（用户、组和角色）身份验证映射到 Kubernetes 基于角色的访问控制 (RBAC) 授权。在您的 Amazon EKS 集群的供应阶段，会自动在集群中创建 `aws-auth` ConfigMap。它最初是为了允许节点加入您的集群而创建的，但如前所述，您也可以使用此 ConfigMap 为 IAM 主体添加 RBAC 访问权限。

要检查您集群的 `aws-auth` ConfigMap，您可以使用以下命令。

```bash
kubectl -n kube-system get configmap aws-auth -o yaml
```

这是 `aws-auth` ConfigMap 的默认配置示例。

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

此 ConfigMap 的主要部分位于 `data` 下的 `mapRoles` 块中，它基本上由 3 个参数组成。

- **groups：**要将 IAM 角色映射到的 Kubernetes 组。这可以是默认组，也可以是在 `clusterrolebinding` 或 `rolebinding` 中指定的自定义组。在上面的示例中，我们只声明了系统组。
- **rolearn：**要映射到 Kubernetes 组的 AWS IAM 角色的 ARN，使用以下格式 `arn:<PARTITION>:iam::<AWS_ACCOUNT_ID>:role/role-name`。
- **username：**在 Kubernetes 中映射到 AWS IAM 角色的用户名。这可以是任何自定义名称。

> 您也可以通过在 `aws-auth` ConfigMap 的 `data` 下定义一个新的 `mapUsers` 配置块来映射 AWS IAM 用户的权限，将 **rolearn** 参数替换为 **userarn**，但是作为**最佳实践**，始终建议使用 `mapRoles`。

要管理权限，您可以通过添加或删除对您的 Amazon EKS 集群的访问权限来编辑 `aws-auth` ConfigMap。虽然可以手动编辑 `aws-auth` ConfigMap，但建议使用 `eksctl` 等工具，因为这是一个非常敏感的配置，不准确的配置可能会将您锁定在 Amazon EKS 集群之外。有关更多详细信息，请查看下面的小节 [使用工具对 aws-auth ConfigMap 进行更改](https://aws.github.io/aws-eks-best-practices/security/docs/iam/#use-tools-to-make-changes-to-the-aws-auth-configmap)。

## 集群访问建议

### 使 EKS 集群端点私有化

默认情况下，当您配置 EKS 集群时，API 集群端点会设置为公共的，即可以从互联网访问。尽管可以从互联网访问，但端点仍然被认为是安全的，因为它要求所有 API 请求都由 IAM 进行身份验证，然后由 Kubernetes RBAC 进行授权。尽管如此，如果您的公司安全策略要求您限制从互联网访问 API 或防止您将流量路由到集群 VPC 之外，您可以：

- 将 EKS 集群端点配置为私有。有关此主题的更多信息，请参阅 [修改集群端点访问](https://docs.aws.amazon.com/eks/latest/userguide/cluster-endpoint.html)。
- 保持集群端点公开，并指定哪些 CIDR 块可以与集群端点通信。这些块实际上是一组允许访问集群端点的公共 IP 地址的白名单。
- 配置公共访问和一组允许的 CIDR 块，并将私有端点访问设置为启用。这将允许从特定范围的公共 IP 进行公共访问，同时强制所有 kubelet（工作节点）与 Kubernetes API 之间的网络流量通过在控制平面配置时在集群 VPC 中配置的跨账户 ENI。

### 不要使用服务账户令牌进行身份验证

服务账户令牌是一种长期的、静态凭证。如果它被泄露、丢失或被盗，攻击者可能能够执行与该令牌关联的所有操作，直到删除该服务账户为止。有时，您可能需要为必须从集群外部消费 Kubernetes API 的应用程序授予例外，例如 CI/CD 管道应用程序。如果此类应用程序运行在 AWS 基础设施（如 EC2 实例）上，请考虑使用实例配置文件并将其映射到 Kubernetes RBAC 角色。

### 对 AWS 资源采用最小特权访问

IAM 用户不需要被分配对 AWS 资源的权限就可以访问 Kubernetes API。如果您需要为 IAM 用户授予对 EKS 集群的访问权限，请在 `aws-auth` ConfigMap 中为该用户创建一个条目，将其映射到特定的 Kubernetes RBAC 组。

### 从集群创建者主体中删除 cluster-admin 权限

默认情况下，创建的 Amazon EKS 集群会将永久的 `cluster-admin` 权限绑定到集群创建者主体。使用集群访问管理器 API，可以在创建集群时通过将 `--access-config bootstrapClusterCreatorAdminPermissions` 设置为 `false` 来创建没有此权限的集群，当使用 `API_AND_CONFIG_MAP` 或 `API` 身份验证模式时。撤销此访问权限被视为最佳实践，以避免对集群配置进行任何不需要的更改。撤销此访问权限的过程与撤销对集群的任何其他访问权限的过程相同。

该 API 让您可以灵活地仅将 IAM 主体与访问策略解除关联，在本例中是 `AmazonEKSClusterAdminPolicy`。

```bash
$ aws eks list-associated-access-policies \
    --cluster-name <CLUSTER_NAME> \
    --principal-arn <IAM_PRINCIPAL_ARN>

$ aws eks disassociate-access-policy --cluster-name <CLUSTER_NAME> \
    --principal-arn <IAM_PRINCIPAL_ARN. \
    --policy-arn arn:aws:eks::aws:cluster-access-policy/AmazonEKSClusterAdminPolicy
```

或者完全删除与 `cluster-admin` 权限关联的访问条目。

```bash
$ aws eks list-access-entries --cluster-name <CLUSTER_NAME>

{
    "accessEntries": []
}

$ aws eks delete-access-entry --cluster-name <CLUSTER_NAME> \
  --principal-arn <IAM_PRINCIPAL_ARN>
```

> 在发生事故、紧急情况或者当集群无法访问时，可以再次授予此访问权限。

如果集群仍然使用 `CONFIG_MAP` 身份验证方法，所有其他用户都应该通过 `aws-auth` ConfigMap 获得对集群的访问权限，并且在配置了 `aws-auth` ConfigMap 之后，可以删除分配给创建集群的实体的角色，并且只在发生事故、紧急情况或者当 `aws-auth` ConfigMap 损坏且集群无法访问时才重新创建该角色。这在生产集群中特别有用。

### 当多个用户需要相同的访问权限时，请使用 IAM 角色

与为每个单独的 IAM 用户创建条目不同，允许这些用户承担 IAM 角色并将该角色映射到 Kubernetes RBAC 组。这将更容易维护，尤其是在需要访问权限的用户数量增加时。

!!! attention
    当使用 `aws-auth` ConfigMap 映射的 IAM 实体访问 EKS 集群时，描述的用户名将记录在 Kubernetes 审计日志的用户字段中。如果您使用 IAM 角色，则实际承担该角色的用户无法被记录和审计。

如果仍在使用 `aws-auth` configMap 作为身份验证方法，当为 IAM 角色分配 K8s RBAC 权限时，您应该在用户名中包含 {{SessionName}}。这样，审计日志将记录会话名称，以便您可以跟踪谁实际承担了此角色，以及 CloudTrail 日志。

```yaml
- rolearn: arn:aws:iam::XXXXXXXXXXXX:role/testRole
  username: testRole:{{SessionName}}
  groups:
    - system:masters
```

> 在 Kubernetes 1.20 及更高版本中，不再需要进行此更改，因为 ```user.extra.sessionName.0``` 已添加到 Kubernetes 审计日志中。

### 在创建 RoleBindings 和 ClusterRoleBindings 时采用最小特权访问

与前面关于授予对 AWS 资源的访问权限的要点一样，RoleBindings 和 ClusterRoleBindings 应该只包含执行特定功能所需的权限集。除非绝对必要，否则请避免在您的角色和集群角色中使用 `["*"]`。如果您不确定要分配哪些权限，请考虑使用 [audit2rbac](https://github.com/liggitt/audit2rbac) 等工具，根据 Kubernetes 审计日志中观察到的 API 调用自动生成角色和绑定。

### 使用自动化流程创建集群

如前面的步骤所示，在创建 Amazon EKS 集群时，如果不使用 `API_AND_CONFIG_MAP` 或 `API` 身份验证模式，并且不选择不将 `cluster-admin` 权限委派给集群创建者，则创建集群的 IAM 实体用户或角色（如联合用户）将自动在集群的 RBAC 配置中获得 `system:masters` 权限。即使将删除此权限视为最佳实践，如果使用 `CONFIG_MAP` 身份验证方法，依赖于 `aws-auth` ConfigMap，也无法撤销此访问权限。因此，最好使用与专用 IAM 角色相关联的基础设施自动化管道来创建集群，该角色没有其他用户或实体可以承担的权限，并定期审核对该角色的权限、策略和谁有权触发管道的访问权限。此外，该角色不应用于对集群执行例行操作，而应专门用于通过 SCM 代码更改等方式触发管道的集群级操作。

### 使用专用 IAM 角色创建集群

当您创建 Amazon EKS 集群时，创建集群的 IAM 实体用户或角色（如联合用户）将自动在集群的 RBAC 配置中获得 `system:masters` 权限。此访问权限无法通过 `aws-auth` ConfigMap 进行管理。因此，最好使用专用 IAM 角色创建集群，并定期审核谁可以承担此角色。此角色不应用于对集群执行例行操作，而应将其他用户通过 `aws-auth` ConfigMap 授予对集群的访问权限。在配置了 `aws-auth` ConfigMap 之后，应该保护该角色，并且只在临时提升特权模式/紧急情况下使用，例如当集群无法访问时。这在没有直接用户访问配置的集群中特别有用。

### 定期审核对集群的访问权限

随着时间的推移，需要访问权限的人员可能会发生变化。计划定期审核 `aws-auth` ConfigMap，查看谁被授予了访问权限以及他们被分配了哪些权限。您还可以使用开源工具，如 [kubectl-who-can](https://github.com/aquasecurity/kubectl-who-can) 或 [rbac-lookup](https://github.com/FairwindsOps/rbac-lookup) 来检查绑定到特定服务账户、用户或组的角色。我们将在 [审计](detective.md) 一节中进一步探讨这个主题。可以在 NCC 集团的这篇[文章](https://www.nccgroup.trust/us/about-us/newsroom-and-events/blog/2019/august/tools-and-methods-for-auditing-kubernetes-rbac-policies/?mkt_tok=eyJpIjoiWWpGa056SXlNV1E0WWpRNSIsInQiOiJBT1hyUTRHYkg1TGxBV0hTZnRibDAyRUZ0VzBxbndnRzNGbTAxZzI0WmFHckJJbWlKdE5WWDdUQlBrYVZpMnNuTFJ1R3hacVYrRCsxYWQ2RTRcL2pMN1BtRVA1ZFZcL0NtaEtIUDdZV3pENzNLcE1zWGVwUndEXC9Pb2tmSERcL1pUaGUifQ%3D%3D) 中找到更多想法。

### 如果依赖 `aws-auth` configMap，请使用工具对其进行更改

格式错误的 aws-auth ConfigMap 可能会导致您无法访问集群。如果您需要对 ConfigMap 进行更改，请使用工具。

**eksctl**
`eksctl` CLI 包括一个用于将身份映射添加到 aws-auth ConfigMap 的命令。

查看 CLI 帮助：

```bash
$ eksctl create iamidentitymapping --help
...
```

检查映射到您的 Amazon EKS 集群的身份。

```bash
$ eksctl get iamidentitymapping --cluster $CLUSTER_NAME --region $AWS_REGION
ARN                                                                   USERNAME                        GROUPS                                                  ACCOUNT
arn:aws:iam::788355785855:role/kube-system-<SELF_GENERATED_UUID>      system:node:{{SessionName}}     system:bootstrappers,system:nodes,system:node-proxier  
```

使 IAM 角色成为集群管理员：

```bash
$ eksctl create iamidentitymapping --cluster  <CLUSTER_NAME> --region=<region> --arn arn:aws:iam::123456:role/testing --group system:masters --username admin
...
```

有关更多信息，请查看 [`eksctl` 文档](https://eksctl.io/usage/iam-identity-mappings/)

**[aws-auth](https://github.com/keikoproj/aws-auth) by keikoproj**

keikoproj 的 `aws-auth` 包括 CLI 和 Go 库。

下载并查看 CLI 帮助：

```bash
$ go get github.com/keikoproj/aws-auth
...
$ aws-auth help
...
```

或者，使用 [krew 插件管理器](https://krew.sigs.k8s.io) 为 kubectl 安装 `aws-auth`。

```bash
$ kubectl krew install aws-auth
...
$ kubectl aws-auth
...
```

[在 GitHub 上查看 aws-auth 文档](https://github.com/keikoproj/aws-auth/blob/master/README.md)了解更多信息，包括 Go 库。

**[AWS IAM Authenticator CLI](https://github.com/kubernetes-sigs/aws-iam-authenticator/tree/master/cmd/aws-iam-authenticator)**

`aws-iam-authenticator` 项目包括一个用于更新 ConfigMap 的 CLI。

在 GitHub 上[下载发行版](https://github.com/kubernetes-sigs/aws-iam-authenticator/releases)。

为 IAM 角色添加集群权限：

```bash
$ ./aws-iam-authenticator add role --rolearn arn:aws:iam::185309785115:role/lil-dev-role-cluster --username lil-dev-user --groups system:masters --kubeconfig ~/.kube/config
...
```

### 身份验证和访问管理的替代方法

虽然 IAM 是用户需要访问 EKS 集群时的首选身份验证方式，但也可以使用 OIDC 身份提供程序（如 GitHub）通过身份验证代理和 Kubernetes [模拟](https://kubernetes.io/docs/reference/access-authn-authz/authentication/#user-impersonation)进行身份验证。AWS Open Source 博客上发布了两种此类解决方案的文章：

- [使用 GitHub 凭据对 EKS 进行身份验证 Teleport](https://aws.amazon.com/blogs/opensource/authenticating-eks-github-credentials-teleport/)
- [使用 kube-oidc-proxy 跨多个 EKS 集群实现一致的 OIDC 身份验证](https://aws.amazon.com/blogs/opensource/consistent-oidc-authentication-across-multiple-eks-clusters-using-kube-oidc-proxy/)

!!! attention
    EKS 原生支持无需使用代理即可进行 OIDC 身份验证。有关更多信息，请阅读发布博客 [为 Amazon EKS 引入 OIDC 身份提供程序身份验证](https://aws.amazon.com/blogs/containers/introducing-oidc-identity-provider-authentication-amazon-eks/)。有关如何使用流行的开源 OIDC 提供程序 Dex（具有各种不同身份验证方法的连接器）配置 EKS 的示例，请参阅 [使用 Dex 和 dex-k8s-authenticator 对 Amazon EKS 进行身份验证](https://aws.amazon.com/blogs/containers/using-dex-dex-k8s-authenticator-to-authenticate-to-amazon-eks/)。如博客所述，通过 OIDC 提供程序进行身份验证的用户的用户名/组将出现在 Kubernetes 审计日志中。

您还可以使用 [AWS SSO](https://docs.aws.amazon.com/singlesignon/latest/userguide/what-is.html) 将 AWS 与外部身份提供程序（如 Azure AD）联合。如果您决定使用它，AWS CLI v2.0 包括一个选项，可以创建一个命名配置文件，从而轻松地将 SSO 会话与当前 CLI 会话关联并承担 IAM 角色。请注意，您必须在运行 `kubectl` 之前承担一个角色，因为 IAM 角色用于确定用户的 Kubernetes RBAC 组。

## EKS pod 的身份和凭证

某些在 Kubernetes 集群内运行的应用程序需要权限来调用 Kubernetes API 才能正常运行。例如，[AWS Load Balancer Controller](https://github.com/kubernetes-sigs/aws-load-balancer-controller) 需要能够列出服务的端点。控制器还需要能够调用 AWS API 来配置和配置 ALB。在本节中，我们将探讨为 Pod 分配权限和特权的最佳实践。

### Kubernetes 服务账户

服务账户是一种特殊类型的对象，允许您将 Kubernetes RBAC 角色分配给 pod。每个命名空间中都会自动创建一个默认服务账户。当您在命名空间中部署 pod 而不引用特定服务账户时，该命名空间的默认服务账户将自动分配给 Pod，并且该服务账户（JWT）令牌的 Secret 将作为卷挂载到 pod 的 `/var/run/secrets/kubernetes.io/serviceaccount` 目录下。解码该目录中的服务账户令牌将显示以下元数据：

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

默认服务账户对 Kubernetes API 具有以下权限。

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

此角色授权未经身份验证和已经过身份验证的用户读取 API 信息，并被视为可公开访问。

当 Pod 中运行的应用程序调用 Kubernetes API 时，需要为该 Pod 分配一个明确授予它调用这些 API 的权限的服务账户。与用户访问权限的指导原则类似，绑定到服务账户的角色或集群角色应该仅限于应用程序正常运行所需的 API 资源和方法。要使用非默认服务账户，只需将 Pod 的 `spec.serviceAccountName` 字段设置为您希望使用的服务账户的名称即可。有关创建服务账户的更多信息，请参阅 [https://kubernetes.io/docs/reference/access-authn-authz/rbac/#service-account-permissions](https://kubernetes.io/docs/reference/access-authn-authz/rbac/#service-account-permissions)。

!!! note
    在 Kubernetes 1.24 之前，Kubernetes 会自动为每个服务账户创建一个 secret。该 secret 将挂载到 pod 的 /var/run/secrets/kubernetes.io/serviceaccount 目录下，pod 将使用它对 Kubernetes API 服务器进行身份验证。在 Kubernetes 1.24 中，当 pod 运行时，将动态生成服务账户令牌，默认情况下该令牌仅有效一小时。不会为服务账户创建 secret。如果您有一个需要对 Kubernetes API 进行身份验证的应用程序运行在集群外部（例如 Jenkins），您需要创建一个类型为 `kubernetes.io/service-account-token` 的 secret，以及一个引用服务账户的注释，如 `metadata.annotations.kubernetes.io/service-account.name: <SERVICE_ACCOUNT_NAME>`。以这种方式创建的 secret 不会过期。

### 服务账户的 IAM 角色 (IRSA)

IRSA 是一项功能，允许您将 IAM 角色分配给 Kubernetes 服务账户。它利用了 Kubernetes 的一个功能，称为 [服务账户令牌卷投影](https://kubernetes.io/docs/tasks/configure-pod-container/configure-service-account/#serviceaccount-token-volume-projection)。当 Pod 配置了引用 IAM 角色的服务账户时，Kubernetes API 服务器将在启动时调用集群的公共 OIDC 发现端点。该端点以加密方式签名 Kubernetes 发出的 OIDC 令牌，并将生成的令牌作为卷挂载。此签名令牌允许 Pod 调用与 IAM 角色关联的 AWS API。当调用 AWS API 时，AWS SDK 将调用 `sts:AssumeRoleWithWebIdentity`。在验证令牌签名后，IAM 将 Kubernetes 发出的令牌与临时 AWS 角色凭证进行交换。

使用 IRSA 时，重要的是[重用 AWS SDK 会话](#reuse-aws-sdk-sessions-with-irsa)以避免不必要的调用 AWS STS。

解码 IRSA 的（JWT）令牌将产生类似于下面示例的输出：

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

此特定令牌授予 Pod 对 S3 的只读权限，方式是承担一个 IAM 角色。当应用程序尝试从 S3 读取时，令牌将被交换为一组临时 IAM 凭证，类似于这样：

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

EKS 控制平面作为一部分运行的一个变异 webhook 将 AWS 角色 ARN 和指向 Web 身份令牌文件的路径注入到 Pod 中作为环境变量。这些值也可以手动提供。

```bash
AWS_ROLE_ARN=arn:aws:iam::AWS_ACCOUNT_ID:role/IAM_ROLE_NAME
AWS_WEB_IDENTITY_TOKEN_FILE=/var/run/secrets/eks.amazonaws.com/serviceaccount/token
```

kubelet 将在令牌的生存时间超过 80% 或 24 小时后自动轮换投影的令牌。AWS SDK 负责在令牌轮换时重新加载令牌。有关 IRSA 的更多信息，请参阅 [https://docs.aws.amazon.com/eks/latest/userguide/iam-roles-for-service-accounts-technical-overview.html](https://docs.aws.amazon.com/eks/latest/userguide/iam-roles-for-service-accounts-technical-overview.html)。

### EKS Pod 身份

[EKS Pod 身份](https://docs.aws.amazon.com/eks/latest/userguide/pod-identities.html)是在 2023 年 re：Invent 上推出的一项功能，允许您将 IAM 角色分配给 kubernetes 服务账户，而无需为您的 AWS 账户中的每个集群配置开放 ID 连接 (OIDC) 身份提供程序 (IDP)。要使用 EKS Pod 身份，您必须部署一个作为 DaemonSet pod 在每个合格的工作节点上运行的代理。此代理作为 EKS 附加组件提供给您，是使用 EKS Pod 身份功能的先决条件。您的应用程序必须使用[支持的 AWS SDK 版本](https://docs.aws.amazon.com/eks/latest/userguide/pod-id-minimum-sdk.html)才能使用此功能。

当为 Pod 配置了 EKS Pod 身份时，EKS 将在 `/var/run/secrets/pods.eks.amazonaws.com/serviceaccount/eks-pod-identity-token` 处挂载和刷新 pod 身份令牌。AWS SDK 将使用此令牌与 EKS Pod 身份代理通信，代理将使用 pod 身份令牌和代理的 IAM 角色通过调用 [AssumeRoleForPodIdentity API](https://docs.aws.amazon.com/eks/latest/APIReference/API_auth_AssumeRoleForPodIdentity.html) 为您的 pod 创建临时凭证。传递给您的 pod 的 pod 身份令牌是从您的 EKS 集群发出并经过加密签名的 JWT，其中包含适用于 EKS Pod 身份的适当 JWT 声明。

要了解有关 EKS Pod 身份的更多信息，请参阅[此博客](https://aws.amazon.com/blogs/containers/amazon-eks-pod-identity-a-new-way-for-applications-on-eks-to-obtain-iam-credentials/)。

您无需对应用程序代码进行任何修改即可使用 EKS Pod 身份。支持的 AWS SDK 版本将自动使用[凭证提供程序链](https://docs.aws.amazon.com/sdkref/latest/guide/standardized-credentials.html)发现通过 EKS Pod 身份提供的凭证。与 IRSA 一样，EKS pod 身份在您的 pod 中设置变量，以指导它们如何找到 AWS 凭证。

#### 使用 EKS Pod 身份的 IAM 角色

- EKS Pod 身份只能直接承担属于与 EKS 集群相同 AWS 账户的 IAM 角色。要访问另一个 AWS 账户中的 IAM 角色，您必须通过[在您的 SDK 配置中配置配置文件](https://docs.aws.amazon.com/sdkref/latest/guide/feature-assume-role-credentials.html)或在[您的应用程序代码中](https://docs.aws.amazon.com/IAM/latest/UserGuide/sts_example_sts_AssumeRole_section.html)承担该角色。
- 在为服务账户配置 EKS Pod 身份时，配置 Pod 身份关联的人员或流程必须具有对该角色的 `iam:PassRole` 权限。
- 每个服务账户只能通过 EKS Pod 身份与一个 IAM 角色关联，但您可以将同一 IAM 角色与多个服务账户关联。
- 与 EKS Pod 身份一起使用的 IAM 角色必须允许 `pods.eks.amazonaws.com` 服务主体承担它们，_并_设置会话标签。以下是一个允许 EKS Pod 身份使用 IAM 角色的角色信任策略示例：

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

AWS 建议使用条件键（如 `aws:SourceOrgId`）来帮助防止[跨服务混淆代理问题](https://docs.aws.amazon.com/IAM/latest/UserGuide/confused-deputy.html#cross-service-confused-deputy-prevention)。在上面的示例角色信任策略中，`ResourceOrgId` 是一个变量，等于 AWS 账户所属的 AWS Organizations 组织的组织 ID。EKS 在使用 EKS Pod 身份承担角色时，将为 `aws:SourceOrgId` 传递一个等于该值的值。

#### ABAC 和 EKS Pod 身份

当 EKS Pod 身份承担 IAM 角色时，它会设置以下会话标签：

|EKS Pod 身份会话标签 | 值 |
|:--|:--|
|kubernetes-namespace | 与 EKS Pod 身份关联的 pod 所在的命名空间。|
|kubernetes-service-account | 与 EKS Pod 身份关联的 kubernetes 服务账户的名称|
|eks-cluster-arn | EKS 集群的 ARN，例如 `arn:${Partition}:eks:${Region}:${Account}:cluster/${ClusterName}`。集群 ARN 是唯一的，但如果在同一区域、同一 AWS 账户中删除并重新创建具有相同名称的集群，它将具有相同的 ARN。 |
|eks-cluster-name | EKS 集群的名称。请注意，您的 AWS 账户中的 EKS 集群名称可能相同，其他 AWS 账户中的 EKS 集群也可能相同。 |
|kubernetes-pod-name | EKS 中 pod 的名称。 |
|kubernetes-pod-uid | EKS 中 pod 的 UID。 |

这些会话标签允许您使用[基于属性的访问控制 (ABAC)](https://docs.aws.amazon.com/IAM/latest/UserGuide/introduction_attribute-based-access-control.html) 仅向特定的 kubernetes 服务账户授予对您的 AWS 资源的访问权限。这样做时，_非常重要的是_要理解 kubernetes 服务账户只在命名空间内是唯一的，kubernetes 命名空间只在 EKS 集群内是唯一的。可以使用 `aws:PrincipalTag/<tag-key>` 全局条件键（如 `aws:PrincipalTag/eks-cluster-arn`）在 AWS 策略中访问这些会话标签。

例如，如果您想仅向特定服务账户授予访问您账户中 AWS 资源的权限，您需要使用 IAM 或资源策略检查 `eks-cluster-arn` 和 `kubernetes-namespace` 标签以及 `kubernetes-service-account`，以确保只有来自预期集群的该服务账户才能访问该资源，因为其他集群可能具有相同的 `kubernetes-service-accounts` 和 `kubernetes-namespaces`。

此示例 S3 存储桶策略仅在 `kubernetes-service-account`、`kubernetes-namespace` 和 `eks-cluster-arn` 都满足其预期值的情况下，才允许对该存储桶中的对象进行访问，其中 EKS 集群托管在 AWS 账户 `111122223333` 中。

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

### EKS Pod 身份与 IRSA 的比较

EKS Pod 身份和 IRSA 都是向 EKS pod 提供临时 AWS 凭证的首选方式。除非您有特定的 IRSA 用例，否则我们建议您在使用 EKS 时使用 EKS Pod 身份。此表有助于比较这两个功能。

|# |EKS Pod 身份 | IRSA |
|:--|:--|:--|
|需要在您的 AWS 账户中创建 OIDC IDP 的权限？|否|是|
|需要为每个集群设置唯一的 IDP？|否|是|
|设置相关会话标签以用于 ABAC？|是|否|
|需要 iam：PassRole 检查？|是| 否 |
|使用您的 AWS 账户的 AWS STS 配额？|否|是|
|可以访问其他 AWS 账户？| 通过角色链接间接访问 | 通过 sts：AssumeRoleWithWebIdentity 直接访问|
|与 AWS SDK 兼容？|是|是|
|需要在节点上有 Pod 身份代理 Daemonset？ |是|否|

## EKS pod 的身份和凭证建议

### 更新 aws-node daemonset 以使用 IRSA

目前，aws-node daemonset 配置为使用分配给 EC2 实例的角色来为 pod 分配 IP。此角色包括几个 AWS 托管策略，例如 AmazonEKS_CNI_Policy 和 EC2ContainerRegistryReadOnly，这实际上允许节点上运行的**所有**pod 附加/分离 ENI、分配/取消分配 IP 地址或从 ECR 拉取镜像。由于这会给您的集群带来风险，因此建议您更新 aws-node daemonset 以使用 IRSA。可以在本指南的[存储库](https://github.com/aws/aws-eks-best-practices/tree/master/projects/enable-irsa/src)中找到执行此操作的脚本。

aws-node daemonset 目前不支持 EKS Pod 身份。

### 限制对分配给工作节点的实例配置文件的访问

当您使用 IRSA 或 EKS Pod 身份时，它会更新 pod 的凭证链以首先使用 IRSA 或 EKS Pod 身份，但是，pod _仍然可以继承分配给工作节点的实例配置文件的权限_。使用 IRSA 或 EKS Pod 身份时，**强烈**建议您阻止访问[实例元数据](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/configuring-instance-metadata-service.html)，以帮助确保您的应用程序只具有所需的权限，而不是它们的节点的权限。

!!! caution
    阻止访问实例元数据将防止不使用 IRSA 或 EKS Pod 身份的 pod 继承分配给工作节点的角色。

您可以通过要求实例仅使用 IMDSv2 并将跃点计数更新为 1 来阻止访问实例元数据，如下例所示。您也可以在节点组的启动模板中包含这些设置。**不要**禁用实例元数据，因为这将阻止依赖实例元数据的组件（如节点终止处理程序等）正常工作。

```bash
$ aws ec2 modify-instance-metadata-options --instance-id <value> --http-tokens required --http-put-response-hop-limit 1
...
```

如果您使用 Terraform 创建用于托管节点组的启动模板，请添加元数据块以配置跃点计数，如此代码片段所示：

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

您还可以通过操作节点上的 iptables 来阻止 pod 访问 EC2 元数据。有关此方法的更多信息，请参阅[限制对实例元数据服务的访问](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/instancedata-data-retrieval.html#instance-metadata-limiting-access)。

如果您有一个使用较旧版本的不支持 IRSA 或 EKS Pod 身份的 AWS SDK 的应用程序，您应该更新 SDK 版本。

### 将 IRSA 角色的信任策略的范围缩小到服务账户名称、命名空间和集群

信任策略可以限定为命名空间或命名空间中的特定服务账户。使用 IRSA 时，最好尽可能明确地制定角色信任策略，包括服务账户名称。这将有效防止同一命名空间中的其他 Pod 承担该角色。CLI `eksctl` 在您使用它创建服务账户/IAM 角色时会自动执行此操作。有关更多信息，请参阅 [https://eksctl.io/usage/iamserviceaccounts/](https://eksctl.io/usage/iamserviceaccounts/)。

直接使用 IAM 时，这是在角色的信任策略中添加条件，使用条件来确保 `:sub` 声明是您期望的命名空间和服务账户。例如，在我们之前有一个 IRSA 令牌，其 sub 声明为 "system:serviceaccount:default:s3-read-only"。这是 `default` 命名空间，服务账户是 `s3-read-only`。您将使用如下条件来确保只有您在给定命名空间中的服务账户来自您的集群才能承担该角色：

```json
  "Condition": {
      "StringEquals": {
          "oidc.eks.us-west-2.amazonaws.com/id/D43CF17C27A865933144EA99A26FB128:aud": "sts.amazonaws.com",
          "oidc.eks.us-west-2.amazonaws.com/id/D43CF17C27A865933144EA99A26FB128:sub": "system:serviceaccount:default:s3-read-only"
      }
  }
```

### 为每个应用程序使用一个 IAM 角色

使用 IRSA 和 EKS Pod 身份时，最佳实践是为每个应用程序提供自己的 IAM 角色。这样可以提高隔离性，因为您可以修改一个应用程序而不影响另一个应用程序，并允许您应用最小特权原则，只为应用程序授予它所需的权限。

使用 EKS Pod 身份的 ABAC 时，您可以跨多个服务账户使用通用 IAM 角色，并依赖其会话属性进行访问控制。在大规模运营时，这尤其有用，因为 ABAC 允许您使用更少的 IAM 角色进行操作。

### 当您的应用程序需要访问 IMDS 时，请使用 IMDSv2 并将 EC2 实例的跃点限制增加到 2

[IMDSv2](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/configuring-instance-metadata-service.html) 要求您使用 PUT 请求来获取会话令牌。初始 PUT 请求必须包含会话令牌的 TTL。较新版本的 AWS SDK 将自动处理这一点以及该令牌的续订。还需要注意的是，EC2 实例上的默认跃点限制有意设置为 1，以防止 IP 转发。因此，在 EC2 实例上运行的请求会话令牌的 Pod 最终可能会超时并回退到使用 IMDSv1 数据流。EKS 通过_启用_v1 和 v2 并将节点上的跃点限制更改为 2 来添加对 IMDSv2 的支持，这些节点是由 eksctl 或使用官方 CloudFormation 模板供应的。

### 禁用自动挂载服务账户令牌

如果您的应用程序不需要调用 Kubernetes API，请在 PodSpec 中将 `automountServiceAccountToken` 属性设置为 `false`，或者修补每个命名空间中的默认服务账户，使其不再自动挂载到 pod。例如：

```bash
kubectl patch serviceaccount default -p $'automountServiceAccountToken: false'
```

### 为每个应用程序使用专用服务账户

每个应用程序都应该有自己专用的服务账户。这适用于 Kubernetes API 的服务账户以及 IRSA 和 EKS Pod 身份。

!!! attention
    如果您在集群升级时采用蓝/绿方法而不是执行就地集群升级，那么在使用 IRSA 时，您需要使用新集群的 OIDC 端点更新每个 IRSA IAM 角色的信任策略。蓝/绿集群升级是指在旧集群旁边创建一个运行较新版本 Kubernetes 的集群，然后使用负载均衡器或服务网格将服务从旧集群无缝切换到新集群。
    使用蓝/绿集群升级与 EKS Pod 身份时，您需要在新集群中创建 pod 身份关联，将 IAM 角色与服务账户关联。如果您有 `sourceArn` 条件，还需要更新 IAM 角色信任策略。

### 以非 root 用户身份运行应用程序

容器默认以 root 身份运行。虽然这允许它们读取 Web 身份令牌文件，但以 root 身份运行容器不被视为最佳实践。作为替代方案，请考虑在 PodSpec 中添加 `spec.securityContext.runAsUser` 属性。`runAsUser` 的值是任意值。

在以下示例中，Pod 中的所有进程都将以 `runAsUser` 字段中指定的用户 ID 运行。

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

当您以非 root 用户身份运行容器时，它会阻止容器读取 IRSA 服务账户令牌，因为该令牌默认被分配 0600 [root] 权限。如果您将容器的 securityContext 更新为包含 fsgroup=65534 [Nobody]，它将允许容器读取令牌。

```yaml
spec:
  securityContext:
    fsGroup: 65534
```

在 Kubernetes 1.19 及更高版本中，不再需要进行此更改，应用程序可以读取 IRSA 服务账户令牌而无需将它们添加到 Nobody 组。

### 为应用程序授予最小特权访问权限

[Action Hero](https://github.com/princespaghetti/actionhero) 是一个实用程序，您可以将其与您的应用程序一起运行，以识别您的应用程序正常运行所需的 AWS API 调用和相应的 IAM 权限。它类似于 [IAM Access Advisor](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_access-advisor.html)，可帮助您逐步限制分配给应用程序的 IAM 角色的范围。有关授予对 AWS 资源的[最小特权访问](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html#grant-least-privilege)的更多信息，请参阅文档。

考虑为 IRSA 和 Pod 身份使用的 IAM 角色设置[权限边界](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_boundaries.html)。您可以使用权限边界来确保 IRSA 或 Pod 身份使用的角色不能超过最大权限级别。有关开始使用权限边界以及示例权限边界策略的示例指南，请参阅此 [github 存储库](https://github.com/aws-samples/example-permissions-boundary)。

### 审查并撤销对您的 EKS 集群的不必要的匿名访问权限

理想情况下，应该为所有 API 操作禁用匿名访问。通过为 Kubernetes 内置用户 system：anonymous 创建 RoleBinding 或 ClusterRoleBinding 来授予匿名访问权限。您可以使用 [rbac-lookup](https://github.com/FairwindsOps/rbac-lookup) 工具来识别 system：anonymous 用户在您的集群上拥有的权限：

```bash
./rbac-lookup | grep -P 'system:(anonymous)|(unauthenticated)'
system:anonymous               cluster-wide        ClusterRole/system:discovery
system:unauthenticated         cluster-wide        ClusterRole/system:discovery
system:unauthenticated         cluster-wide        ClusterRole/system:public-info-viewer
```

除 system：public-info-viewer 之外，任何其他角色或集群角色都不应绑定到 system：anonymous 用户或 system：unauthenticated 组。

在某些特定情况下，为特定 API 启用匿名访问权限可能是合理的。如果这对您的集群来说是必需的，请确保只有那些特定 API 可以在不进行身份验证的情况下访问，并且不会使您的集群面临风险。

在 Kubernetes/EKS 版本 1.14 之前，system:unauthenticated 组默认与 system：discovery 和 system：basic-user ClusterRoles 关联。请注意，即使您已将集群更新到 1.14 或更高版本，这些权限可能仍然在您的集群上启用，因为集群更新不会撤销这些权限。
要检查除 system：public-info-viewer 之外哪些 ClusterRoles 具有 "system:unauthenticated"，您可以运行以下命令（需要 jq 实用程序）：

```bash
kubectl get ClusterRoleBinding -o json | jq -r '.items[] | select(.subjects[]?.name =="system:unauthenticated") | select(.metadata.name != "system:public-info-viewer") | .metadata.name'
```

并且可以使用以下命令从除 "system:public-info-viewer" 之外的所有角色中删除 "system:unauthenticated"：

```bash
kubectl get ClusterRoleBinding -o json | jq -r '.items[] | select(.subjects[]?.name =="system:unauthenticated") | select(.metadata.name != "system:public-info-viewer") | del(.subjects[] | select(.name =="system:unauthenticated"))' | kubectl apply -f -
```

或者，您可以使用 kubectl describe 和 kubectl edit 手动检查和删除。要检查 system：unauthenticated 组在您的集群上是否具有 system：discovery 权限，请运行以下命令：

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

要检查 system：unauthenticated 组在您的集群上是否具有 system：basic-user 权限，请运行以下命令：

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

如果 system：unauthenticated 组在您的集群上绑定到 system：discovery 和/或 system：basic-user ClusterRoles，您应该将这些角色与 system：unauthenticated 组解除关联。使用以下命令编辑 system：discovery ClusterRoleBinding：

```bash
kubectl edit clusterrolebindings system:discovery
```

上述命令将在编辑器中打开 system：discovery ClusterRoleBinding 的当前定义，如下所示：

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

从上面的编辑器屏幕中的 "subjects" 部分删除 system：unauthenticated 组的条目。

对于 system：basic-user ClusterRoleBinding 重复相同的步骤。

### 重用 IRSA 的 AWS SDK 会话

当您使用 IRSA 时，使用 AWS SDK 编写的应用程序会使用传递给您的 pod 的令牌调用 `sts:AssumeRoleWithWebIdentity` 来生成临时 AWS 凭证。这与其他 AWS 计算服务不同，在其他 AWS 计算服务中，计算服务直接向  AWS 计算资源（如 Lambda 函数）提供临时 AWS 凭证。这意味着每次初始化 AWS SDK 会话时，都会进行一次对 `AssumeRoleWithWebIdentity` 的调用。如果您的应用程序快速扩展并初始化了许多 AWS SDK 会话，您可能会遇到来自 AWS STS 的节流，因为您的代码将进行许多对 `AssumeRoleWithWebIdentity` 的调用。

为了避免这种情况，我们建议在您的应用程序中重用 AWS SDK 会话，以避免不必要的对 `AssumeRoleWithWebIdentity` 的调用。

在以下示例代码中，使用 boto3 python SDK 创建了一个会话，并使用同一个会话创建了用于与 Amazon S3 和 Amazon SQS 交互的客户端。`AssumeRoleWithWebIdentity` 只调用一次，AWS SDK 将在凭证过期时自动刷新 `my_session` 的凭证。

```py hl_lines="4 7 8"  
import boto3

# Create your own session
my_session = boto3.session.Session()

# Now we can create low-level clients from our session
sqs = my_session.client('sqs')
s3 = my_session.client('s3')

s3response = s3.list_buckets()
sqsresponse = sqs.list_queues()


#print the response from the S3 and SQS APIs
print("s3 response:")
print(s3response)
print("---")
print("sqs response:")
print(sqsresponse)
```

如果您正在将应用程序从其他 AWS 计算服务（如 EC2）迁移到使用 IRSA 的 EKS，这一点尤其重要。在其他计算服务上，初始化 AWS SDK 会话不会调用 AWS STS，除非您指示它这样做。

### 替代方法

虽然 IRSA 和 EKS Pod 身份是为 pod 分配 AWS 身份的_首选方式_，但它们需要您在应用程序中包含最新版本的 AWS SDK。有关当前支持 IRSA 的 SDK 的完整列表，请参阅 [https://docs.aws.amazon.com/eks/latest/userguide/iam-roles-for-service-accounts-minimum-sdk.html](https://docs.aws.amazon.com/eks/latest/userguide/iam-roles-for-service-accounts-minimum-sdk.html)，对于 EKS Pod 身份，请参阅 [https://docs.aws.amazon.com/eks/latest/userguide/pod-id-minimum-sdk.html](https://docs.aws.amazon.com/eks/latest/userguide/pod-id-minimum-sdk.html)。如果您有一个暂时无法使用兼容 SDK 更新的应用程序，社区提供了几种为 Kubernetes pod 分配 IAM 角色的解决方案，包括 [kube2iam](https://github.com/jtblin/kube2iam) 和 [kiam](https://github.com/uswitch/kiam)。虽然 AWS 不认可、支持或支持使用这些解决方案，但它们经常被广大社区用来实现与 IRSA 和 EKS Pod 身份类似的结果。

如果您需要使用这些非 AWS 提供的解决方案之一，请谨慎行事并确保您了解这样做的安全影响。

## 工具和资源

- [Amazon EKS 安全沉浸式研讨会 - 身份和访问管理](https://catalog.workshops.aws/eks-security-immersionday/en-US/2-identity-and-access-management)
- [Terraform EKS 蓝图模式 - 完全私有 Amazon EKS 集群](https://github.com/aws-ia/terraform-aws-eks-blueprints/tree/main/patterns/fully-private-cluster)
- [Terraform EKS 蓝图模式 - Amazon EKS 集群的 IAM Identity Center 单点登录](https://github.com/aws-ia/terraform-aws-eks-blueprints/tree/main/patterns/sso-iam-identity-center)
- [Terraform EKS 蓝图模式 - Amazon EKS 集群的 Okta 单点登录](https://github.com/aws-ia/terraform-aws-eks-blueprints/tree/main/patterns/sso-okta)
- [audit2rbac](https://github.com/liggitt/audit2rbac)
- [rbac.dev](https://github.com/mhausenblas/rbac.dev) Kubernetes RBAC 的其他资源列表，包括博客和工具
- [Action Hero](https://github.com/princespaghetti/actionhero)
- [kube2iam](https://github.com/jtblin/kube2iam)
- [kiam](https://github.com/uswitch/kiam)