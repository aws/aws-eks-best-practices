---
date: 2023-09-29
authors: 
  - Justin Garrison
  - Rajdeep Saha
---
# Cost Optimization - Compute and Autoscaling

As a developer, you'll make estimates about your application’s resource requirements, e.g. CPU and memory, but if you’re not continually adjusting them they may become outdated which could increase your costs and worsen performance and reliability. Continually adjusting an application's resource requirements is more important than getting them right the first time.

The best practices mentioned below will help you build and operate cost-aware workloads that achieve business outcomes while minimizing costs and allowing your organization to maximize its return on investment. A high level order of importance for optimizing your cluster compute costs are:

1. Right-size workloads
2. Reduce unused capacity
3. Optimize compute capacity types (e.g. Spot) and accelerators (e.g. GPUs)

## Right-size your workloads

In most EKS clusters, the bulk of cost come from the EC2 instances that are used to run your containerized workloads. You will not be able to right-size your compute resources without understanding your workloads requirements. This is why it is essential that you use the appropriate requests and limits and make adjustments to those settings as necessary. In addition, dependencies, such as instance size and storage selection, may effect workload performance which can have a variety of unintended consequences on costs and reliability.

*Requests* should align with the actual utilization. If a container's requests are too high there will be unused capacity which is a large factor in total cluster costs. Each container in a pod, e.g. application and sidecars, should have their own requests and limits set to make sure the aggregate pod limits are as accurate as possible.

