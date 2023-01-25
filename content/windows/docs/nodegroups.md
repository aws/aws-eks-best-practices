# Creating a managed node group<a name="create-managed-node-group"></a>

This topic describes how you can launch Amazon EKS managed node groups of nodes that register with your Amazon EKS cluster\. After the nodes join the cluster, you can deploy Kubernetes applications to them\.

If this is your first time launching an Amazon EKS managed node group, we recommend that you follow one of our [Getting started with Amazon EKS](getting-started.md) guides instead\. The guides provide walkthroughs for creating an Amazon EKS cluster with nodes\.

**Important**  
Amazon EKS nodes are standard Amazon EC2 instances\. You're billed based on the normal Amazon EC2 prices\. For more information, see [Amazon EC2 Pricing](https://aws.amazon.com/ec2/pricing/)\.
You can't create managed nodes in an AWS Region where you have AWS Outposts, AWS Wavelength, or AWS Local Zones enabled\. You can create self\-managed nodes in an AWS Region where you have AWS Outposts, AWS Wavelength, or AWS Local Zones enabled\. For more information, see [Launching self\-managed Amazon Linux nodes](launch-workers.md), [Launching self\-managed Windows nodes](launch-windows-workers.md), and [Launching self\-managed Bottlerocket nodes](launch-node-bottlerocket.md)\. You can also create a self\-managed Amazon Linux node group on an Outpost\. For more information, see [Launching self\-managed Amazon Linux nodes on an Outpost](eks-outposts-self-managed-nodes.md)\.

**Prerequisites**
+ An existing Amazon EKS cluster\. To deploy one, see [Creating an Amazon EKS cluster](create-cluster.md)\.
+ \(Optional, but recommended\) The Amazon VPC CNI plugin for Kubernetes add\-on configured with its own IAM role that has the necessary IAM policy attached to it\. For more information, see [Configuring the Amazon VPC CNI plugin for Kubernetes to use IAM roles for service accounts](cni-iam-role.md)\.
+ Familiarity with the considerations listed in [Choosing an Amazon EC2 instance type](choosing-instance-type.md)\. Depending on the instance type you choose, there may be additional prerequisites for your cluster and VPC\.

You can create a managed node group with `eksctl` or the AWS Management Console\.

------
#### [ eksctl ]

**To create a managed node group with `eksctl`**

This procedure requires `eksctl` version `0.126.0` or later\. You can check your version with the following command:

```
eksctl version
```

For instructions on how to install or upgrade `eksctl`, see [Installing or updating `eksctl`](eksctl.md)\.

1. \(Optional\) If the **AmazonEKS\_CNI\_Policy** managed IAM policy is attached to your [Amazon EKS node IAM role](create-node-role.md), we recommend assigning it to an IAM role that you associate to the Kubernetes `aws-node` service account instead\. For more information, see [Configuring the Amazon VPC CNI plugin for Kubernetes to use IAM roles for service accounts](cni-iam-role.md)\.

1. Create a managed node group with or without using a custom launch template\. Manually specifying a launch template allows for greater customization of a node group\. For example, it can allow deploying a custom AMI or providing arguments to the `boostrap.sh` script in an Amazon EKS optimized AMI\. For a complete list of every available option and default, enter the following command\.

   ```
   eksctl create nodegroup --help
   ```

   In the following command, replace `my-cluster` with the name of your cluster and replace `my-mng` with the name of your node group\. The names can contain only alphanumeric characters \(case\-sensitive\) and hyphens\. The names must start with an alphabetic character and can't be longer than 100 characters\.
