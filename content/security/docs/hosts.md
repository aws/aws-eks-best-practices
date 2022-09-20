# Protecting the infrastructure (hosts)
Inasmuch as it's important to secure your container images, it's equally important to safeguard the infrastructure that runs them. This section explores different ways to mitigate risks from attacks launched directly against the host.  These guidelines should be used in conjunction with those outlined in the [Runtime Security](runtime.md) section.

## Recommendations

### Use an OS optimized for running containers
Consider using Flatcar Linux, Project Atomic, RancherOS, and [Bottlerocket](https://github.com/bottlerocket-os/bottlerocket/), a special purpose OS from AWS designed for running Linux containers.  It includes a reduced attack surface, a disk image that is verified on boot, and enforced permission boundaries using SELinux.

Alternately, use the [EKS optimized AMI][eks-ami] for your Kubernetes worker nodes. The EKS optimized AMI is released regularly and contains a minimal set of OS packages and binaries necessary to run your containerized workloads.

[eks-ami]: https://docs.aws.amazon.com/eks/latest/userguide/eks-optimized-amis.html

### Keep your worker node OS updated

Regardless of whether you use a container-optimized host OS like Bottlerocket or a larger, but still minimalist, Amazon Machine Image like the EKS optimized AMIs, it is best practice to keep these host OS images up to date with the latest security patches.

For the EKS optimized AMIs, regularly check the [CHANGELOG][eks-ami-changes] and/or [release notes channel][eks-ami-releases] and automate the rollout of updated worker node images into your cluster.

[eks-ami-changes]: https://github.com/awslabs/amazon-eks-ami/blob/master/CHANGELOG.md
[eks-ami-releases]: https://github.com/awslabs/amazon-eks-ami/releases

### Treat your infrastructure as immutable and automate the replacement of your worker nodes
Rather than performing in-place upgrades, replace your workers when a new patch or update becomes available. This can be approached a couple of ways. You can either add instances to an existing autoscaling group using the latest AMI as you sequentially cordon and drain nodes until all of the nodes in the group have been replaced with the latest AMI.  Alternatively, you can add instances to a new node group while you sequentially cordon and drain nodes from the old node group until all of the nodes have been replaced.  EKS [managed node groups](https://docs.aws.amazon.com/eks/latest/userguide/managed-node-groups.html) uses the first approach and will display a message in the console to upgrade your workers when a new AMI becomes available. `eksctl` also has a mechanism for creating node groups with the latest AMI and for gracefully cordoning and draining pods from nodes groups before the instances are terminated. If you decide to use a different method for replacing your worker nodes, it is strongly recommended that you automate the process to minimize human oversight as you will likely need to replace workers regularly as new updates/patches are released and when the control plane is upgraded. 

With EKS Fargate, AWS will automatically update the underlying infrastructure as updates become available.  Oftentimes this can be done seamlessly, but there may be times when an update will cause your pod to be rescheduled.  Hence, we recommend that you create deployments with multiple replicas when running your application as a Fargate pod.

### Periodically run kube-bench to verify compliance with [CIS benchmarks for Kubernetes](https://www.cisecurity.org/benchmark/kubernetes/)
kube-bench is an open source project from Aqua that evaluates your cluster against the CIS benchmarks for Kubernetes. The benchmark describes the best practices for securing unmanaged Kubernetes clusters. The CIS Kubernetes Benchmark encompasses the control plane and the data plane. Since Amazon EKS provides a fully managed control plane, not all of the recommendations from the CIS Kubernetes Benchmark are applicable. To ensure this scope reflects how Amazon EKS is implemented, AWS created the *CIS Amazon EKS Benchmark*. The EKS benchmark inherits from CIS Kubernetes Benchmark with additional inputs from the community with specific configuration considerations for EKS clusters.

When running [kube-bench](https://github.com/aquasecurity/kube-bench) against an EKS cluster, follow these instructions from Aqua Security, [https://github.com/aquasecurity/kube-bench#running-in-an-eks-cluster](https://github.com/aquasecurity/kube-bench#running-in-an-eks-cluster). For further information see [Introducing The CIS Amazon EKS Benchmark](https://aws.amazon.com/blogs/containers/introducing-cis-amazon-eks-benchmark/). 

### Minimize access to worker nodes
Instead of enabling SSH access, use [SSM Session Manager](https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager.html) when you need to remote into a host.  Unlike SSH keys which can be lost, copied, or shared, Session Manager allows you to control access to EC2 instances using IAM.  Moreover, it provides an audit trail and log of the commands that were run on the instance.

As of August 19th, 2020 Managed Node Groups support custom AMIs and EC2 Launch Templates.  This allows you to embed the SSM agent into the AMI or install it as the worker node is being bootstrapped. If you rather not modify the Optimized AMI or the ASG's launch template, you can install the SSM agent with a DaemonSet as in this example, https://github.com/aws-samples/ssm-agent-daemonset-installer. 

#### Minimal IAM policy for SSM based SSH Access

The `AmazonSSMManagedInstanceCore` AWS managed policy contains a number of permissions that are not required for SSM Session Manager / SSM RunCommand if you're just looking to avoid SSH access. Of concern specifically is the
`*` permissions for `ssm:GetParameter(s)` which would allow for the role to access all parameters in Parameter Store (including SecureStrings with the AWS managed KMS key configured).

The following IAM policy contains the minimal set of permissions to enable node access via SSM Systems Manager.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "EnableAccessViaSSMSessionManager",
      "Effect": "Allow",
      "Action": [
        "ssmmessages:OpenDataChannel",
        "ssmmessages:OpenControlChannel",
        "ssmmessages:CreateDataChannel",
        "ssmmessages:CreateControlChannel",
        "ssm:UpdateInstanceInformation"
      ],
      "Resource": "*"
    },
    {
      "Sid": "EnableSSMRunCommand",
      "Effect": "Allow",
      "Action": [
        "ssm:UpdateInstanceInformation",
        "ec2messages:SendReply",
        "ec2messages:GetMessages",
        "ec2messages:GetEndpoint",
        "ec2messages:FailMessage",
        "ec2messages:DeleteMessage",
        "ec2messages:AcknowledgeMessage"
      ],
      "Resource": "*"
    }
  ]
}
```

With this policy in place and the [Session Manager plugin](https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-install-plugin.html) installed, you can then run 
```bash
aws ssm start-session --target [INSTANCE_ID_OF_EKS_NODE]
``` 
to access the node.

!!! note
    You may also want to consider adding permissions to [enable Session Manager logging](https://docs.aws.amazon.com/systems-manager/latest/userguide/getting-started-create-iam-instance-profile.html#create-iam-instance-profile-ssn-logging).

### Deploy workers onto private subnets
By deploying workers onto private subnets, you minimize their exposure to the Internet where attacks often originate.  Beginning April 22, 2020, the assignment of public IP addresses to nodes in a managed node groups will be controlled by the subnet they are deployed onto.  Prior to this, nodes in a Managed Node Group were automatically assigned a public IP. If you choose to deploy your worker nodes on to public subnets, implement restrictive AWS security group rules to limit their exposure.

### Run Amazon Inspector to assess hosts for exposure, vulnerabilities, and deviations from best practices
You can use [Amazon Inspector](https://docs.aws.amazon.com/inspector/latest/user/what-is-inspector.html) to check for unintended network access to your nodes and for vulnerabilities on the underlying Amazon EC2 instances.

Amazon Inspector can provide common vulnerabilities and exposures (CVE) data for your Amazon EC2 instances only if the Amazon EC2 Systems Manager (SSM) agent is installed and enabled. This agent is preinstalled on several [Amazon Machine Images (AMIs)](https://docs.aws.amazon.com/systems-manager/latest/userguide/ami-preinstalled-agent.html) including [EKS optimized Amazon Linux AMIs](https://docs.aws.amazon.com/eks/latest/userguide/eks-optimized-ami.html). Regardless of SSM agent status, all of your Amazon EC2 instances are scanned for network reachability issues. For more information about configuring scans for Amazon EC2, see [Scanning Amazon EC2 instances](https://docs.aws.amazon.com/inspector/latest/user/enable-disable-scanning-ec2.html).

!!! attention
    Inspector cannot be run on the infrastructure used to run Fargate pods.

## Alternatives

### Run SELinux

!!! info
    Available on Red Hat Enterprise Linux (RHEL), CentOS, and CoreOS

SELinux provides an additional layer of security to keep containers isolated from each other and from the host. SELinux allows administrators to enforce mandatory access controls (MAC) for every user, application, process, and file.  Think of it as a backstop that restricts the operations that can be performed against to specific resources based on a set of labels.  On EKS, SELinux can be used to prevent containers from accessing each other's resources.

Container SELinux policies are defined in the [container-selinux](https://github.com/containers/container-selinux) package.  Docker CE requires this package (along with its dependencies) so that the processes and files created by Docker (or other container runtimes) run with limited system access. Containers leverage the `container_t` label which is an alias to `svirt_lxc_net_t`. These policies effectively prevent containers from accessing certain features of the host.

When you configure SELinux for Docker, Docker automatically labels workloads `container_t` as a type and gives each container a unique MCS level. This will isolate containers from one another. If you need looser restrictions, you can create your own profile in SElinux which grants a container permissions to specific areas of the file system.  This is similiar to PSPs in that you can create different profiles for different containers/pods.  For example, you can have a profile for general workloads with a set of restrictive controls and another for things that require privileged access.

SELinux for Containers has a set of options that can be configured to modify the default restrictions. The following SELinux Booleans can be enabled or disabled based on your needs:

| Boolean | Default | Description|
|---|:--:|---|
| `container_connect_any` | `off` | Allow containers to access privileged ports on the host. For example, if you have a container that needs to map ports to 443 or 80 on the host. |
| `container_manage_cgroup` | `off` | Allow containers to manage cgroup configuration. For example, a container running systemd will need this to be enabled. |
| `container_use_cephfs` | `off` | Allow containers to use a ceph file system. |

By default, containers are allowed to read/execute under `/usr` and read most content from `/etc`. The files under `/var/lib/docker` and `/var/lib/containers` have the label `container_var_lib_t`. To view a full list of default, labels see the [container.fc](https://github.com/containers/container-selinux/blob/master/container.fc) file.

```bash
docker container run -it \
  -v /var/lib/docker/image/overlay2/repositories.json:/host/repositories.json \
  centos:7 cat /host/repositories.json
