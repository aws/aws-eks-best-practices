# Reliability Pillar

The reliability pillar encompasses the ability of a system to recover itself from infrastructure or service disruptions, dynamically acquiring computing resources to meet demand, and mitigate disruptions such as misconfigurations or transient network issues.

Containers must be measured on at least two dimensions in terms of reliability. First, can the container be made reliable and recover from a transient failure, and second, can both the container and the underlying host meet changing demand based on CPU, memory, or custom metrics.

## Design Principles

There are five design principles for reliability in the cloud:

* Automatic recovery from failure
* Horizontal scaling to increase aggregate system availability
* Automatic scaling
* Automating changes
* Recovery mechanism(s)

To achieve reliability, a system must have a well-planned foundation and monitoring in place, with mechanisms for handling changes in demand or requirements. The system should be designed to detect failure and automatically heal itself.

## Best Practices
### Reliability of EKS Clusters
Amazon EKS provides a highly-available control plane that runs across multiple availability zones in AWS Region. EKS automatically manages the availability and scalability of the Kubernetes API servers and the etcd persistence layer for each cluster. Amazon EKS runs the Kubernetes control plane across three Availability Zones in order to ensure high availability, and it automatically detects and replaces unhealthy masters. Hence, reliability of an EKS cluster is not a customer
responsibility, it is already built-in.

