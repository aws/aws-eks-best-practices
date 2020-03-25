# Runtime security 
Runtime security provides active protection for your containers while they're running.  The idea is to detect and/or prevent malicious activity from occuring inside the container. With secure computing (seccomp) you can prevent a containerized application from making certain syscalls to the underlying host operating system's kernel. While the Linux operating system has a few hundred system calls, the lion's share of them are not necessary for running containers. By restricting what syscalls can be made by a container, you can effectively decrease your application's attack surface. To get started with seccomp, analyze the results of a stack trace to see which calls your application is making or use a tool such as [syscall2seccomp](https://github.com/antitree/syscall2seccomp).

> Seccomp profiles are a Kubelet alpha feature.  You'll need to add the `--seccomp-profile-root` flag to the Kubelet arguments to make use of this feature. 

AppArmor is similar to seccomp, only it restricts an container's capabilities including accessing parts of the file system. It can be run in either enforcement or complain mode. Since building Apparmor profiles can be challenging, it is recommended you use a tool like [bane](https://github.com/genuinetools/bane) instead. 

> Apparmor is only available Ubuntu/Debian distributions of Linux. 

> Kubernetes does not currently provide any native mechanisms for loading AppArmor or seccomp profiles onto nodes.  They either have to be loaded manually or installed onto nodes when they are bootstrapped.  This has to be done prior to referencing them in your Pods because the scheduler is unaware of which nodes have profiles. 

## Recommendations
+ **Use a 3rd party solution for runtime defense**. Creating and managing seccomp and Apparmor profiles can be difficult if you're not familiar with Linux security.  If you don't have the time to become proficient, consider using a commercial solution.  A lot of them have moved beyond static profiles like Apparmor and seccomp and have begun using machine learning to block or alert on suspicious activity. 

+ **Consider add/dropping Linux capabilities before writing seccomp policies**. Capabilities involve various checks in kernel functions reachable by syscalls. If the check fails, the syscall typically returns an error. The check can be done either right at the beginning of a specific syscall, or deeper in the kernel in areas that might be reachable through multiple different syscalls (such as writing to a specific privileged file).  Seccomp, on the other hand, is a syscall filter which is applied to all syscalls before they are run. A process can set up a filter which allows them to revoke their right to run certain syscalls, or specific arguments for certain syscalls. 

Before using seccomp, consider whether adding/removing Linux capabilities gives you the control you need. See https://kubernetes.io/docs/tasks/configure-pod-container/security-context/#set-capabilities-for-a-container for further information. 

+ **See whether you can accomplish your aims by using Pod Security Policies (PSPs)**. Pod Security Policies offer a lot of different ways to improve your security posture without introducing undue complexity.  Explore the options available in PSPs before venturing into building seccomp and Apparmor profiles. 

## Additional Resources
+ https://itnext.io/seccomp-in-kubernetes-part-i-7-things-you-should-know-before-you-even-start-97502ad6b6d6
+ https://github.com/kubernetes/kubernetes/tree/master/test/images/apparmor-loader
+ https://kubernetes.io/docs/tutorials/clusters/apparmor/#setting-up-nodes-with-profiles

## Tools
+ [Aqua](https://www.aquasec.com/products/aqua-cloud-native-security-platform/)
+ [Qualys](https://www.qualys.com/apps/container-security/)
+ [Sysdig Secure](https://sysdig.com/products/kubernetes-security/)
+ [Twistlock](https://www.twistlock.com/platform/runtime-defense/)