# cat: /host/repositories.json: Permission denied

docker container run -it \
  -v /etc/passwd:/host/etc/passwd \
  centos:7 cat /host/etc/passwd
# cat: /host/etc/passwd: Permission denied
```

Files labeled with `container_file_t` are the only files that are writable by containers. If you want a volume mount to be writeable, you will needed to specify `:z` or `:Z` at the end.

- `:z` will re-label the files so that the container can read/write
- `:Z` will re-label the files so that **only** the container can read/write

```bash
ls -Z /var/lib/misc
# -rw-r--r--. root root system_u:object_r:var_lib_t:s0   postfix.aliasesdb-stamp

docker container run -it \
  -v /var/lib/misc:/host/var/lib/misc:z \
  centos:7 echo "Relabeled!"

ls -Z /var/lib/misc
#-rw-r--r--. root root system_u:object_r:container_file_t:s0 postfix.aliasesdb-stamp
```

```bash
docker container run -it \
  -v /var/log:/host/var/log:Z \
  fluentbit:latest
```

In Kubernetes, relabeling is slightly different. Rather than having Docker automatically relabel the files, you can specify a custom MCS label to run the pod. Volumes that support relabeling will automatically be relabeled so that they are accessible. Pods with a matching MCS label will be able to access the volume. If you need strict isolation, set a different MCS label for each pod.

```yaml
securityContext:
  seLinuxOptions:
    # Provide a unique MCS label per container
    # You can specify user, role, and type also
    # enforcement based on type and level (svert)
    level: s0:c144:c154