**Important**  
If you don't use a custom launch template when first creating a managed node group, don't use one at a later time for the node group\. If you didn't specify a custom launch template, the system auto\-generates a launch template that we don't recommend that you modify manually\. Manually modifying this auto\-generated launch template might cause errors\.
   + **Without a launch template** – `eksctl` creates a default Amazon EC2 launch template in your account and deploys the node group using a launch template that it creates based on options that you specify\. Before specifying a value for `--node-type`, see [Choosing an Amazon EC2 instance type](choosing-instance-type.md)\. 

     Replace `ami-family` with an allowed keyword\. For more information, see [Setting the node AMI Family](https://eksctl.io/usage/custom-ami-support/#setting-the-node-ami-family) in the `eksctl` documentation\. Replace `my-key` with the name of your Amazon EC2 key pair or public key\. This key is used to SSH into your nodes after they launch\.
**Note**  
For Windows, this command doesn't enable SSH\. Instead, it associates your Amazon EC2 key pair with the instance so that you can obtain your RDP password\. Then you must configure your security group to open the Windows port `3389` before you can use RDP\.

     If you don't already have an Amazon EC2 key pair, you can create one in the AWS Management Console\. For Linux information, see [Amazon EC2 key pairs and Linux instances](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-key-pairs.html) in the *Amazon EC2 User Guide for Linux Instances*\. For Windows information, see [Amazon EC2 key pairs and Windows instances](https://docs.aws.amazon.com/AWSEC2/latest/WindowsGuide/ec2-key-pairs.html) in the *Amazon EC2 User Guide for Windows Instances*\.

     We recommend blocking pod access to IMDS if the following conditions are true:
     + You plan to assign IAM roles to all of your Kubernetes service accounts so that pods only have the minimum permissions that they need\.
     + No pods in the cluster require access to the Amazon EC2 instance metadata service \(IMDS\) for other reasons, such as retrieving the current AWS Region\.

     For more information, see [Restrict access to the instance profile assigned to the worker node](https://aws.github.io/aws-eks-best-practices/security/docs/iam/#restrict-access-to-the-instance-profile-assigned-to-the-worker-node)\.

     If you want to block pod access to IMDS, then add the `--disable-pod-imds` option to the following command\.

     ```
     eksctl create nodegroup \
       --cluster my-cluster \
       --region region-code \
       --name my-mng \
       --node-ami-family ami-family \
       --node-type m5.large \
       --nodes 3 \
       --nodes-min 2 \
       --nodes-max 4 \
       --ssh-access \
       --ssh-public-key my-key
     ```

     Your instances can optionally assign a significantly higher number of IP addresses to pods, assign IP addresses to pods from a different CIDR block than the instance's, and be deployed to a cluster without internet access\. For more information, see [Increase the amount of available IP addresses for your Amazon EC2 nodes](cni-increase-ip-addresses.md), [Tutorial: Custom networking](cni-custom-network.md), and [Private cluster requirements](private-clusters.md) for additional options to add to the previous command\.

     Managed node groups calculates and applies a single value for the maximum number of pods that can run on each node of your node group, based on instance type\. If you create a node group with different instance types, the smallest value calculated across all instance types is applied as the maximum number of pods that can run on every instance type in the node group\. Managed node groups calculates the value using the script referenced in [Amazon EKS recommended maximum pods for each Amazon EC2 instance type](choosing-instance-type.md#determine-max-pods)\.
   + **With a launch template** – The launch template must already exist and must meet the requirements specified in [Launch template configuration basics](launch-templates.md#launch-template-basics)\.

     We recommend blocking pod access to IMDS if the following conditions are true:
     + You plan to assign IAM roles to all of your Kubernetes service accounts so that pods only have the minimum permissions that they need\.
     + No pods in the cluster require access to the Amazon EC2 instance metadata service \(IMDS\) for other reasons, such as retrieving the current AWS Region\.

     For more information, see [Restrict access to the instance profile assigned to the worker node](https://aws.github.io/aws-eks-best-practices/security/docs/iam/#restrict-access-to-the-instance-profile-assigned-to-the-worker-node)\.

     If you want to block pod access to IMDS, then specify the necessary settings in the launch template\.

     1. Copy the following contents to your device\. Replace the *example values* and then run the modified command to create the `eks-nodegroup.yaml` file\. Several settings that you specify when deploying without a launch template are moved into the launch template\. If you don't specify a `version`, the template's default version is used\.

        ```
        cat >eks-nodegroup.yaml <<EOF
        apiVersion: eksctl.io/v1alpha5
        kind: ClusterConfig
        metadata:
          name: my-cluster
          region: region-code
        managedNodeGroups:
        - name: my-mng
          launchTemplate:
            id: lt-id
            version: "1"
        EOF
        ```

        For a complete list of `eksctl` config file settings, see [Config file schema](https://eksctl.io/usage/schema/) in the `eksctl` documentation\. Your instances can optionally assign a significantly higher number of IP addresses to pods, assign IP addresses to pods from a different CIDR block than the instance's, use the `containerd` runtime, and be deployed to a cluster without outbound internet access\. For more information, see [Increase the amount of available IP addresses for your Amazon EC2 nodes](cni-increase-ip-addresses.md), [Tutorial: Custom networking](cni-custom-network.md), [Enable the `containerd` runtime bootstrap flag](eks-optimized-ami.md#containerd-bootstrap), and [Private cluster requirements](private-clusters.md) for additional options to add to the config file\.

        If you didn't specify an AMI ID in your launch template, managed node groups calculates and applies a single value for the maximum number of pods that can run on each node of your node group, based on instance type\. If you create a node group with different instance types, the smallest value calculated across all instance types is applied as the maximum number of pods that can run on every instance type in the node group\. Managed node groups calculates the value using the script referenced in [Amazon EKS recommended maximum pods for each Amazon EC2 instance type](choosing-instance-type.md#determine-max-pods)\.

        If you specified an AMI ID in your launch template, specify the maximum number of pods that can run on each node of your node group if you're using [custom networking](cni-custom-network.md) or want to [increase the number of IP addresses assigned to your instance](cni-increase-ip-addresses.md)\. For more information, see [Amazon EKS recommended maximum pods for each Amazon EC2 instance type](choosing-instance-type.md#determine-max-pods)\.

     1. Deploy the nodegroup with the following command\.

        ```
        eksctl create nodegroup --config-file eks-nodegroup.yaml
        ```

------
#### [ AWS Management Console ]

**To create a managed node group using the AWS Management Console**

1. Wait for your cluster status to show as `ACTIVE`\. You can't create a managed node group for a cluster that isn't already `ACTIVE`\.

1. Open the Amazon EKS console at [https://console\.aws\.amazon\.com/eks/home\#/clusters](https://console.aws.amazon.com/eks/home#/clusters)\.

1. Choose the name of the cluster that you want to create a managed node group in\.

1. Select the **Compute** tab\.

1. Choose **Add node group**\.

1. On the **Configure node group** page, fill out the parameters accordingly, and then choose **Next**\.
   + **Name** – Enter a unique name for your managed node group\. The name can contain only alphanumeric characters \(case\-sensitive\) and hyphens\. It must start with an alphabetic character and can't be longer than 100 characters\.
   + **Node IAM role** – Choose the node instance role to use with your node group\. For more information, see [Amazon EKS node IAM role](create-node-role.md)\.
**Important**  
You can't use the same role that is used to create any clusters\.
We recommend using a role that's not currently in use by any self\-managed node group\. Otherwise, you plan to use with a new self\-managed node group\. For more information, see [Deleting a managed node group](delete-managed-node-group.md)\.
   + **Use launch template** – \(Optional\) Choose if you want to use an existing launch template\. Select a **Launch Template Name**\. Then, select a **Launch template version**\. If you don't select a version, then Amazon EKS uses the template's default version\. Launch templates allow for more customization of your node group, such as allowing you to deploy a custom AMI, assign a significantly higher number of IP addresses to pods, assign IP addresses to pods from a different CIDR block than the instance's, enable the `containerd` runtime for your instances, and deploying nodes to a cluster without outbound internet access\. For more information, see [Increase the amount of available IP addresses for your Amazon EC2 nodes](cni-increase-ip-addresses.md), [Tutorial: Custom networking](cni-custom-network.md), [Enable the `containerd` runtime bootstrap flag](eks-optimized-ami.md#containerd-bootstrap), and [Private cluster requirements](private-clusters.md)\. 

     The launch template must meet the requirements in [Launch template support](launch-templates.md)\. If you don't use your own launch template, the Amazon EKS API creates a default Amazon EC2 launch template in your account and deploys the node group using the default launch template\. 

     If you implement [IAM roles for service accounts](iam-roles-for-service-accounts.md), assign necessary permissions directly to every pod that requires access to AWS services, and no pods in your cluster require access to IMDS for other reasons, such as retrieving the current AWS Region, then you can also disable access to IMDS for pods that don't use host networking in a launch template\. For more information, see [Restrict access to the instance profile assigned to the worker node](https://aws.github.io/aws-eks-best-practices/security/docs/iam/#restrict-access-to-the-instance-profile-assigned-to-the-worker-node)\.
   + **Kubernetes labels** – \(Optional\) You can choose to apply Kubernetes labels to the nodes in your managed node group\.
   + **Kubernetes taints** – \(Optional\) You can choose to apply Kubernetes taints to the nodes in your managed node group\. The available options in the **Effect** menu are `NoSchedule`, `NoExecute`, and `PreferNoSchedule` \.
   + **Tags** – \(Optional\) You can choose to tag your Amazon EKS managed node group\. These tags don't propagate to other resources in the node group, such as Auto Scaling groups or instances\. For more information, see [Tagging your Amazon EKS resources](eks-using-tags.md)\.

1. On the **Set compute and scaling configuration** page, fill out the parameters accordingly, and then choose **Next**\.
   + **AMI type** – Select an AMI type\. If you are deploying Arm instances, be sure to review the considerations in [Amazon EKS optimized Arm Amazon Linux AMIs](eks-optimized-ami.md#arm-ami) before deploying\.

     If you specified a launch template on the previous page, and specified an AMI in the launch template, then you can't select a value\. The value from the template is displayed\. The AMI specified in the template must meet the requirements in [Specifying an AMI](launch-templates.md#launch-template-custom-ami)\.
   + **Capacity type** – Select a capacity type\. For more information about choosing a capacity type, see [Managed node group capacity types](managed-node-groups.md#managed-node-group-capacity-types)\. You can't mix different capacity types within the same node group\. If you want to use both capacity types, create separate node groups, each with their own capacity and instance types\.
   + **Instance types** – By default, one or more instance type is specified\. To remove a default instance type, select the `X` on the right side of the instance type\. Choose the instance types to use in your managed node group\. For more information, see [Choosing an Amazon EC2 instance type](choosing-instance-type.md)\.

     The console displays a set of commonly used instance types\. If you need to create a managed node group with an instance type that's not displayed, then use `eksctl`, the AWS CLI, AWS CloudFormation, or an SDK to create the node group\. If you specified a launch template on the previous page, then you can't select a value because the instance type must be specified in the launch template\. The value from the launch template is displayed\. If you selected **Spot** for **Capacity type**, then we recommend specifying multiple instance types to enhance availability\.
   + **Disk size** – Enter the disk size \(in GiB\) to use for your node's root volume\.

     If you specified a launch template on the previous page, then you can't select a value because it must be specified in the launch template\.
   + **Desired size** – Specify the current number of nodes that the managed node group should maintain at launch\.
**Note**  
Amazon EKS doesn't automatically scale your node group in or out\. However, you can configure the Kubernetes [Cluster Autoscaler](autoscaling.md#cluster-autoscaler) to do this for you\.
   + **Minimum size** – Specify the minimum number of nodes that the managed node group can scale in to\.
   + **Maximum size** – Specify the maximum number of nodes that the managed node group can scale out to\.
   + **Node group update configuration** – \(Optional\) You can select the number or percentage of nodes to be updated in parallel\. These nodes will be unavailable during the update\. For **Maximum unavailable**, select one of the following options and specify a **Value**:
     + **Number** – Select and specify the number of nodes in your node group that can be updated in parallel\.
     + **Percentage** – Select and specify the percentage of nodes in your node group that can be updated in parallel\. This is useful if you have a large number of nodes in your node group\.

1. On the **Specify networking** page, fill out the parameters accordingly, and then choose **Next**\.
   + **Subnets** – Choose the subnets to launch your managed nodes into\. 
**Important**  
If you are running a stateful application across multiple Availability Zones that is backed by Amazon EBS volumes and using the Kubernetes [Cluster Autoscaler](autoscaling.md#cluster-autoscaler), you should configure multiple node groups, each scoped to a single Availability Zone\. In addition, you should enable the `--balance-similar-node-groups` feature\.
**Important**  
If you choose a public subnet, and your cluster has only the public API server endpoint enabled, then the subnet must have `MapPublicIPOnLaunch` set to `true` for the instances to successfully join a cluster\. If the subnet was created using `eksctl` or the [Amazon EKS vended AWS CloudFormation templates](creating-a-vpc.md) on or after March 26, 2020, then this setting is already set to `true`\. If the subnets were created with `eksctl` or the AWS CloudFormation templates before March 26, 2020, then you need to change the setting manually\. For more information, see [Modifying the public `IPv4` addressing attribute for your subnet](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-ip-addressing.html#subnet-public-ip)\.
If you use a launch template and specify multiple network interfaces, Amazon EC2 won't auto\-assign a public `IPv4` address, even if `MapPublicIpOnLaunch` is set to `true`\. For nodes to join the cluster in this scenario, you must either enable the cluster's private API server endpoint, or launch nodes in a private subnet with outbound internet access provided through an alternative method, such as a NAT Gateway\. For more information, see [Amazon EC2 instance IP addressing](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-instance-addressing.html) in the *Amazon EC2 User Guide for Linux Instances*\.
   + **Configure SSH access to nodes** \(Optional\)\. Enabling SSH allows you to connect to your instances and gather diagnostic information if there are issues\. We highly recommend enabling remote access when you create a node group\. You can't enable remote access after the node group is created\.

     If you chose to use a launch template, then this option isn't shown\. To enable remote access to your nodes, specify a key pair in the launch template and ensure that the proper port is open to the nodes in the security groups that you specify in the launch template\. For more information, see [Using custom security groups](launch-templates.md#launch-template-security-groups)\.
**Note**  
For Windows, this option doesn't enable SSH\. Instead, it associates your Amazon EC2 key pair with the instance so that you can obtain your RDP password\. Then you must configure your security group to open the Windows port `3389` before you can use RDP\.
   + For **SSH key pair** \(Optional\), choose an Amazon EC2 SSH key to use\. For Linux information, see [Amazon EC2 key pairs and Linux instances](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-key-pairs.html) in the *Amazon EC2 User Guide for Linux Instances*\. For Windows information, see [Amazon EC2 key pairs and Windows instances](https://docs.aws.amazon.com/AWSEC2/latest/WindowsGuide/ec2-key-pairs.html) in the *Amazon EC2 User Guide for Windows Instances*\. If you chose to use a launch template, then you can't select one\. When an Amazon EC2 SSH key is provided for node groups using Bottlerocket AMIs, the administrative container is also enabled\. For more information, see [Admin container](https://github.com/bottlerocket-os/bottlerocket#admin-container) on GitHub\.
   + For **Allow SSH remote access from**, if you want to limit access to specific instances, then select the security groups that are associated to those instances\. If you don't select specific security groups, then SSH access is allowed from anywhere on the internet \(`0.0.0.0/0`\)\.

1. On the **Review and create** page, review your managed node group configuration and choose **Create**\.

   If nodes fail to join the cluster, then see [Nodes fail to join cluster](troubleshooting.md#worker-node-fail) in the Troubleshooting guide\.

1. Watch the status of your nodes and wait for them to reach the `Ready` status\.

   ```
   kubectl get nodes --watch
   ```

1. \(GPU nodes only\) If you chose a GPU instance type and the Amazon EKS optimized accelerated AMI, then you must apply the [NVIDIA device plugin for Kubernetes](https://github.com/NVIDIA/k8s-device-plugin) as a DaemonSet on your cluster with the following command\.

   ```
   kubectl apply -f https://raw.githubusercontent.com/NVIDIA/k8s-device-plugin/v0.9.0/nvidia-device-plugin.yml
   ```

1. \(Optional\) After you add Linux nodes to your cluster, follow the procedures in [Enabling Windows support for your Amazon EKS cluster](windows-support.md) to add Windows support to your cluster and to add Windows worker nodes\. Every Amazon EKS cluster must contain at least one Linux node, even if you only want to run Windows workloads in your cluster\.

------

Now that you have a working Amazon EKS cluster with nodes, you're ready to start installing Kubernetes add\-ons and deploying applications to your cluster\. The following documentation topics help you to extend the functionality of your cluster\.
+ The IAM entity \(user or role\) that created the cluster is the only IAM entity that can make calls to the Kubernetes API server with `kubectl` or the AWS Management Console\. If you want other IAM users or roles to have access to your cluster, then you need to add them\. For more information, see [Enabling IAM user and role access to your cluster](add-user-role.md) and [Required permissions](view-kubernetes-resources.md#view-kubernetes-resources-permissions)\.
+ We recommend blocking pod access to IMDS if the following conditions are true:
  + You plan to assign IAM roles to all of your Kubernetes service accounts so that pods only have the minimum permissions that they need\.
  + No pods in the cluster require access to the Amazon EC2 instance metadata service \(IMDS\) for other reasons, such as retrieving the current AWS Region\.

  For more information, see [Restrict access to the instance profile assigned to the worker node](https://aws.github.io/aws-eks-best-practices/security/docs/iam/#restrict-access-to-the-instance-profile-assigned-to-the-worker-node)\.
+ [Cluster Autoscaler](autoscaling.md#cluster-autoscaler) – Configure the Kubernetes Cluster Autoscaler to automatically adjust the number of nodes in your node groups\.
+ Deploy a [sample application](sample-deployment.md) to your cluster\.
+ [Cluster management](eks-managing.md) – Learn how to use important tools for managing your cluster\.