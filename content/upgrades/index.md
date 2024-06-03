# Best Practices for Cluster Upgrades

This guide shows cluster administrators how to plan and execute their Amazon EKS upgrade strategy. It also describes how to upgrade self-managed nodes, managed node groups, Karpenter nodes, and Fargate nodes. It does not include guidance on EKS Anywhere, self-managed Kubernetes, AWS Outposts, or AWS Local Zones. 

## Overview

A Kubernetes version encompasses both the control plane and the data plane. To ensure smooth operation, both the control plane and the data plane should run the same [Kubernetes minor version, such as 1.24](https://kubernetes.io/releases/version-skew-policy/#supported-versions). While AWS manages and upgrades the control plane, updating the worker nodes in the data plane is your responsibility.

* **Control plane** — The version of the control plane is determined by the Kubernetes API server. In Amazon EKS clusters, AWS takes care of managing this component. Control plane upgrades can be initiated via the AWS API. 
* **Data plane** — The data plane version is associated with the Kubelet versions running on your individual nodes. It's possible to have nodes in the same cluster running different versions. You can check the versions of all nodes by running `kubectl get nodes`.

## Before Upgrading

If you're planning to upgrade your Kubernetes version in Amazon EKS, there are a few important policies, tools, and procedures you should put in place before starting an upgrade. 

* **Understand Deprecation Policies** — Gain a deep understanding of how the  [Kubernetes deprecation policy](https://kubernetes.io/docs/reference/using-api/deprecation-policy/) works. Be aware of any upcoming changes that may affect your existing applications. Newer versions of Kubernetes often phase out certain APIs and features, potentially causing issues for running applications.
* **Review Kubernetes Change Log** — Thoroughly review the [Kubernetes change log](https://github.com/kubernetes/kubernetes/tree/master/CHANGELOG) alongside [Amazon EKS Kubernetes versions](https://docs.aws.amazon.com/eks/latest/userguide/kubernetes-versions.html) to understand any possible impact to your cluster, such as breaking changes that may affect your workloads.
* **Assess Cluster Add-Ons Compatibility** — Amazon EKS doesn't automatically update an add-on when new versions are released or after you update your cluster to a new Kubernetes minor version. Review [Updating an add-on](https://docs.aws.amazon.com/eks/latest/userguide/managing-add-ons.html#updating-an-add-on) to understand the compatibility of any existing cluster add-ons with the cluster version you intend to upgrade to.
* **Enable Control Plane Logging** — Enable [control plane logging](https://docs.aws.amazon.com/eks/latest/userguide/control-plane-logs.html) to capture logs, errors, or issues that can arise during the upgrade process. Consider reviewing these logs for any anomalies. Test cluster upgrades in a non-production environment, or integrate automated tests into your continuous integration workflow to assess version compatibility with your applications, controllers, and custom integrations.
* **Explore eksctl for Cluster Management** — Consider using [eksctl](https://eksctl.io/) to manage your EKS cluster. It provides you with the ability to [upgrade the control plane, manage add-ons, and handle worker node upgrades](https://eksctl.io/usage/cluster-upgrade/) out-of-the-box. 
* **Opt for Managed Node Groups or EKS on Fargate** — Streamline and automate worker node upgrades by using [EKS managed node groups](https://docs.aws.amazon.com/eks/latest/userguide/managed-node-groups.html) or [EKS on Fargate](https://docs.aws.amazon.com/eks/latest/userguide/fargate.html). These options simplify the process and reduce manual intervention.
* **Utilize kubectl Convert Plugin** — Leverage the [kubectl convert plugin](https://kubernetes.io/docs/tasks/tools/install-kubectl-linux/#install-kubectl-convert-plugin) to facilitate the [conversion of Kubernetes manifest files](https://kubernetes.io/docs/tasks/tools/included/kubectl-convert-overview/) between different API versions. This can help ensure that your configurations remain compatible with the new Kubernetes version.

## Keep your cluster up-to-date

Staying current with Kubernetes updates is paramount for a secure and efficient EKS environment, reflecting the shared responsibility model in Amazon EKS. By integrating these strategies into your operational workflow, you're positioning yourself to maintain up-to-date, secure clusters that take full advantage of the latest features and improvements. Tactics:

* **Supported Version Policy** — Aligned with the Kubernetes community, Amazon EKS typically provides three active Kubernetes versions while deprecating a fourth version each year. Deprecation notices are issued at least 60 days before a version reaches its end-of-support date. For more details, refer to the [EKS Version FAQ](https://aws.amazon.com/eks/eks-version-faq/).
* **Auto-Upgrade Policy** — We strongly recommend staying in sync with Kubernetes updates in your EKS cluster. Kubernetes community support, including bug fixes and security patches, typically ceases for versions older than one year. Deprecated versions may also lack vulnerability reporting, posing a potential risk. Failure to proactively upgrade before a version's end-of-life triggers an automatic upgrade, which could disrupt your workloads and systems. For additional information, consult the [EKS Version Support Policy](https://aws.amazon.com/eks/eks-version-support-policy/).
* **Create Upgrade Runbooks** — Establish a well-documented process for managing upgrades. As part of your proactive approach, develop runbooks and specialized tools tailored to your upgrade process. This not only enhances your preparedness but also simplifies complex transitions. Make it a standard practice to upgrade your clusters at least once a year. This practice aligns you with ongoing technological advancements, thereby boosting the efficiency and security of your environment.

## Review the EKS release calendar

[Review the EKS Kubernetes release calendar](https://docs.aws.amazon.com/eks/latest/userguide/kubernetes-versions.html#kubernetes-release-calendar) to learn when new versions are coming, and when support for specific versions end. Generally, EKS releases three minor versions of Kubernetes annually, and each minor version is supported for about 14 months. 

Additionally, review the upstream [Kubernetes release information](https://kubernetes.io/releases/).

## Understand how the shared responsibility model applies to cluster upgrades

You are responsible for initiating upgrade for both cluster control plane as well as the data plane. [Learn how to initiate an upgrade.](https://docs.aws.amazon.com/eks/latest/userguide/update-cluster.html) When you initiate a cluster upgrade, AWS manages upgrading the cluster control plane. You are responsible for upgrading the data plane, including Fargate pods and [other add-ons.](#upgrade-add-ons-and-components-using-the-kubernetes-api) You must validate and plan upgrades for workloads running on your cluster to ensure their availability and operations are not impacted after cluster upgrade

## Upgrade clusters in-place

EKS supports an in-place cluster upgrade strategy. This maintains cluster resources, and keeps cluster configuration consistent (e.g., API endpoint, OIDC, ENIs, load balancers). This is less disruptive for cluster users, and it will use the existing workloads and resources in the cluster without requiring you to redeploy workloads or migrate external resources (e.g., DNS, storage).

When performing an in-place cluster upgrade, it is important to note that only one minor version upgrade can be executed at a time (e.g., from 1.24 to 1.25). 

This means that if you need to update multiple versions, a series of sequential upgrades will be required. Planning sequential upgrades is more complicated, and has a higher risk of downtime. In this situation, [evaluate a blue/green cluster upgrade strategy.](#evaluate-bluegreen-clusters-as-an-alternative-to-in-place-cluster-upgrades)

## Upgrade your control plane and data plane in sequence

To upgrade a cluster you will need to take the following actions:

1. [Review the Kubernetes and EKS release notes.](#use-the-eks-documentation-to-create-an-upgrade-checklist)
2. [Take a backup of the cluster. (optional)](#backup-the-cluster-before-upgrading)
3. [Identify and remediate deprecated and removed API usage in your workloads.](#identify-and-remediate-removed-api-usage-before-upgrading-the-control-plane)
4. [Ensure Managed Node Groups, if used, are on the same Kubernetes version as the control plane.](#track-the-version-skew-of-nodes-ensure-managed-node-groups-are-on-the-same-version-as-the-control-plane-before-upgrading) EKS managed node groups and nodes created by EKS Fargate Profiles only support 1 minor version skew between the control plane and data plane.
5. [Upgrade the cluster control plane using the AWS console or cli.](https://docs.aws.amazon.com/eks/latest/userguide/update-cluster.html)
6. [Review add-on compatibility.](#upgrade-add-ons-and-components-using-the-kubernetes-api) Upgrade your Kubernetes add-ons and custom controllers, as required. 
7. [Update kubectl.](https://docs.aws.amazon.com/eks/latest/userguide/install-kubectl.html)
8. [Upgrade the cluster data plane.](https://docs.aws.amazon.com/eks/latest/userguide/update-managed-node-group.html)  Upgrade your nodes to the same Kubernetes minor version as your upgraded cluster. 

## Use the EKS Documentation to create an upgrade checklist

The EKS Kubernetes [version documentation](https://docs.aws.amazon.com/eks/latest/userguide/kubernetes-versions.html) includes a detailed list of changes for each version. Build a checklist for each upgrade. 

For specific EKS version upgrade guidance, review the documentation for notable changes and considerations for each version.

* [EKS 1.27](https://docs.aws.amazon.com/eks/latest/userguide/kubernetes-versions.html#kubernetes-1.27)
* [EKS 1.26](https://docs.aws.amazon.com/eks/latest/userguide/kubernetes-versions.html#kubernetes-1.26)
* [EKS 1.25](https://docs.aws.amazon.com/eks/latest/userguide/kubernetes-versions.html#kubernetes-1.25)
* [EKS 1.24](https://docs.aws.amazon.com/eks/latest/userguide/kubernetes-versions.html#kubernetes-1.24)
* [EKS 1.23](https://docs.aws.amazon.com/eks/latest/userguide/kubernetes-versions.html#kubernetes-1.23)
* [EKS 1.22](https://docs.aws.amazon.com/eks/latest/userguide/kubernetes-versions.html#kubernetes-1.22)

## Upgrade add-ons and components using the Kubernetes API

Before you upgrade a cluster, you should understand what versions of Kubernetes components you are using. Inventory cluster components, and identify components that use the Kubernetes API directly. This includes critical cluster components such as monitoring and logging agents, cluster autoscalers, container storage drivers (e.g. [EBS CSI](https://docs.aws.amazon.com/eks/latest/userguide/ebs-csi.html), [EFS CSI](https://docs.aws.amazon.com/eks/latest/userguide/efs-csi.html)), ingress controllers, and any other workloads or add-ons that rely on the Kubernetes API directly. 

!!! tip
    Critical cluster components are often installed in a `*-system` namespace
    
    ```
    kubectl get ns | grep '-system'
    ```

Once you have identified components that rely the Kubernetes API, check their documentation for version compatibility and upgrade requirements. For example, see the [AWS Load Balancer Controller](https://kubernetes-sigs.github.io/aws-load-balancer-controller/v2.4/deploy/installation/) documentation for version compatibility. Some components may need to be upgraded or configuration changed before proceeding with a cluster upgrade. Some critical components to check include [CoreDNS](https://github.com/coredns/coredns), [kube-proxy](https://kubernetes.io/docs/concepts/overview/components/#kube-proxy), [VPC CNI](https://github.com/aws/amazon-vpc-cni-k8s), and storage drivers. 

Clusters often contain many workloads that use the Kubernetes API and are required for workload functionality such as ingress controllers, continuous delivery systems, and monitoring tools. When you upgrade an EKS cluster, you must also upgrade your add-ons and third-party tools to make sure they are compatible.
 
See the following examples of common add-ons and their relevant upgrade documentation:

* **Amazon VPC CNI:** For the recommended version of the Amazon VPC CNI add-on for each cluster version, see [Updating the Amazon VPC CNI plugin for Kubernetes self-managed add-on](https://docs.aws.amazon.com/eks/latest/userguide/managing-vpc-cni.html). **When installed as an Amazon EKS Add-on, it can only be upgraded one minor version at a time.**
* **kube-proxy:** See [Updating the Kubernetes kube-proxy self-managed add-on](https://docs.aws.amazon.com/eks/latest/userguide/managing-kube-proxy.html).
* **CoreDNS:** See [Updating the CoreDNS self-managed add-on](https://docs.aws.amazon.com/eks/latest/userguide/managing-coredns.html).
* **AWS Load Balancer Controller:** The AWS Load Balancer Controller needs to be compatible with the EKS version you have deployed. See the [installation guide](https://docs.aws.amazon.com/eks/latest/userguide/aws-load-balancer-controller.html) for more information. 
* **Amazon Elastic Block Store (Amazon EBS) Container Storage Interface (CSI) driver:** For installation and upgrade information, see [Managing the Amazon EBS CSI driver as an Amazon EKS add-on](https://docs.aws.amazon.com/eks/latest/userguide/managing-ebs-csi.html).
* **Amazon Elastic File System (Amazon EFS) Container Storage Interface (CSI) driver:** For installation and upgrade information, see [Amazon EFS CSI driver](https://docs.aws.amazon.com/eks/latest/userguide/efs-csi.html).
* **Kubernetes Metrics Server:** For more information, see [metrics-server](https://kubernetes-sigs.github.io/metrics-server/) on GitHub.
* **Kubernetes Cluster Autoscaler****:** To upgrade the version of Kubernetes Cluster Autoscaler, change the version of the image in the deployment. The Cluster Autoscaler is tightly coupled with the Kubernetes scheduler. You will always need to upgrade it when you upgrade the cluster. Review the [GitHub releases](https://github.com/kubernetes/autoscaler/releases) to find the address of the latest release corresponding to your Kubernetes minor version.
* **Karpenter:** For installation and upgrade information, see the [Karpenter documentation.](https://karpenter.sh/docs/upgrading/)

## Verify basic EKS requirements before upgrading

AWS requires certain resources in your account to complete the upgrade process. If these resources aren’t present, the cluster cannot be upgraded. A control plane upgrade requires the following resources:

1. Available IP addresses: Amazon EKS requires up to five available IP addresses from the subnets you specified when you created the cluster in order to update the cluster. If not, update your cluster configuration to include new cluster subnets prior to performing the version update.
2. EKS IAM role: The control plane IAM role is still present in the account with the necessary permissions.
3. If your cluster has secret encryption enabled, then make sure that the cluster IAM role has permission to use the AWS Key Management Service (AWS KMS) key.

### Verify available IP addresses

To update the cluster, Amazon EKS requires up to five available IP addresses from the subnets that you specified when you created your cluster.

To verify that your subnets have enough IP addresses to upgrade the cluster you can run the following command:

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

The [VPC CNI Metrics Helper](https://github.com/aws/amazon-vpc-cni-k8s/blob/master/cmd/cni-metrics-helper/README.md) may be used to create a CloudWatch dashboard for VPC metrics. 
Amazon EKS recommends updating the cluster subnets using the "UpdateClusterConfiguration" API prior to beginning a Kubernetes version upgrade if you are running out of IP addresses in the subnets initially specified during cluster creation. Please verify that the new subnets you will be provided:

* belong to same set of AZs that are selected during cluster creation. 
* belong to the same VPC provided during cluster creation

Please consider associating additional CIDR blocks if the IP addresses in the existing VPC CIDR block run out. AWS enables the association of additional CIDR blocks with your existing cluster VPC, effectively expanding your IP address pool. This expansion can be accomplished by introducing additional private IP ranges (RFC 1918) or, if necessary, public IP ranges (non-RFC 1918). You must add new VPC CIDR blocks and allow VPC refresh to complete before Amazon EKS can use the new CIDR. After that, you can update the subnets based on the newly set up CIDR blocks to the VPC.


### Verify EKS IAM role

To verify that the IAM role is available and has the correct assume role policy in your account you can run the following commands:

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

## Migrate to EKS Add-ons

Amazon EKS automatically installs add-ons such as the Amazon VPC CNI plugin for Kubernetes, `kube-proxy`, and CoreDNS for every cluster. Add-ons may be self-managed, or installed as Amazon EKS Add-ons. Amazon EKS Add-ons is an alternate way to manage add-ons using the EKS API. 

You can use Amazon EKS Add-ons to update versions with a single command. For Example:

```
aws eks update-addon —cluster-name my-cluster —addon-name vpc-cni —addon-version version-number \
--service-account-role-arn arn:aws:iam::111122223333:role/role-name —configuration-values '{}' —resolve-conflicts PRESERVE
```

Check if you have any EKS Add-ons with:

```
aws eks list-addons --cluster-name <cluster name>
```

!!! warning
      
    EKS Add-ons are not automatically upgraded during a control plane upgrade. You must initiate EKS add-on updates, and select the desired version. 

    * You are responsible for selecting a compatible version from all available versions. [Review the guidance on add-on version compatibility.](#upgrade-add-ons-and-components-using-the-kubernetes-api)
    * Amazon EKS Add-ons may only be upgraded one minor version at a time. 

[Learn more about what components are available as EKS Add-ons, and how to get started.](https://docs.aws.amazon.com/eks/latest/userguide/eks-add-ons.html)

[Learn how to supply a custom configuration to an EKS Add-on.](https://aws.amazon.com/blogs/containers/amazon-eks-add-ons-advanced-configuration/)

## Identify and remediate removed API usage before upgrading the control plane

You should identify API usage of removed APIs before upgrading your EKS control plane. To do that we recommend using tools that can check a running cluster or static, rendered Kubernetes manifest files. 

Running the check against static manifest files is generally more accurate. If run against live clusters, these tools may return false positives. 

A deprecated Kubernetes API does not mean the API has been removed. You should check the [Kubernetes Deprecation Policy](https://kubernetes.io/docs/reference/using-api/deprecation-policy/) to understand how API removal affects your workloads.

### Cluster Insights
[Cluster Insights](https://docs.aws.amazon.com/eks/latest/userguide/cluster-insights.html) is a feature that provides findings on issues that may impact the ability to upgrade an EKS cluster to newer versions of Kubernetes. These findings are curated and managed by Amazon EKS and offer recommendations on how to remediate them. By leveraging Cluster Insights, you can minimize the effort spent to upgrade to newer Kubernetes versions.

To view insights of an EKS cluster, you can run the command:
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

For a more descriptive output about the insight received, you can run the command:
```
aws eks describe-insight --region <region-code> --id <insight-id> --cluster-name <my-cluster>
```

You also have the option to view insights in the [Amazon EKS Console](https://console.aws.amazon.com/eks/home#/clusters). After selecting your cluster from the cluster list, insight findings are located under the ```Upgrade Insights``` tab.

If you find a cluster insight with `"status": ERROR`, you must address the issue prior to performing the cluster upgrade. Run the `aws eks describe-insight` command which will share the following remediation advice: 

Resources affected:
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

APIs deprecated:
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

Recommended action to take:
```
"recommendation": "Update manifests and API clients to use newer Kubernetes APIs if applicable before upgrading to Kubernetes v1.26."
```

Utilizing cluster insights through the EKS Console or CLI help speed the process of successfully upgrading EKS cluster versions. Learn more with the following resources:
* [Official EKS Docs](https://docs.aws.amazon.com/eks/latest/userguide/cluster-insights.html)
* [Cluster Insights launch blog](https://aws.amazon.com/blogs/containers/accelerate-the-testing-and-verification-of-amazon-eks-upgrades-with-upgrade-insights/).

### Kube-no-trouble

[Kube-no-trouble](https://github.com/doitintl/kube-no-trouble) is an open source command line utility with the command `kubent`. When you run `kubent` without any arguments it will use your current KubeConfig context and scan the cluster and print a report with what APIs will be deprecated and removed. 

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

It can also be used to scan static manifest files and helm packages. It is recommended to run `kubent` as part of a continuous integration (CI) process to identify issues before manifests are deployed. Scanning manifests is also more accurate than scanning live clusters. 

Kube-no-trouble provides a sample [Service Account and Role](https://github.com/doitintl/kube-no-trouble/blob/master/docs/k8s-sa-and-role-example.yaml) with the appropriate permissions for scanning the cluster. 

### Pluto

Another option is [pluto](https://pluto.docs.fairwinds.com/) which is similar to `kubent` because it supports scanning a live cluster, manifest files, helm charts and has a GitHub Action you can include in your CI process.

```
pluto detect-all-in-cluster

NAME             KIND                VERSION          REPLACEMENT   REMOVED   DEPRECATED   REPL AVAIL  
eks.privileged   PodSecurityPolicy   policy/v1beta1                 false     true         true
```

### Resources

To verify that your cluster don't use deprecated APIs before the upgrade, you should monitor:

* metric `apiserver_requested_deprecated_apis` since Kubernetes v1.19:

```
kubectl get --raw /metrics | grep apiserver_requested_deprecated_apis

apiserver_requested_deprecated_apis{group="policy",removed_release="1.25",resource="podsecuritypolicies",subresource="",version="v1beta1"} 1
```

* events in the [audit logs](https://docs.aws.amazon.com/eks/latest/userguide/control-plane-logs.html) with `k8s.io/deprecated` set to `true`:

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

Which will output lines if deprecated APIs are in use:

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

## Update Kubernetes workloads. Use kubectl-convert to update manifests

After you have identified what workloads and manifests need to be updated, you may need to change the resource type in your manifest files (e.g. PodSecurityPolicies to PodSecurityStandards). This will require updating the resource specification and additional research depending on what resource is being replaced.

If the resource type is staying the same but API version needs to be updated you can use the `kubectl-convert` command to automatically convert your manifest files.  For example, to convert an older Deployment to `apps/v1`. For more information, see [Install kubectl convert plugin](https://kubernetes.io/docs/tasks/tools/install-kubectl-linux/#install-kubectl-convert-plugin)on the Kubernetes website.

`kubectl-convert -f <file> --output-version <group>/<version>`

## Configure PodDisruptionBudgets and topologySpreadConstraints to ensure availability of your workloads while the data plane is upgraded

Ensure your workloads have the proper [PodDisruptionBudgets](https://kubernetes.io/docs/concepts/workloads/pods/disruptions/#pod-disruption-budgets) and [topologySpreadConstraints](https://kubernetes.io/docs/concepts/scheduling-eviction/topology-spread-constraints) to ensure availability of your workloads while the data plane is upgraded. Not every workload requires the same level of availability so you need to validate the scale and requirements of your workload.

Make sure workloads are spread in multiple Availability Zones and on multiple hosts with topology spreads will give a higher level of confidence that workloads will migrate to the new data plane automatically without incident. 

Here is an example workload that will always have 80% of replicas available and spread replicas across zones and hosts

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

[AWS Resilience Hub](https://aws.amazon.com/resilience-hub/) has added Amazon Elastic Kubernetes Service (Amazon EKS) as a supported resource. Resilience Hub provides a single place to define, validate, and track the resilience of your applications so that you can avoid unnecessary downtime caused by software, infrastructure, or operational disruptions.

## Use Managed Node Groups or Karpenter to simplify data plane upgrades

Managed Node Groups and Karpenter both simplify node upgrades, but they take different approaches.

Managed node groups automate the provisioning and lifecycle management of nodes. This means that you can create, automatically update, or terminate nodes with a single operation.

For Karpenter data plane updgrades, refer to below sections:
* [Use Drift feature for Karpenter managed nodes](#use-drift-feature-for-karpenter-managed-nodes)
* [Use Node expiry for Karpenter managed nodes](#use-node-expiry-for-karpenter-managed-nodes)

## Confirm version compatibility with existing nodes and the control plane

Before proceeding with a Kubernetes upgrade in Amazon EKS, it's vital to ensure compatibility between your managed node groups, self-managed nodes, and the control plane. Compatibility is determined by the Kubernetes version you are using, and it varies based on different scenarios. Tactics:

* **Kubernetes v1.28+** — **** Starting from Kubernetes version 1.28 and onwards, there's a more lenient version policy for core components. Specifically, the supported skew between the Kubernetes API server and the kubelet has been extended by one minor version, going from n-2 to n-3. For example, if your EKS control plane version is 1.28, you can safely use kubelet versions as old as 1.25. This version skew is supported across [AWS Fargate](https://docs.aws.amazon.com/eks/latest/userguide/fargate.html), [managed node groups](https://docs.aws.amazon.com/eks/latest/userguide/managed-node-groups.html), and [self-managed nodes](https://docs.aws.amazon.com/eks/latest/userguide/worker.html). We highly recommend keeping your [Amazon Machine Image (AMI)](https://docs.aws.amazon.com/eks/latest/userguide/eks-optimized-amis.html) versions up-to-date for security reasons. Older kubelet versions might pose security risks due to potential Common Vulnerabilities and Exposures (CVEs), which could outweigh the benefits of using older kubelet versions.
* **Kubernetes < v1.28** — If you are using a version older than v1.28, the supported skew between the API server and the kubelet is n-2. For example, if your EKS version is 1.27, the oldest kubelet version you can use is 1.25. This version skew is applicable across [AWS Fargate](https://docs.aws.amazon.com/eks/latest/userguide/fargate.html), [managed node groups](https://docs.aws.amazon.com/eks/latest/userguide/managed-node-groups.html), and [self-managed nodes](https://docs.aws.amazon.com/eks/latest/userguide/worker.html).

## Use Drift feature for Karpenter managed nodes

Karpenter’s [Drift feature](https://karpenter.sh/docs/concepts/disruption/#drift) can automatically upgrade the Karpenter-provisioned nodes to stay in-sync with the EKS control plane. Refer to [How to upgrade an EKS Cluster with Karpenter](https://karpenter.sh/docs/faq/#how-do-i-upgrade-an-eks-cluster-with-karpenter) for more details.

This means that if the AMI ID specified in the Karpenter EC2 Nodeclass is updated, Karpenter will detect the drift and start replacing the nodes with the new AMI. 
To understand how Karpenter manages AMIs and the different options available to Karpenter users to control the AMI upgrade process see the documentation on [how to manage AMIs in Karpenter](https://karpenter.sh/docs/tasks/managing-amis/).

[Karpenter can be configured to use custom AMIs.](https://karpenter.sh/docs/concepts/nodeclasses/) If you use custom AMIs with Karpenter, you are responsible for the version of kubelet. 

## Use Node expiry for Karpenter managed nodes

One way Karpenter implements node upgrades is using the concept of node expiry. This reduces the planning required for node upgrades. Karpenter will mark nodes as expired and disrupt them after they have lived a set number of seconds, based on the NodePool’s `spec.disruption.expireAfter` value. This node expiry helps to reduce security vulnerabilities and issues that can arise from long-running nodes, such as file fragmentation or memory leaks. When you set a value for expireAfter in your NodePool, this activates node expiry. For more information, see [Disruption](https://karpenter.sh/docs/concepts/disruption/#methods) on the Karpenter website.

If it’s happened that the node is drifted, but hasn’t been cleaned up, node expiration will also replace the instance with the new AMI in EC2NodeClass.

## Use eksctl to automate upgrades for self-managed node groups

Self managed node groups are EC2 instances that were deployed in your account and attached to the cluster outside of the EKS service. These are usually deployed and managed by some form of automation tooling. To upgrade self-managed node groups you should refer to your tools documentation.

For example, eksctl supports [deleting and draining self-managed nodes.](https://eksctl.io/usage/managing-nodegroups/#deleting-and-draining) 

Some common tools include:

* [eksctl](https://eksctl.io/usage/nodegroup-upgrade/)
* [kOps](https://kops.sigs.k8s.io/operations/updates_and_upgrades/)
* [EKS Blueprints](https://aws-ia.github.io/terraform-aws-eks-blueprints/node-groups/#self-managed-node-groups)

## Backup the cluster before upgrading

New versions of Kubernetes introduce significant changes to your Amazon EKS cluster. After you upgrade a cluster, you can’t downgrade it.

[Velero](https://velero.io/) is an community supported open-source tool that can be used to take backups of existing clusters and apply the backups to a new cluster.

Note that you can only create new clusters for Kubernetes versions currently supported by EKS. If the version your cluster is currently running is still supported and an upgrade fails, you can create a new cluster with the original version and restore the data plane. Note that AWS resources, including IAM, are not included in the backup by Velero. These resources would need to be recreated. 

## Restart Fargate deployments after upgrading the control plane

To upgrade Fargate data plane nodes you need to redeploy the workloads. You can identify which workloads are running on fargate nodes by listing all pods with the `-o wide` option. Any node name that begins with `fargate-` will need to be redeployed in the cluster.


## Evaluate Blue/Green Clusters as an alternative to in-place cluster upgrades

Some customers prefer to do a blue/green upgrade strategy. This can have benefits, but also includes downsides that should be considered.

Benefits include:

* Possible to change multiple EKS versions at once (e.g. 1.23 to 1.25)
* Able to switch back to the old cluster
* Creates a new cluster which may be managed with newer systems (e.g. terraform)
* Workloads can be migrated individually

Some downsides include:

* API endpoint and OIDC change which requires updating consumers (e.g. kubectl and CI/CD)
* Requires 2 clusters to be run in parallel during the migration, which can be expensive and limit region capacity
* More coordination is needed if workloads depend on each other to be migrated together
* Load balancers and external DNS cannot easily span multiple clusters

While this strategy is possible to do, it is more expensive than an in-place upgrade and requires more time for coordination and workload migrations. It may be required in some situations and should be planned carefully.

With high degrees of automation and declarative systems like GitOps, this may be easier to do. You will need to take additional precautions for stateful workloads so data is backed up and migrated to new clusters.

Review these blogs posts for more information:

* [Kubernetes cluster upgrade: the blue-green deployment strategy](https://aws.amazon.com/blogs/containers/kubernetes-cluster-upgrade-the-blue-green-deployment-strategy/)
* [Blue/Green or Canary Amazon EKS clusters migration for stateless ArgoCD workloads](https://aws.amazon.com/blogs/containers/blue-green-or-canary-amazon-eks-clusters-migration-for-stateless-argocd-workloads/)

## Track planned major changes in the Kubernetes project — Think ahead

Don’t look only at the next version. Review new versions of Kubernetes as they are released, and identify major changes. For example, some applications directly used the docker API, and support for Container Runtime Interface (CRI) for Docker (also known as Dockershim) was removed in Kubernetes `1.24`. This kind of change requires more time to prepare for. 
 
Review all documented changes for the version that you’re upgrading to, and note any required upgrade steps. Also, note any requirements or procedures that are specific to Amazon EKS managed clusters.

* [Kubernetes changelog](https://github.com/kubernetes/kubernetes/tree/master/CHANGELOG)

## Specific Guidance on Feature Removals

### Removal of Dockershim in 1.25 - Use Detector for Docker Socket (DDS)

The EKS Optimized AMI for 1.25 no longer includes support for Dockershim. If you have a dependency on Dockershim, e.g. you are mounting the Docker socket, you will need to remove those dependencies before upgrading your worker nodes to 1.25. 

Find instances where you have a dependency on the Docker socket before upgrading to 1.25. We recommend using [Detector for Docker Socket (DDS), a kubectl plugin.](https://github.com/aws-containers/kubectl-detector-for-docker-socket). 

### Removal of PodSecurityPolicy in 1.25 - Migrate to Pod Security Standards or a policy-as-code solution

`PodSecurityPolicy` was [deprecated in Kubernetes 1.21](https://kubernetes.io/blog/2021/04/06/podsecuritypolicy-deprecation-past-present-and-future/), and has been removed in Kubernetes 1.25. If you are using PodSecurityPolicy in your cluster, then you must migrate to the built-in Kubernetes Pod Security Standards (PSS) or to a policy-as-code solution before upgrading your cluster to version 1.25 to avoid interruptions to your workloads. 

AWS published a [detailed FAQ in the EKS documentation.](https://docs.aws.amazon.com/eks/latest/userguide/pod-security-policy-removal-faq.html)

Review the [Pod Security Standards (PSS) and Pod Security Admission (PSA)](https://aws.github.io/aws-eks-best-practices/security/docs/pods/#pod-security-standards-pss-and-pod-security-admission-psa) best practices. 

Review the [PodSecurityPolicy Deprecation blog post](https://kubernetes.io/blog/2021/04/06/podsecuritypolicy-deprecation-past-present-and-future/) on the Kubernetes website.

### Deprecation of In-Tree Storage Driver in 1.23 - Migrate to Container Storage Interface (CSI) Drivers

The Container Storage Interface (CSI) was designed to help Kubernetes replace its existing, in-tree storage driver mechanisms. The Amazon EBS container storage interface (CSI) migration feature is enabled by default in Amazon EKS `1.23` and later clusters. If you have pods running on a version `1.22` or earlier cluster, then you must install the [Amazon EBS CSI driver](https://docs.aws.amazon.com/eks/latest/userguide/ebs-csi.html) before updating your cluster to version `1.23` to avoid service interruption. 

Review the [Amazon EBS CSI migration frequently asked questions](https://docs.aws.amazon.com/eks/latest/userguide/ebs-csi-migration-faq.html).

## Additional Resources

### ClowdHaus EKS Upgrade Guidance

[ClowdHaus EKS Upgrade Guidance](https://clowdhaus.github.io/eksup/) is a CLI to aid in upgrading Amazon EKS clusters. It can analyze a cluster for any potential issues to remediate prior to upgrade. 

### GoNoGo

[GoNoGo](https://github.com/FairwindsOps/GoNoGo) is an alpha-stage tool to determine the upgrade confidence of your cluster add-ons. 

