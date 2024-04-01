# 集群升级的最佳实践

本指南向集群管理员展示如何规划和执行Amazon EKS升级策略。它还描述了如何升级自管理节点、托管节点组、Karpenter节点和Fargate节点。它不包括有关EKS Anywhere、自管理Kubernetes、AWS Outposts或AWS Local Zones的指导。

## 概述

Kubernetes版本包括控制平面和数据平面。为确保顺利运行，控制平面和数据平面应运行相同的[Kubernetes小版本，如1.24](https://kubernetes.io/releases/version-skew-policy/#supported-versions)。虽然AWS管理和升级控制平面，但更新数据平面中的工作节点是您的责任。

* **控制平面** - 控制平面的版本由Kubernetes API服务器确定。在Amazon EKS集群中，AWS负责管理此组件。可以通过AWS API启动控制平面升级。
* **数据平面** - 数据平面版本与运行在您各个节点上的Kubelet版本相关联。同一集群中的节点可能运行不同的版本。您可以通过运行`kubectl get nodes`来检查所有节点的版本。

## 升级前

如果您计划在Amazon EKS中升级Kubernetes版本，在开始升级之前，有一些重要的政策、工具和程序需要您落实。

* **了解弃用政策** - 深入了解[Kubernetes弃用政策](https://kubernetes.io/docs/reference/using-api/deprecation-policy/)的工作方式。注意任何可能影响您现有应用程序的即将发生的变化。Kubernetes的新版本通常会逐步淘汰某些API和功能，可能会导致正在运行的应用程序出现问题。
* **查看Kubernetes变更日志** - 彻底查看[Kubernetes变更日志](https://github.com/kubernetes/kubernetes/tree/master/CHANGELOG)以及[Amazon EKS Kubernetes版本](https://docs.aws.amazon.com/eks/latest/userguide/kubernetes-versions.html),了解可能对您的集群产生影响的任何内容，例如可能影响您的工作负载的重大变更。
* **评估集群插件的兼容性** - 当新版本发布或在您将集群升级到新的Kubernetes小版本后，Amazon EKS不会自动更新插件。查看[更新插件](https://docs.aws.amazon.com/eks/latest/userguide/managing-add-ons.html#updating-an-add-on),了解任何现有集群插件与您打算升级到的集群版本的兼容性。
* **启用控制平面日志记录** - 启用[控制平面日志记录](https://docs.aws.amazon.com/eks/latest/userguide/control-plane-logs.html),以捕获升级过程中可能出现的日志、错误或问题。考虑查看这些日志以检查任何异常情况。在非生产环境中测试集群升级，或将自动化测试集成到您的持续集成工作流中，以评估版本与您的应用程序、控制器和自定义集成的兼容性。
* **探索eksctl进行集群管理** - 考虑使用[eksctl](https://eksctl.io/)来管理您的EKS集群。它为您提供了[更新控制平面、管理插件和处理工作节点更新](https://eksctl.io/usage/cluster-upgrade/)的能力。
* **选择托管节点组或EKS on Fargate** - 通过使用[EKS托管节点组](https://docs.aws.amazon.com/eks/latest/userguide/managed-node-groups.html)或[EKS on Fargate](https://docs.aws.amazon.com/eks/latest/userguide/fargate.html),可以简化和自动化工作节点升级。这些选项可以简化该过程并减少手动干预。
* **利用kubectl Convert插件** - 利用[kubectl convert插件](https://kubernetes.io/docs/tasks/tools/install-kubectl-linux/#install-kubectl-convert-plugin)来促进[Kubernetes清单文件](https://kubernetes.io/docs/tasks/tools/included/kubectl-convert-overview/)在不同API版本之间的转换。这可以帮助确保您的配置与新的Kubernetes版本保持兼容。

## 保持集群的最新状态

保持与Kubernetes更新同步对于安全高效的EKS环境至关重要，这反映了Amazon EKS中的共享责任模型。通过将这些策略集成到您的操作工作流中，您就可以保持最新、安全的集群，充分利用最新的功能和改进。策略：

* **支持版本政策** - 与Kubernetes社区保持一致，Amazon EKS通常提供三个活跃的Kubernetes版本，同时每年弃用第四个版本。在版本到达其支持终止日期前至少60天，将发出弃用通知。有关更多详细信息，请参阅[EKS版本常见问题解答](https://aws.amazon.com/eks/eks-version-faq/)。
* **自动升级政策** - 我们强烈建议您在EKS集群中与Kubernetes更新保持同步。Kubernetes社区支持(包括错误修复和安全补丁)通常会在一年后停止支持旧版本。弃用的版本可能也缺乏漏洞报告，存在潜在风险。如果未主动在版本生命周期结束前进行升级，将会触发自动升级，这可能会中断您的工作负载和系统。有关更多信息，请参阅[EKS版本支持政策](https://aws.amazon.com/eks/eks-version-support-policy/)。
* **创建升级运行手册** - 建立管理升级的明确流程。作为主动方法的一部分，制定适合您升级流程的运行手册和专门工具。这不仅增强了您的准备工作，而且还简化了复杂的过渡。将至少每年升级一次集群作为标准做法。这种做法使您与不断发展的技术保持一致，从而提高了环境的效率和安全性。

## 查看EKS发布日历

[查看EKS Kubernetes发布日历](https://docs.aws.amazon.com/eks/latest/userguide/kubernetes-versions.html#kubernetes-release-calendar),了解新版本的发布时间以及特定版本的支持终止时间。通常，EKS每年发布三个Kubernetes小版本，每个小版本的支持期约为14个月。

此外，请查看上游[Kubernetes发布信息](https://kubernetes.io/releases/)。

## 了解共享责任模型如何应用于集群升级

您负责启动对控制平面和数据平面的升级。[了解如何启动升级。](https://docs.aws.amazon.com/eks/latest/userguide/update-cluster.html)当您启动集群升级时，AWS负责升级集群控制平面。您负责升级数据平面，包括Fargate pods和[其他插件。](#upgrade-add-ons-and-components-using-the-kubernetes-api)您必须验证和规划在集群上运行的工作负载的升级，以确保在集群升级后它们的可用性和操作不会受到影响。

## 就地升级集群

EKS支持就地集群升级策略。这可以保留集群资源，并保持集群配置的一致性(例如，API端点、OIDC、ENI、负载均衡器)。这对集群用户的干扰较小，并且它将使用集群中现有的工作负载和资源，而无需您重新部署工作负载或迁移外部资源(例如DNS、存储)。

在执行就地集群升级时，请注意一次只能执行一个小版本升级(例如，从1.24升级到1.25)。

这意味着如果您需要更新多个版本，则需要进行一系列连续升级。规划连续升级更加复杂，并且存在更高的停机风险。在这种情况下，[评估蓝/绿集群升级策略。](#evaluate-bluegreen-clusters-as-an-alternative-to-in-place-cluster-upgrades)

## 按顺序升级控制平面和数据平面

要升级集群，您需要执行以下操作：

1. [查看Kubernetes和EKS发行说明。](#use-the-eks-documentation-to-create-an-upgrade-checklist)
2. [备份集群。(可选)](#backup-the-cluster-before-upgrading)
3. [识别并修复工作负载中已弃用和已删除的API使用情况。](#identify-and-remediate-removed-api-usage-before-upgrading-the-control-plane)
4. [确保使用的托管节点组(如果有)与控制平面运行相同的Kubernetes版本。](#track-the-version-skew-of-nodes-ensure-managed-node-groups-are-on-the-same-version-as-the-control-plane-before-upgrading)EKS托管节点组和由EKS Fargate配置文件创建的节点仅支持控制平面和数据平面之间的1个小版本偏差。
5. [使用AWS控制台或cli升级集群控制平面。](https://docs.aws.amazon.com/eks/latest/userguide/update-cluster.html)
6. [查看插件兼容性。](#upgrade-add-ons-and-components-using-the-kubernetes-api)根据需要升级您的Kubernetes插件和自定义控制器。
7. [更新kubectl。](https://docs.aws.amazon.com/eks/latest/userguide/install-kubectl.html)
8. [升级集群数据平面。](https://docs.aws.amazon.com/eks/latest/userguide/update-managed-node-group.html)将您的节点升级到与升级后的集群相同的Kubernetes小版本。

## 使用EKS文档创建升级清单

EKS Kubernetes[版本文档](https://docs.aws.amazon.com/eks/latest/userguide/kubernetes-versions.html)包括每个版本的详细更改列表。为每次升级构建清单。

对于特定的EKS版本升级指南，请查看每个版本的文档，了解值得注意的变更和注意事项。

* [EKS 1.27](https://docs.aws.amazon.com/eks/latest/userguide/kubernetes-versions.html#kubernetes-1.27)
* [EKS 1.26](https://docs.aws.amazon.com/eks/latest/userguide/kubernetes-versions.html#kubernetes-1.26)
* [EKS 1.25](https://docs.aws.amazon.com/eks/latest/userguide/kubernetes-versions.html#kubernetes-1.25)
* [EKS 1.24](https://docs.aws.amazon.com/eks/latest/userguide/kubernetes-versions.html#kubernetes-1.24)
* [EKS 1.23](https://docs.aws.amazon.com/eks/latest/userguide/kubernetes-versions.html#kubernetes-1.23)
* [EKS 1.22](https://docs.aws.amazon.com/eks/latest/userguide/kubernetes-versions.html#kubernetes-1.22)

## 使用Kubernetes API升级插件和组件

在升级集群之前，您应该了解您正在使用的Kubernetes组件版本。列出集群组件，并识别直接使用Kubernetes API的组件。这包括关键集群组件，如监控和日志记录代理、集群自动扩缩器、容器存储驱动程序(例如[EBS CSI](https://docs.aws.amazon.com/eks/latest/userguide/ebs-csi.html)、[EFS CSI](https://docs.aws.amazon.com/eks/latest/userguide/efs-csi.html))、Ingress控制器以及任何其他直接依赖Kubernetes API的工作负载或插件。

!!! 提示
    关键集群组件通常安装在`*-system`命名空间中
    
    ```
    kubectl get ns | grep '-system'
    ```

一旦识别出依赖Kubernetes API的组件，请查看其文档以了解版本兼容性和升级要求。例如，请参阅[AWS Load Balancer Controller](https://kubernetes-sigs.github.io/aws-load-balancer-controller/v2.4/deploy/installation/)文档以了解版本兼容性。在继续集群升级之前，可能需要升级或更改某些组件的配置。需要检查的一些关键组件包括[CoreDNS](https://github.com/coredns/coredns)、[kube-proxy](https://kubernetes.io/docs/concepts/overview/components/#kube-proxy)、[VPC CNI](https://github.com/aws/amazon-vpc-cni-k8s)和存储驱动程序。

集群通常包含许多使用Kubernetes API的工作负载，这些工作负载对于工作负载功能(如Ingress控制器、持续交付系统和监控工具)是必需的。当您升级EKS集群时，您还必须升级您的插件和第三方工具，以确保它们与新版本兼容。

以下是一些常见插件及其相关升级文档的示例：

* **Amazon VPC CNI:** 有关每个集群版本推荐的Amazon VPC CNI插件版本，请参阅[更新Kubernetes自管理插件的Amazon VPC CNI插件](https://docs.aws.amazon.com/eks/latest/userguide/managing-vpc-cni.html)。**当作为Amazon EKS插件安装时，它只能一次升级一个小版本。**
* **kube-proxy:** 请参阅[更新Kubernetes kube-proxy自管理插件](https://docs.aws.amazon.com/eks/latest/userguide/managing-kube-proxy.html)。
* **CoreDNS:** 请参阅[更新CoreDNS自管理插件](https://docs.aws.amazon.com/eks/latest/userguide/managing-coredns.html)。
* **AWS Load Balancer Controller:** AWS Load Balancer Controller需要与您部署的EKS版本兼容。有关更多信息，请参阅[安装指南](https://docs.aws.amazon.com/eks/latest/userguide/aws-load-balancer-controller.html)。
* **Amazon Elastic Block Store (Amazon EBS) Container Storage Interface (CSI) 驱动程序：** 有关安装和升级信息，请参阅[作为Amazon EKS插件管理Amazon EBS CSI驱动程序](https://docs.aws.amazon.com/eks/latest/userguide/managing-ebs-csi.html)。
* **Amazon Elastic File System (Amazon EFS) Container Storage Interface (CSI) 驱动程序：** 有关安装和升级信息，请参阅[Amazon EFS CSI驱动程序](https://docs.aws.amazon.com/eks/latest/userguide/efs-csi.html)。
* **Kubernetes Metrics Server:** 有关更多信息，请参阅GitHub上的[metrics-server](https://kubernetes-sigs.github.io/metrics-server/)。
* **Kubernetes Cluster Autoscaler:** 要升级Kubernetes Cluster Autoscaler的版本，请在部署中更改镜像的版本。Cluster Autoscaler与Kubernetes调度程序紧密耦合。您需要在升级集群时始终升级它。查看[GitHub发行版](https://github.com/kubernetes/autoscaler/releases),找到与您的Kubernetes小版本对应的最新发行版地址。
* **Karpenter:** 有关安装和升级信息，请参阅[Karpenter文档。](https://karpenter.sh/docs/upgrading/)

## 在升级前验证基本的EKS要求

AWS要求您的账户中具有某些资源，以完成升级过程。如果这些资源不存在，则无法升级集群。控制平面升级需要以下资源：

1. 可用IP地址：Amazon EKS需要您在创建集群时指定的子网中最多5个可用IP地址，以便更新集群。如果没有，请在执行版本更新之前更新集群配置以包含新的集群子网。
2. EKS IAM角色：控制平面IAM角色仍存在于账户中，并具有必要的权限。
3. 如果您的集群启用了密钥加密，请确保集群IAM角色具有使用AWS Key Management Service (AWS KMS)密钥的权限。

### 验证可用IP地址

要更新集群，Amazon EKS需要您在创建集群时指定的子网中最多5个可用IP地址。

要验证您的子网是否有足够的IP地址来升级集群，您可以运行以下命令：

```
CLUSTER=<cluster name>
aws ec2 describe-subnets --subnet-ids \
  $(aws eks describe-cluster --name ${CLUSTER} \
  --query 'cluster.resourcesVpcConfig.subnetIds' \
  --output text) \
  --query 'Subnets[*].[SubnetId,AvailabilityZone,AvailableIpAddressCount]' \
  --output table

----------------------------------------------------
|                  DescribeSubnets                 |
+---------------------------+--------------+-------+
|  subnet-067fa8ee8476abbd6 |  us-east-1a  |  8184 |
|  subnet-0056f7403b17d2b43 |  us-east-1b  |  8153 |
|  subnet-09586f8fb3addbc8c |  us-east-1a  |  8120 |
|  subnet-047f3d276a22c6bce |  us-east-1b  |  8184 |
+---------------------------+--------------+-------+
```

[VPC CNI Metrics Helper](https://github.com/aws/amazon-vpc-cni-k8s/blob/master/cmd/cni-metrics-helper/README.md)可用于为VPC指标创建CloudWatch仪表板。
如果您在最初创建集群时指定的子网中的IP地址用尽，Amazon EKS建议在开始Kubernetes版本升级之前使用"UpdateClusterConfiguration"API更新集群子网。请验证您将提供的新子网：

* 属于集群创建期间选择的相同一组可用区。
* 属于集群创建期间提供的相同VPC

请考虑将额外的CIDR块与现有的集群VPC关联，从而有效扩展您的IP地址池。AWS允许将额外的CIDR块与现有集群VPC关联。这可以通过引入额外的私有IP范围(RFC 1918)或(如果必要)公共IP范围(非RFC 1918)来实现。您必须添加新的VPC CIDR块并允许VPC刷新完成，然后Amazon EKS才能使用新的CIDR。之后，您可以根据新设置的CIDR块更新子网。


### 验证EKS IAM角色

要验证IAM角色在您的账户中可用并具有正确的assume role策略，您可以运行以下命令：

```
CLUSTER=<cluster name>
ROLE_ARN=$(aws eks describe-cluster --name ${CLUSTER} \
  --query 'cluster.roleArn' --output text)
aws iam get-role --role-name ${ROLE_ARN##*/} \
  --query 'Role.AssumeRolePolicyDocument'
  
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "eks.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }
    ]
}
```

## 迁移到EKS插件

Amazon EKS会为每个集群自动安装插件，如Amazon VPC CNI插件for Kubernetes、`kube-proxy`和CoreDNS。插件可以是自管理的，也可以作为Amazon EKS插件安装。Amazon EKS插件是使用EKS API管理插件的另一种方式。

您可以使用Amazon EKS插件通过单个命令更新版本。例如：

```
aws eks update-addon —cluster-name my-cluster —addon-name vpc-cni —addon-version version-number \
--service-account-role-arn arn:aws:iam::111122223333:role/role-name —configuration-values '{}' —resolve-conflicts PRESERVE
```

使用以下命令检查是否有任何EKS插件：

```
aws eks list-addons --cluster-name <cluster name>
```

!!! 警告
      
    在控制平面升级期间，EKS插件不会自动升级。您必须启动EKS插件更新，并选择所需的版本。

    * 您负责从所有可用版本中选择兼容版本。[查看有关插件版本兼容性的指导。](#upgrade-add-ons-and-components-using-the-kubernetes-api)
    * Amazon EKS插件只能一次升级一个小版本。

[了解有关哪些组件可作为EKS插件以及如何入门的更多信息。](https://docs.aws.amazon.com/eks/latest/userguide/eks-add-ons.html)

[了解如何为EKS插件提供自定义配置。](https://aws.amazon.com/blogs/containers/amazon-eks-add-ons-advanced-configuration/)

## 在升级控制平面之前识别并修复已删除的API使用情况

在升级EKS控制平面之前，您应该识别已删除API的使用情况。为此，我们建议使用可以检查正在运行的集群或静态渲染的Kubernetes清单文件的工具。

对静态清单文件进行扫描通常更加准确。如果针对实时集群运行，这些工具可能会返回误报。

Kubernetes弃用的API并不意味着该API已被删除。您应该查看[Kubernetes弃用政策](https://kubernetes.io/docs/reference/using-api/deprecation-policy/)以了解API删除对您的工作负载的影响。

### Cluster Insights
[Cluster Insights](https://docs.aws.amazon.com/eks/latest/userguide/cluster-insights.html)是一项功能，可提供有关可能影响升级EKS集群到更新版本的Kubernetes的问题的发现。这些发现由Amazon EKS策划和管理，并提供了如何修复它们的建议。通过利用Cluster Insights，您可以最小化升级到更新的Kubernetes版本所需的工作量。

要查看EKS集群的见解，您可以运行以下命令：
```
aws eks list-insights --region <region-code> --cluster-name <my-cluster>

{
    "insights": [
        {
            "category": "UPGRADE_READINESS", 
            "name": "Deprecated APIs removed in Kubernetes v1.29", 
            "insightStatus": {
                "status": "PASSING", 
                "reason": "No deprecated API usage detected within the last 30 days."
            }, 
            "kubernetesVersion": "1.29", 
            "lastTransitionTime": 1698774710.0, 
            "lastRefreshTime": 1700157422.0, 
            "id": "123e4567-e89b-42d3-a456-579642341238", 
            "description": "Checks for usage of deprecated APIs that are scheduled for removal in Kubernetes v1.29. Upgrading your cluster before migrating to the updated APIs supported by v1.29 could cause application impact."
        }
    ]
}
```

要获取收到的见解的更多描述性输出，您可以运行以下命令：
```
aws eks describe-insight --region <region-code> --id <insight-id> --cluster-name <my-cluster>
```

您也可以在[Amazon EKS控制台](https://console.aws.amazon.com/eks/home#/clusters)中查看见解。从集群列表中选择您的集群后，见解发现位于```Upgrade Insights```选项卡下。

如果您发现集群见解的`"status": ERROR`,则必须在执行集群升级之前解决该问题。运行`aws eks describe-insight`命令，它将分享以下修复建议：

受影响的资源：
```
"resources": [
      {
        "insightStatus": {
          "status": "ERROR"
        },
        "kubernetesResourceUri": "/apis/policy/v1beta1/podsecuritypolicies/null"
      }
]
```

已弃用的API：
```
"deprecationDetails": [
      {
        "usage": "/apis/flowcontrol.apiserver.k8s.io/v1beta2/flowschemas", 
        "replacedWith": "/apis/flowcontrol.apiserver.k8s.io/v1beta3/flowschemas", 
        "stopServingVersion": "1.29", 
        "clientStats": [], 
        "startServingReplacementVersion": "1.26"
      }
]
```

建议采取的行动：
```
"recommendation": "Update manifests and API clients to use newer Kubernetes APIs if applicable before upgrading to Kubernetes v1.26."
```

利用EKS控制台或CLI中的集群见解可加快成功升级EKS集群版本的过程。了解更多信息的资源：
* [官方EKS文档](https://docs.aws.amazon.com/eks/latest/userguide/cluster-insights.html)
* [Cluster Insights发布博客](https://aws.amazon.com/blogs/containers/accelerate-the-testing-and-verification-of-amazon-eks-upgrades-with-upgrade-insights/)。

### Kube-no-trouble

[Kube-no-trouble](https://github.com/doitintl/kube-no-trouble)是一个开源命令行实用程序，带有命令`kubent`。当您在没有任何参数的情况下运行`kubent`时，它将使用您当前的KubeConfig上下文并扫描集群，并打印出哪些API将被弃用和删除的报告。

```
kubent

4:17PM INF >>> Kube No Trouble `kubent` <<<
4:17PM INF version 0.7.0 (git sha d1bb4e5fd6550b533b2013671aa8419d923ee042)
4:17PM INF Initializing collectors and retrieving data
4:17PM INF Target K8s version is 1.24.8-eks-ffeb93d
4:l INF Retrieved 93 resources from collector name=Cluster
4:17PM INF Retrieved 16 resources from collector name="Helm v3"
4:17PM INF Loaded ruleset name=custom.rego.tmpl
4:17PM INF Loaded ruleset name=deprecated-1-16.rego
4:17PM INF Loaded ruleset name=deprecated-1-22.rego
4:17PM INF Loaded ruleset name=deprecated-1-25.rego
4:17PM INF Loaded ruleset name=deprecated-1-26.rego
4:17PM INF Loaded ruleset name=deprecated-future.rego
__________________________________________________________________________________________
>>> Deprecated APIs removed in 1.25 <<<
------------------------------------------------------------------------------------------
KIND                NAMESPACE     NAME             API_VERSION      REPLACE_WITH (SINCE)
PodSecurityPolicy   <undefined>   eks.privileged   policy/v1beta1   <removed> (1.21.0)
```

它还可用于扫描静态清单文件和Helm包。建议将`kubent`作为持续集成(CI)过程的一部分运行，以在部署清单之前识别问题。扫描清单也比扫描实时集群更加准确。

Kube-no-trouble提供了一个示例[服务账户和角色](https://github.com/doitintl/kube-no-trouble/blob/master/docs/k8s-sa-and-role-example.yaml),具有扫描集群的适当权限。

### Pluto

另一个选择是[pluto](https://pluto.docs.fairwinds.com/),它类似于`kubent`,因为它支持扫描实时集群、清单文件、Helm图表，并且您可以在CI过程中包含GitHub Action。

```
pluto detect-all-in-cluster

NAME             KIND                VERSION          REPLACEMENT   REMOVED   DEPRECATED   REPL AVAIL  
eks.privileged   PodSecurityPolicy   policy/v1beta1                 false     true         true
```

### 资源

要在升级EKS控制平面之前验证您的集群不使用已弃用的API，您应该监控：

* 自Kubernetes v1.19起的指标`apiserver_requested_deprecated_apis`:

```
kubectl get --raw /metrics | grep apiserver_requested_deprecated_apis

apiserver_requested_deprecated_apis{group="policy",removed_release="1.25",resource="podsecuritypolicies",subresource="",version="v1beta1"} 1
```

* [审计日志](https://docs.aws.amazon.com/eks/latest/userguide/control-plane-logs.html)中`k8s.io/deprecated`设置为`true`的事件：

```
CLUSTER="<cluster_name>"
QUERY_ID=$(aws logs start-query \
 --log-group-name /aws/eks/${CLUSTER}/cluster \
 --start-time $(date -u --date="-30 minutes" "+%s") # or date -v-30M "+%s" on MacOS \
 --end-time $(date "+%s") \
 --query-string 'fields @message | filter `annotations.k8s.io/deprecated`="true"' \
 --query queryId --output text)

echo "Query started (query id: $QUERY_ID), please hold ..." && sleep 5 # give it some time to query

aws logs get-query-results --query-id $QUERY_ID
```

如果使用了已弃用的API，将输出以下行：

```
{
    "results": [
        [
            {
                "field": "@message",
                "value": "{\"kind\":\"Event\",\"apiVersion\":\"audit.k8s.io/v1\",\"level\":\"Request\",\"auditID\":\"8f7883c6-b3d5-42d7-967a-1121c6f22f01\",\"stage\":\"ResponseComplete\",\"requestURI\":\"/apis/policy/v1beta1/podsecuritypolicies?allowWatchBookmarks=true\\u0026resourceVersion=4131\\u0026timeout=9m19s\\u0026timeoutSeconds=559\\u0026watch=true\",\"verb\":\"watch\",\"user\":{\"username\":\"system:apiserver\",\"uid\":\"8aabfade-da52-47da-83b4-46b16cab30fa\",\"groups\":[\"system:masters\"]},\"sourceIPs\":[\"::1\"],\"userAgent\":\"kube-apiserver/v1.24.16 (linux/amd64) kubernetes/af930c1\",\"objectRef\":{\"resource\":\"podsecuritypolicies\",\"apiGroup\":\"policy\",\"apiVersion\":\"v1beta1\"},\"responseStatus\":{\"metadata\":{},\"code\":200},\"requestReceivedTimestamp\":\"2023-10-04T12:36:11.849075Z\",\"stageTimestamp\":\"2023-10-04T12:45:30.850483Z\",\"annotations\":{\"authorization.k8s.io/decision\":\"allow\",\"authorization.k8s.io/reason\":\"\",\"k8s.io/deprecated\":\"true\",\"k8s.io/removed-release\":\"1.25\"}}"
            },
[...]
```

## 使用kubectl-convert更新Kubernetes工作负载。更新清单

在识别需要更新的工作负载和清单后，您可能需要在清单文件中更改资源类型(例如，从PodSecurityPolicies更改为PodSecurityStandards)。这将需要更新资源规范并进行额外研究，具体取决于要替换的资源。

如果资源类型保持不变但需要更新API版本，您可以使用`kubectl-convert`命令自动转换清单文件。例如，将较旧的Deployment转换为`apps/v1`。有关更多信息，请参阅Kubernetes网站上的[安装kubectl convert插件](https://kubernetes.io/docs/tasks/tools/install-kubectl-linux/#install-kubectl-convert-plugin)。

`kubectl-convert -f <file> --output-version <group>/<version>`

## 配置PodDisruptionBudgets和topologySpreadConstraints以确保在升级数据平面时工作负载的可用性

确保您的工作负载具有适当的[PodDisruptionBudgets](https://kubernetes.io/docs/concepts/workloads/pods/disruptions/#pod-disruption-budgets)和[topologySpreadConstraints](https://kubernetes.io/docs/concepts/scheduling-eviction/topology-spread-constraints),以确保在升级数据平面时工作负载的可用性。并非每个工作负载都需要相同级别的可用性，因此您需要验证工作负载的规模和要求。

确保工作负载分布在多个可用区和多个主机上，并使用拓扑扩展将为工作负载自动迁移到新的数据平面提供更高的信心，而不会发生任何事故。

以下是一个工作负载的示例，它将始终保持80%的副本可用，并跨区域和主机分布副本

```
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: myapp
spec:
  minAvailable: "80%"
  selector:
    matchLabels:
      app: myapp
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp
spec:
  replicas: 10
  selector:
    matchLabels:
      app: myapp
  template:
    metadata:
      labels:
        app: myapp
    spec:
      containers:
      - image: public.ecr.aws/eks-distro/kubernetes/pause:3.2
        name: myapp
        resources:
          requests:
            cpu: "1"
            memory: 256M
      topologySpreadConstraints:
      - labelSelector:
          matchLabels:
            app: host-zone-spread
        maxSkew: 2
        topologyKey: kubernetes.io/hostname
        whenUnsatisfiable: DoNotSchedule
      - labelSelector:
          matchLabels:
            app: host-zone-spread
        maxSkew: 2
        topologyKey: topology.kubernetes.io/zone
        whenUnsatisfiable: DoNotSchedule
```

[AWS Resilience Hub](https://aws.amazon.com/resilience-hub/)已将Amazon Elastic Kubernetes Service (Amazon EKS)作为支持的资源。Resilience Hub提供了一个单一位置，用于定义、验证和跟踪应用程序的弹性，以避免由于软件、基础设施或操作中断而导致的不必要的停机时间。

## 使用托管节点组或Karpenter来简化数据平面升级

托管节点组和Karpenter都可以简化节点升级，但它们采用了不同的方法。

托管节点组可自动执行节点的供应和生命周期管理。这意味着您可以通过单个操作创建、自动更新或终止节点。

在默认配置中，Karpenter使用最新的兼容EKS优化AMI自动创建新节点。当EKS发布更新的EKS优化AMI或集群升级时，Karpenter将自动开始使用这些镜像。[Karpenter还实现了节点过期来更新节点。](#enable-node-expiry-for-karpenter-managed-nodes)

[Karpenter可以配置为使用自定义AMI。](https://karpenter.sh/docs/concepts/nodeclasses/)如果您在Karpenter中使用自定义AMI，则需要负责kubelet的版本。

## 在升级前确认现有节点与控制平面的版本兼容性

在Amazon EKS中继续Kubernetes升级之前，确保您的托管节点组、自管理节点与控制平面之间的兼容性至关重要。兼容性由您使用的Kubernetes版本决定，并且因不同情况而有所不同。策略：

* **Kubernetes v1.28+** - 从Kubernetes版本1.28开始，核心组件采用了更宽松的版本策略。具体而言，Kubernetes API服务器和kubelet之间支持的版本偏差已从n-2扩展到n-3。例如，如果您的EKS控制平面版本是1.28,您可以安全地使用1.25及更高版本的kubelet。这种版本偏差适用于[AWS Fargate](https://docs.aws.amazon.com/eks/latest/userguide/fargate.html)、[托管节点组](https://docs.aws.amazon.com/eks/latest/userguide/managed-node-groups.html)和[自管理节点](https://docs.aws.amazon.com/eks/latest/userguide/worker.html)。出于安全原因，我们强烈建议保持[Amazon Machine Image (AMI)](https://docs.aws.amazon.com/eks/latest/userguide/eks-optimized-amis.html)版本的最新状态。较旧的kubelet版本可能存在潜在的常见漏洞和暴露(CVE)，这可能会超过使用较旧kubelet版本的好处。
* **Kubernetes < v1.28** - 如果您使用的是1.28之前的版本，API服务器和kubelet之间支持的版本偏差为n-2。例如，如果您的EKS版本是1.27,您可以使用的最旧kubelet版本是1.25。此版本偏差适用于[AWS Fargate](https://docs.aws.amazon.com/eks/latest/userguide/fargate.html)、[托管节点组](https://docs.aws.amazon.com/eks/latest/userguide/managed-node-groups.html)和[自管理节点](https://docs.aws.amazon.com/eks/latest/userguide/worker.html)。

## 为Karpenter管理的节点启用节点过期

Karpenter实现节点升级的一种方式是使用节点过期的概念。这减少了节点升级所需的规划。当您为provisioner设置**ttlSecondsUntilExpired**值时，这将激活节点过期。节点达到定义的秒数年龄后，它们将被安全地耗尽和删除。即使它们正在使用，也是如此，从而允许您使用新供应的升级实例替换节点。当节点被替换时，Karpenter将使用最新的EKS优化AMI。有关更多信息，请参阅Karpenter网站上的[去供应](https://karpenter.sh/docs/concepts/deprovisioning/#methods)。

Karpenter不会自动为此值添加抖动。为防止过多的工作负载中断，请定义[pod中断预算](https://kubernetes.io/docs/tasks/run-application/configure-pdb/),如Kubernetes文档所示。

如果您在provisioner上配置了**ttlSecondsUntilExpired**,这将应用于与该provisioner关联的现有节点。

## 对于Karpenter管理的节点使用Drift功能

[Karpenter的Drift功能](https://karpenter.sh/docs/concepts/deprovisioning/#drift)可以自动将Karpenter供应的节点升级到与EKS控制平面保持同步。目前需要使用[功能门](https://karpenter.sh/docs/concepts/settings/#feature-gates)启用Karpenter Drift。Karpenter的默认配置使用与EKS集群控制平面相同的主要和次要版本的最新EKS优化AMI。

EKS集群升级完成后，Karpenter的Drift功能将检测到Karpenter供应的节点正在使用上一个集群版本的EKS优化AMI，并自动封锁、耗尽和替换这些节点。为支持pod移动到新节点，请遵循Kubernetes最佳实践，设置适当的pod[资源配额](https://kubernetes.io/docs/concepts/policy/resource-quotas/)并使用[pod中断预算](https://kubernetes.io/docs/concepts/workloads/pods/disruptions/)(PDB)。Karpenter的去供应将根据pod资源请求预先启动替换节点，并在去供应节点时将遵守PDB。

## 使用eksctl自动升级自管理节点组

自管理节点组是在您的账户中部署并附加到集群之外的EC2实例。这些通常由某种形式的自动化工具部署和管理。要升级自管理节点组，您应参考您的工具文档。

例如，eksctl支持[删除和耗尽自管理节点。](https://eksctl.io/usage/managing-nodegroups/#deleting-and-draining)

一些常见工具包括：

* [eksctl](https://eksctl.io/usage/nodegroup-upgrade/)
* [kOps](https://kops.sigs.k8s.io/operations/updates_and_upgrades/)
* [EKS Blueprints](https://aws-ia.github.io/terraform-aws-eks-blueprints/node-groups/#self-managed-node-groups)

## 在升级前备份集群

Kubernetes的新版本会对您的Amazon EKS集群引入重大变更。升级集群后，您无法降级。

[Velero](https://velero.io/)是一个社区支持的开源工具，可用于对现有集群进行备份并将备份应用于新集群。

请注意，您只能为EKS当前支持的Kubernetes版本创建新集群。如果您当前运行的集群版本仍受支持且升级失败，您可以使用原始版本创建新集群并恢复数据平面。请注意，AWS资源(包括IAM)不包含在Velero的备份中。这些资源需要重新创建。

## 在升级控制平面后重新启动Fargate部署

要升级Fargate数据平面节点，您需要重新部署工作负载。您可以通过使用`-o wide`选项列出所有pod来识别在fargate节点上运行的工作负载。任何以`fargate-`开头的节点名称都需要在集群中重新部署。


## 评估蓝/绿集群作为就地集群升级的替代方案

一些客户更喜欢采用蓝/绿升级策略。这可能有一些好处，但也应该考虑一些缺点。

优点包括：

* 可以一次更改多个EKS版本(例如，从1.23升级到1.25)
* 能够切换回旧集群
* 创建新集群，可能会使用更新的系统进行管理(例如terraform)
* 工作负载可以单独迁移

一些缺点包括：

* API端点和OIDC发生变化，需要更新使用者(例如kubectl和CI/CD)
* 在迁移期间需要并行运行2个集群，这可能会增加成本并限制区域容量
* 如果工作负载相互依赖，则需要更多协调以一起迁移
* 负载均衡器和外部DNS无法轻易跨多个集群

虽然可以采用这种策略，但与就地升级相比，它更加昂贵并需要更多时间进行协调和工作负载迁移。在某些情况下可能需要这样做，并且应该进行仔细规划。

通过高度自动化和声明式系统(如GitOps)，这可能会更容易做到。您需要为有状态工作负载采取额外的预防措施，以便备份和迁移数据到新集群。

查看以下博客文章以了解更多信息：

* [Kubernetes集群升级：蓝/绿部署策略](https://aws.amazon.com/blogs/containers/kubernetes-cluster-upgrade-the-blue-green-deployment-strategy/)
* [用于无状态ArgoCD工作负载的蓝/绿或金丝雀Amazon EKS集群迁移](https://aws.amazon.com/blogs/containers/blue-green-or-canary-amazon-eks-clusters-migration-for-stateless-argocd-workloads/)

## 跟踪Kubernetes项目中计划的重大变更 - 提前思考

不要只关注下一个版本。在新版本的Kubernetes发布时进行审查，并识别重大变更。例如，一些应用程序直接使用了docker API，而对Docker的容器运行时接口(CRI)(也称为Dockershim)的支持在Kubernetes `1.24`中被删除。这种变更需要更多时间来准备。

查看您要升级到的版本的所有记录的更改，并注意任何必需的升级步骤。还要注意Amazon EKS托管集群特有的任何要求或程序。

* [Kubernetes变更日志](https://github.com/kubernetes/kubernetes/tree/master/CHANGELOG)

## 特性删除的具体指导

### 1.25中删除Dockershim - 使用Detector for Docker Socket (DDS)

1.25的EKS优化AMI不再包含对Dockershim的支持。如果您依赖Dockershim，例如您正在挂载Docker套接字，则需要在将工作节点升级到1.25之前删除这些依赖项。

在升级到1.25之前，找出您对Docker套接字的依赖。我们建议使用[Detector for Docker Socket (DDS),一个kubectl插件。](https://github.com/aws-containers/kubectl-detector-for-docker-socket)。

### 1.25中删除PodSecurityPolicy - 迁移到Pod Security Standards或策略即代码解决方案

`PodSecurityPolicy`在[Kubernetes 1.21中被弃用](https://kubernetes.io/blog/2021/04/06/podsecuritypolicy-deprecation-past-present-and-future/),并在Kubernetes 1.25中被删除。如果您在集群中使用PodSecurityPolicy，那么在将集群升级到1.25版本之前，您必须迁移到内置的Kubernetes Pod Security Standards (PSS)或策略即代码解决方案，以避免对您的工作负载造成中断。

AWS在EKS文档中发布了[详细的常见问题解答。](https://docs.aws.amazon.com/eks/latest/userguide/pod-security-policy-removal-faq.html)

查看[Pod Security Standards (PSS)和Pod Security Admission (PSA)](https://aws.github.io/aws-eks-best-practices/security/docs/pods/#pod-security-standards-pss-and-pod-security-admission-psa)最佳实践。

查看Kubernetes网站上的[PodSecurityPolicy弃用博客文章](https://kubernetes.io/blog/2021/04/06/podsecuritypolicy-deprecation-past-present-and-future/)。

### 1.23中弃用内置存储驱动程序 - 迁移到容器存储接口(CSI)驱动程序

容器存储接口(CSI)旨在帮助Kubernetes取代其现有的内置存储驱动程序机制。Amazon EBS容器存储接口(CSI)迁移功能在Amazon EKS `1.23`及更高版本的集群中默认启用。如果您在1.22或更早版本的集群上运行pods，那么在将集群更新到1.23版本之前，您必须安装[Amazon EBS CSI驱动程序](https://docs.aws.amazon.com/eks/latest/userguide/ebs-csi.html),以避免服务中断。

查看[Amazon EBS CSI迁移常见问题解答](https://docs.aws.amazon.com/eks/latest/userguide/ebs-csi-migration-faq.html)。

## 其他资源

### ClowdHaus EKS升级指南

[ClowdHaus EKS升级指南](https://clowdhaus.github.io/eksup/)是一个CLI，可帮助升级Amazon EKS集群。它可以分析集群是否存在任何需要在升级之前修复的潜在问题。

### GoNoGo

[GoNoGo](https://github.com/FairwindsOps/GoNoGo)是一个alpha阶段的工具，用于确定集群插件的升级置信度。