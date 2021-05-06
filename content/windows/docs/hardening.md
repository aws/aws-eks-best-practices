# Hardening the Windows worker node

Windows Server hardening involves identifying and remediating security vulnerabilities before they are exploited. 

Microsoft offers a range of tools like [Microsoft Security Compliance Toolkit](https://www.microsoft.com/en-us/download/details.aspx?id=55319) and [Security Baselines](https://docs.microsoft.com/en-us/windows/security/threat-protection/windows-security-baselines) that should be applied to an operational system.

This guide focus specifically on Windows nodes running on Amazon Elastic Kubernetes Service (EKS).

## Reducing attack surface with Windows Server Core

Windows Server Core is a minimal installation option that is available as part of the [EKS Optimized Windows AMI](https://docs.aws.amazon.com/eks/latest/userguide/eks-optimized-windows-ami.html). Deploying Windows Server Core has a couple benefits. First, it has a relatively small disk footprint being 6GB on Server Core against 10GB on Windows Server with Desktop experience. Second, it has smaller attack surface because of its smaller code base.

You can specify the Server Core EKS Optimized AMI for Windows during when you deploy your nodes through `eksctl` or Cloudformation.

The example below is an eksctl manifest for a Windows node group based on Windows Server Core 2004:

```yaml
nodeGroups:
- name: windows-ng
  instanceType: c5.xlarge
  minSize: 1
  volumeSize: 50
  amiFamily: WindowsServer2004CoreContainer
  ssh:
    allow: false
```

The amiFamily name conventions can be found on the [eksctl official documentation.](https://eksctl.io/usage/custom-ami-support/)

## Avoiding RDP connections

Remote Desktop Protocol (RDP) is a connection protocol developed by Microsoft to provide users with a graphical interface to connect to another Windows computer over a network. 

As a best practice, you should treat your Windows worker nodes as if they were immutable. That means no management connections, no updates, and no troubleshooting. Any modification and update should be implemented as a new custom AMI and replaced by updating an Auto Scaling group. See **Patching Windows Servers and Containers** and **Amazon EKS optimized Windows AMI management**.

Disable RDP connections on Windows nodes during the deployment by passing the value **false** on the ssh property, as the example below:

```yaml 
nodeGroups:
- name: windows-ng
  instanceType: c5.xlarge
  minSize: 1
  volumeSize: 50
  amiFamily: WindowsServer2004CoreContainer
  ssh:
    allow: false
```

If access to the Windows node is needed, use [AWS System Manager Session Manager](https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager.html) to establish a secure PowerShell session through AWS Console or SSM agent. To see how to implement the solution watch [Securely Access Windows Instances Using AWS Systems Manager Session Manager](https://www.youtube.com/watch?v=nt6NTWQ-h6o)

In order to use System Manager Session Manager an additional IAM policy must be applied to the Windows nodes. Below is an example where the **AmazonSSMManagedInstanceCore** is specified in the eksctl cluster manifest:

```yaml 
 nodeGroups:
- name: windows-ng
  instanceType: c5.xlarge
  minSize: 1
  volumeSize: 50
  amiFamily: WindowsServer2004CoreContainer
  ssh:
    allow: false
  iam:
    attachPolicyARNs:
      - arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy
      - arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy
      - arn:aws:iam::aws:policy/ElasticLoadBalancingFullAccess
      - arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly
      - arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore
```

## Amazon Inspector
> [Amazon Inspector](https://aws.amazon.com/inspector/) is an automated security assessment service that helps improve the security and compliance of applications deployed on AWS. Amazon Inspector automatically assesses applications for exposure, vulnerabilities, and deviations from best practices. After performing an assessment, Amazon Inspector produces a detailed list of security findings prioritized by level of severity. These findings can be reviewed directly or as part of detailed assessment reports which are available via the Amazon Inspector console or API.

Amazon Inspector can be used to run CIS Benchmark assessment on the Windows worker node and it can be installed on a Windows Server Core by performing the following tasks:

1. Download the following .exe file:
https://inspector-agent.amazonaws.com/windows/installer/latest/AWSAgentInstall.exe
2. Transfer the agent to the Windows worker node.
3. Run the following command on PowerShell to install the Amazon Inspector Agent: `.\AWSAgentInstall.exe /install`

Below is the ouput after the first run. As you can see, it generated findings based on the [CVE](https://cve.mitre.org/) database. You can use this to harden your Worker nodes or create an AMI based on the hardened configurations.

![](./images/inspector-agent.png)

For more information on how to use Amazon Inspector, watch the [Improving the security and compliance of Windows Workloads with Amazon Inspector](https://www.youtube.com/watch?v=nIcwiJ85EKU) video to learn how to install Amazon Inspector agents, set up the CIS Benchmark assessment, and generate reports.

## Amazon GuardDuty
> [Amazon GuardDuty](https://aws.amazon.com/guardduty/) is a threat detection service that continuously monitors for malicious activity and unauthorized behavior to protect your AWS accounts, workloads, and data stored in Amazon S3. With the cloud, the collection and aggregation of account and network activities is simplified, but it can be time consuming for security teams to continuously analyze event log data for potential threats. 

By using Amazon GuardDuty you can have visilitiby on malicious actitivy against Windows Worker nodes, like RDP brute force and Port Probe. 

Watch the [Threat Detection for Windows Workloads using Amazon GuardDuty](https://www.youtube.com/watch?v=ozEML585apQ) video to learn how to implement and run CIS Benchmarks on Optimized EKS Windows AMI

## Security in Amazon EC2
Follow the [Security in Amazon EC2 best practices](https://docs.aws.amazon.com/AWSEC2/latest/WindowsGuide/ec2-security.html) security best practices to implement security controls an every layer.
