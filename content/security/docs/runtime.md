# Runtime security

Runtime security provides active protection for your containers while they're running.  The idea is to detect and/or prevent malicious activity from occurring inside the container. This can be achieved with a number of mechanisms in the Linux kernel or kernel extensions that are integrated with Kubernetes, such as Linux capabilities, secure computing (seccomp), AppArmor, or SELinux. There are also options like Amazon GuardDuty and third party tools that can assist with establishing baselines and detecting anomalous activity with less manual configuration of Linux kernel mechanisms.

!!! attention
    Kubernetes does not currently provide any native mechanisms for loading seccomp, AppArmor, or SELinux profiles onto Nodes.  They either have to be loaded manually or installed onto Nodes when they are bootstrapped. This has to be done prior to referencing them in your Pods because the scheduler is unaware of which nodes have profiles. See below how tools like Security Profiles Operator can help automate provisioning of profiles onto nodes.

## Security contexts and built-in Kubernetes controls

Many Linux runtime security mechanisms are tightly integrated with Kubernetes and can be configured through Kubernetes [security contexts](https://kubernetes.io/docs/tasks/configure-pod-container/security-context/). One such option is the `privileged` flag, which is `false` by default and if enabled is essentially equivalent to root on the host. It is nearly always inappropriate to enable privileged mode in production workloads, but there are many more controls that can provide more granular privileges to containers as appropriate.

### Linux capabilities

Linux capabilities allow you to grant certain capabilities to a Pod or container without providing all the abilities of the root user. Examples include `CAP_NET_ADMIN`, which allows configuring network interfaces or firewalls, or `CAP_SYS_TIME`, which allows manipulation of the system clock.

### Seccomp

With secure computing (seccomp) you can prevent a containerized application from making certain syscalls to the underlying host operating system's kernel. While the Linux operating system has a few hundred system calls, the lion's share of them are not necessary for running containers. By restricting what syscalls can be made by a container, you can effectively decrease your application's attack surface.

Seccomp works by intercepting syscalls and only allowing those that have been allowlisted to pass through. Docker has a [default](https://github.com/moby/moby/blob/master/profiles/seccomp/default.json) seccomp profile which is suitable for a majority of general purpose workloads, and other container runtimes like containerd provide comparable defaults. You can configure your container or Pod to use the container runtime's default seccomp profile by adding the following to the `securityContext` section of the Pod spec:

```yaml
securityContext:
  seccompProfile:
    type: RuntimeDefault
```

As of 1.22 (in alpha, stable as of 1.27), the above `RuntimeDefault` can be used for all Pods on a Node using a [single kubelet flag](https://kubernetes.io/docs/tutorials/security/seccomp/#enable-the-use-of-runtimedefault-as-the-default-seccomp-profile-for-all-workloads), `--seccomp-default`. Then the profile specified in `securityContext` is only needed for other profiles.

It's also possible to create your own profiles for things that require additional privileges. This can be very tedious to do manually, but there are tools like [Inspektor Gadget](https://github.com/inspektor-gadget/inspektor-gadget) (also recommended in the [network security section](../network/) for generating network policies) and [Security Profiles Operator](https://github.com/inspektor-gadget/inspektor-gadget) that support using tools like eBPF or logs to record baseline privilege requirements as seccomp profiles. Security Profiles Operator further allows automating the deployment of recorded profiles to nodes for use by Pods and containers.

### AppArmor and SELinux

AppArmor and SELinux are known as [mandatory access control or MAC systems](https://en.wikipedia.org/wiki/Mandatory_access_control). They are similar in concept to seccomp but with different APIs and abilities, allowing access control for e.g. specific filesystem paths or network ports. Support for these tools depends on the Linux distribution, with Debian/Ubuntu supporting AppArmor and RHEL/CentOS/Bottlerocket/Amazon Linux 2023 supporting SELinux. Also see the [infrastructure security section](./hosts.md#run-selinux) for further discussion of SELinux.

Both AppArmor and SELinux are integrated with Kubernetes, but as of Kubernetes 1.28 AppArmor profiles must be specified via [annotations](https://kubernetes.io/docs/tutorials/security/apparmor/#securing-a-pod) while SELinux labels can be set through the [SELinuxOptions](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.28/#selinuxoptions-v1-core) field on the security context directly.

As with seccomp profiles, the Security Profiles Operator mentioned above can assist with deploying profiles onto nodes in the cluster. (In the future, the project also aims to generate profiles for AppArmor and SELinux as it does for seccomp.)

## Recommendations

### Use Amazon GuardDuty for runtime monitoring and detecting threats to your EKS environments

If you do not currently have a solution for continuously monitoring EKS runtimes and analyzing EKS audit logs, and scanning for malware and other suspicious activity, Amazon strongly recommends the use of [Amazon GuardDuty](https://aws.amazon.com/guardduty/) for customers who want a simple, fast, secure, scalable, and cost-effective one-click way to protect their AWS environments. Amazon GuardDuty is a security monitoring service that analyzes and processes foundational data sources, such as AWS CloudTrail management events, AWS CloudTrail event logs, VPC flow logs (from Amazon EC2 instances), Kubernetes audit logs, and DNS logs. It also includes EKS runtime monitoring. It uses continuously updated threat intelligence feeds, such as lists of malicious IP addresses and domains, and machine learning to identify unexpected, potentially unauthorized, and malicious activity within your AWS environment. This can include issues like escalation of privileges, use of exposed credentials, or communication with malicious IP addresses, domains, presence of malware on your Amazon EC2 instances and EKS container workloads, or discovery of suspicious API activity. GuardDuty informs you of the status of your AWS environment by producing security findings that you can view in the GuardDuty console or through Amazon EventBridge. GuardDuty also provides support for you to export your findings to an Amazon Simple Storage Service (S3) bucket, and integrate with other services such as AWS Security Hub and Detective.

Watch this AWS Online Tech Talk ["Enhanced threat detection for Amazon EKS with Amazon GuardDuty - AWS Online Tech Talks"](https://www.youtube.com/watch?v=oNHGRRroJuE) to see how to enable these additional EKS security features step-by-step in minutes.

### Optionally: Use a 3rd party solution for runtime monitoring

Creating and managing seccomp and Apparmor profiles can be difficult if you're not familiar with Linux security.  If you don't have the time to become proficient, consider using a 3rd party commercial solution.  A lot of them have moved beyond static profiles like Apparmor and seccomp and have begun using machine learning to block or alert on suspicious activity. A handful of these solutions can be found below in the [tools](#tools-and-resources) section. Additional options can be found on the [AWS Marketplace for Containers](https://aws.amazon.com/marketplace/features/containers).

### Consider add/dropping Linux capabilities before writing seccomp policies

Capabilities involve various checks in kernel functions reachable by syscalls. If the check fails, the syscall typically returns an error. The check can be done either right at the beginning of a specific syscall, or deeper in the kernel in areas that might be reachable through multiple different syscalls (such as writing to a specific privileged file).  Seccomp, on the other hand, is a syscall filter which is applied to all syscalls before they are run. A process can set up a filter which allows them to revoke their right to run certain syscalls, or specific arguments for certain syscalls.

Before using seccomp, consider whether adding/removing Linux capabilities gives you the control you need. See [Setting capabilities for- containers](https://kubernetes.io/docs/tasks/configure-pod-container/security-context/#set-capabilities-for-a-container) for further information.

### See whether you can accomplish your aims by using Pod Security Policies (PSPs)

Pod Security Policies offer a lot of different ways to improve your security posture without introducing undue complexity. Explore the options available in PSPs before venturing into building seccomp and Apparmor profiles.

!!! warning
    As of Kubernetes 1.25, PSPs have been removed and replaced with the [Pod Security Admission](https://kubernetes.io/docs/concepts/security/pod-security-admission/) controller. Third-party alternatives which exist include OPA/Gatekeeper and Kyverno. A collection of Gatekeeper constraints and constraint templates for implementing policies commonly found in PSPs can be pulled from the [Gatekeeper library](https://github.com/open-policy-agent/gatekeeper-library/tree/master/library/pod-security-policy) repository on GitHub. And many replacements for PSPs can be found in the [Kyverno policy library](https://main.kyverno.io/policies/) including the full collection of [Pod Security Standards](https://kubernetes.io/docs/concepts/security/pod-security-standards/).

## Tools and Resources

- [7 things you should know before you start](https://itnext.io/seccomp-in-kubernetes-part-i-7-things-you-should-know-before-you-even-start-97502ad6b6d6)
- [AppArmor Loader](https://github.com/kubernetes/kubernetes/tree/master/test/images/apparmor-loader)
- [Setting up nodes with profiles](https://kubernetes.io/docs/tutorials/clusters/apparmor/#setting-up-nodes-with-profiles)
- [Security Profiles Operator](https://github.com/kubernetes-sigs/security-profiles-operator) is a Kubernetes enhancement which aims to make it easier for users to use SELinux, seccomp and AppArmor in Kubernetes clusters. It provides capabilities for both generating profiles from running workloads and loading profiles onto Kubernetes nodes for use in Pods.
- [Inspektor Gadget](https://github.com/inspektor-gadget/inspektor-gadget) allows inspecting, tracing, and profiling many aspects of runtime behavior on Kubernetes, including assisting in the generation of seccomp profiles.
- [Aqua](https://www.aquasec.com/products/aqua-cloud-native-security-platform/)
- [Qualys](https://www.qualys.com/apps/container-security/)
- [Stackrox](https://www.stackrox.com/use-cases/threat-detection/)
- [Sysdig Secure](https://sysdig.com/products/kubernetes-security/)
- [Prisma](https://docs.paloaltonetworks.com/cn-series)
- [NeuVector by SUSE](https://www.suse.com/neuvector/) open source, zero-trust container security platform, provides process profile rules and file access rules.
