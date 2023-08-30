# Runtime security 
Runtime security provides active protection for your containers while they're running.  The idea is to detect and/or prevent malicious activity from occurring inside the container. With secure computing (seccomp) you can prevent a containerized application from making certain syscalls to the underlying host operating system's kernel. While the Linux operating system has a few hundred system calls, the lion's share of them are not necessary for running containers. By restricting what syscalls can be made by a container, you can effectively decrease your application's attack surface. To get started with seccomp, use [`strace`](https://man7.org/linux/man-pages/man1/strace.1.html) to generate a stack trace to see which system calls your application is making, then use a tool such as [syscall2seccomp](https://github.com/antitree/syscall2seccomp) to create a seccomp profile from the data gathered from the trace.

Unlike SELinux, seccomp was not designed to isolate containers from each other, however, it will protect the host kernel from unauthorized syscalls. It works by intercepting syscalls and only allowing those that have been allowlisted to pass through. Docker has a [default](https://github.com/moby/moby/blob/master/profiles/seccomp/default.json) seccomp profile which is suitable for a majority of general purpose workloads. You can configure your container or Pod to use this profile by adding the following annotation to your container's or Pod's spec (pre-1.19):

```
annotations:
  seccomp.security.alpha.kubernetes.io/pod: "runtime/default"
```

1.19 and later: 

```
securityContext:
  seccompProfile:
    type: RuntimeDefault
```

It's also possible to create your own profiles for things that require additional privileges.  

!!! caution
    seccomp profiles are a Kubelet alpha feature, before 1.22.  You'll need to add the `--seccomp-profile-root` flag to the Kubelet arguments to make use of this feature.

As of 1.22 (in alpha, stable as of 1.27), the above `RuntimeDefault` can be used for all Pods on a Node using a [single kubelet flag](https://kubernetes.io/docs/tutorials/security/seccomp/#enable-the-use-of-runtimedefault-as-the-default-seccomp-profile-for-all-workloads), `--seccomp-default`. The annotation is no longer needed, and the `securityContext` profile is only needed for other profiles.

AppArmor is similar to seccomp, only it restricts an container's capabilities including accessing parts of the file system. It can be run in either enforcement or complain mode. Since building Apparmor profiles can be challenging, it is recommended you use a tool like [bane](https://github.com/genuinetools/bane) instead. 

!!! attention
    Apparmor is only available Ubuntu/Debian distributions of Linux. 

!!! attention 
    Kubernetes does not currently provide any native mechanisms for loading AppArmor or seccomp profiles onto Nodes.  They either have to be loaded manually or installed onto Nodes when they are bootstrapped.  This has to be done prior to referencing them in your Pods because the scheduler is unaware of which nodes have profiles. 

## Recommendations

### Use Amazon GuardDuty For ML-Powered Threat Detection and Monitoring Of EKS Environments
Amazon strongly recommends the use of [Amazon GuardDuty](https://docs.aws.amazon.com/guardduty/) for one-click monitoring and protecting EKS clusters and runtimes for customers who want a simple, fast, secure, scalable, and cost-effective way to protect their AWS environments. Amazon GuardDuty is a security monitoring service that analyzes and processes Foundational data sources, such as AWS CloudTrail management events, AWS CloudTrail event logs, VPC flow logs (from Amazon EC2 instances), and DNS logs. It also processes Features such as Kubernetes audit logs, RDS login activity, S3 logs, EBS volumes, Runtime monitoring, and Lambda network activity logs. It uses threat intelligence feeds, such as lists of malicious IP addresses and domains, and machine learning to identify unexpected, potentially unauthorized, and malicious activity within your AWS environment. This can include issues like escalation of privileges, use of exposed credentials, or communication with malicious IP addresses, domains, presence of malware on your Amazon EC2 instances and container workloads, or discovery of unusual patterns of login events on your database. For example, GuardDuty can detect compromised EC2 instances and container workloads serving malware, or mining bitcoin. It also monitors AWS account access behavior for signs of compromise, such as unauthorized infrastructure deployments, like instances deployed in a Region that hasn't been used before, or unusual API calls like a password policy change to reduce password strength. GuardDuty informs you of the status of your AWS environment by producing security findings that you can view in the GuardDuty console or through Amazon EventBridge. GuardDuty also provides support for you to export your findings to an Amazon Simple Storage Service (S3) bucket, and integrate with other services such as AWS Security Hub and Detective.

#### Enable Amazon GuardDuty EKS Protection
We strongly recommend using Amazon GuardDuty's one-click EKS Protection. EKS Runtime Monitoring provides runtime threat detection coverage for Amazon Elastic Kubernetes Service (Amazon EKS) nodes and containers within your AWS environment. EKS Runtime Monitoring uses a new GuardDuty security agent (EKS add-on) that adds runtime visibility into individual EKS workloads, for example, file access, process execution, and network connections. The GuardDuty security agent helps GuardDuty identify specific containers within your EKS clusters that are potentially compromised. It can also detect attempts to escalate privileges from an individual container to the underlying EC2 host, and the broader AWS environment. 

For more information, visit [Amazon GuardDuty User Guide - Configuring EKS Runtime Monitoring](https://docs.aws.amazon.com/guardduty/latest/ug/eks-protection-configuration.html)

#### Enable Amazon GuardDuty EKS Audit Log Monitoring
EKS Audit Log Monitoring helps you detect potentially suspicious activities in your EKS clusters within Amazon Elastic Kubernetes Service. When you enable EKS Audit Log Monitoring, GuardDuty immediately begins to monitor Kubernetes audit logs from your Amazon EKS clusters and analyze them for potentially malicious and suspicious activity. It consumes Kubernetes audit log events directly from the Amazon EKS control plane logging feature through an independent and duplicative stream of flow logs. This process does not require any additional set up or affect any existing Amazon EKS control plane logging configurations that you might have. When you disable EKS Audit Log Monitoring, GuardDuty immediately stops monitoring and analyzing the Kubernetes audit logs for your EKS resources. 

For more information, visit [Amazon GuardDuty User Guide - EKS Audit Log Monitoring](https://docs.aws.amazon.com/guardduty/latest/ug/guardduty-eks-audit-log-monitoring.html). 

#### Enable Amazon GuardDuty Malware Protection 
Malware Protection helps you detect the potential presence of malware by scanning the Amazon Elastic Block Store (Amazon EBS) volumes that are attached to the Amazon Elastic Compute Cloud (Amazon EC2) instances and container workloads. Malware Protection provides scan options where you can decide if you want to include or exclude specific Amazon EC2 instances and container workloads at the time of scanning. It also provides an option to retain the snapshots of Amazon EBS volumes attached to the Amazon EC2 instances or container workloads, in your GuardDuty accounts. The snapshots get retained only when malware is found and Malware Protection findings are generated. Malware Protection offers two types of scans to detect potentially malicious activity in your Amazon EC2 instances and container workloads – GuardDuty-initiated malware scan and On-demand malware scan. 

For more information, visit [Amazon GuardDuty User Guide - Malware Protection in Amazon GuardDuty (https://docs.aws.amazon.com/guardduty/latest/ug/malware-protection.html)

#### Enable Amazon GuardDuty S3 Protection
S3 Protection helps Amazon GuardDuty monitor AWS CloudTrail data events for Amazon Simple Storage Service (Amazon S3) that include object-level API operations to identify potential security risks for data within your Amazon S3 buckets. GuardDuty monitors both AWS CloudTrail management events and AWS CloudTrail S3 data events to identify potential threats in your Amazon S3 resources. Both the data sources monitor different kinds of activities. Examples of CloudTrail management events for S3 include operations that list or configure Amazon S3 buckets, such as ListBuckets, DeleteBuckets, and PutBucketReplication. Examples of CloudTrail data events for S3 include object-level API operations, such as GetObject, ListObjects, DeleteObject, and PutObject.

For more information, visit [Amazon GuardDuty User Guide - Amazon S3 Protection In Amazon GuardDuty](https://docs.aws.amazon.com/guardduty/latest/ug/s3-protection.html)

#### Enable Amazon GuardDuty RDS Protection
RDS Protection in Amazon GuardDuty analyzes and profiles RDS login activity for potential access threats to your Amazon Aurora databases (Amazon Aurora MySQL-Compatible Edition and Aurora PostgreSQL-Compatible Edition). This feature allows you to identify potentially suspicious login behavior. RDS Protection doesn't require additional infrastructure; it is designed so as not to affect the performance of your database instances. When RDS Protection detects a potentially suspicious or anomalous login attempt that indicates a threat to your database, GuardDuty generates a new finding with details about the potentially compromised database. For more information visit [Amazon GuardDuty User Guide - GuardDuty RDS Protection](https://docs.aws.amazon.com/guardduty/latest/ug/rds-protection.html)

For more information, visit [Amazon GuardDuty User Guide - Amazon GuardDuty RDS Protection](https://docs.aws.amazon.com/guardduty/latest/ug/malware-protection.html)

#### Enable Amazon GuardDuty Lambda Protection
Lambda Protection helps you identify potential security threats when an AWS Lambda function gets invoked in your AWS environment. When you enable Lambda Protection, GuardDuty starts monitoring Lambda network activity logs, starting with VPC Flow Logs from all Lambda functions for account, including those logs that don't use VPC networking, and are generated when the Lambda function gets invoked. If GuardDuty identifies suspicious network traffic that is indicative of the presence of a potentially malicious piece of code in your Lambda function, GuardDuty will generate a finding.

For more information visit [Amazon GuardDuty User Guide - Lambda Protection In Amazon GuardDuty](https://docs.aws.amazon.com/guardduty/latest/ug/lambda-protection.html)

### Optionally: Use a 3rd party solution for runtime defense
Creating and managing seccomp and Apparmor profiles can be difficult if you're not familiar with Linux security.  If you don't have the time to become proficient, consider using a commercial solution.  A lot of them have moved beyond static profiles like Apparmor and seccomp and have begun using machine learning to block or alert on suspicious activity. A handful of these solutions can be found below in the [tools](##Tools) section. Additional options can be found on the [AWS Marketplace for Containers](https://aws.amazon.com/marketplace/features/containers).

### Consider add/dropping Linux capabilities before writing seccomp policies
Capabilities involve various checks in kernel functions reachable by syscalls. If the check fails, the syscall typically returns an error. The check can be done either right at the beginning of a specific syscall, or deeper in the kernel in areas that might be reachable through multiple different syscalls (such as writing to a specific privileged file).  Seccomp, on the other hand, is a syscall filter which is applied to all syscalls before they are run. A process can set up a filter which allows them to revoke their right to run certain syscalls, or specific arguments for certain syscalls. 

Before using seccomp, consider whether adding/removing Linux capabilities gives you the control you need. See [https://kubernetes.io/docs/tasks/configure-pod-container/security-context/#set-capabilities-for-a-container](https://kubernetes.io/docs/tasks/configure-pod-container/security-context/#set-capabilities-for-a-container) for further information. 

### See whether you can accomplish your aims by using Pod Security Policies (PSPs)
Pod Security Policies offer a lot of different ways to improve your security posture without introducing undue complexity. Explore the options available in PSPs before venturing into building seccomp and Apparmor profiles.

!!! warning 
    As of Kubernetes 1.25, PSPs have been removed and replaced with the [Pod Security Admission](https://kubernetes.io/docs/concepts/security/pod-security-admission/) controller. Third-party alternatives which exist include OPA/Gatekeeper and Kyverno. A collection of Gatekeeper constraints and constraint templates for implementing policies commonly found in PSPs can be pulled from the [Gatekeeper library](https://github.com/open-policy-agent/gatekeeper-library/tree/master/library/pod-security-policy) repository on GitHub. And many replacements for PSPs can be found in the [Kyverno policy library](https://main.kyverno.io/policies/) including the full collection of [Pod Security Standards](https://kubernetes.io/docs/concepts/security/pod-security-standards/).

## Additional Resources
+ [7 things you should know before you start](https://itnext.io/seccomp-in-kubernetes-part-i-7-things-you-should-know-before-you-even-start-97502ad6b6d6)
+ [AppArmor Loader](https://github.com/kubernetes/kubernetes/tree/master/test/images/apparmor-loader)
+ [Setting up nodes with profiles](https://kubernetes.io/docs/tutorials/clusters/apparmor/#setting-up-nodes-with-profiles)
+ [seccomp-operator](https://github.com/kubernetes-sigs/seccomp-operator) Is similar to the AppArmor Loader, only instead of AppArmor profiles, it creates a seccomp profiles on each host 

## Tools
+ [Aqua](https://www.aquasec.com/products/aqua-cloud-native-security-platform/)
+ [Qualys](https://www.qualys.com/apps/container-security/)
+ [Stackrox](https://www.stackrox.com/use-cases/threat-detection/)
+ [Sysdig Secure](https://sysdig.com/products/kubernetes-security/)
+ [Prisma](https://docs.paloaltonetworks.com/cn-series)
