# VPC and Subnet Considerations

Operating an EKS cluster requires knowledge of AWS VPC networking, in addition to Kubernetes networking.

We recommend you understand the EKS control plane communication mechanisms before you start designing your VPC or deploying clusters into existing VPCs.

Refer to [Cluster VPC considerations](https://docs.aws.amazon.com/eks/latest/userguide/network_reqs.html) and [Amazon EKS security group considerations](https://docs.aws.amazon.com/eks/latest/userguide/sec-group-reqs.html) when architecting a VPC and subnets to be used with EKS.

## Overview

### EKS Cluster Architecture

An EKS cluster consists of two VPCs: 

* An AWS-managed VPC that hosts the Kubernetes control plane. This VPC does not appear in the customer account. 
* A customer-managed VPC that hosts the Kubernetes nodes. This is where containers run, as well as other customer-managed AWS infrastructure such as load balancers used by the cluster. This VPC appears in the customer account. You need to create customer-managed VPC prior creating a cluster. The eksctl creates a VPC if you do not provide one.

The nodes in the customer VPC need the ability to connect to the managed API server endpoint in the AWS VPC. This allows the nodes to register with the Kubernetes control plane and receive requests to run application Pods.

The nodes connect to the EKS control plane through (a) an EKS public endpoint or (b) a Cross-Account [elastic network interfaces](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-eni.html)  (X-ENI) managed by EKS. When a cluster is created, you need to specify at least two VPC subnets. EKS places a X-ENI in each  subnet specified during cluster create (also called cluster subnets). The Kubernetes API server uses these Cross-Account ENIs to communicate with nodes deployed on the customer-managed cluster VPC subnets. 

![general illustration of cluster networking, including load balancer, nodes, and pods.](./image.png)

As the node starts, the EKS bootstrap script is executed and Kubernetes node configuration files are installed. As part of the boot process on each instance, the container runtime agents, kubelet, and Kubernetes node agents are launched.

To register a node, Kubelet contacts the Kubernetes cluster endpoint. It establishes a connection with either the public endpoint outside of the VPC or the private endpoint within the VPC. Kubelet receives API instructions and provides status updates and heartbeats to the endpoint on a regular basis.

### EKS Control Plane Communication

EKS has two ways to control access to the [cluster endpoint](https://docs.aws.amazon.com/eks/latest/userguide/cluster-endpoint.html). Endpoint access control lets you choose whether the endpoint can be reached from the public internet or only through your VPC. You can turn on the public endpoint (which is the default), the private endpoint, or both at once. 

The configuration of the cluster API endpoint determines the path that nodes take to communicate to the control plane. Note that these endpoint settings can be changed at any time through the EKS console or API.

#### Public Endpoint

This is the default behavior for new Amazon EKS clusters. When only the public endpoint for the cluster is enabled, Kubernetes API requests that originate from within your cluster’s VPC (such as worker node to control plane communication) leave the VPC, but not Amazon’s network. In order for nodes to connect to the control plane, they must have a public IP address and a route to an internet gateway or a route to a NAT gateway where they can use the public IP address of the NAT gateway.

#### Public and Private Endpoint

When both the public and private endpoints are enabled, Kubernetes API requests from within the VPC communicate to the control plane via the X-ENIs within your VPC. Your cluster API server is accessible from the internet.

#### Private Endpoint

There is no public access to your API server from the internet when only private endpoint is enabled. All traffic to your cluster API server must come from within your cluster’s VPC or a connected network. The nodes communicate to API server via X-ENIs within your VPC. Note that cluster management tools must have access to the private endpoint. Learn more about [how to connect to a private Amazon EKS cluster endpoint from outside the Amazon VPC.](https://aws.amazon.com/premiumsupport/knowledge-center/eks-private-cluster-endpoint-vpc/)

Note that the cluster's API server endpoint is resolved by public DNS servers to a private IP address from the VPC. In the past, the endpoint could only be resolved from within the VPC.

### Guidance on Designing Hyperscale VPCs

An environment can be considered “Hyperscale” once it supports thousands of application endpoints and tens or hundreds of gigabits of traffic per second. 

When operating at Hyperscale, additional planning is required for network connectivity, security, private IPv4 address scarcity and overlap. Hyperscale network design involves leveraging cell-based infrastructure units, and understanding the benefits and limitations of each of the various AWS networking services.

Learn more about [Designing Hyperscale Amazon VPC networks](https://aws.amazon.com/blogs/networking-and-content-delivery/designing-hyperscale-amazon-vpc-networks/) on the AWS Networking & Content Delivery Blog. 


### VPC configurations

Amazon VPC supports IPv4 and IPv6 addressing. Amazon EKS supports IPv4 by default. A VPC must have an IPv4 CIDR block associated with it. You can optionally associate multiple IPv4 [Classless Inter-Domain Routing](http://en.wikipedia.org/wiki/CIDR_notation) (CIDR) blocks and multiple IPv6 CIDR blocks to your VPC. When you create a VPC, you must specify an IPv4 CIDR block for the VPC from the private IPv4 address ranges as specified in [RFC 1918](http://www.faqs.org/rfcs/rfc1918.html). The allowed block size is between a `/16` prefix (65,536 IP addresses) and `/28` prefix (16 IP addresses). 

When creating a new VPC, you can attach a single IPv6 CIDR block, and up to five when changing an existing VPC. The prefix length of the CIDR block is fixed at /64 for IPv6 VPCs, which has [more than one trillion IP addresses](https://www.ripe.net/about-us/press-centre/understanding-ip-addressing#:~:text=IPv6%20Relative%20Network%20Sizes%20%20%20%2F128%20,Minimum%20IPv6%20allocation%20%201%20more%20rows%20). You can request an IPv6 CIDR block from the pool of IPv6 addresses maintained by Amazon.

Amazon EKS clusters support both IPv4 and IPv6. By default, EKS clusters use IPv4 IP. Specifying IPv6 at cluster creation time will enable the use IPv6 clusters. IPv6 clusters require dual-stack VPCs and subnets.

Amazon EKS recommends you use at least two subnets that are in different Availability Zones during cluster creation. The subnets you pass in during cluster creation are known as cluster subnets. When you create a cluster, Amazon EKS creates up to 4 cross account (x-account or x-ENIs) ENIs in the subnets that you specify. The x-ENIs are always deployed and are used for cluster administration traffic such as log delivery, exec, and proxy. Please refer to the EKS user guide for complete [VPC and subnet requirement](https://docs.aws.amazon.com/eks/latest/userguide/network_reqs.html#network-requirements-subnets) details. 

Kubernetes worker nodes can run in the cluster subnets, but it is not recommended. During [cluster upgrades](https://aws.github.io/aws-eks-best-practices/upgrades/#verify-available-ip-addresses) Amazon EKS provisions additional ENIs in the cluster subnets. When your cluster scales out, worker nodes and pods may consume the available IPs in the cluster subnet. Hence in order to make sure there are enough available IPs you might want to consider using dedicated cluster subnets with /28 netmask.

Kubernetes worker nodes can run in either a public or a private subnet. Whether a subnet is public or private refers to whether traffic within the subnet is routed through an [internet gateway](https://docs.aws.amazon.com/vpc/latest/userguide/VPC_Internet_Gateway.html). Public subnets have a route table entry to the internet through the internet gateway, but private subnets don't.

The traffic that originates somewhere else and reaches your nodes is called *ingress*. Traffic that originates from the nodes and leaves the network is called *egress*. Nodes with public or elastic IP addresses (EIPs) within a subnet configured with an internet gateway allow ingress from outside of the VPC. Private subnets usually include a [NAT gateway](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-nat-gateway.html), which only allows ingress traffic to the nodes from within the VPC while still allowing traffic *from* the nodes to leave the VPC (*egress*).

In the IPv6 world, every address is internet routable. The IPv6 addresses associated with the nodes and pods are public. Private subnets are supported by implementing an [egress-only internet gateways (EIGW)](https://docs.aws.amazon.com/vpc/latest/userguide/egress-only-internet-gateway.html) in a VPC, allowing outbound traffic while blocking all incoming traffic. Best practices for implementing IPv6 subnets can be found in the [VPC user guide](https://docs.aws.amazon.com/vpc/latest/userguide/VPC_Scenario2.html).

### You can configure VPC and Subnets in three different ways:

#### Using only public subnets

In the same public subnets, both nodes and ingress resources (such as load balancers) are created. Tag the public subnet with [`kubernetes.io/role/elb`](http://kubernetes.io/role/elb) to construct load balancers that face the internet. In this configuration, the cluster endpoint can be configured to be public, private, or both (public and private).

#### Using private and public subnets

Nodes are created on private subnets, whereas Ingress resources are instantiated in public subnets. You can enable public, private, or both (public and private) access to the cluster endpoint. Depending on the configuration of the cluster endpoint, node traffic will enter via the NAT gateway or the ENI.

#### Using only private subnets

Both nodes and ingress are created in private subnets. Using the [`kubernetes.io/role/internal-elb`](http://kubernetes.io/role/internal-elb:1) subnet tag to construct internal load balancers. Accessing your cluster's endpoint will require a VPN connection. You must activate [AWS PrivateLink](https://docs.aws.amazon.com/vpc/latest/userguide/endpoint-service.html) for EC2 and all Amazon ECR and S3 repositories. Only the private endpoint of the cluster should be enabled. We suggest going through the [EKS private cluster requirements](https://docs.aws.amazon.com/eks/latest/userguide/private-clusters.html) before provisioning private clusters.


### Communication across VPCs

There are many scenarios when you require multiple VPCs and separate EKS clusters deployed to these VPCs. Multiple VPCs are needed when you have to support security, billing, multiple regions, or internal charge-back requirements. We recommend following the design patterns mentioned in the VPC-to-VPC connectivity [guide](https://docs.aws.amazon.com/whitepapers/latest/aws-vpc-connectivity-options/amazon-vpc-to-amazon-vpc-connectivity-options.html) to integrate multiple Amazon VPCs into a larger virtual network. 

VPC connectivity is best achieved when using non-overlapping IP ranges for each VPC being connected. For operational efficiency, we strongly recommend deploying EKS clusters and nodes to IP ranges that do not overlap. We suggest [Private NAT Gateway](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-nat-gateway.html#nat-gateway-basics), or VPC CNI in [custom networking](../custom-networking/index.md) mode in conjunction with [transit gateway](https://docs.aws.amazon.com/whitepapers/latest/aws-vpc-connectivity-options/aws-transit-gateway.html) to integrate workloads on EKS to solve overlapping CIDR challenges while preserving routable RFC1918 IP addresses. Consider utilizing [AWS PrivateLink](https://docs.aws.amazon.com/vpc/latest/privatelink/privatelink-share-your-services.html), also known as an endpoint service, if you are the service provider and would want to share your Kubernetes service and ingress (either ALB or NLB) with your customer VPC in separate accounts.

### Sharing VPC across multiple accounts

Many enterprises adopted shared Amazon VPCs as a means to streamline network administration, reduce costs and improve security across multiple AWS Accounts in an AWS Organization. They utilize AWS Resource Access Manager (RAM) to securely share supported [AWS resources](https://docs.aws.amazon.com/ram/latest/userguide/shareable.html) with individual AWS Accounts, organizational units (OUs) or entire AWS Organization.

You can deploy Amazon EKS clusters, managed node groups and other supporting AWS resources (like LoadBalancers, security groups, end points, etc.,) in shared VPC Subnets from an another AWS Account using AWS RAM. Below figure depicts an example highlevel architecture. This allows central networking teams control over the networking constructs like VPCs, Subnets, etc., while allowing application or platform teams to deploy Amazon EKS clusters in their respective AWS Accounts. A complete walkthrough of this scenario is available at this [github repository](https://github.com/aws-samples/eks-shared-subnets).

![Deploying Amazon EKS in VPC Shared Subnets across AWS Accounts.](./eks-shared-subnets.png)

#### Considerations when using Shared Subnets

* Amazon EKS clusters and worker nodes can be created within shared subnets that are all part of the same VPC. Amazon EKS does not support the creation of clusters across multiple VPCs. 

* Amazon EKS uses AWS VPC Security Groups (SGs) to control the traffic between the Kubernetes control plane and the cluster's worker nodes. Security groups are also used to control the traffic between worker nodes, and other VPC resources, and external IP addresses. You must create these security groups in the application/participant account. Ensure that the security groups you intend to use for your pods are also located in the participant account. You can configure the inbound and outbound rules within your security groups to permit the necessary traffic to and from security groups located in the Central VPC account.

* Create IAM roles and associated policies within the participant account where your Amazon EKS cluster resides. These IAM roles and policies are essential for granting the necessary permissions to Kubernetes clusters managed by Amazon EKS, as well as to the nodes and pods running on Fargate. The permissions enable Amazon EKS to make calls to other AWS services on your behalf.

* You can follow following approaches to allow cross Account access to AWS resources like Amazon S3 buckets, Dynamodb tables, etc., from k8s pods:
    * **Resource based policy approach**: If the AWS service supports resource policies, you can add appropriate resource based policy to allow cross account access to IAM Roles assigned to the kubernetes pods. In this scenario, OIDC provider, IAM Roles, and permission policies exist in the application account. To find AWS Services that support Resource based policies, refer [AWS services that work with IAM](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_aws-services-that-work-with-iam.html) and look for the services that have Yes in the Resource Based column.

    * **OIDC Provider approach**: IAM resources like OIDC Provider, IAM Roles, Permission, and Trust policies will be created in other participant AWS Account where the resources exists. These roles will be assigned to Kubernetes pods in application account, so that they can access cross account resources. Refer [Cross account IAM roles for Kubernetes service accounts](https://aws.amazon.com/blogs/containers/cross-account-iam-roles-for-kubernetes-service-accounts/) blog for a complete walkthrough of this approach.

* You can deploy the Amazon Elastic Loadbalancer (ELB) resources (ALB or NLB) to route traffic to k8s pods either in application or central networking accounts. Refer to [Expose Amazon EKS Pods Through Cross-Account Load Balancer](https://aws.amazon.com/blogs/containers/expose-amazon-eks-pods-through-cross-account-load-balancer/) walkthrough for detailed instructions on deploying the ELB resources in central networking account. This option offers enhanced flexibility, as it grants the Central Networking account full control over the security configuration of the Load Balancer resources.

* When using `custom networking feature` of Amazon VPC CNI, you need to use the Availability Zone (AZ) ID mappings listed in the central networking account to create each `ENIConfig`. This is due to random mapping of physical AZs to the AZ names in each AWS account.

### Security Groups 

A [*security group*](https://docs.aws.amazon.com/vpc/latest/userguide/VPC_SecurityGroups.html) controls the traffic that is allowed to reach and leave the resources that it is associated with. Amazon EKS uses security groups to manage the communication between the [control plane and nodes](https://docs.aws.amazon.com/eks/latest/userguide/sec-group-reqs.html). When you create a cluster, Amazon EKS creates a security group that's named `eks-cluster-sg-my-cluster-uniqueID`. EKS associates these security groups to the managed ENIs and the nodes. The default rules allow all traffic to flow freely between your cluster and nodes, and allows all outbound traffic to any destination. 

When you create a cluster, you can specify your own security groups. Please see [recommendation for security groups](https://docs.aws.amazon.com/eks/latest/userguide/sec-group-reqs.html) when you specify own security groups. 

## Recommendations

### Consider Multi-AZ  Deployment

AWS Regions provide multiple physically separated and isolated Availability Zones (AZ), which are connected with low-latency, high-throughput, and highly redundant networking. With Availability Zones, you can design and operate applications that automatically fail over between Availability Zones without interruption. Amazon EKS strongly recommends deploying EKS clusters to multiple availability zones. Please consider specifying subnets in at least two availability zones when you create the cluster.

Kubelet running on nodes automatically adds labels to the node object such as [`topology.kubernetes.io/region=us-west-2`, and `topology.kubernetes.io/zone=us-west-2d`](http://topology.kubernetes.io/region=us-west-2,topology.kubernetes.io/zone=us-west-2d). We recommend to use node labels in conjunction with [Pod topology spread constraints](https://kubernetes.io/docs/concepts/scheduling-eviction/topology-spread-constraints/) to control how Pods are spread across zones. These hints enable Kubernetes [scheduler](https://kubernetes.io/docs/reference/command-line-tools-reference/kube-scheduler/) to place Pods for better expected availability, reducing the risk that a correlated failure affects your whole workload. Please refer [Assigning nodes to Pods](https://kubernetes.io/docs/concepts/scheduling-eviction/assign-pod-node/#nodeselector) to see examples for node selector and AZ spread constraints.

You can define the subnets or availability zones when you create nodes. The nodes are placed in cluster subnets if no subnets are configured. EKS support for managed node groups automatically spreads the nodes across multiple availability zones on available capacity. [Karpenter](https://karpenter.sh/)will honor the AZ spread placement by scaling nodes to specified AZs if workloads define topology spread limits.

AWS Elastic Load Balancers are managed by the AWS Load Balancer Controller for a Kubernetes cluster. It provisions an Application Load Balancer (ALB) for Kubernetes ingress resources and a Network Load Balancer (NLB) for Kubernetes services of type Loadbalancer. The Elastic Load Balancer controller uses [tags](https://aws.amazon.com/premiumsupport/knowledge-center/eks-vpc-subnet-discovery/) to discover the subnets. ELB controller requires a minimum of two availability zones (AZs) to provision ingress resource successfully. Consider setting subnets in at least two AZs to take advantage of geographic redundancy's safety and reliability. 

### Deploy Nodes to Private Subnets

A VPC including both private and public subnets is the ideal method for deploying Kubernetes workloads on EKS. Consider setting a minimum of two public subnets and two private subnets in two distinct availability zones. The related route table of a public subnet contains a route to an internet gateway . Pods are able to interact with the Internet via a NAT gateway. Private subnets are supported by [egress-only internet gateways](https://docs.aws.amazon.com/vpc/latest/userguide/egress-only-internet-gateway.html) in the IPv6 environment (EIGW).

Instantiating nodes in private subnets offers maximal control over traffic to the nodes and is effective for the vast majority of Kubernetes applications. Ingress resources (like as load balancers) are instantiated in public subnets and route traffic to Pods operating on private subnets.

Consider private only mode if you demand strict security and network isolation. In this configuration, three private subnets are deployed in distinct Availability Zones within the AWS Region's VPC. The resources deployed to the subnets cannot access the internet, nor can the internet access the resources in the subnets. In order for your Kubernetes application to access other AWS services, you must configure PrivateLink interfaces and/or gateway endpoints. You may setup internal load balancers to redirect traffic to Pods using AWS Load Balancer Controller. The private subnets must be tagged ([`kubernetes.io/role/internal-elb: 1`](http://kubernetes.io/role/internal-elb)) for the controller to provision load balancers. For nodes to register with the cluster, the cluster endpoint must be set to private mode.  Please visit [private cluster guide](https://docs.aws.amazon.com/eks/latest/userguide/private-clusters.html) for complete requirements and considerations.

### Consider Public and Private Mode for Cluster Endpoint

Amazon EKS offers public-only, public-and-private, and private-only cluster endpoint modes. The default mode is public-only, however we recommend configuring cluster endpoint in public and private mode. This option allows Kubernetes API calls within your cluster's VPC (such as node-to-control-plane communication) to utilize the private VPC endpoint and traffic to remain within your cluster's VPC. Your cluster API server, on the other hand, can be reached from the internet. However, we strongly recommend limiting the CIDR blocks that can use the public endpoint. [Learn how to configure public and private endpoint access, including limiting CIDR blocks.](https://docs.aws.amazon.com/eks/latest/userguide/cluster-endpoint.html#modify-endpoint-access)

We suggest a private-only endpoint when you need security and network isolation. We recommend using either of the options listed in the [EKS user guide](https://docs.aws.amazon.com/eks/latest/userguide/cluster-endpoint.html#private-access) to connect to an API server privately.

### Check available IPs

When you create a cluster, Amazon EKS creates up to 4 elastic network interfaces in the cluster subnets. When you upgrade the cluster, Amazon EKS creates new X-ENIs and deletes the old ones when the upgrade is successful. Amazon EKS recommends a netmask of /28 (16 IP addresses) for cluster subnets to accommodate upgrades of the cluster.

Before building VPC and subnets, it is advised to work backwards from the required workload scale. When clusters are built using “ekstcl”, /19 subnets are created by default. A netmask of /19 is suitable for the majority of workload types. To learn about Pod IP allocations, refer [Amazon VPC CNI](../vpc-cni/index.md). Consider using [subnet-calc](../subnet-calc/subnet-calc.xlsx), a tool developed by EKS to help with subnet sizing.

For IPv6 VPCs, a subnet's CIDR block has a fixed prefix length of `/64`. We recommend to deploy nodes and workloads to cluster subnets to maximize IP usage. 

### Configure Security Groups Carefully

Amazon EKS supports using custom security groups. Any custom security groups must allow communication between nodes and the Kubernetes control plane. Please check [port requirements](https://docs.aws.amazon.com/eks/latest/userguide/sec-group-reqs.html) and configure rules manually when your organization doesn't allow for open communication. 

EKS applies the custom security groups that you provide during cluster creation to the managed interfaces (X-ENIs). However, it does not immediately associate them with nodes. While creating node groups, it is strongly recommended to [associate custom security groups](https://eksctl.io/usage/schema/#nodeGroups-securityGroups) manually. Please consider enabling [securityGroupSelector](https://karpenter.sh/docs/concepts/node-templates/#specsecuritygroupselector) to enable Karpenter node template discovery of custom security groups during autoscaling of nodes. 

We strongly recommend creating a security group to allow all inter-node communication traffic. During the bootstrap process, nodes require outbound Internet connectivity to access the cluster endpoint. Evaluate outward access requirements, such as on-premise connection and container registry access, and set rules appropriately. Before putting changes into production, we strongly suggest that you check connections carefully in your development environment.

### Deploy NAT Gateways in each Availability Zone

If you deploy nodes in private subnets (IPv4 and IPv6), consider creating a NAT Gateway in each Availability Zone (AZ) to ensure zone-independent architecture and reduce cross AZ expenditures. Each NAT gateway in an AZ is implemented with redundancy.

### Use Cloud9 to access Private Clusters

AWS Cloud9 is a web-based IDE than can run securely in Private Subnets without ingress access, using AWS Systems Manager. Egress can also be disabled on the Cloud9 instance. [Learn more about using Cloud9 to access private clusters and subnets.](https://aws.amazon.com/blogs/security/isolating-network-access-to-your-aws-cloud9-environments/)

![illustration of AWS Cloud9 console connecting to no-ingress EC2 instance.](./image-2.jpg)

