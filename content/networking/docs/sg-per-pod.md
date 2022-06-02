# Pod Per Branch Interface Mode (Security Group Per Pod)

A security group acts as a virtual firewall for instances to control inbound and outbound traffic. Just like applications running on EC2 instances, containerized applications (pods) running on Amazon EKS frequently require access to other services running within the cluster as well as external AWS services, such as [Amazon Relational Database Service](https://aws.amazon.com/rds/) (Amazon RDS) or [Amazon ElastiCache](https://aws.amazon.com/elasticache/). On AWS, controlling network level access between services is often accomplished via [EC2 security groups](https://docs.aws.amazon.com/vpc/latest/userguide/VPC_SecurityGroups.html).

Security groups are automatically created when you provision an EKS cluster. By default, the Amazon VPC CNI will use security groups at the node level, and every pod on a node shares the same security groups. However, security groups at the node level can be customized by customers.

As seen in the image below, all application pods operating on worker nodes will have access to the RDS database service. Although you may workaround this limitation by setting up a new node group for each application and defining taint and affinity rules to assign pods to the appropriate nodes, this appears to be a laborious process. This inefficient process is difficult to manage at scale and can result in underutilized nodes.

![Without Security Groups Per Pod](../images/sgp1.png)

You can use [IAM roles for service accounts](https://docs.aws.amazon.com/eks/latest/userguide/iam-roles-for-service-accounts.html) to address pod-level security challenges at the authentication layer. Using security groups for pods, on the other hand, may be a good idea if your organization's compliance rules also call for network segmentation as an extra defense in depth strategy.

Kubernetes [network policies] provide a mechanism for controlling ingress and egress traffic both within and outside the cluster. Network policies are not, however, natively integrated with AWS security groups. This makes it difficult to restrict network access to VPC resources, such as RDS databases or EC2 instances, solely using network policies. With security groups for pods, you can reuse your operational knowledge, tooling, and experience around existing policies rather than reimplementing network policies at the Kubernetes layer.

With security groups for pods, you can easily achieve network security compliance by running applications with varying network security requirements on shared compute resources. Network security rules that span pod to pod and pod to external AWS service traffic can be defined in a single place with EC2 security groups and applied to applications with Kubernetes native APIs. The below image shows security groups applied at the pod level and how they simplify your application deployment and node architecture.

![With Security Groups Per Pod](../images/sgp2.png)

You can enable security groups for pods by setting ENABLE_POD_ENI = true for VPC CNI. Security groups for pods use a separate ENI called a branch interface, which is associated with the main trunk interface attached to the node.

## Recommendations

### Internet Access

Source NAT is disabled for outbound traffic from pods with assigned security groups so that outbound security group rules are applied.  To access the internet, you may consider launching your worker nodes on private subnets configured with a NAT gateway or instance, and you will need to enable [external SNAT](https://docs.aws.amazon.com/eks/latest/userguide/external-snat.html) in the CNI.

```bash
kubectl set env daemonset -n kube-system aws-node AWS_VPC_K8S_CNI_EXTERNALSNAT=true
```

Pods with assigned security groups must be launched on nodes that are deployed in a private subnet. Please note that Pods with assigned security groups deployed to public subnets will not able to access the internet.

### Custom Networking

When security groups for pods are used in combination with custom networking, the security group defined in security groups for pods is used rather than the security group specified in the ENIConfig for custom networking. As a result, when custom networking is enabled, carefully assess security group ordering while using security groups per pod.

### Clean up network completely

You must compulsorily define *terminationGracePeriodSeconds* in your pod specification file for VPC CNI to delete the pod network from the underlying worker node. Without this setting, the CNI plugin doesn't remove the pod network on the host.

Cluster DNS Performance with NodeLocal DNSCache

You can’t use security groups per pod if your use case requires enabling NodeLocal DNSCache for faster DNS queries. Security groups for pods create additional network interfaces and are assigned a unique security group, and Pods will not be able to reach the DNS caching agent running on the node.

### IPv6 Support

You may consider deploying IPv6 clusters with only Fargate nodes if you have a strict requirement for using security groups for a pod. Security groups for a pod solve a niche use case by defining rules that allow inbound and outbound network traffic to and from pods directly through a separate ENI called a branch interface, which is associated with the main trunk interface attached to the node. As of today, IPv6 is supported in prefix mode only. Support for security groups per pod requires management of branch ENI’s in non-prefix mode. As a result, you cannot use the security groups for pod functionality during the initial deployment phase of an IPv6 cluster.

### Restrict Access to Pod Mutation

If you want to restrict access to pod mutation while using security groups per pod, you will need to specify eks-vpc-resource-controller and vpc-resource-controller Kubernetes service accounts in the Kubernetes ClusterRoleBinding for the role that your pod security policy is assigned to. Please find the steps mentioned in the [EKS user guide](https://docs.aws.amazon.com/eks/latest/userguide/security-groups-for-pods.html).  

### Preserving the client source IP

To enable preservation of the client IP, Kubernetes services of type NodePort and LoadBalancer using instance targets with an externalTrafficPolicy set to Local. You can't use Local policy when running pods with their own security groups. It is recommended to use the cluster mode for services of pods using their own security groups. The exteranlTrafficPolicy: Cluster a default mode provides good overall load-spreading.

### Using Liveness and Readiness Probe

If are you using liveness or readiness probes, you also need to disable TCP early demux, so that the kubelet can connect to pods on branch network interfaces via TCP. To do this run the following command:

```bash
kubectl edit daemonset aws-node -n kube-system
```

Under the initContainer section, change the value for DISABLE_TCP_EARLY_DEMUX from false to true, and save the file.