```

In this example `s0:c144:c154` corresponds to an MCS label assigned to a file that the container is allowed to access.

On EKS you could create policies that allow for privileged containers to run, like FluentD and create an SELinux policy to allow it to read from /var/log on the host without needing to relabel the host directory. Pods with the same label will be able to access the same host volumes.

We have implemented [sample AMIs for Amazon EKS](https://github.com/aws-samples/amazon-eks-custom-amis) that have SELinux configured on CentOS 7 and RHEL 7. These AMIs were developed to demonstrate sample implementations that meet requirements of highly regulated customers, such as STIG, CJIS, and C2S.

!!! caution
    SELinux will ignore containers where the type is unconfined.

#### Additional resources
+ [SELinux Kubernetes RBAC and Shipping Security Policies for On-prem Applications](https://platform9.com/blog/selinux-kubernetes-rbac-and-shipping-security-policies-for-on-prem-applications/)
+ [Iterative Hardening of Kubernetes](https://jayunit100.blogspot.com/2019/07/iterative-hardening-of-kubernetes-and.html)
+ [Audit2Allow](https://linux.die.net/man/1/audit2allow)
+ [SEAlert](https://linux.die.net/man/8/sealert)
+ [Generate SELinux policies for containers with Udica](https://www.redhat.com/en/blog/generate-selinux-policies-containers-with-udica) describes a tool that looks at container spec files for Linux capabilities, ports, and mount points, and generates a set of SELinux rules that allow the container to run properly
+ [AMI Hardening](https://github.com/aws-samples/amazon-eks-custom-amis#hardening) playbooks for hardening the OS to meet different regulatory requirements

## Tools
+ [Keiko Upgrade Manager](https://github.com/keikoproj/upgrade-manager) an open source project from Intuit that orchestrates the rotation of worker nodes.
+ [Sysdig Secure](https://sysdig.com/products/kubernetes-security/)
+ [eksctl](https://eksctl.io/)