### Understanding service limits
AWS sets service limits (an upper limit on the number of each resource your team can request) to protect you from accidentally over-provisioning resources. [Amazon EKS Service Quotas](https://docs.aws.amazon.com/eks/latest/userguide/service-quotas.html) lists the service limits. There are two types of limits, soft limits, that can be changed with proper justification via a support ticket. Hard limits cannot be changed. Because of this, you should carefully architect your applications
keeping these limits in mind. Consider reviewing these service limits periodically and apply them during your application design. 

Besides the limits from orchestration engines, there are limits in other AWS services, such as Elastic Load Balancing (ELB) and Amazon VPC, that may affect your application performance.
More about EC2 limits here: [EC2 service limits](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-resource-limits.html). 

### Networking limits considerations
With Amazon EKS, the default networking driver is [Amazon VPC CNI](https://github.com/aws/amazon-vpc-cni-k8s). There are a few design tradeoffs that you need to make when customizing the CNI configuration. Each instance is bound by the [number of elastic network interfaces that can be attached and the number of secondary IP addresses it can consume](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-eni.html). VPC CNI caches a certain number of IP addresses so that Kubernetes scheduler can schedule pods on these worker nodes. The IP addresses are available on the worker nodes whether you launch pods or not. If you need to constrain these IP addresses, you can customize them at the worker node level.

Since Amazon VPC CNI assigns an IP addresses from one of the subnets from your VPC to each pod, you need to have enough IP addresses available. If you do not have enough IP addresses available in the subnet that the CNI uses, your pods will not receive an IP address, and the pods will remain in pending state until an IP address is released from use. 

[CNI Metrics Helper](https://docs.aws.amazon.com/eks/latest/userguide/cni-metrics-helper.html) is a tool that can help you monitor number of IP addresses that are available and in use. 

### Scaling Kubernetes applications
When it comes to scaling your applications in Kubernetes, you need to think about two components in your application architecture, first your Kubernetes Worker Nodes and the application pods themselves.

There are two common ways to scale worker nodes in EKS. 

1. [Cluster Autoscaler](https://github.com/kubernetes/autoscaler/blob/master/cluster-autoscaler/cloudprovider/aws/README.md) 
2. [EC2 Auto Scaling Groups](https://docs.aws.amazon.com/autoscaling/ec2/userguide/AutoScalingGroup.html)


### Scaling Kubernetes worker nodes
Cluster Autoscaler is the preferred way to automatically scale EC2 worker nodes in EKS even though it performs reactive scaling. Cluster Autoscaler will adjust the size of your Kubernetes cluster when there are pods that cannot be run because the cluster has insufficient resources and adding another worker node would help. On the other hand, if a worker node is consistently underutilized and all of its pods can be scheduled on other worker nodes, Cluster Autoscaler will terminate
it. 

Cluster Autoscaler uses EC2 Auto Scaling groups (ASG) to adjust the size of the cluster. Typically all worker nodes are part of an auto scaling group. You may have multiple ASGs within a cluster. For example, if you co-locate two distinct workloads in your cluster you may want to use two different types of EC2 instances, each suited for its workload. In this case you would have two auto scaling groups.

Another reason for having multiple ASGs is if you use EBS to provide persistent
volumes for your pods or using statefulsets. At the time of writing, EBS volumes are only available within a single AZ. When your pods use EBS for storage, they need to reside in the same AZ as the EBS volume. In other words, a pod running in an AZ cannot access EBS volumes in another AZ. For this reason the scheduler needs to know that if a pod that uses an EBS volume crashes or gets terminated, it needs to be scheduled on a worker node in the same AZ, or else it will not be able to
access the volume. 

Using [EFS](https://github.com/kubernetes-sigs/aws-efs-csi-driver) can simplify cluster autoscaling when running applications that need persistent storage. In EFS, a file system can be concurrently accessed from all the AZs in the region, this means if you persistent storage using pod ceases to exist, and is resurrected in another AZ, it will still have access to the data stored by its predecessor.

If you are using EBS, then you should create one autoscaling group for each AZ. If you use managed nodegroups, then you should create nodegroup per AZ. In addition, you should enable the `--balance-similar-node-groups feature` in Cluster Autoscaler.

So you will need multiple autoscaling groups if you are:

1. running worker nodes using a mix of EC2 instance families or purchasing options (on demand or spot)
2. using EBS volumes.

If you are running an application that uses EBS volume but has no requirements to be highly available then you may also choose to restrict your deployment of the application to a single AZ. To do this you will need to have an autoscaling group that only includes subnet(s) in a single AZ. Then you can constraint the application's pods to run on nodes with particular labels. In EKS worker nodes are automatically added `failure-domain.beta.kubernetes.io/zone` label which contains the name of the AZ. You can see all the labels attached to your nodes by running `kubectl describe nodes {name-of-the-node}`. More information about built-in node labels is available [here](https://kubernetes.io/docs/concepts/configuration/assign-pod-node/#built-in-node-labels). Similarly persistent volumes (backed by EBS) are also automatically labeled with AZ name, you can see which AZ your persistent volume belongs to by running `kubectl get nodes -L topology.ebs.csi.aws.com/zone`. When a pod is created and it claims a volume, Kubernetes will schedule the pod on a node in the same AZ as the volume. 

Consider this scenario, you have an EKS cluster with one node group (or one autoscaling group), this node group has three worker nodes spread across three AZs. You have an application that needs to persist its data using an EBS volume. When you create this application and the corresponding volume, it gets created in the first of the three AZs. Your application running inside a Kubernetes pod is successfully able to store data on the persistent volume. Then, the worker node that runs this aforementioned pod becomes unhealthy and subsequently unavailable for use. Cluster Autoscaler will replace the unhealthy node with a new worker node, however because the autoscaling group spans across three AZs, the new worker node may get launched in the second or the third AZ, but not in the first AZ as our situation demands. Now we have a problem, the AZ-constrained volume only exists in the first AZ, but there are no worker nodes available in that AZ and hence, the pod cannot be scheduled. And due to this, you will have to create one node group in each AZ so there is always enough capacity available to run pods that cannot function in other AZs. 


Note:
When autosclaing, always know the EC2 limits in your account and if the limits need to be increased request a [limit increase](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-resource-limits.html)


### Scaling Kubernetes pods
You can use [Horizontal Pod Autoscaler](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/) (HPA) to autoscale the applications running in your cluster. HPA uses metrics such as CPU utilization or custom metrics provided by the application to scale the pods. It is also possible to scale pods using Amazon CloudWatch, at the time of writing, to do this you have to use `k8s-cloudwatch-adapter`. There is also a feature request to [enable HPA with CloudWatch
metrics and alarms](https://github.com/aws/containers-roadmap/issues/120). 

Before you can use HPA to autoscaling your applications, you will need to [install metrics server](https://aws.amazon.com/premiumsupport/knowledge-center/eks-metrics-server-pod-autoscaler/).


### Health checks

### Observability 

### Service Meshes

### CI/CD

### Simulating failure

