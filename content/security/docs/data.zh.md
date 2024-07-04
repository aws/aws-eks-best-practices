# 数据加密和密钥管理

## 静态加密

您可以在 Kubernetes 中使用三种不同的 AWS 原生存储选项：[EBS](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/AmazonEBS.html)、[EFS](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/AmazonEFS.html) 和 [FSx for Lustre](https://docs.aws.amazon.com/fsx/latest/LustreGuide/what-is.html)。所有三种选项都提供使用服务管理密钥或客户主密钥 (CMK) 的静态加密。对于 EBS，您可以使用内置存储驱动程序或 [EBS CSI 驱动程序](https://github.com/kubernetes-sigs/aws-ebs-csi-driver)。两者都包含用于加密卷和提供 CMK 的参数。对于 EFS，您可以使用 [EFS CSI 驱动程序](https://github.com/kubernetes-sigs/aws-efs-csi-driver)，但与 EBS 不同，EFS CSI 驱动程序不支持动态配置。如果您想在 EKS 中使用 EFS，您需要在创建 PV 之前预先配置文件系统的静态加密。有关 EFS 文件加密的更多信息，请参阅 [加密静态数据](https://docs.aws.amazon.com/efs/latest/ug/encryption-at-rest.html)。除了提供静态加密外，EFS 和 FSx for Lustre 还包括加密传输中数据的选项。FSx for Luster 默认执行此操作。对于 EFS，您可以通过在 PV 的 `mountOptions` 中添加 `tls` 参数来启用传输加密，如下例所示：

```yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: efs-pv
spec:
  capacity:
    storage: 5Gi
  volumeMode: Filesystem
  accessModes:
    - ReadWriteOnce
  persistentVolumeReclaimPolicy: Retain
  storageClassName: efs-sc
  mountOptions:
    - tls
  csi:
    driver: efs.csi.aws.com
    volumeHandle: <file_system_id>
```

[FSx CSI 驱动程序](https://github.com/kubernetes-sigs/aws-fsx-csi-driver)支持动态配置 Lustre 文件系统。它默认使用服务管理密钥加密数据，但也可以选择提供您自己的 CMK，如下例所示：

```yaml
kind: StorageClass
apiVersion: storage.k8s.io/v1
metadata:
  name: fsx-sc
provisioner: fsx.csi.aws.com
parameters:
  subnetId: subnet-056da83524edbe641
  securityGroupIds: sg-086f61ea73388fb6b
  deploymentType: PERSISTENT_1
  kmsKeyId: <kms_arn>
```

!!! attention
    截至 2020 年 5 月 28 日，所有写入 EKS Fargate pod 临时卷的数据都默认使用行业标准 AES-256 加密算法进行加密。您无需对应用程序进行任何修改，因为加密和解密由服务无缝处理。

### 加密静态数据

加密静态数据被认为是最佳实践。如果您不确定是否需要加密，请加密您的数据。

### 定期轮换您的 CMK

配置 KMS 自动轮换您的 CMK。这将每年轮换一次您的密钥，同时无限期保留旧密钥，以便您的数据仍可解密。有关更多信息，请参阅 [轮换客户主密钥](https://docs.aws.amazon.com/kms/latest/developerguide/rotate-keys.html)

### 使用 EFS 访问点来简化对共享数据集的访问

如果您有具有不同 POSIX 文件权限的共享数据集或想通过创建不同的挂载点来限制对共享文件系统的部分访问，请考虑使用 EFS 访问点。要了解有关使用访问点的更多信息，请参阅 [https://docs.aws.amazon.com/efs/latest/ug/efs-access-points.html](https://docs.aws.amazon.com/efs/latest/ug/efs-access-points.html)。如今，如果您想使用访问点 (AP)，您需要在 PV 的 `volumeHandle` 参数中引用该 AP。

!!! attention
    截至 2021 年 3 月 23 日，EFS CSI 驱动程序支持动态配置 EFS 访问点。访问点是进入 EFS 文件系统的应用程序特定入口点，可以更轻松地在多个 pod 之间共享文件系统。每个 EFS 文件系统最多可以有 120 个 PV。有关更多信息，请参阅 [介绍 Amazon EFS CSI 动态配置](https://aws.amazon.com/blogs/containers/introducing-efs-csi-dynamic-provisioning/)。

## 密钥管理

Kubernetes 密钥用于存储敏感信息，如用户证书、密码或 API 密钥。它们以 base64 编码的字符串形式持久化存储在 etcd 中。在 EKS 上，etcd 节点的 EBS 卷使用 [EBS 加密](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/EBSEncryption.html)进行加密。Pod 可以通过在 `podSpec` 中引用密钥来检索 Kubernetes 密钥对象。这些密钥可以映射为环境变量或挂载为卷。有关创建密钥的更多信息，请参阅 [https://kubernetes.io/docs/concepts/configuration/secret/](https://kubernetes.io/docs/concepts/configuration/secret/)。

!!! caution
    特定命名空间中的所有 pod 都可以引用该命名空间中的密钥。

!!! caution
    节点授权器允许 Kubelet 读取挂载到节点的所有密钥。

### 使用 AWS KMS 对 Kubernetes 密钥进行信封加密

这允许您使用唯一的数据加密密钥 (DEK) 加密您的密钥。然后，DEK 使用来自 AWS KMS 的密钥加密密钥 (KEK) 进行加密，KEK 可以按照定期计划自动轮换。使用 Kubernetes 的 KMS 插件，所有 Kubernetes 密钥都以密文形式存储在 etcd 中，而不是明文，并且只能由 Kubernetes API 服务器解密。
有关更多详细信息，请参阅 [使用 EKS 加密提供程序支持实现深度防御](https://aws.amazon.com/blogs/containers/using-eks-encryption-provider-support-for-defense-in-depth/)

### 审计 Kubernetes 密钥的使用情况

在 EKS 上，启用审计日志记录并创建 CloudWatch 指标过滤器和警报，以在使用密钥时向您发出警报（可选）。以下是 Kubernetes 审计日志的指标过滤器示例：`{($.verb="get") && ($.objectRef.resource="secret")}`。您还可以使用以下查询与 CloudWatch Log Insights 一起使用：

```bash
fields @timestamp, @message
| sort @timestamp desc
| limit 100
| stats count(*) by objectRef.name as secret
| filter verb="get" and objectRef.resource="secrets"
```

上述查询将显示在特定时间范围内访问密钥的次数。

```bash
fields @timestamp, @message
| sort @timestamp desc
| limit 100
| filter verb="get" and objectRef.resource="secrets"
| display objectRef.namespace, objectRef.name, user.username, responseStatus.code
```

此查询将显示密钥以及尝试访问密钥的用户的命名空间、用户名和响应代码。

### 定期轮换您的密钥

Kubernetes 不会自动轮换密钥。如果您必须轮换密钥，请考虑使用外部密钥存储，例如 Vault 或 AWS Secrets Manager。

### 使用单独的命名空间作为隔离不同应用程序密钥的方式

如果您有不能在命名空间之间共享的密钥，请为这些应用程序创建单独的命名空间。

### 使用卷挂载而不是环境变量

环境变量的值可能会无意中出现在日志中。挂载为卷的密钥会实例化为 tmpfs 卷（基于 RAM 的文件系统），当 pod 被删除时，这些卷会自动从节点中删除。

### 使用外部密钥提供程序

有几种可行的替代方案可以代替使用 Kubernetes 密钥，包括 [AWS Secrets Manager](https://aws.amazon.com/secrets-manager/) 和 Hashicorp 的 [Vault](https://www.hashicorp.com/blog/injecting-vault-secrets-into-kubernetes-pods-via-a-sidecar/)。这些服务提供了 Kubernetes 密钥所没有的功能，如细粒度访问控制、强加密和自动轮换密钥。Bitnami 的 [Sealed Secrets](https://github.com/bitnami-labs/sealed-secrets) 是另一种方法，它使用非对称加密来创建"密封的密钥"。公钥用于加密密钥，而用于解密密钥的私钥则保存在集群内部，允许您安全地将密封的密钥存储在 Git 等源代码控制系统中。有关更多信息，请参阅 [使用 Sealed Secrets 在 Kubernetes 中管理密钥部署](https://aws.amazon.com/blogs/opensource/managing-secrets-deployment-in-kubernetes-using-sealed-secrets/)。

随着对外部密钥存储的使用不断增加，将它们与 Kubernetes 集成的需求也随之增长。[Secret Store CSI 驱动程序](https://github.com/kubernetes-sigs/secrets-store-csi-driver)是一个社区项目，它使用 CSI 驱动程序模型从外部密钥存储中获取密钥。目前，该驱动程序支持 [AWS Secrets Manager](https://github.com/aws/secrets-store-csi-driver-provider-aws)、Azure、Vault 和 GCP。AWS 提供程序同时支持 AWS Secrets Manager **和** AWS Parameter Store。它还可以配置为在密钥过期时轮换密钥，并可以将 AWS Secrets Manager 密钥同步到 Kubernetes 密钥。当您需要将密钥作为环境变量进行引用而不是从卷中读取时，密钥同步可能很有用。

!!! note
    当密钥存储 CSI 驱动程序需要获取密钥时，它会假定引用密钥的 pod 分配的 IRSA 角色。此操作的代码可在 [此处](https://github.com/aws/secrets-store-csi-driver-provider-aws/blob/main/auth/auth.go) 找到。

有关 AWS Secrets & Configuration Provider (ASCP) 的更多信息，请参阅以下资源：

- [如何将 AWS Secrets Configuration Provider 与 Kubernetes Secret Store CSI 驱动程序一起使用](https://aws.amazon.com/blogs/security/how-to-use-aws-secrets-configuration-provider-with-kubernetes-secrets-store-csi-driver/)
- [将 Secrets Manager 密钥与 Kubernetes Secrets Store CSI 驱动程序集成](https://docs.aws.amazon.com/secretsmanager/latest/userguide/integrating_csi_driver.html)

[external-secrets](https://github.com/external-secrets/external-secrets) 是另一种在 Kubernetes 中使用外部密钥存储的方式。与 CSI 驱动程序一样，external-secrets 也可以与各种不同的后端一起使用，包括 AWS Secrets Manager。不同之处在于，external-secrets 不是从外部密钥存储中检索密钥，而是将密钥从这些后端复制到 Kubernetes 作为密钥。这让您可以使用首选的密钥存储来管理密钥，并以 Kubernetes 原生的方式与密钥交互。

## 工具和资源

- [Amazon EKS 安全沉浸式研讨会 - 数据加密和密钥管理](https://catalog.workshops.aws/eks-security-immersionday/en-US/13-data-encryption-and-secret-management)