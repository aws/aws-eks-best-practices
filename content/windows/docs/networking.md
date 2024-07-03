# Windows Networking

## Windows Container Networking Overview
Windows containers are fundamentally different than Linux containers. Linux containers use Linux constructs like namespaces, the union file system, and cgroups. On Windows, those constructs are abstracted from containerd by the [Host Compute Service (HCS)](https://github.com/microsoft/hcsshim). HCS acts as an API layer that sits above the container implementation on Windows. Windows containers also leverage the Host Network Service (HNS) that defines the network topology on a node. 

![](./images/windows-networking.png)

From a networking perspective, HCS and HNS make Windows containers function like virtual machines. For example, each container has a virtual network adapter (vNIC) that is connected to a Hyper-V virtual switch (vSwitch) as shown in the diagram above.

## IP Address Management
A node in Amazon EKS uses it's Elastic Network Interface (ENI) to connect to an AWS VPC network. Presently, **only a single ENI per Windows worker node is supported**. The IP address management for Windows nodes is performed by [VPC Resource Controller](https://github.com/aws/amazon-vpc-resource-controller-k8s) which runs in control plane. More details about the workflow for IP address management of Windows nodes can be found [here](https://github.com/aws/amazon-vpc-resource-controller-k8s#windows-ipv4-address-management).

The number of pods that a Windows worker node can support is dictated by the size of the node and the number of available IPv4 addresses. You can calculate the IPv4 address available on the node as below:
- By default, only secondary IPv4 addresses are assigned to the ENI. In such a case:
  ```
  Total IPv4 addresses available for Pods = Number of supported IPv4 addresses in the primary interface - 1
  ```
  We subtract one from the total count since one IPv4 addresses will be used as the primary address of the ENI and hence cannot be allocated to the Pods.

- If the cluster has been configured for high pod density by enabling [prefix delegation feature](../../networking/prefix-mode/index_windows.md) then-
  ```
  Total IPv4 addresses available for Pods = (Number of supported IPv4 addresses in the primary interface - 1) * 16
  ```
  Here, instead of allocating secondary IPv4 addresses, VPC Resource Controller will allocate `/28 prefixes` and therefore, the overall number of available IPv4 addresses will be boosted 16 times.

Using the formula above, we can calculate max pods for an Windows worker noded based on a m5.large instance as below:
- By default, when running in secondary IP mode-
  ```
  10 secondary IPv4 addresses per ENI - 1 = 9 available IPv4 addresses
  ```
- When using `prefix delegation`-
  ```
  (10 secondary IPv4 addresses per ENI - 1) * 16 = 144 available IPv4 addresses
  ```

For more information on how many IP addresses an instance type can support, see [IP addresses per network interface per instance type](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-eni.html#AvailableIpPerENI). 

---

Another key consideration is the flow of network traffic. With Windows there is a risk of port exhaustion on nodes with more than 100 services. When this condition arises, the nodes will start throwing errors with the following message:

**"Policy creation failed: hcnCreateLoadBalancer failed in Win32: The specified port already exists."**

To address this issue, we leverage Direct Server Return (DSR). DSR is an implementation of asymmetric network load distribution. In other words, the request and response traffic use different network paths. This feature speeds up communication between pods and reduces the risk of port exhaustion. We therefore recommend enabling DSR on Windows nodes. 

 DSR is enabled by default in Windows Server SAC EKS Optimized AMIs. For Windows Server 2019 LTSC EKS Optimized AMIs, you will need to enable it during instance provisioning using the script below and by using Windows Server 2019 Full or Core as the amiFamily in the `eksctl` nodeGroup. See [eksctl custom AMI](https://eksctl.io/usage/custom-ami-support/) for additional information. 

```yaml
nodeGroups:
- name: windows-ng
  instanceType: c5.xlarge
  minSize: 1
  volumeSize: 50
  amiFamily: WindowsServer2019CoreContainer
  ssh:
    allow: false
```
In order to utilize DSR in Windows Server 2019 and above, you will need to specify the following [**kube-proxy**](https://kubernetes.io/docs/setup/production-environment/windows/intro-windows-in-kubernetes/#load-balancing-and-services) flags during instance startup.  You can do this by adjusting the userdata script associated with the [self-managed node groups Launch Template](https://docs.aws.amazon.com/eks/latest/userguide/launch-windows-workers.html).

```powershell
<powershell>
[string]$EKSBinDir = "$env:ProgramFiles\Amazon\EKS"
[string]$EKSBootstrapScriptName = 'Start-EKSBootstrap.ps1'
[string]$EKSBootstrapScriptFile = "$EKSBinDir\$EKSBootstrapScriptName"
(Get-Content $EKSBootstrapScriptFile).replace('"--proxy-mode=kernelspace",', '"--proxy-mode=kernelspace", "--feature-gates WinDSR=true", "--enable-dsr",') | Set-Content $EKSBootstrapScriptFile 
& $EKSBootstrapScriptFile -EKSClusterName "eks-windows" -APIServerEndpoint "https://<REPLACE-EKS-CLUSTER-CONFIG-API-SERVER>" -Base64ClusterCA "<REPLACE-EKSCLUSTER-CONFIG-DETAILS-CA>" -DNSClusterIP "172.20.0.10" -KubeletExtraArgs "--node-labels=alpha.eksctl.io/cluster-name=eks-windows,alpha.eksctl.io/nodegroup-name=windows-ng-ltsc2019 --register-with-taints=" 3>&1 4>&1 5>&1 6>&1
</powershell>
```

DSR enablement can be verified following the instructions in the [Microsoft Networking blog](https://techcommunity.microsoft.com/t5/networking-blog/direct-server-return-dsr-in-a-nutshell/ba-p/693710) and the [Windows Containers on AWS Lab](https://catalog.us-east-1.prod.workshops.aws/workshops/1de8014a-d598-4cb5-a119-801576492564/en-US/module1-eks/lab3-handling-mixed-clusters).

![](./images/dsr.png)

If preserving your available IPv4 addresses and minimizing wastage is crucial for your subnet, it is generally recommended to avoid using prefix delegation mode as mentioned in [Prefix Mode for Windows - When to avoid](../../networking/prefix-mode/index_windows.md#avoid-prefix-delegation-when). If using prefix delegation is still desired, you can take steps to optimize IPv4 address utilization in your subnet. See [Configuring Parameters for Prefix Delegation](../../networking/prefix-mode/index_windows.md#configure-parameters-for-prefix-delegation-to-conserve-ipv4-addresses) for detailed instructions on how to fine-tune the IPv4 address request and allocation process. Adjusting these configurations can help you strike a balance between conserving IPv4 addresses and pod density benefits of prefix delegation.

When using the default setting of assigning secondary IPv4 addresses, there are currently no supported configurations to manipulate how the VPC Resource Controller requests and allocates IPv4 addresses. More specifically, `minimum-ip-target` and `warm-ip-target` are only supported for prefix delegation mode. Also take note that in secondary IP mode, depending on the available IP addresses on the interface, the VPC Resource Controller will typically allocate 3 unused IPv4 addresses on the node on your behalf to maintain warm IPs for faster pod startup times. If you would like to minimize IP wastage of unused warm IP addresses, you could aim to schedule more pods on a given Windows node such that you use as much IP address capacity of the ENI as possible. More explicitly, you could avoid having warm unused IPs if all IP addresses on the ENI are already in use by the node and running pods. Another workaround to help you resolve constraints with IP address availability in your subnet(s) could be to explore [increasing your subnet size](https://docs.aws.amazon.com/vpc/latest/userguide/modify-subnets.html) or separating your Windows nodes into their own dedicated subnets.

Additionally, it's important to note that IPv6 is not supported on Windows nodes at the moment.

## Container Network Interface (CNI) options
The AWSVPC CNI is the de facto CNI plugin for Windows and Linux worker nodes. While the AWSVPC CNI satisfies the needs of many customers, still there may be times when you need to consider alternatives like an overlay network to avoid IP exhaustion. In these cases, the Calico CNI can be used in place of the AWSVPC CNI. [Project Calico](https://www.projectcalico.org/) is open source software that was developed by [Tigera](https://www.tigera.io/). That software includes a CNI that works with EKS. Instructions for installing Calico CNI in EKS can be found on the [Project Calico EKS installation](https://docs.projectcalico.org/getting-started/kubernetes/managed-public-cloud/eks) page.

## Network Polices 
It is considered a best practice to change from the default mode of open communication between pods on your Kubernetes cluster to limiting access based on network polices. The open source [Project Calico](https://www.tigera.io/tigera-products/calico/) has strong support for network polices that work with both Linux and Windows nodes. This feature is separate and not dependent on using the Calico CNI. We therefore recommend installing Calico and using it for network policy management. 

Instructions for installing Calico in EKS can be found on the [Installing Calico on Amazon EKS](https://docs.aws.amazon.com/eks/latest/userguide/calico.html) page.

In addition, the advice provided in the [Amazon EKS Best Practices Guide for Security - Network Section](https://aws.github.io/aws-eks-best-practices/security/docs/network/) applies equally to EKS clusters with Windows worker nodes, however, some features like "Security Groups for Pods" are not supported by Windows at this time.
