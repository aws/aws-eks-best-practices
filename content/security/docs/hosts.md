# Protecting the infrastructure (hosts)
Inasmuch as it's important to secure your container images, it's equally important to safeguard the infrastructure that runs them. This section explores different ways to mitigate risks from attacks launched directly against the host.  These guidelines should be used in conjunction with those outlined in the [Runtime Security](runtime.md) section. 

## Recommendations
### Use a OS optimized for running containers
Conside using Flatcar Linux, Project Atomic, RancherOS, and [Bottlerocket](https://github.com/bottlerocket-os/bottlerocket/) (currently in preview), a special purpose OS from AWS designed for running Linux containers.  It includes a reduced attack surface, a disk image that is verified on boot, and enforced permission boundaries using SELinux. 

### Treat your infrastructure as immutable and automate the replacement of your worker nodes
Rather than performing in-place upgrades, replace your workers when a new patch or update becomes available. This can be approached a couple of ways. You can either add instances to an existing autoscaling group using the latest AMI as you sequentially cordon and drain nodes until all of the nodes in the group have been replaced with the latest AMI.  Alternatively, you can add instances to a new node group while you sequentally cordon and drain nodes from the old node group until all of the nodes have been replaced.  EKS [managed node groups](https://docs.aws.amazon.com/eks/latest/userguide/managed-node-groups.html) utilizes the second approach and will present an option to upgrade workers when a new AMI becomes available. `eksctl` also has a mechanism for creating node groups with the latest AMI and for gracefully cordoning and draining pods from nodes groups before the instances are terminated. If you decide to use a different method for replacing your worker nodes, it is strongly recommended that you automate the process to minimize human oversight as you will likely need to replace workers regularly as new updates/patches are released and when the control plane is upgraded. 

With EKS Fargate, AWS will automatically update the underlying infrastructure as updates become available.  Oftentimes this can be done seamlessly, but there may be times when an update will cause your task to be rescheduled.  Hence, we recommend that you create deployments with multiple replicas when running your application as a Fargate pod. 

### Periodically run [kube-bench](https://github.com/aquasecurity/kube-bench) to verify compliance with [CIS benchmarks for Kubernetes](https://www.cisecurity.org/benchmark/kubernetes/)
When running kube-bench against an EKS cluster, follow these instructions from Aqua Security, https://github.com/aquasecurity/kube-bench#running-in-an-eks-cluster. 

> Caution: false positives may appear in the report because of the way the EKS optimized AMI configures the kubelet.  The issue is currently being tracked on [GitHub](https://github.com/aquasecurity/kube-bench/issues/571). 

### Minimize access to worker nodes
Instead of enabling SSH access, use [SSM Session Manager](https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager.html) when you need to remote into a host.  Unlike SSH keys which can be lost, copied, or shared, Session Manager allows you to control access to EC2 instances using IAM.  Moreover, it provides an audit trail and log of the commands that were run on the instance.

### Deploy workers onto private subnets
By deploying workers onto private subnets, you minimize their exposure to the Internet where attacks often originate.  At present, worker nodes that are part of a managed node group are are automatically assigned a public IP. If you plan to use managed node groups use AWS security groups to restrict or deny inbound access from the Internet (0.0.0.0/0). Risk to workers that are deployed onto public subnets can also be mitigated by implementing restrictive security group rules. 

### Run [Amazon Inspector](https://docs.aws.amazon.com/inspector/latest/userguide/inspector_introduction.html) to assesses hosts for exposure, vulnerabilities, and deviations from best practices  
Inspector requires the deployment of an agent that continually monitors activity on the instance while using set of rules to assess alignment with best practices. 

> At present, managed node groups do not allow you to supply user metadata or your own AMI.  If you want to run Inspector on managed workers, you will need to install the agent after the node has been bootstrapped.

> Inspector cannot be run on the infrastructure used to run Fargate pods. 

## Alternatives
### Run SELinux 
> Available on RHEL instances

SELinux provides an additional layer of security to keep containers isolated from each other and from the host. SELinux allows administrators to enforce mandatory access controls (MAC) for every user, application, process, and file.  Think of it as a backstop that restricts access to specific resources on the operation based on a set of labels.  On EKS it can be used to prevent containers from accessing each other's resources. 

SELinux has a module called `container_t` which general module used for running containers.  When you configure SELinux for Docker, Docker automatically labels workloads `container_t` as a type and gives each container a unique MCS level.  This alone will effectively isolate containers from each another.  If you need to give it more privileged access to a container, you can create your own profile in SElinux which grants it permissions to specific areas of the file system.  This is similiar to PSPs in that you can create different profiles for different containers/pods.  For example, you can have a profile for general workloads with a set of restrictive controls and another for things that require privileged access.

You can assign SELinux labels using pods or container security context as in the following `podSec` excerpt: 

```yaml
securityContext:
  seLinuxOptions:
    # Provide a unique MCS label per container
    # You can specify user, role, and type also
    # enforcement based on type and level (svert)
    level: s0:c144:c154
```
In this example `s0:c144:c154` corresponds to an MCS label assigned to a file that the container is allowed to access. 

On EKS you could create policies that allow for privileged containers to run, like FluentD and create an SELinux policy to allow it to read from /var/log on the host. 

> Caution: SELinux will ignore containers where the type is unconfined. 
#### Additional resources
+ [SELinux Kubernetes RBAC and Shipping Security Policies for On-prem Applications](https://platform9.com/blog/selinux-kubernetes-rbac-and-shipping-security-policies-for-on-prem-applications/)
+ [Iterative Hardening of Kubernetes](https://jayunit100.blogspot.com/2019/07/iterative-hardening-of-kubernetes-and.html) 
+ [Audit2Allow](https://linux.die.net/man/1/audit2allow)
+ [SEAlert](https://linux.die.net/man/8/sealert)

## Tools
+ [Keiko](https://github.com/keikoproj/keiko)
+ [Sysdig Secure](https://sysdig.com/products/kubernetes-security/)
+ [eksctl](https://eksctl.io/)