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

/Kubernetes Cluster Autoscaler/
/HPA & Metrics Server/
/Nodegroups/
/multi-az vs single-az nodegroups/
