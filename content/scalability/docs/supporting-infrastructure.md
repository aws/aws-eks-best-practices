# Supporting Infrastructure

Supporting infrastructure is resources outside of your cluster but required for your workloads to run. It includes EC2 instances, load balancers, external storage, and other APIs used by the Kubernetes control plane. For simplicity, we won’t address APIs that workloads use because that could be every API.

Helping EKS clusters scale to large sizes requires using the supporting infrastructure wisely. There are multiple areas you need to consider in planning before they become a problem. The main concerns are for compute availability and network routing.

## EC2 instances

Selecting your EC2 instance types is possibly one of the hardest decisions customers face because in clusters with multiple different workloads there is no one-size-fits all solution. Here are some tips to help you avoid common pitfalls.

## Use Karpenter for node autoscaling

[Karpenter](https://karpenter.sh/) is a workload-native node autoscaler created by AWS. It can scale nodes in a cluster based on the workload requirements for resources (e.g. GPU) and taints and tolerations (e.g. zone spread) without needing to manage node groups for each workload requirement. Nodes are created directly from EC2 instead of using Auto Scaling Groups (ASG) which avoids default node group quotas—450 nodes per group—and provides greater instance selection flexibility with less operational overhead.

We highly recommend customers use Karpenter when possible. It optimizes clusters for cost and scalability and has many features that were built to help customers reduce operational overhead and increase cluster scalability.

## Use many different EC2 instance types

Each AWS region has a limited number of available instances per instance type. If you create a cluster that uses only one instance type and scale the number of nodes beyond the capacity of the region you will receive an error that no instances are available. To avoid this issue you should not arbitrarily limit the type of instances that can be use in your cluster.

Karpenter will use a broad set of compatible instance types by default and will pick an instance at provisioning time based on pending workload requirements, availability, and cost. You can broaden the list of instance types used in the `karpenter.k8s.aws/instance-category` key of [the provisioner](https://karpenter.sh/v0.20.0/concepts/provisioning/).

The Kubernetes Cluster Autoscaler requires node groups to be similarly sized so they can be consistently scaled. You should create multiple groups based on CPU and memory size and scale them independently. Use the [ec2-instance-selector](https://github.com/aws/amazon-ec2-instance-selector) to identify instances that are similarly sized for your node groups.

```
ec2-instance-selector --service eks --vcpus-min 8 --memory-min 16
a1.2xlarge
a1.4xlarge
a1.metal
c4.4xlarge
c4.8xlarge
c5.12xlarge
c5.18xlarge
c5.24xlarge
c5.2xlarge
c5.4xlarge
c5.9xlarge
c5.metal
```

## Prefer larger nodes to reduce control plane load

When deciding what instance types to use, fewer large nodes will put less load on the Kubernetes control plane because there will be fewer kubelets and DaemonSets running. However, large nodes may not be utilized the same as smaller nodes depending on your workloads. Node sizes should be evaluated based on your workload availability and scale requirements.

If you run a cluster with three u-24tb1.metal instances (24 TB memory and 448 cores) you would have 3 kublets, but you would be limited to 110 pods per node by default. If your pods use 4 cores each then this might be expected (4 cores x 110 = 440 cores/node). With a 3 node cluster your ability to handle an instance incident would be low. You should specify node requirements and pod spread directly in your workloads so the Kubernetes scheduler can place workloads properly and Karpenter can provision the best node.

Workloads should define the resources they need and the availability required via taints, tolerations, and [PodTopologySpread](https://kubernetes.io/blog/2020/05/introducing-podtopologyspread/). They should prefer the largest nodes that can be fully utilized and meet availability goals to reduce control plane load, lower operations, and reduce cost.

The Kubernetes Scheduler will automatically try to spread workloads across zones and hosts if resources are available. The Kubernetes Cluster Autoscaler will attempt to add nodes in each Availability Zone evenly. Karpenter will not spread nodes or pods by default. To force workloads to spread you should use topologySpreadConstraints:

```
spec:
  topologySpreadConstraints:
    - maxSkew: 3
      topologyKey: "topology.kubernetes.io/zone"
      whenUnsatisfiable: ScheduleAnyway
      labelSelector:
        matchLabels:
          dev: my-deployment
    - maxSkew: 2
      topologyKey: "kubernetes.io/hostname"
      whenUnsatisfiable: ScheduleAnyway
      labelSelector:
        matchLabels:
          dev: my-deployment
```

## Avoid instances with burstable CPUs

Avoid instance types that use burstable CPUs like T series instances. Workloads should define what size nodes they need to be run on to allow consistent performance and predictable scaling. A workload requesting 500m CPU will perform differently on an instance with 4 cores vs one with 16 cores.

A workload being scheduled in a cluster with Karpenter can use the [supported labels](https://karpenter.sh/v0.19.3/tasks/scheduling/#supported-labels) to target specific instances sizes.

```
kind: deployment
...
spec:
  template:
    spec:
    containers:
    nodeSelector:
      karpenter.k8s.aws/instance-size: 8xlarge
```

Workloads being scheduled in a cluster with the Kubernetes Cluster Autoscaler should match a node selector to node groups based on label matching.

```
spec:
  affinity:
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
        - matchExpressions:
          - key: eks.amazonaws.com/nodegroup
            operator: In
            values:
            - 8-core-node-group    # match your node group name
```

## Avoid instances with low EBS attach limits if workloads use EBS volumes

EBS is one of the easiest ways for workloads to have persistent storage, but it also comes with scalability limitations. Each instance type has a maximum number of [EBS volumes that can be attached](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/volume_limits.html). Workloads need to declare what instance types they should run on and limit the number of replicas on a single instance with Kubernetes taints.

EBS volumes are only available within a single Availability Zone (AZ). Workloads that consume a volume will be limited to run within the AZ where the volume is available. If you ‘re using node groups you will need to add AZ specific tolerations to your workload definition after the volume has been created. If you are using Karpenter, nodes will automatically be provisioned in the correct AZ where the volume was created.

## Use compute resources efficiently

Compute resources include EC2 instances and availability zones. Using compute resources effectively will increase your scalability, availability, performance, and reduce your total cost. Predicting what instance types your cluster will need is an extremely difficult problem which is why we recommend not trying to predict every use case when you create a cluster. Instead of predicting and creating node groups you should use [Karpenter](https://karpenter.sh/) to provision workload instances on-demand based on the workload needs.

Karpenter allows you to take advantage of all EKS compatible EC2 instance types as well as their different capacity types (e.g. on-demand, spot). This allows workloads to declare the type of compute resources it needs without first creating node groups or configuring label taints only for specific workloads. Please see the [Karpenter best practices](https://aws.github.io/aws-eks-best-practices/karpenter/) for more information.

Review the guide for setting up [highly-available applications](https://aws.github.io/aws-eks-best-practices/reliability/docs/application/) to make sure you have enough replicas to handle incidents.

## Split large services into multiple load balancers

Depending on the size of your services you can share a single ALB with multiple services. The [AWS Load Balancer Controller](https://github.com/kubernetes-sigs/aws-load-balancer-controller/) has configuration available to expose services with multiple load balancers. You will need to create multiple load balancers for services that exceed the target group limits for a single load balancer.

To make a service using multiple load balancers available as a single endpoint you need to use [Amazon CloudFront](https://aws.amazon.com/cloudfront/), [AWS Global Accelerator](https://aws.amazon.com/global-accelerator/), or [Amazon Route 53](https://aws.amazon.com/route53/) to expose all of the load balancers as a single, customer facing endpoint. Each options has different benefits and can be used separately or together depending on your needs.

Route 53 can expose multiple load balancers under a common name and can send traffic to each of them based on the weight assigned. You can read more about [DNS weights in the documentation](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/resource-record-sets-values-weighted.html#rrsets-values-weighted-weight) and you can read how to implement them with the [Kubernetes external DNS controller](https://github.com/kubernetes-sigs/external-dns) in the [AWS Load Balancer Controller documentation](https://kubernetes-sigs.github.io/aws-load-balancer-controller/v2.4/guide/integrations/external_dns/#usage).

Global Accelerator can route workloads to the nearest region based on request IP address. This may be useful for workloads that are deployed to multiple regions, but it does not improve routing to a single cluster in a single region. Using Route 53 in combination with the Global Accelerator has additional benefits such as health checking and automatic failover if an AZ is not available. You can see an example of using Global Accelerator with Route 53 in [this blog post](https://aws.amazon.com/blogs/containers/operating-a-multi-regional-stateless-application-using-amazon-eks/).

CloudFront can be use with Route 53 and Global Accelerator or by itself to route traffic to multiple destinations. CloudFront caches assets being served from the origin sources which may reduce bandwidth requirements depending on what you are serving.

## Use AWS Systems Manager Patch Manager to automate patching nodes

To patch a Linux host it takes seconds to install a package which can be run in parallel without disrupting containerized workloads. The package can be installed and validated without cordoning, draining, or replacing the instance.

To replace an instance you first need to create, validate, and distribute new AMIs. The instance needs to have a replacement created, and the old instance needs to be cordoned and drained. Then workloads need to be created on the new instance, verified, and repeated for all instances that need to be patched. It takes hours, days, or weeks to replace all instances in a large cluster safely without disrupting workloads.

Amazon recommends using immutable infrastructure that is built, tested, and promoted from an automated, declarative system, but if you have clusters larger than 300 nodes and you have a requirement to patch systems in 24 hours or less then you will likely need to patch existing systems in place. Because of the large time differential between patching and replacing systems we recommend using [AWS Systems Manager Patch Manager](https://docs.aws.amazon.com/systems-manager/latest/userguide/systems-manager-patch.html) to automate patching nodes when required to do so. This will allow you to quickly roll out security updates and replace the instances on a regular schedule after your base AMI has been patched. If you are using Bottlerocket we recommend using the [Bottlerocket update operator](https://github.com/bottlerocket-os/bottlerocket-update-operator) to keep your nodes up to date.

Replacing nodes in a cluster can take days or weeks depending on how many instances you replace at once. With managed node groups you can increase the number of nodes to replace at once in the [node group configuration](https://docs.aws.amazon.com/eks/latest/userguide/update-managed-node-group.html). With Karpenter you should use *ttlSecondsUntilExpired* to make sure nodes are regularly replaced. If you are performing cluster upgrades with thousands of nodes it is advised to upgrade your control plane and then use node cycling replace and upgrade your worker nodes.