Utilize tools such as [Goldilocks](https://www.youtube.com/watch?v=DfmQWYiwFDk), [KRR](https://www.youtube.com/watch?v=uITOzpf82RY), and [Kubecost](https://aws.amazon.com/blogs/containers/aws-and-kubecost-collaborate-to-deliver-cost-monitoring-for-eks-customers/) which estimate resource requests and limits for your containers. Depending on the nature of the applications, performance/cost requirements, and complexity you need to evaluate which metrics are best to scale on, at what point your application performance degrades (saturation point), and how to tweak request and limits accordingly. Please refer to [Application right sizing](https://aws.github.io/aws-eks-best-practices/scalability/docs/node_efficiency/#application-right-sizing) for further guidance on this topic.

We recommend using the Horizontal Pod Autoscaler (HPA) to control how many replicas of your application should be running, the Vertical Pod Autoscaler (VPA) to adjust how many requests and limits your application needs per replica, and a node autoscaler like [Karpenter](http://karpenter.sh/) or [Cluster Autoscaler](https://github.com/kubernetes/autoscaler) to continually adjust the total number of nodes in your cluster. Cost optimization techniques using Karpenter and Cluster Autoscaler are documented in a later section of this document.

The Vertical Pod Autoscaler can adjust the requests and limits assigned to containers so workloads run optimally. You should run the VPA in auditing mode so it does not automatically make changes and restart your pods. It will suggest changes based on observed metrics. With any changes that affect production workloads you should review and test those changes first in a non-production environment because these can have impact on your application’s reliability and performance.

## Reduce consumption

The best way to save money is to provision fewer resources. One way to do that is to adjust workloads based on their current requirements. You should start any cost optimization efforts with making sure your workloads define their requirements and scale dynamically. This will require getting metrics from your applications and setting configurations such as [`PodDisruptionBudgets`](https://kubernetes.io/docs/tasks/run-application/configure-pdb/) and [Pod Readiness Gates](https://kubernetes-sigs.github.io/aws-load-balancer-controller/v2.5/deploy/pod_readiness_gate/) to make sure your application can safely scale up and down dynamically. Its important to consider that restrictive PodDisruptionBudgets can prevent Cluster Autoscaler and Karpenter from scaling down Nodes, since both Cluster Autoscaler and Karpenter respect PodDisruptionBudgets. The 'minAvailable' value in the PodDisruptionBudget should always be lower than the number of pods in the deployment and you should keep a good buffer between the two e.g. In a deployment of 6 pods where you want a minimum of 4 pods running at all times, set the 'minAvailable' in your PodDisruptionBidget to 4. This will allow Cluster Autoscaler and Karpenter to safely drain and evict pods from the under-utilized nodes during a Node scale-down event. Please refer to [Cluster Autoscaler FAQ](https://github.com/kubernetes/autoscaler/blob/master/cluster-autoscaler/FAQ.md#what-types-of-pods-can-prevent-ca-from-removing-a-node) doc.

The Horizontal Pod Autoscaler is a flexible workload autoscaler that can adjust how many replicas are needed to meet the performance and reliability requirements of your application. It has a flexible model for defining when to scale up and down based on various metrics such as CPU, memory, or custom metrics e.g. queue depth, number of connections to a pod, etc.

The Kubernetes Metrics Server enables scaling in response to built-in metrics like CPU and memory usage, but if you want to scale based on other metrics, such as Amazon CloudWatch or SQS queue depth, you should consider event driven autoscaling projects such as [KEDA](https://keda.sh/). Please refer to [this blog post](https://aws.amazon.com/blogs/mt/proactive-autoscaling-of-kubernetes-workloads-with-keda-using-metrics-ingested-into-amazon-cloudwatch/) on how to use KEDA with CloudWatch metrics. If you are unsure, which metrics to monitor and scale based on, check out the [best practices on monitoring metrics that matters](https://aws-observability.github.io/observability-best-practices/guides/#monitor-what-matters).


Reducing workload consumption creates excess capacity in a cluster and with proper autoscaling configuration allows you to scale down nodes automatically and reduce your total spend. We recommend you do not try to optimize compute capacity manually. The Kubernetes scheduler and node autoscalers were designed to handle this process for you.

## Reduce unused capacity

After you have determined the correct size for applications, reducing excess requests, you can begin to reduce the provisioned compute capacity. You should be able to do this dynamically if you have taken the time to correctly size your workloads from the sections above. There are two primary node autoscalers used with Kubernetes in AWS.

### Karpenter and Cluster Autoscaler

Both Karpenter and the Kubernetes Cluster Autoscaler will scale the number of nodes in your cluster as pods are created or removed and compute requirements change. The primary goal of both is the same, but Karpenter takes a different approach for node management provisioning and de-provisioning which can help reduce costs and optimize cluster wide usage.

As clusters grow in size and the variety of workloads increases it becomes more difficult to pre-configure node groups and instances. Just like with workload requests it’s important to set an initial baseline and continually adjust as needed.

If you are using Cluster Autoscaler, it will respect the "minimum" and "maximum" values of each Auto Scaling group (ASG) and only adjust the "desired" value. It's important to pay attention while setting these values for the underlying ASG since Cluster Autoscaler will not be able to scale down an ASG beyond its "minimum" count. Set the "desired" count as the number of nodes you need during normal business hours and "minimum" as the number of nodes you need during off-business hours. Please refer to [Cluster Autoscaler FAQ](https://github.com/kubernetes/autoscaler/blob/master/cluster-autoscaler/cloudprovider/aws/README.md#auto-discovery-setup) doc.

### Cluster Autoscaler Priority Expander

The Kubernetes Cluster Autoscaler works by scaling groups of nodes — called a node group — up and down as applications scale up and down. If you are not dynamically scaling workloads then the Cluster Autoscaler will not help you save money. The Cluster Autoscaler requires a cluster admin to create node groups ahead of time for workloads to consume. The node groups need to configured to use instances that have the same "profile", i.e. roughly the same amount of CPU and memory.

You can have multiple node groups and the Cluster Autoscaler can be configured to set priority scaling levels and each node group can contain different sized nodes. Node groups can have different capacity types and the priority expander can be used to scale less expensive groups first.

Below is an example of a snippet of cluster configuration that uses a `ConfigMap`` to prioritize reserved capacity before using on-demand instances.  You can use the same technique to prioritize Graviton or Spot Instances over other types.  

```yaml
apiVersion: eksctl.io/v1alpha5
kind: ClusterConfig
metadata:
  name: my-cluster
managedNodeGroups:
  - name: managed-ondemand
    minSize: 1
    maxSize: 7
    instanceType: m5.xlarge
  - name: managed-reserved
    minSize: 2
    maxSize: 10
    instanceType: c5.2xlarge
```

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: cluster-autoscaler-priority-expander
  namespace: kube-system
data:
  priorities: |-
    10:
      - .*ondemand.*
    50:
      - .*reserved.*
```

Using node groups can help the underlying compute resources do the expected thing by default, e.g. spread nodes across AZs, but not all workloads have the same requirements or expectations and it’s better to let applications declare their requirements explicitly. For more information about Cluster Autoscaler, please see the [best practices section](https://aws.github.io/aws-eks-best-practices/cluster-autoscaling/).

### Descheduler

The Cluster Autoscaler can add and remove node capacity from a cluster based on new pods needing to be scheduled or nodes being underutilized. It does not take a wholistic view of pod placement after it has been scheduled to a node. If you are using the Cluster Autoscaler you should also look at the [Kubernetes descheduler](https://github.com/kubernetes-sigs/descheduler) to avoid wasting capacity in your cluster.

If you have 10 nodes in a cluster and each node is 60% utilized you are not using 40% of the provisioned capacity in the cluster. With the Cluster Autoscaler you can set the utilization threashold per node to 60%, but that would only try to scale down a single node after utilization dropped below 60%.

With the descheduler it can look at cluster capacity and utilization after pods have been scheduled or nodes have been added to the cluster. It attempts to keep the total capacity of the cluster above a specified threshold. It can also remove pods based on node taints or new nodes that join the cluster to make sure pods are running in their optimal compute environment. Note that, descheduler does not schedule replacement of evicted pods but relies on the default scheduler for that.

### Karpenter Consolidation

Karpenter takes a “groupless” approach to node management. This approach is more flexible for different workload types and requires less up front configuration for cluster administrators. Instead of pre-defining groups and scaling each group as workloads need, Karpenter uses provisioners and node templates to define broadly what type of EC2 instances can be created and settings about the instances as they are created.

Bin packing is the practice of utilizing more of the instance’s resources by packing more workloads onto fewer, optimally sized, instances. While this helps to reduce your compute costs by only provisioning resources your workloads use, it has a trade-off. It can take longer to start new workloads because capacity has to be added to the cluster, especially during large scaling events. Consider the balance between cost optimization, performance, and availability when setting up bin packing. 

Karpenter can continuously monitor and binpack to improve instance resource utilization and lower your compute costs. Karpenter can also select a more cost efficient worker node for your workload. This can be achieved by turning on “consolidation” flag to true in the provisioner (sample code snippet below).  The example below shows an example provisioner that enables consolidation. At the time of writing this guide, Karpenter won’t replace a running Spot instance with a cheaper Spot instance. For further details on Karpenter consolidation, refer to [this blog](https://aws.amazon.com/blogs/containers/optimizing-your-kubernetes-compute-costs-with-karpenter-consolidation/).  

```yaml
apiVersion: karpenter.sh/v1alpha5
kind: Provisioner
metadata:
  name: enable-binpacking
spec:
  consolidation:
    enabled: true
```

For workloads that might not be interruptible e.g. long running batch jobs without checkpointing, consider annotating pods with the `do-not-evict` annotation. By opting pods out of eviction, you are telling Karpenter that it should not voluntarily remove nodes containing this pod. However, if a `do-not-evict` pod is added to a node while the node is draining, the remaining pods will still evict, but that pod will block termination until it is removed. In either case, the node will be cordoned to prevent additional work from being scheduled on the node. Below is an example showing how set the annotation:

```yaml hl_lines="8"
apiVersion: v1
kind: Pod
metadata:
  name: label-demo
  labels:
    environment: production
  annotations:  
    "karpenter.sh/do-not-evict": "true"
spec:
  containers:
  - name: nginx
    image: nginx
    ports:
    - containerPort: 80
```

### Remove under-utilized nodes by adjusting Cluster Autoscaler parameters

Node utilization is defined as the sum of requested resources divided by capacity. By default `scale-down-utilization-threshold` is set to 50%. This parameter can be used along with and `scale-down-unneeded-time`, which determines how long a node should be unneeded before it is eligible for scale down — the default is 10 minutes. Pods still running on a node that was scaled down will get scheduled on other nodes by kube-scheduler.  Adjusting these settings can help remove nodes that are underutilized, but it’s important you test these values first so you don’t force the cluster to scale down prematurely.

You can prevent scale down from happening by ensuring that pods that are expensive to evict are protected by a label recognized by the Cluster Autoscaler. To do this, ensure that pods that are expensive to evict have the annotation `cluster-autoscaler.kubernetes.io/safe-to-evict=false`. Below is an example yaml to set the annotation:

```yaml hl_lines="8"
apiVersion: v1
kind: Pod
metadata:
  name: label-demo
  labels:
    environment: production
  annotations:  
    "cluster-autoscaler.kubernetes.io/safe-to-evict": "false"
spec:
  containers:
  - name: nginx
    image: nginx
    ports:
    - containerPort: 80
```

### Tag nodes with Cluster Autoscaler and Karpenter

AWS resource [tags](https://docs.aws.amazon.com/tag-editor/latest/userguide/tagging.html) are used to organize your resources, and to track your AWS costs on a detailed level. They do not directly correlate with Kubernetes labels for cost tracking. It’s recommended to start with Kubernetes resource labeling and utilize tools like [Kubecost](https://aws.amazon.com/blogs/containers/aws-and-kubecost-collaborate-to-deliver-cost-monitoring-for-eks-customers/) to get infrastructure cost reporting based on Kubernetes labels on pods, namespaces etc.

Worker nodes need to have tags to show billing information in AWS Cost Explorer. With Cluster Autoscaler, tag your worker nodes inside a managed node group using [launch template](https://docs.aws.amazon.com/eks/latest/userguide/launch-templates.html). For self managed node groups, tag your instances using [EC2 auto scaling group](https://docs.aws.amazon.com/autoscaling/ec2/userguide/ec2-auto-scaling-tagging.html). For instances provisioned by Karpenter, tag them using [spec.tags in the node template](https://karpenter.sh/docs/concepts/nodeclasses/#spectags).

### Multi-tenant clusters

When working on clusters that are shared by different teams you may not have visibility to other workloads running on the same node. While resource requests can help isolate some “noisy neighbor” concerns, such as CPU sharing, they may not isolate all resource boundaries such as disk I/O exhaustion. Not every consumable resource by a workload can be isolated or limited. Workloads that consume shared resources at higher rates than other workloads should be isolated through node [taints and tolerations](https://kubernetes.io/docs/concepts/scheduling-eviction/taint-and-toleration/). Another advanced technique for such workload is [CPU pinning](https://kubernetes.io/docs/tasks/administer-cluster/cpu-management-policies/#static-policy) which ensures exclusive CPU instead of shared CPU for the container.

Isolating workloads at a node level can be more expensive, but it may be possible to schedule [BestEffort](https://kubernetes.io/docs/concepts/workloads/pods/pod-qos/#besteffort) jobs or take advantage of additional savings by using [Reserved Instances](https://aws.amazon.com/ec2/pricing/reserved-instances/), [Graviton processors](https://aws.amazon.com/ec2/graviton/), or [Spot](https://aws.amazon.com/ec2/spot/).

Shared clusters may also have cluster level resource constraints such as IP exhaustion, Kubernetes service limits, or API scaling requests. You should review the [scalability best practices guide](https://aws.github.io/aws-eks-best-practices/scalability/docs/control-plane/) to make sure your clusters avoid these limits.

You can isolate resources at a namespace or Karpenter provisioner level. [Resource Quotas](https://kubernetes.io/docs/concepts/policy/resource-quotas/) provide a way to set limits on how many resources workloads in a namespace can consume. This can be a good initial guard rail but it should be continually evaluated to make sure it doesn’t artificially restrict workloads from scaling.

Karpenter provisioners can [set limits on some of the consumable resources](https://karpenter.sh/docs/concepts/nodepools/#speclimitsresources) in a cluster (e.g. CPU, GPU), but you will need to configure tenant applications to use the appropriate provisioner. This can prevent a single provisioner from creating too many nodes in a cluster, but it should be continually evaluated to make sure the limit isn’t set too low and in turn, prevent workloads from scaling.

### Scheduled Autoscaling

You may have the need to scale down your clusters on weekends and off hours. This is particularly relevant for test and non-production clusters where you want to scale down to zero when they are not in use. Solutions like [cluster-turndown](https://github.com/kubecost/cluster-turndown) and [kube-downscaler](https://codeberg.org/hjacobs/kube-downscaler) can scale down the replicas to zero based on a cron schedule.    

## Optimize compute capacity types

After optimizing the total capacity of compute in your cluster and utilizing bin packing, you should look at what type of compute you have provisioned in your clusters and how you pay for those resources. AWS has [Compute Savings plans](https://aws.amazon.com/savingsplans/compute-pricing/) that can reduce the cost for your compute which we will categorize into the following capacity types:

* Spot
* Savings Plans
* On-Demand
* Fargate

Each capacity type has different trade-offs for management overhead, availability, and long term commitments and you will need to decide which is right for your environment. No environment should rely on a single capacity type and you can mix multiple run types in a single cluster to optimize specific workload requirements and cost.

### Spot

The [spot](https://aws.amazon.com/ec2/spot/) capacity type provisions EC2 instances from spare capacity in an Availability Zone. Spot offers the largest discounts—up to 90% — but those instances can be interrupted when they are needed elsewhere. Additionally, there may not always be capacity to provision new Spot instances and existing Spot instances can be reclaimed with a [2 minute interruption notice](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/spot-interruptions.html). If your application has a long startup or shutdown process, Spot instances may not be the best option.

Spot compute should use a wide variety of instance types to reduce the likelihood of not having spot capacity available. Instance interruptions need to be handled to safely shutdown nodes. Nodes provisioned with Karpenter or part of a Managed Node Group automatically support [instance interruption notifications](https://aws.github.io/aws-eks-best-practices/karpenter/#enable-interruption-handling-when-using-spot). If you are using self-managed nodes you will need to run the [node termination handler](https://github.com/aws/aws-node-termination-handler) separately to gracefully shutdown spot instances.

It is possible to balance spot and on-demand instances in a single cluster. With Karpenter you can create [weighted provisioners](https://karpenter.sh/docs/concepts/scheduling/#on-demandspot-ratio-split) to achieve a balance of different capacity types. With Cluster Autoscaler you can create [mixed node groups with spot and on-demand or reserved instances](https://aws.amazon.com/blogs/containers/amazon-eks-now-supports-provisioning-and-managing-ec2-spot-instances-in-managed-node-groups/).

Here is an example of using Karpenter to prioritize Spot instances ahead of On-Demand instances. When creating a provisioner, you can specify either Spot, On-Demand, or both (as shown below). When you specify both, and if the pod does not explicitly specify whether it needs to use Spot or On-Demand, then Karpenter prioritizes Spot when provisioning a node with [price-capacity-optimization allocation strategy](https://aws.amazon.com/blogs/compute/introducing-price-capacity-optimized-allocation-strategy-for-ec2-spot-instances/) .

```yaml hl_lines="9"
apiVersion: karpenter.sh/v1alpha5
kind: Provisioner
metadata:
  name: spot-prioritized
spec:
  requirements:
    - key: "karpenter.sh/capacity-type" 
      operator: In
        values: ["spot", "on-demand"]
```

### Savings Plans, Reserved Instances, and AWS EDP

You can reduce your compute spend by using a [compute savings plan](https://aws.amazon.com/savingsplans/compute-pricing/). Savings plans offer reduced prices for a 1 or 3 year commitment of compute usage. The usage can apply to EC2 instances in an EKS cluster but also applies to any compute usage such as Lambda and Fargate. With savings plans you can reduce costs and still pick any EC2 instance type during your commitment period.

Compute savings plan can reduce your EC2 cost by up to 66% without requiring commitments on what instance types, families, or regions you want to use. Savings are automatically applied to instances as you use them.

EC2 Instance Savings Plans provides up to 72% savings on compute with a commitment of usage in a specific region and EC2 family, e.g. instances from the C family. You can shift usage to any AZ within the region, use any generation of the instance family, e.g. c5 or c6, and use any size of instance within the family. The discount will automatically be applied for any instance in your account that matches the savings plan criteria.

[Reserved Instances](https://aws.amazon.com/ec2/pricing/reserved-instances/) are similar to EC2 Instance Savings Plan but they also guarantee capacity in an Availability Zone or Region and reduce cost—up to 72% — over on-demand instances. Once you calculate how much reserved capacity you will need you can select how long you would like to reserve them for (1 year or 3 years). The discounts will automatically be applied as you run those EC2 instances in your account.

Customers also have the option to enroll in an Enterprise Agreement with AWS. Enterprise Agreements give customers the option to tailor agreements that best suit their needs. Customers can enjoy discounts on the pricing based on AWS EDP (Enterprise Discount Program). For additional information on Enterprise Agreements please contact your AWS sales representative. 

### On-Demand

On-Demand EC2 instances have the benefit of availability without interruptions — compared to spot — and no long term commitments — compared to savings plans. If you are looking to reduce costs in a cluster you should reduce your usage of on-demand EC2 instances.

After optimizing your workload requirements you should be able to calculate a minimum and maximum capacity for your clusters. This number may change over time but rarely goes down. Consider using a Savings Plan for everything under the minimum, and spot for capacity that will not affect your application’s availability. Anything else that may not be continuously used or is required for availability can use on-demand.

As mentioned in this section, the best way to reduce your usage is to consume fewer resources and utilize the resources you provision to the fullest extent possible. With the Cluster Autoscaler you can remove underutilized nodes with the `scale-down-utilization-threshold` setting. With Karpenter it is recommended to enable consolidation.

To manually identify EC2 instance types that can be used with your workloads you should use [ec2-instance-selector](https://github.com/aws/amazon-ec2-instance-selector) which can show instances that are available in each region as well as instances compatible with EKS. Example usage for instances with x86 process architecture, 4 Gb of memory, 2 vCPUs and available in the us-east-1 region.

```bash
ec2-instance-selector --memory 4 --vcpus 2 --cpu-architecture x86_64 \
  -r us-east-1 --service eks
c5.large
c5a.large
c5ad.large
c5d.large
c6a.large
c6i.large
t2.medium
t3.medium
t3a.medium
```

For non-production environments you can automatically have clusters scaled down during unused hours such as night and weekends. The kubecost project [cluster-turndown](https://github.com/kubecost/cluster-turndown) is an example of a controller that can automatically scale your cluster down based on a set schedule.

### Fargate compute

Fargate compute is a fully managed compute option for EKS clusters. It provides pod isolation by scheduling one pod per node in a Kubernetes cluster. It allows you to size your compute nodes to the CPU and RAM requirements of your workload to tightly control workload usage in a cluster.

Fargate can scale workloads as small as .25 vCPU with 0.5 GB memory and as large as 16 vCPU with 120 GB memory. There are limits on how many [pod size variations](https://docs.aws.amazon.com/eks/latest/userguide/fargate-pod-configuration.html) are available and you will need to understand how your workload best fits into a Fargate configuration. For example, if your workload requires 1 vCPU with 0.5 GB of memory the smallest Fargate pod will be 1 vCPU with 2 GB of memory.

While Fargate has many benefits such as no EC2 instance or operating system management, it may require more compute capacity than traditional EC2 instances due to the fact that every deployed pod is isolated as a separate node in the cluster. This requires more duplication for things like the Kubelet, logging agents, and any DaemonSets you would typically deploy to a node. DaemonSets are not supported in Fargate and they will need to be converted into pod “sidecars“ and run alongside the application.

Fargate cannot benefit from bin packing or CPU over provisioning because the boundary for the workload is a node which is not burstable or shareable between workloads. Fargate will save you EC2 instance management time which itself has a cost, but CPU and memory costs may be more expensive than other EC2 capacity types. Fargate pods can take advantage of compute savings plan to reduce the on-demand cost.

## Optimize Compute Usage

Another way to save money on your compute infrastructure is to use more efficient compute for the workload. This can come from more performant general purpose compute like [Graviton processors](https://aws.amazon.com/ec2/graviton/) which are up to 20% cheaper and 60% more energy efficient than x86—or workload specific accelerators such as GPUs and [FPGAs](https://aws.amazon.com/ec2/instance-types/f1/). You will need to build containers that can [run on arm architecture](https://aws.amazon.com/blogs/containers/how-to-build-your-containers-for-arm-and-save-with-graviton-and-spot-instances-on-amazon-ecs/) and [set up nodes with the right accelerators](https://aws.amazon.com/blogs/compute/running-gpu-accelerated-kubernetes-workloads-on-p3-and-p2-ec2-instances-with-amazon-eks/) for your workloads.

EKS has the ability to run clusters with mixed architecture (e.g. amd64 and arm64) and if your containers are compiled for multiple architectures you can take advantage of Graviton processors with Karpenter by allowing both architectures in your provisioner. To keep consistent performance, however, it is recommended you keep each workload on a single compute architecture and only use different architecture if there is no additional capacity available.

Provisioners can be configured with multiple architectures and workloads can also request specific architectures in their workload specification.

```yaml
apiVersion: karpenter.sh/v1alpha5
kind: Provisioner
metadata:
  name: default
spec:
  requirements:
  - key: "kubernetes.io/arch"
    operator: In
    values: ["arm64", "amd64"]
```

With Cluster Autoscaler you will need to create a node group for Graviton instances and set [node tolerations on your workload](https://kubernetes.io/docs/concepts/scheduling-eviction/taint-and-toleration/) to utilize the new capacity.

GPUs and FPGAs can greatly increase the performance for your workload, but the workload will need to be optimized to use the accelerator. Many workload types for machine learning and artificial intelligence can use GPUs for compute and instances can be added to a cluster and mounted into a workload using resource requests.

```yaml
spec:
  template:
    spec:
    - containers:
      ...
      resources:
          limits:
            nvidia.com/gpu: "1"
```

Some GPU hardware can be shared across multiple workloads so a single GPU can be provisioned and used. To see how to configure workload GPU sharing see the [virtual GPU device plugin](https://aws.amazon.com/blogs/opensource/virtual-gpu-device-plugin-for-inference-workload-in-kubernetes/) for more information. You can also refer to the following blogs: 

* [GPU sharing on Amazon EKS with NVIDIA time-slicing and accelerated EC2 instances](https://aws.amazon.com/blogs/containers/gpu-sharing-on-amazon-eks-with-nvidia-time-slicing-and-accelerated-ec2-instances/)
* [Maximizing GPU utilization with NVIDIA’s Multi-Instance GPU (MIG) on Amazon EKS: Running more pods per GPU for enhanced performance](https://aws.amazon.com/blogs/containers/maximizing-gpu-utilization-with-nvidias-multi-instance-gpu-mig-on-amazon-eks-running-more-pods-per-gpu-for-enhanced-performance/)
