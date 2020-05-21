# Reliability Pillar

The reliability pillar encompasses the ability of a system to recover itself from infrastructure or service disruptions, dynamically acquiring computing resources to meet demand, and mitigate disruptions such as misconfigurations or transient network issues.

Containerized applications must be measured on at least two dimensions in terms of reliability. First, can the application  be made reliable and recover from a transient failure, and second, can both the application containers and the underlying host meet changing demand based on CPU, memory, or other relevant metrics.

## Design Principles

There are five design principles for reliability in the cloud:

* Test recovery procedures
* Automatically recover from failure
* Scale horizontally to increase aggregate system availability
* Stop guessing capacity
* Manage change in automation

To achieve reliability, a system must have a well-planned foundation and monitoring in place, with mechanisms for handling changes in demand or requirements. The system should be designed to detect failure and automatically heal itself.

## Best Practices
### Reliability of EKS control plane
Amazon EKS provides a highly-available control plane that runs across three availability zones in an AWS Region. EKS automatically manages the availability and scalability of the Kubernetes API servers and the etcd cluster. EKS automatically detects and replaces unhealthy master nodes. Hence, the reliability of an EKS control plane is not a customer responsibility, it is already built-in.

### Understanding service limits
AWS sets service limits (an upper limit on the number of each resource your team can request) to protect you from accidentally over-provisioning resources. [Amazon EKS Service Quotas](https://docs.aws.amazon.com/eks/latest/userguide/service-quotas.html) lists the service limits. There are two types of limits, soft limits, that can be changed with proper justification via a support ticket. Hard limits cannot be changed. Because of this, you should carefully architect your applications keeping these limits in mind. Consider reviewing these service limits periodically and apply them during your application design. 

Besides the limits from orchestration engines, there are limits in other AWS services, such as Elastic Load Balancing (ELB) and Amazon VPC, that may affect your application performance.
More about EC2 limits here: [EC2 service limits](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-resource-limits.html). 

### Networking considerations
In order to create an EKS cluster you need subnets in at least two Availabiilty Zones. The subnets that you pass when you create the cluster influence where EKS places elastic network interfaces that are used for the control plane to worker node communication. Consider using a network topology that uses private subnets for worker nodes, and public subnets for internet-facing load balancers. [EKS documentation](https://docs.aws.amazon.com/eks/latest/userguide/network_reqs.html) includes more information about VPC considerations for EKS clusters.


---

## Amazon VPC CNI
Amazon EKS supports native VPC networking via the [Amazon VPC Container Network Interface (CNI)](https://github.com/aws/amazon-vpc-cni-k8s) plugin for Kubernetes.
Amazon EKS [Amazon VPC CNI](https://github.com/aws/amazon-vpc-cni-k8s) for networking. Using this CNI plugin allows Kubernetes pods to have the same IP address inside the Pod as they do on the VPC network.The CNI plugin uses [Elastic Network Interface (ENI)](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-eni.html) for Pod networking. The [maximum number of network interfaces, and the maximum number of private IPv4 addresses]](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-eni.html#AvailableIpPerENI) that you can use varies by the type of EC2 Instance. Since each Pod uses an IP address, the number of Pods you can run on a particular EC2 Instance depends on how many ENIs can be attached to it and how many IP addresses it supports.

This [file](https://github.com/awslabs/amazon-eks-ami/blob/master/files/eni-max-pods.txt) is contains the maximum number of pods you can run on an EC2 Instance.

The CNI plugin has two componenets:

* [CNI plugin](https://kubernetes.io/docs/concepts/extend-kubernetes/compute-storage-net/network-plugins/#cni), which will wire up host’s and pod’s network stack when called.
* `L-IPAMD` (aws-node daemonSet) runs on every node is a long running node-Local IP Address Management (IPAM) daemon and is responsible for:
    * maintaining a warm-pool of available IP addresses, and
    * assigning an IP address to a Pod.
    
The details can be found in [Proposal: CNI plugin for Kubernetes networking over AWS VPC](https://github.com/aws/amazon-vpc-cni-k8s/blob/master/docs/cni-proposal.md).

The CNI caches a certain number of IP addresses so that Kubernetes scheduler can schedule pods on these worker nodes. The IP addresses are available on the worker nodes whether you launch pods or not. If you need to constrain these IP addresses, you can customize them at the worker node level. The CNI supports customization of a number of configurations options, these options are set through environment variables. To configure these options, you can download aws-k8s-cni.yaml compatible
with your cluster and set environment variables. At the time of writing, the latest release is located here https://github.com/aws/amazon-vpc-cni-k8s/blob/master/config/v1.6/aws-k8s-cni.yaml .


## Recommendations
* Size the subnets you will use for Pod networking for growth. If you have insufficient IP addresses available in the subnet that the CNI uses, your pods will not get an IP address. And the pods will remain in pending state until an IP address is available.
* Consider using [CNI Metrics Helper](https://docs.aws.amazon.com/eks/latest/userguide/cni-metrics-helper.html) to monitor the number of IP addresses. 
* If your cluster has high pod churn rate, then consider creating [separate subnets for Pod networking](https://docs.aws.amazon.com/eks/latest/userguide/cni-custom-network.html) in each Availability Zone. Doing so will prevent IP address allocation conflicts with other resources in the VPC. 

---

## Scaling Kubernetes data plane (worker nodes)
There are two common ways to scale worker nodes in EKS. 

1. [Cluster Autoscaler](https://github.com/kubernetes/autoscaler/blob/master/cluster-autoscaler/cloudprovider/aws/README.md)
2. [EC2 Auto Scaling Groups](https://docs.aws.amazon.com/autoscaling/ec2/userguide/AutoScalingGroup.html)

### Kubernetes Cluster Autoscaler
Cluster Autoscaler is the preferred way to automatically scale EC2 worker nodes in EKS. Cluster Autoscaler will adjust the size of your data plane when there are pods that cannot be run because the cluster has insufficient resources and adding another worker node would help. On the other hand, if a worker node is consistently underutilized and all of its pods can be scheduled on other worker nodes, Cluster Autoscaler will terminate it.

Cluster Autoscaler uses EC2 Auto Scaling groups (ASG) to adjust the size of the cluster. You may have multiple Auto Scaling Groups in a cluster. For example, if you co-locate two distinct workloads in your cluster you may prefer using two different types of EC2 instances, each suited for a workload. In this case you will need two Auto Scaling Groups. 

If you use EBS to provide Persistent Volumes, consider creating a node group - a node group typically translates to one autoscaling group - in each AZ you use. At the time of writing, EBS volumes are only available within a single AZ. When you use EBS for Persistent Volumes, Pods need to reside in the same AZ as the EBS volume. A Pod cannot access EBS-backed persistent volumes located in a different AZ. Kubernetes [scheduler knows which AZ a worker node](https://kubernetes.io/docs/reference/kubernetes-api/labels-annotations-taints/#topologykubernetesiozone) is located in. Kubernetes will automatically schedule a Pod that requires an EBS volume in the same AZ as the volume. However, if there are no worker nodes available in the AZ where the volume is located, the Pod will remain in pending state. 


So you will need multiple node groups if you are:

1. running worker nodes using a mix of EC2 instance families or purchasing options (on demand or spot)
2. using EBS volumes for pods that can be scheduled in multiple AZs.

If you are running an application that uses EBS volume but has no requirements to be highly available then you may also choose to restrict your deployment of the application to a single AZ. To do this you will need to have an autoscaling group that only includes subnet(s) in a single AZ. Then you can constraint the application’s pods to run on nodes with particular labels. In EKS worker nodes are automatically added `failure-domain.beta.kubernetes.io/zone` label which contains the name of the AZ. You can see all the labels attached to your nodes by running `kubectl describe nodes {name-of-the-node}`. More information about built-in node labels is available [here](https://kubernetes.io/docs/concepts/configuration/assign-pod-node/#built-in-node-labels). Similarly persistent volumes (backed by EBS) are also automatically labeled with AZ name, you can see which AZ your persistent volume belongs to by running `kubectl get pv -L topology.ebs.csi.aws.com/zone`. When a pod is created and it claims a volume, Kubernetes will schedule the pod on a node in the same AZ as the volume. 

Consider this scenario, you have an EKS cluster with one node group, this node group has three worker nodes spread across three AZs. You have an application that uses EBS-backed Persistent Volume. When you create this application and the corresponding volume, its Pod gets created in the first of the three AZs. Then, the worker node that runs this aforementioned pod becomes unhealthy and subsequently unavailable for use. Cluster Autoscaler will replace the unhealthy node with a new worker node, however because the autoscaling group spans across three AZs, the new worker node may get launched in the second or the third AZ, but not in the first AZ as the situation demands. Now you have a problem, the AZ-constrained volume only exists in the first AZ, but there are no worker nodes available in that AZ, and so, the pod cannot be scheduled. For this reason you should create one node group in each AZ so there is always enough capacity available to run pods that cannot function in other AZs. 

Using [EFS](https://github.com/kubernetes-sigs/aws-efs-csi-driver) can simplify cluster autoscaling when running applications that need persistent storage. In EFS, a file system can be concurrently accessed from all the AZs in the region. Even if a Pod using EFS-backed Persistent Volume gets terminated and gets scheduled in different AZ, it will be able to mount the volume.

## Recommendations
* Consider running worker nodes in multiple AZ to protect your workloads from failures in an individual AZ.
* If you run stateless applications and use single EC2 Instance type then you can create one node group that spans across multiple Availability Zones. 
* If your cluster uses different types of EC2 instances then you should create multiple node groups, one for each instance type. 
* For stateful workloads you should create a node group per Availability Zone. 
* If you are using EBS, then you should create one autoscaling group for each AZ. If you use managed nodegroups, then you should create nodegroup per AZ. In addition, you should enable the `--balance-similar-node-groups feature` in Cluster Autoscaler.
* Consider using EFS for storage. EFS volumes are accessible in all the Availability Zones in a region and support concurrency, i.e., one EFS volume can be used by multiple Pods/EC2 Instances. 
* The Cluster Autoscaler does not support Auto Scaling Groups which span multiple
Availability Zones; instead you should use an Auto Scaling Group for each
Availability Zone and enable the --balance-similar-node-groups feature. If you do
use a single Auto Scaling Group that spans multiple Availability Zones you will find
that AWS unexpectedly terminates nodes without them being drained because of the [rebalancing](https://docs.aws.amazon.com/autoscaling/ec2/userguide/auto-scaling-benefits.html#arch-AutoScalingMultiAZ) feature.
* Run the Cluster Autoscaler with the `--node-group-auto-discovery` flag enabled. This
will enable the Cluster Autoscaler to find all autoscaling groups that include a
particular defined tag and prevents the need to define and maintain each and every
autoscaling group in the manifest.
* When using Cluster Autoscaler with more than one autoscaling-group, there
are 4 expander options for determining which instance group to use for the scaling
activity: random (selects the ASG randomly), most-pods (chooses the ASG that will
allow for the scheduling of the most pods), least-waste (chooses the ASG that will
provide the least waste of CPU and Memory resources), and price (selects the ASG
based on price). By default the random expander is used. Consider using `most-pods` for faster scaling, or `least-waste` to optimize cost. 
* By default the Cluster Autoscaler does not scale-down nodes that have pods
deployed with local storage attached. Set the `--skip-nodes-with-local-storage` flag
to false to allow Cluster Autoscaler to scale-down these nodes.
* The Cluster Autoscaler’s level of aggressiveness when triggering scale-down events
can be adjusted through the use of several flags: `--scale-down-delay-after-add`, `--scale-down-delay-after-delete`, and `--scale-down-delay-after-failure`. A sample
command value for the cluster-autoscaler including expander and scale-down limits
is as follows:
```
command:
  - ./cluster-autoscaler
  - --v=4
  - --stderrthreshold=info
  - --cloud-provider=aws
  - --skip-nodes-with-local-storage=false
  - --expander=least-waste
  - --node-group-auto-discovery=asg:tag=k8s.io/cluster-autoscaler/enabled,k8s.io/cluster-autoscaler/dev
  - --skip-nodes-with-system-pods=false
  - --scale-down-delay-after-add=60m
  - --scale-down-delay-after-delete=60m
  - --scale-down-unneeded-time=60m
  - --max-graceful-termination-sec=1800
  - --scale-down-utilization-threshold=0.25}
```
* Consider running [node-problem-detector](https://github.com/kubernetes/node-problem-detector) to monitor health of worker nodes. 


---

Here is a helpful flowchart to determine when to create node groups:


![auto-scaling group-flowchart](../images/reliability-ca-asg.jpg)


---

> When autosclaing, always know the EC2 limits in your account and if the limits need to be increased request a [limit increase](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-resource-limits.html).

---

## Running highly-available applications 
Highly available systems are designed to mitigate harmful impacts in the environment. Most modern applications depend on a network of resources that must all work together. Highly available applications are designed so a user never experiences a failure due to a malfunctioning component in the system. In order to make a service or application highly available, you need to eliminate any single points of failure and automatically heal unhealthy components. 

Kubernetes provides us tools to easily run highly available services. Running multiple replicas of a service helps you eliminate single points of failure. In Kubernetes pods are the smallest deployable units. While Kubernetes allows you to create individual pods, creating individual pods outside of testing and troubleshooting scenarios is not recommended. [Kubernetes Deployments](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/) provides abstraction layer for pods, you describe a desired state in a [Deployment](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/#creating-a-deployment) and the Deployment controller changes the actual state to match the desired state. 

You can use Deployment resource to run a replicated service. You can scale-out your service by adjusting the number of `replicas`. If a replica becomes unhealthy, Kubernetes can also automatically replace it.

### Scaling Kubernetes pods
Kubernetes can scale your services horizontally and vertically. [Horizontal Pod Autoscaler](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/) or HPA automatically adjusts replica count in a Deployment based on a scaling metric. Vertical Pod Autoscaler or VPA automaticaly adjusts compute resource requirements of a Pod.

### Kubernetes Metrics Server
Before you can use the HPA to autoscale your applications, you will need [Kubernetes Metrics Server](https://github.com/kubernetes-sigs/metrics-server). Metrics Server defines itself as a *cluster-wide aggregator resource usage data* and it has been inspired by [Heapster](https://github.com/kubernetes-retired/heapster).The metrics-server is responsible for collecting resource metrics from kubelets and serving them in [Metrics API format](https://github.com/kubernetes/metrics). These metrics are consumed by monitoring systems like Prometheus. The metrics-server only stores metrics in memory.

[EKS documentation contains the instructions](https://docs.aws.amazon.com/eks/latest/userguide/metrics-server.html) to install  metrics-server .

You can see data provided by the metrics-server api directly using curl like this 

```
$ kubectl get —raw /apis/metrics.k8s.io/v1beta1/nodes     

{“kind”:”NodeMetricsList”,”apiVersion”:”metrics.k8s.io/v1beta1”,”metadata”:{“selfLink”:”/apis/metrics.k8s.io/v1beta1/nodes”},”items”
:[{“metadata”:{“name”:”ip-192-168-76-71.us-west-2.compute.internal”,”selfLink”:”/apis/metrics.k8s.io/v1beta1/nodes/ip-192-168-76-71.
us-west-2.compute.internal”,”creationTimestamp”:”2020-03-04T16:29:47Z”},”timestamp”:”2020-03-04T16:29:35Z”,”window”:”30s”,”usage”:{“
cpu”:”25468986n”,”memory”:”481412Ki”}},{“metadata”:{“name”:”ip-192-168-50-160.us-west-2.compute.internal”,”selfLink”:”/apis/metrics.
k8s.io/v1beta1/nodes/ip-192-168-50-160.us-west-2.compute.internal”,”creationTimestamp”:”2020-03-04T16:29:47Z”},”timestamp”:”2020-03-
04T16:29:29Z”,”window”:”30s”,”usage”:{“cpu”:”27248899n”,”memory”:”467580Ki”}}]}”
“}}]}
```

Once the metrics-server has been installed, it will collect metrics and provide the aggregated metrics for consumption. One of the consumers of data provided by metrics API is kubectl, you can get the same information you retrieved using curl example above using kubectl.

```
$ kubectl top nodes

NAME                                           CPU(cores)   CPU%   MEMORY(bytes)   MEMORY%   
ip-192-168-50-160.us-west-2.compute.internal   30m          1%     456Mi           6%        
ip-192-168-76-71.us-west-2.compute.internal    25m          1%     470Mi           6%  
```
This is more sightly. 

### Autoscaling deployments using the Horizontal Pod Autoscaler (HPA)

Now that resource metrics are available, you can configure HPA to autoscale a Deployment based on CPU utilization. The Horizontal Pod Autoscaler is implemented as a control loop in Kubernetes, it periodically queries metrics from APIs that provide resource metrics.

The Horizontal Pod Autoscaler can retrieve metrics from the following APIs:
1. `metrics.k8s.io` also known as Resource Metrics API — Provides CPU and memory usage for pods
2. `custom.metrics.k8s.io` — Provides metrics from other metric collectors like Prometheus, these metrics are __internal__ to your Kubernetes cluster. 
3. `external.metrics.k8s.io` — Provides metrics that are __external__ to your Kubernetes cluster (E.g., SQS Queue Depth, ELB latency).

Any metric that you want to use to scale should be provided by one of these three APIs. 

[How do I set up Kubernetes Metrics Server and Horizontal Pod Autoscaler on Amazon EKS?](https://aws.amazon.com/premiumsupport/knowledge-center/eks-metrics-server-pod-autoscaler/)

### Custom and external metrics for autoscaling deployments

In pod autoscaling context, besides CPU and memory utilization - which is provided by the metrics-server - any other metric is called custom metric. [Custom Metrics](https://github.com/kubernetes/community/blob/master/contributors/design-proposals/instrumentation/custom-metrics-api.md) API servers provide the `custom-metrics.k8s.io` API which is queried by the Horizontal Pod Autoscaler. 

You can use the [Prometheus Adapter for Kubernetes Metrics APIs](https://github.com/directxman12/k8s-prometheus-adapter) to collect metrics from Prometheus and use with the HPA. In this case Prometheus adapter will expose Prometheus metrics in [Metrics API format](https://github.com/kubernetes/metrics/blob/master/pkg/apis/metrics/v1alpha1/types.go). A list of all custom metrics implementation can be found in [Kubernetes Documentation](https://github.com/kubernetes/metrics/blob/master/IMPLEMENTATIONS.md#custom-metrics-api). 

Once you deploy the Prometheus Adapter, you can query custom metrics using kubectl.
`kubectl get —raw /apis/custom.metrics.k8s.io/v1beta1/`

You will need to start producing custom metrics before consuming them for autoscaling. 

[kube-state-metrics](https://github.com/kubernetes/kube-state-metrics) can be used to generate metrics derived from the state of Kubernetes objects. It is not focused on the health of the individual Kubernetes components, but rather on the health of the various objects inside, such as deployments, nodes and pods. 

[External metrics](https://github.com/kubernetes/community/blob/master/contributors/design-proposals/instrumentation/external-metrics-api.md), as the name suggests provide the Horizontal Pod Autoscaler the ability to scale deployments using metrics that are external to Kubernetes cluster. For example, in batch processing workloads, it is common to scale the number of replicas based on the number of jobs in flight in an SQS queue.

You can also scale deployments using Amazon CloudWatch, at the time of writing, to do this you have to use `k8s-cloudwatch-adapter`. There is also a feature request to [enable HPA with CloudWatch metrics and alarms](https://github.com/aws/containers-roadmap/issues/120). 

## Recommendations
### Implement horizontal scaling 
* Consider using Zolando’s [kube-metrics-adapter](https://github.com/zalando-incubator/kube-metrics-adapter), it can collect and serve custom and external metrics for Horizontal Pod Autoscaling. It supports scaling based on Prometheus metrics, SQS queues and others out of the box.
### Spread out application replicas to different worker node availability zones for redundancy
If you are using EKS optimized AMIs, worker nodes are automatically labelled with failure-domain.beta.kubernetes.io/zone as key and the corresponding availability zone with the value. You can decorate your application’s manifest files with NodeAffinity and AntiAffinity specs as follows, so that the replica sets are distributed across AZs and hence redundant to AZ failures. There are two types of node affinity currently supported in Kubernetes: `requiredDuringSchedulingIgnoredDuringExecution` and `preferredDuringSchedulingIgnoredDuringExecution`.
* `requiredDuringSchedulingIgnoredDuringExecution` is the "hard" rule for scheduling pod deployments because the first half (requiredDuringScheduling) details the rules that are required to be met before a pod can be scheduled to deploy onto a node. The second half (IgnoredDuringExecution) states that if a node changes in such a way that the requirements are no longer met (post deployment) that the pod is allowed to continue to run on the node.
* `preferredDuringSchedulingIgnoredDuringExecution` is the "soft" rule for scheduling pod deployments because the first half (preferredDuringScheduling) details the rules that are desired to be met before a pod can be scheduled to deploy onto a node. If no node is available where those conditions are met the pod will still be scheduled for deployment. The second half (IgnoredDuringExecution) states that if a node changes in such a way that the requirements are no longer met (post deployment) that the pod is allowed to continue to run on the node.
* In the example below, the requiredDuringSchedulingIgnoredDuringExecution statement indicates that the pod should not be placed in the same availability zone as another pod with the same name (to ensure that the replicaSet is spread across all of the availability zones to achieve high availability). The preferredDuringSchedulingIgnoredDuringExecution statement indicates that ideally the pod should not be placed on a node where a pod of the same node is already running.
```
---   
spec:   
  affinity:   
    podAffinity:   
      requiredDuringSchedulingIgnoredDuringExecution:   
        -   
          podAffinityTerm:   
            labelSelector:   
              matchExpressions:   
                -   
                  key: component  
                  operator: In  
                  values:   
                    - ${NAME_OF_THE_APP}  
            topologyKey: failure-domain.beta.kubernetes.io/zone  
          weight: 100  
    podAntiAffinity:   
      preferredDuringSchedulingIgnoredDuringExecution:   
        -   
          podAffinityTerm:   
            labelSelector:   
              matchExpressions:   
                -   
                  key: app  
                  operator: In  
                  values:   
                    - ${NAME_OF_THE_APP}  
            topologyKey: kubernetes.io/hostname  
          weight: 99  
   
```
* The `topologyKey` value can be any label key but note that for any affinity rule and for `requiredDuringSchedulingIgnoredDuringExecution` anti-affinity rules the `toplogyKey` is not allowed to be empty. Additionally, if it is empty on a `preferredDUringSchedulingIgnoredDuringExecution` then the `topologyKey` is interpreted as "all topologies" which means the combination of `kubernetes.io/hostname`, `failure-domain.beta.kubernetes.io/zone`, and `failure-domain.beta.kubernetes.io/region` (node hostname, availability zone, and region).


### Vertical Pod Autoscaler (VPA)

You might have wondered why the Horizontal Pod Autoscaler is not simply called “the Autoscaler”, this is because besides horizontally scaling your services, Kubernetes can also scale your Pods vertically. The [Vertical Pod Autoscaler](https://github.com/kubernetes/autoscaler/tree/master/vertical-pod-autoscaler) automatically adjusts the CPU and memory reservations for your pods to help you “right-size” your applications. Vertical Pod Autoscaler’s current implementation does not perform in-place adjustments to pods, instead it will restart the pod that needs to be scaled. 

[EKS Documentation](https://docs.aws.amazon.com/eks/latest/userguide/vertical-pod-autoscaler.html) includes a walkthrough for setting up VPA. 

[Fairwinds Goldilocks](https://github.com/FairwindsOps/goldilocks/) project simplifies implementation of VPA. Goldilocks can provide VPA recommendations and it can optionally auto-scale the Pods. 

---

## Health checks and self-healing
It’s a truism that no software is bug-free. Kubernetes gives you the ability to minimize impact of software failures. In the past, if an application crashed, someone had to manually remediate the situation by restarting the application. Kubernetes gives you the ability to detect software failures in your application and automatically heal them. Kubernetes can minimize the impact to the clients by monitoring the health of your service and stop sending requests to its Pod if it fails health-checks.  

Kubernetes supports three types of [health-checks](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/):

1. Liveness probe
2. Startup probe (requires Kubernetes 1.16+)
3. Readiness probe

[Kubelet](https://kubernetes.io/docs/reference/command-line-tools-reference/kubelet/) is responsible for running all the above-mentioned checks. Kubelet can check the health of the Pods in three ways, it can either run a shell command inside its container, send a HTTP GET request to its container or open a TCP socket on a specified port. 

#### Liveness Probe
You can use the Liveness probe to detect failure in a running service. For example, if you are running a web service that listens on port 80, you can configure a Liveness probe to send a HTTP GET request on Pod’s port 80. Kubelet will periodically send a GET request to the Pod and expect a response, if the Pod responds between 200-399 then kubelet considers that Pod as healthy, otherwise the Pod will be considered unhealthy. If a Pod fails health-checks continously, kubelet will terminate it. 

#### Startup Probe
When your service needs additional time to startup, you can use the Startup Probe to delay the Liveness Probe. Once the Startup Probe succeeds, the Liveness Probe takes over. You can define maximum time Kubernetes should wait for application startup. If after the maximum configured time, the Pod still fails Startup Probes, it will be terminated and a new Pod will be created. 

#### Readiness Probe
While Liveness probe is used to detect failure in an application that can only be remediated by terminating the Pod, Readiness Probe can be used to detect situations where the service may be _temporarily_ unavailable. Some services have external dependencies or need to perform actions such as opening a database connection, loading a large file, etc. And, they may need to do this not just during startup. In these situations the service may become temporarily unresponsive however once this operation completes, it is expected to be healthy again. You can use the Readiness Probe to detect this behavior and stop sending requests to the Pod until it becomes healthy again. Unlike Liveness Probe, where a failure would result in a recreation of Pod, a failed Readiness Probe would mean that Pod will not receive any traffic from Kubernetes Service. When the Liveness Probe succeeds, Pod will resume receiving traffic from Service.
 
## Recommendations
Configure both Readiness and Liveness probe in your Pods. Use `initialDelaySeconds` to delay the first probe. For example, if in your tests you’ve identified that your service takes on an average 60 seconds to load libraries, open database connections, etc, then configure `initialDelaySeconds` to 60 seconds plus ~10 seconds for grace period. 

---

## Disruptions

A Pod will run indefinitely unless a user stops or the worker node it runs on fails. Outside of failed health-checks and autoscaling there aren’t many situations where Pods need to be terminated. Performing Kubernetes cluster upgrades is one such event. When you  upgrade your Kubernetes cluster, after upgrading the control plane, you will upgrade the worker nodes. If you are not using [EKS managed node group](https://docs.aws.amazon.com/eks/latest/userguide/managed-node-groups.html), we recommend you create new node group with updated Kubernetes components rather than performing an in-place upgrade on your existing worker nodes. 

Worker node upgrades are generally done by terminating old worker nodes and creating new worker nodes. Before terminating a worker nodes, you should `drain` it. When a worker node is drained, all its pods are safely evicted. Safely is a key word here, when Pods on a worker are evicted, they are not sent a KILL signal. Instead a TERM signal is sent to the main process of each container in the Pods being evicted. After the TERM signal is sent, Kubernetes will give the process some time (grace period) before a KILL signal is sent. This grace period is 30 seconds by default, you can override the default by using `grace-period` flag in kubectl. 

`kubectl delete pod <pod name> —grace-period=<seconds>`

Draining also respects `PodDisruptionBudgets`

### Pod Disruption Budget

Pod Disruption Budget or PDB can temporarily halt the eviction process if the number of replicas of an application fall below the declared threshold. The eviction process will continue once the number of available replicas is over the threshold. You can use PDB to declare the `minAvailable` and `maxUnavailable` number of replicas. For example, if you want at least three copies of your service to be available, you can create a PDB. 

```
apiVersion: policy/v1beta1
kind: PodDisruptionBudget
metadata:
  name: my-svc-pdb
spec:
  minAvailable: 3
  selector:
    matchLabels:
      app: my-svc
```

This tells Kubernetes to halt the eviction process until three or more replicas are available. 

## Recommendations
### Protect critical workloads
Configure `PodDisruptionBudget` for critical services so a voluntary change doesn't impact its availability. 
### Practice chaos engineering 
> Chaos Engineering is discipline of experimenting on a distributed system in order to build confidence in the system’s capability to withstand turbulent conditions in production.

[Kubernetes is declarative system](https://medium.com/@dominik.tornow/the-mechanics-of-kubernetes-ac8112eaa302) where user defines the *desired state* and the system works towards transitioning from the current state to the desired state. This means Kubernetes always knows the *desired state* and if the system deviates, Kubernetes can (or at least attempt to) restore state. For example, if a worker node becomes unavailable, Kubernetes will schedule the Pods on another worker node. Similarly, if a `replica` crashes, the [Deployment Contoller](https://kubernetes.io/docs/concepts/architecture/controller/#design) will create a new `replica`. In this way, Kubernetes controllers automatically fix failures. 

Consider testing the resiliency of your cluster by using a tool that *breaks things on purpose* to detect failures. 

### Resources
* [Gremlin](https://www.gremlin.com)
* [Chaos Mesh](https://github.com/pingcap/chaos-mesh)
* [PowerfulSeal](https://github.com/bloomberg/powerfulseal)
* [kube-monkey](https://github.com/asobti/kube-monkey)
* [chaoskube](https://github.com/linki/chaoskube)

---

## Observability 

Observability, in this context, is an umbrella term that includes monitoring, logging and tracing. Microservices based applications are distributed by nature. Unlike monolithic applications where monitoring a single system is sufficient, in microservices architecture each component needs to be monitored individually as well as cohesively, as one application. Cluster-level monitoring, logging and distributed tracing systems improve the observabiliaty of distributed applications. 

Kubernetes tools for troubleshooting and monitoring are limited. The metrics-server collects resource metrics and stores them in memory but doesn’t persist them. You can view the logs of a Pod using kubectl but these logs are not retained. And implementation of distributed tracing is done either at application code level or using services meshes. 

This is where Kubernetes extensibility shines, you can bring your own preferred centralized monitoring, logging and tracing solution and use Kubernetes to manage and run it. 


## Recommendations
### Use a cluster-wide monitoring tool 
Consider using a tool like [Prometheus](https://prometheus.io) or [CloudWatch Container Insights](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/ContainerInsights.html) for centralized monitoring Kubernetes infrastructure and applications. 

### Use Prometheus cient library to expose application metrics
In addition to monitoring the state of the appliation and aggregating standard metrics, you can also use Prometheus client library to expose application specifc custom metrics to improve application's observability. 

### Use a centralized logging solution
For centralized logging, you can use tools like [FluentD](https://www.fluentd.org) or [CloudWatch Container Insights](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/ContainerInsights.html) 

### Use a distributed tracing system
Modern applications have components that are distributed over the network and inter-connectivity is provided using REST, gRPC, or similar technologies. Distributed tracing solutions will help you understand how requests flows and how systems communicate. Consider using a distributed tracing system that will help you identify bottlenecks and identify problematic components.

You can enable tracing in your applications in two ways. You can either implement distributed tracing at the code level by using shared libraries or you can use a service mesh. 

Implementing tracing at the code level can be disadvantageous. In this method, you have to make changes to your code. This is further complicated if you have polyglot applications. You’re also responsible to maintaining yet another library, across your services. 

Service Meshes like [LinkerD](http://linkerd.io), [Istio](http://istio.io), and [AWS App Mesh](https://aws.amazon.com/app-mesh/) can be used to implement distributed tracing in your application. 

Tracing tools like [AWS X-Ray](https://aws.amazon.com/xray/), [Jaeger](https://www.jaegertracing.io) support both shared library and service mesh implementations. 

Consider using a tracing tool that supports both implementations so you will not have to switch tools if you adopt service mesh. 

### Distributed tracing systems
* [AWS X-Ray](https://aws.amazon.com/xray/)
* [Jaeger](https://github.com/jaegertracing/jaeger)
* [Zipkin](https://zipkin.io)

### Use a Service Mesh
Service meshes enable service-to-service communication in a secure, reliable, and greatly increase observability of your microservices network. Most service mesh products works by having a small network proxy run alongside each service. The service proxy intercept, inspects, and can manipulate Pod's network traffic, while primary container needs no alteration or even knowledge that this is happening. Service proxy can alos generate statistics, create access logs and add HTTP headers to outbound requests for tracing.

You can also use service mesh features like automatic retries and rate limiting to make your microservices more resilient.

### Service Meshes
+ [AWS App Mesh](https://aws.amazon.com/app-mesh/)
+ [Istio](https://istio.io)
+ [LinkerD](http://linkerd.io)
+ [Consul](https://www.consul.io)


## CoreDNS

CoreDNS fulfills name resolution and service discovery functions in Kubernetes. It is installed by default on EKS clusters. For interoperability, the Kubernetes service for CoreDNS is still named [kube-dns](https://kubernetes.io/docs/tasks/administer-cluster/dns-custom-nameservers/). CoreDNS runs as a deployment in kube-system namespaces, and by default it runs two replicas with declared requests and limits. 

## Recommendations
### Monitor CoreDNS metrics
CoreDNS has built in support for [Prometheus](https://github.com/coredns/coredns/tree/master/plugin/metrics). You should especially consider monitoring CoreDNS latency (`coredns_dns_request_duration_seconds_sum`), errors (`coredns_dns_response_rcode_count_total`, NXDOMAIN, SERVFAIL, FormErr) and CoreDNS Pod’s memory consumption. 

For troubleshooting purposes, you can use kubectl to view CoreDNS logs:
`for p in $(kubectl get pods —namespace=kube-system -l k8s-app=kube-dns -o name); do kubectl logs —namespace=kube-system $p; done`
### Use NodeLocal DNSCacehe
NodeLocal DNSCache improves Cluster DNS performance by running a dns caching agent on cluster nodes as a DaemonSet.

---

## Resource management
Kubernetes allows you to declare CPU and memory resources for the containers in a Pod to avoid CPU and memory over-subscription. When you run a Pod, you can optionally define `requests` and `limits` for containers to set Pod’s [Quality of Service class](https://kubernetes.io/docs/tasks/configure-pod-container/quality-service-pod/). If the cluster is under *pressure*, Pods with lower QoS class are evicted. 

Pod level requests and limits are computed by summing up per-resource requests and limits across all containers. Kubernetes scheduler will use these values to place the Pod and it will ensure that, for each compute resource type (CPU or memory), the sum of the resource requests of the scheduled containers is less than the capacity of the node.

You can control the minimum compute resources a container needs by declaring `requests` and you define a maximum resources by declaring `limits`. Based on the values of `requests` and `limits`, a Pod will be assigned a QoS class.

There are three QoS classes:
* **Guaranteed**. The values of `limits` and `requests` for any container in the Pod are the same. 
* **Burstable**. The value of `limits` is either undefined or is greater than `requests`. 
* **BestEffort**. Both `requests` and `limits` are undefined for any container in the Pod. 

Kubernetes documentation defines CPU as a compressible resource while memory is incompressible resource. Pods that are guaranteed get the amount of CPU they request and they get throttled if they exceed their limit. If a CPU limit is undefined then the Pods can use excess CPU when available. 

Similarly, Pods are guaranteed the amount of memory they request and they will get killed if they exceed their memory request, they could be killed if another Pod needs memory. If they exceed their limit a process that is using the most amount of memory, inside one of the pod’s containers, will be killed by the kernel.

## Recommendations
### Use Pod priority
[Priority](https://kubernetes.io/docs/concepts/configuration/pod-priority-preemption/#priorityclass) indicates the importance of a Pod relative to other Pods. If a Pod cannot be scheduled, the scheduler tries to preempt (evict) lower priority Pods to make scheduling of the pending Pod possible.

### Implement QoS
For critical applications, consider defining `requests`=`limits` for the container in the Pod. This will ensure that the container will not be killed if another Pod requests resources.  

Consider implementing CPU and memory limits for all containers, this will prevent a container inadvertently consuming system resources impacting other co-located processes.

### Configure resource quotas for namespaces
Namespaces are intended for use in environments with many users spread across multiple teams, or projects. They provide a scope for names and are a way to divide cluster resources between multiple teams, projects, workloads. You can limit the aggregate resource consumption in a namespace. The [`ResourceQuota`](https://kubernetes.io/docs/concepts/policy/resource-quotas/) object can limit the quantity of objects that can be created in a namespace by type, as well as the total amount of compute resources that may be consumed by resources in that project. You can limit the total sum of storage and/or compute (CPU and memory) resources that can be requested in a given namespace.

> If resource quota is enabled for a namespace for compute resources like CPU and memory, users must specify requests or limits for each container in that namespace.

Consider configuring quotas for each namespace. Consider using `LimitRanges` to automatically apply preconfigured limits to containers within a namespaces. 

### Limit container resource usage within a namespace
Resource Quotas help limit the amount of resources a namespace can use. The [`LimitRange` object](https://kubernetes.io/docs/concepts/policy/limit-range/) can help you implement minimum and maximum resources a container can request. Using `LimitRange` you can set a default request and limits for containers, which is helpful if setting compute resource limits is not a standard practice in your organization. As the name suggests, `LimitRange` can enforce minimum and maximum compute resources usage per Pod or Container in a namespace. As well as, enforce minimum and maximum storage request per PersistentVolumeClaim in a namespace.

Consider using `LimitRange` in conjunction with `ResourceQuota` to enforce limits at a container as well as namespace level. Setting these limits will ensure that a container or a namespace does not usurp upon resources used by other tenants in the cluster. 

