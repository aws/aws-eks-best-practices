# Karpenter Best Practices

## Karpenter

Karpenter is an open-source cluster autoscaler that automatically provisions new nodes in response to unschedulable pods. Karpenter evaluates the aggregate resource requirements of the pending pods and chooses the optimal instance type to run them. It will automatically scale-in or terminate instances that don’t have any non-daemonset pods to reduce waste. It also supports a consolidation feature which will actively move pods around and either delete or replace nodes with cheaper versions to reduce cluster cost.

**Reasons to use Karpenter**

Before the launch of Karpenter, Kubernetes users relied primarily on [Amazon EC2 Auto Scaling groups](https://docs.aws.amazon.com/autoscaling/ec2/userguide/AutoScalingGroup.html) and the [Kubernetes Cluster Autoscaler](https://github.com/kubernetes/autoscaler/tree/master/cluster-autoscaler) (CAS) to dynamically adjust the compute capacity of their clusters. With Karpenter, you don’t need to create dozens of node groups to achieve the flexibility and diversity you get with Karpenter. Moreover, Karpenter is not as tightly coupled to Kubernetes versions (as CAS is) and doesn’t require you to jump between AWS and Kubernetes APIs.

Karpenter consolidates instance orchestration responsibilities within a single system, which is simpler, more stable and cluster-aware. Karpenter was designed to overcome some of the challenges presented by Cluster Autoscaler by providing simplified ways to:

* Provision nodes based on workload requirements.
* Create diverse node configurations by instance type, using flexible workload provisioner options. Instead of managing many specific custom node groups, Karpenter could let you manage diverse workload capacity with a single, flexible provisioner.
* Achieve improved pod scheduling at scale by quickly launching nodes and scheduling pods.

For information and documentation on using Karpenter, visit the [karpenter.sh](https://karpenter.sh/) site.

## Recommendations

Best practices are divided into sections on Karpenter itself, provisioners, and pod scheduling.

## Karpenter best practices

The following best practices cover topics related to Karpenter itself.

### Use Karpenter for workloads with changing capacity needs

Karpenter brings scaling management closer to Kubernetes native APIs than do [Autoscaling Groups](https://aws.amazon.com/blogs/containers/amazon-eks-cluster-multi-zone-auto-scaling-groups/) (ASGs) and [Managed Node Groups](https://docs.aws.amazon.com/eks/latest/userguide/managed-node-groups.html) (MNGs). ASGs and MNGs are AWS-native abstractions where scaling is triggered based on AWS level metrics, such as EC2 CPU load. [Cluster Autoscaler](https://docs.aws.amazon.com/eks/latest/userguide/autoscaling.html#cluster-autoscaler) bridges the Kubernetes abstractions into AWS abstractions, but loses some flexibility because of that, such as scheduling for a specific availability zone.

Karpenter removes a layer of AWS abstraction to bring some of the flexibility directly into Kubernetes. Karpenter is best used for clusters with workloads that encounter periods of high, spiky demand or have diverse compute requirements. MNGs and ASGs are good for clusters running workloads that tend to be more static and consistent.  You can use a mix of dynamically and statically managed nodes, depending on your requirements.

### Consider other autoscaling projects when...

You need features that are still being developed in Karpenter. Because Karpenter is a relatively new project, consider other autoscaling projects for the time being if you have a need for features that are not yet part of Karpenter.

### Run the Karpenter controller on EKS Fargate or on a worker node that belongs to a node group

Karpenter is installed using a [Helm chart](https://karpenter.sh/v0.10.0/getting-started/). The Helm chart installs the Karpenter controller and a webhook pod as a Deployment that needs to run before the controller can be used for scaling your cluster. We recommend a minimum of one small node group with at least one worker node. As an alternative, you can run these pods on EKS Fargate by creating a Fargate profile for the `karpenter` namespace. Doing so will cause all pods deployed into this namespace to run on EKS Fargate. Do not run Karpenter on a node that is managed by Karpenter.

### Avoid using custom launch templates with Karpenter

Karpenter strongly recommends against using custom launch templates. Using custom launch templates prevents multi-architecture support, the ability to automatically upgrade nodes, and securityGroup discovery. Using launch templates may also cause confusion because certain fields are duplicated within Karpenter’s provisioners while others are ignored by Karpenter, e.g. subnets and instance types.

You can often avoid using launch templates by using custom user data and/or directly specifying custom AMIs in the AWS node template.  More information on how to do this is available at [Customer User Data and Ami](https://karpenter.sh/preview/aws/user-data/).

Granted, there may be times when you will want to use your own custom launch template, rather than using what Karpenter uses by default. The reasons to create custom launch templates may include the need to:

* Integrate with existing infrastructure.
* Meet compliance requirements.

To learn more, see [Launch Templates and Custom Images](https://karpenter.sh/preview/aws/launch-templates/) in the Karpenter documentation. For background on building custom AMIs, see [Amazon EKS AMI Build using EC2 Image Builder](https://www.sufle.io/blog/custom-amazon-eks-ami-build), [Packer scripts](https://github.com/awslabs/amazon-eks-ami), and [Create custom Amazon Linux AMIs for Amazon EKS](https://aws.amazon.com/premiumsupport/knowledge-center/eks-custom-linux-ami/).

### Exclude instance types that do not fit your workload

Consider excluding specific instances types with the [node.kubernetes.io/instance-type](http://node.kubernetes.io/instance-type) key if they are not required by workloads running in your cluster.

The following example shows how to avoid provisioning large Graviton instances.

```yaml
- key: node.kubernetes.io/instance-type
    operator: NotIn
    values:
      'm6g.16xlarge'
      'm6gd.16xlarge'
      'r6g.16xlarge'
      'r6gd.16xlarge'
      'c6g.16xlarge'
```

### Enable Interruption handling when using Spot

Since Karpenter v0.19.3 there is [native node termination handling](https://karpenter.sh/v0.21.1/concepts/deprovisioning/#interruption) baked into Karpenter that watches for upcoming involuntary interruption events that would cause disruption to your workloads such as;
- Spot Interruption Warnings
- Scheduled Change Health Events (Maintenance Events)
- Instance Terminating Events
- Instance Stopping Events

When Karpenter detects one of these events will occur to your nodes, it automatically cordons, drains, and terminates the node(s) ahead of the interruption event to give the maximum amount of time for workload cleanup prior to compute disruption. It is disadvised to use [AWS Node Termination Handler alongside Karpenter](https://karpenter.sh/v0.21.1/faq/#interruption-handling).

### **Amazon EKS private cluster without outbound internet access**

When provisioning an EKS Cluster into a VPC with no route to the internet, you have to make sure you’ve configured your environment in accordance with the private cluster [requirements](https://docs.aws.amazon.com/eks/latest/userguide/private-clusters.html#private-cluster-requirements) that appear in EKS documentation. In addition, you need to make sure you’ve created an STS VPC regional endpoint in your VPC. If not, you will see errors similar to those that appear below.

```console
ERROR controller.controller.metrics Reconciler error {"commit": "5047f3c", "reconciler group": "karpenter.sh", "reconciler kind": "Provisioner", "name": "default", "namespace": "", "error": "fetching instance types using ec2.DescribeInstanceTypes, WebIdentityErr: failed to retrieve credentials\ncaused by: RequestError: send request failed\ncaused by: Post \"https://sts.<region>.amazonaws.com/\": dial tcp x.x.x.x:443: i/o timeout"}
```

These changes are necessary in a private cluster because the Karpenter Controller uses IAM Roles for Service Accounts (IRSA). Pods configured with IRSA acquire credentials by calling the AWS Security Token Service (AWS STS) API. If there is no outbound internet access, you must create and use an ***AWS STS VPC endpoint in your VPC***.

Private clusters also require you to create a ***VPC endpoint for SSM***. When Karpenter tries to provision a new node, it queries the Launch template configs and an SSM parameter. If you do not have a SSM VPC endpoint in your VPC, it will cause the following error:

```console
INFO    controller.provisioning Waiting for unschedulable pods  {"commit": "5047f3c", "provisioner": "default"}
INFO    controller.provisioning Batched 3 pods in 1.000572709s  {"commit": "5047f3c", "provisioner": "default"}
INFO    controller.provisioning Computed packing of 1 node(s) for 3 pod(s) with instance type option(s) [c4.xlarge c6i.xlarge c5.xlarge c5d.xlarge c5a.xlarge c5n.xlarge m6i.xlarge m4.xlarge m6a.xlarge m5ad.xlarge m5d.xlarge t3.xlarge m5a.xlarge t3a.xlarge m5.xlarge r4.xlarge r3.xlarge r5ad.xlarge r6i.xlarge r5a.xlarge]        {"commit": "5047f3c", "provisioner": "default"}
ERROR   controller.provisioning Could not launch node, launching instances, getting launch template configs, getting launch templates, getting ssm parameter, RequestError: send request failed
caused by: Post "https://ssm.<region>.amazonaws.com/": dial tcp x.x.x.x:443: i/o timeout  {"commit": "5047f3c", "provisioner": "default"}
```

There is no ***VPC endpoint for the [Price List Query API](https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/using-pelong.html)***.
As a result, pricing data will go stale over time.
Karpenter gets around this by including on-demand pricing data in its binary, but only updates that data when Karpenter is upgraded.
Failed requests for pricing data will result in the following error messages:

```console
ERROR   controller.aws.pricing  updating on-demand pricing, RequestError: send request failed
caused by: Post "https://api.pricing.us-east-1.amazonaws.com/": dial tcp 52.94.231.236:443: i/o timeout; RequestError: send request failed
caused by: Post "https://api.pricing.us-east-1.amazonaws.com/": dial tcp 52.94.231.236:443: i/o timeout, using existing pricing data from 2022-08-17T00:19:52Z  {"commit": "4b5f953"}
```

In summary, to use Karpenter in a completely Private EKS Clusters, you need to create the following VPC endpoints:

```console
com.amazonaws.<region>.ec2
com.amazonaws.<region>.ecr.api
com.amazonaws.<region>.ecr.dkr
com.amazonaws.<region>.s3 – For pulling container images
com.amazonaws.<region>.sts – For IAM roles for service accounts
com.amazonaws.<region>.ssm - If using Karpenter
```

!!! note
    Karpenter (controller and webhook deployment) container images must be in or copied to Amazon ECR private or to a another private registry accessible from inside the VPC. The reason for this is that the Karpenter controller and webhook pods currently use Public ECR images. If these are not available from within the VPC, or from networks peered with the VPC, you will get Image pull errors when Kubernetes tries to pull these images from ECR public.

For further information, see [Issue 988](https://github.com/aws/karpenter/issues/988) and [Issue 1157](https://github.com/aws/karpenter/issues/1157).

## Creating provisioners

The following best practices cover topics related to creating provisioners.

### Create multiple provisioners when...

When different teams are sharing a cluster and need to run their workloads on different worker nodes, or have different OS or instance type requirements, create multiple provisioners. For example, one team may want to use Bottlerocket, while another may want to use Amazon Linux. Likewise, one team might have access to expensive GPU hardware that wouldn’t be needed by another team. Using multiple provisioners makes sure that the most appropriate assets are available to each team.

### Create provisioners that are mutually exclusive or weighted

It is recommended to create Provisioners that are either mutually exclusive or weighted to provide consistent scheduling behavior. If they are not and multiple Provisioners are matched, Karpenter will randomly choose which to use, causing unexpected results. Useful examples for creating multiple provisioners include the following:

Creating a Provisioner with GPU and only allowing special workloads to run on these (expensive) nodes:

```yaml
# Provisioner for GPU Instances with Taints
apiVersion: karpenter.sh/v1alpha5
kind: Provisioner
metadata:
  name: gpu
spec:
  requirements:
  - key: node.kubernetes.io/instance-type
    operator: In
    values:
    - p3.8xlarge
    - p3.16xlarge
  taints:
  - effect: NoSchedule
    key: nvidia.com/gpu
    value: "true"
  ttlSecondsAfterEmpty: 60
```

Deployment with toleration for the taint:

```yaml
# Deployment of GPU Workload will have tolerations defined
apiVersion: apps/v1
kind: Deployment
metadata:
  name: inflate-gpu
spec:
  ...
    spec:
      tolerations:
      - key: "nvidia.com/gpu"
        operator: "Exists"
        effect: "NoSchedule"
```

For a general deployment for another team, the provisioner spec could include nodeAffinify. A Deployment could then use nodeSelectorTerms to match `billing-team`.

```yaml
# Provisioner for regular EC2 instances
apiVersion: karpenter.sh/v1alpha5
kind: Provisioner
metadata:
  name: generalcompute
spec:
  labels:
    billing-team: my-team
  requirements:
  - key: node.kubernetes.io/instance-type
    operator: In
    values:
    - m5.large
    - m5.xlarge
    - m5.2xlarge
    - c5.large
    - c5.xlarge
    - c5a.large
    - c5a.xlarge
    - r5.large
    - r5.xlarge
```

Deployment using nodeAffinity:

```yaml
# Deployment will have spec.affinity.nodeAffinity defined
kind: Deployment
metadata:
  name: workload-my-team
spec:
  replicas: 200
  ...
    spec:
      affinity:
        nodeAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
            nodeSelectorTerms:
              - matchExpressions:
                - key: "billing-team"
                  operator: "In"
                  values: ["my-team"]
```

### Use timers (TTL) to automatically delete nodes from the cluster

You can use timers on provisioned nodes to set when to delete nodes that are devoid of workload pods or have reached an expiration time. Node expiry can be used as a means of upgrading, so that nodes are retired and replaced with updated versions. See [How Karpenter nodes are deprovisioned](https://karpenter.sh/preview/tasks/deprovisioning/#how-karpenter-nodes-are-deprovisioned) in the Karpenter documentation for information on using  **`ttlSecondsUntilExpired`** and **`ttlSecondsAfterEmpty`** to deprovision nodes.

### Avoid overly constraining the Instance Types that Karpenter can provision, especially when utilizing Spot

When using Spot, Karpenter uses the [Capacity Optimized](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-fleet-allocation-strategy.html)[Prioritized allocation strategy](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-fleet-allocation-strategy.html) to provision EC2 instances. The Capacity Optimized allocation strategy will instruct EC2 to provision instances from deeper spot pools in order to decrease the likelihood of interruption. The more instance types you allow Karpenter to utilize, the better EC2 can optimize your spot instance’s runtime. By default, Karpenter will use all Instance Types EC2 offers in the region and availability zones your cluster is deployed in. Karpenter intelligently chooses from the set of all instance types based on pending pods to make sure your pods are scheduled onto appropriately sized and equipped instances. For example, if your pod does not require a GPU, Karpenter will not schedule your pod to an EC2 instance type supporting a GPU. When you're unsure about which instance types to use, you can run the Amazon [ec2-instance-selector](https://github.com/aws/amazon-ec2-instance-selector) to generate a list of instance types that match your compute requirements. For example, the CLI takes memory vCPU, architecture, and region as input parameters and provides you with a list of EC2 instances that satisfy those constraints.

```console
$ ec2-instance-selector --memory 4 --vcpus 2 --cpu-architecture x86_64 -r ap-southeast-1
c5.large
c5a.large
c5ad.large
c5d.large
c6i.large
t2.medium
t3.medium
t3a.medium
```

You shouldn’t place too many constraints on Karpenter when using Spot instances because doing so can affect the availability of your applications. Say, for example, all of the instances of a particular type are reclaimed and there are no suitable alternatives available to replace them. Your pods will remain in a pending state until the spot capacity for the configured instance types is replenished. You can reduce the risk of insufficient capacity errors by spreading your instances across different availability zones, because spot pools are different across AZs. That said, the general best practice is to allow Karpenter to use a diverse set of instance types when using Spot.

## Scheduling Pods

The following best practices relate to deploying pods In a cluster using Karpenter for node provisioning.

### Follow EKS best practices for high availability

If you need to run highly available applications, follow general EKS best practice [recommendations](https://aws.github.io/aws-eks-best-practices/reliability/docs/application/#recommendations). See [Topology Spread](https://karpenter.sh/preview/tasks/scheduling/#topology-spread) in Karpenter documentation for details on how to spread pods across nodes and zones. Use [Disruption Budgets](https://karpenter.sh/preview/tasks/deprovisioning/#disruption-budgets) to set the minimum available pods that need to be maintained, in case there are attempts to evict or delete pods.

### Use layered Constraints to constrain the compute features available from your cloud provider

Karpenter’s model of layered constraints allows you to create a complex set of provisioner and pod deployment constraints to get the best possible matches for pod scheduling. Examples of constraints that a pod spec can request include the following:

* Needing to run in availability zones where only particular applications are available. Say, for example, you have pod that has to communicate with another application that runs on an EC2 instance residing in a particular availability zone. If your aim is to reduce cross-AZ traffic in your VPC, you may want to co-locate the pods in the AZ where the EC2 instance is located. This sort of targeting is often accomplished using node selectors. For additional information on [Node selectors](https://karpenter.sh/preview/tasks/scheduling/#node-selectors), please refer to the Kubernetes documentation.
* Requiring certain kinds of processors or other hardware. See the [Accelerators](https://karpenter.sh/v0.6.1/aws/provisioning/#accelerators-gpu) section of the Karpenter docs for a podspec example that requires the pod to run on a GPU processor.

### Create billing alarms to monitor your compute spend

When you configure your cluster to automatically scale, you should create billing alarms to warn you when your spend has exceeded a threshold and add resource limits to your Karpenter configuration. Setting resource limits with Karpenter is similar to setting an AWS autoscaling group’s maximum capacity in that it represents the maximum amount of compute resources that can be instantiated by a Karpenter provisioner.

!!! note
    It is not possible to set a global limit for the whole cluster. Limits apply to specific provisioners.

The snippet below tells Karpenter to only provision a maximum of 1000 CPU cores and 1000Gi of memory. Karpenter will stop adding capacity only when the limit is met or exceeded. When a limit is exceeded the Karpenter controller will write `memory resource usage of 1001 exceeds limit of 1000` or a similar looking message to the controller’s logs. If you are routing your container logs to CloudWatch logs, you can create a [metrics filter](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/MonitoringLogData.html) to look for specific patterns or terms in your logs and then create a [CloudWatch alarm](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/AlarmThatSendsEmail.html) to alert you when your configured metrics threshold is breached.

For further information using limits with Karpenter, see [Setting Resource Limits](https://karpenter.sh/preview/tasks/set-resource-limits/) in the Karpenter documentation.

```yaml
spec:
  limits:
    resources:
      cpu: 1000
      memory: 1000Gi
```

!!! note
    Setting GPU limits is not supported at this time.

If you don’t use limits or constrain the instance types that Karpenter can provision, Karpenter will continue adding compute capacity to your cluster as needed. While configuring Karpenter in this way allows your cluster to scale freely, it can also have significant cost implications. It is for this reason that we recommend that configuring billing alarms. Billing alarms allow you to be alerted and proactively notified when the calculated estimated charges in your account(s) exceed a defined threshold. See [Setting up an Amazon CloudWatch Billing Alarm to Proactively Monitor Estimated Charges](https://aws.amazon.com/blogs/mt/setting-up-an-amazon-cloudwatch-billing-alarm-to-proactively-monitor-estimated-charges/) for additional information.

You may also want to enable Cost Anomaly Detection which is an AWS Cost Management feature that uses machine learning to continuously monitor your cost and usage to detect unusual spends. Further information can be found in the [AWS Cost Anomaly Detection Getting Started](https://docs.aws.amazon.com/cost-management/latest/userguide/getting-started-ad.html) guide. If you’ve gone so far as to create a budget in AWS Budgets, you can also configure an action to notify you when a specific threshold has been breached. With budget actions you can send an email, post a message to an SNS topic, or send a message to a chatbot like Slack. For further information see [Configuring AWS Budgets actions](https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-controls.html).

### Use the do-not-evict annotation to prevent Karpenter from deprovisioning a node

If you are running a critical application on a Karpenter-provisioned node, such as a *long running* batch job or stateful application, *and* the node’s TTL has expired, the application will be interrupted when the instance is terminated. By adding a `karpenter.sh/do-not-evict` annotation to the pod, you are instructing Karpenter to preserve the node until the Pod is terminated or the `do-not-evict` annotation is removed. See [Deprovisioning](https://karpenter.sh/preview/tasks/deprovisioning/#pod-set-to-do-not-evict) documentation for further information.

If the only non-daemonset pods left on a node are those associated with jobs, Karpenter is able to target and terminate those nodes so long as the job status is succeed or failed.

### Configure requests=limits for all non-CPU resources when using consolidation

Consolidation and scheduling in general work by comparing the pods resource requests vs the amount of allocatable resources on a node.  The resource limits are not considered.  As an example, pods that have a memory limit that is larger than the memory request can burst above the request.  If several pods on the same node burst at the same time, this can cause some of the pods to be terminated due to an out of memory (OOM) condition.  Consolidation can make this more likely to occur as it works to pack pods onto nodes only considering their requests.

### Use LimitRanges to configure defaults for resource requests and limits

Because Kubernetes doesn’t set default requests or limits, a container’s consumption of resources from the underlying host, CPU, and memory is unbound. The Kubernetes scheduler looks at a pod’s total requests (the higher of the total requests from the pod’s containers or the total resources from the pod’s Init containers) to determine which worker node to schedule the pod onto. Similarly, Karpenter considers a pod’s requests to determine which type of instance it provisions. You can use a limit range to apply a sensible default for a namespace, in case resource requests are not specified by some pods.

See [Configure Default Memory Requests and Limits for a Namespace](https://kubernetes.io/docs/tasks/administer-cluster/manage-resources/memory-default-namespace/)

### Apply accurate resource requests to all workloads

Karpenter is able to launch nodes that best fit your workloads when its information about your workloads requirements is accurate.  This is particularly important if using Karpenter's consolidation feature.

See [Configure and Size Resource Requests/Limits for all Workloads](https://aws.github.io/aws-eks-best-practices/reliability/docs/dataplane/#configure-and-size-resource-requestslimits-for-all-workloads)

## Additional Resources
* [Karpenter/Spot Workshop](https://ec2spotworkshops.com/karpenter.html)
* [Karpenter Node Provisioner](https://youtu.be/_FXRIKWJWUk)
* [TGIK Karpenter](https://youtu.be/zXqrNJaTCrU)
* [Karpenter vs. Cluster Autoscaler](https://youtu.be/3QsVRHVdOnM)
* [Groupless Autoscaling with Karpenter](https://www.youtube.com/watch?v=43g8uPohTgc)
