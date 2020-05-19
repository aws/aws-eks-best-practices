# Pod Security

Pods have a variety of different settings that can strengthen or weaken your overall security posture.  As a Kubernetes practitioner your chief concern should be preventing a process that’s running in a container from escaping the isolation boundaries of Docker and gaining access to the underlying host.  The reason for this is twofold.  First, the processes that run within a container run under the context of the \[Linux\] root user by default.  Although the actions of root within a container are partially constrained by the set of Linux capabilities that Docker assigns to the containers, these default privileges could allow an attacker to escalate their privileges and/or gain access to sensitive information bound to the host, including Secrets and ConfigMaps.  Below is a list of the default capabilities assigned to Docker containers.  For additional information about each capability, see http://man7.org/linux/man-pages/man7/capabilities.7.html.

`CAP_CHOWN, CAP_DAC_OVERERIDE, CAP_FOWNER, CAP_FSETID, CAP_KILL, CAP_SETGID, CAP_SETUID, CAP_SETPCAP, CAP_NET_BIND_SERVICE, CAP_NET_RAW, CAP_SYS_CHROOT, CAP_MKNOD, CAP_AUDIT_WRITE, CAP_SETFCAP`

!!! info 
    EC2 and Fargate pods are assigned the aforementioned capabilites by default. Additionally, Linux capabilities can only be dropped from Fargate pods. 

Pods that are run as privileged, inherit _all_ of the Linux capabilities associated with root on the host and should be avoided if possible.

Second, all Kubernetes worker nodes use an authorization mode called the node authorizer.  The node authorizer authorizes all API requests that originate from the kubelet and allows nodes to perform the following actions: 

Read operations:

+ services
+ endpoints
+ nodes
+ pods
+ secrets, configmaps, persistent volume claims and persistent volumes related to pods bound to the kubelet’s node

Write operations:

+ nodes and node status (enable the `NodeRestriction` admission plugin to limit a kubelet to modify its own node)
+ pods and pod status (enable the `NodeRestriction` admission plugin to limit a kubelet to modify pods bound to itself)
+ events

Auth-related operations:

+ Read/write access to the CertificateSigningRequest (CSR) API for TLS bootstrapping
+ the ability to create TokenReview and SubjectAccessReview for delegated authentication/authorization checks

EKS uses the [node restriction admission controller](https://kubernetes.io/docs/reference/access-authn-authz/admission-controllers/#noderestriction) which only allows the node to modify a limited set of node attributes and pod objects that are bound to the node.   Nevertheless, an attacker who manages to get access to the host will still be able to glean sensitive information about the environment from the Kubernetes API that could allow them to move laterally within the cluster.

## Recommendations

### Restrict the containers that can run as privileged
As mentioned, containers that run as privileged inherit all of the Linux capabilities assigned to root on the host.  Seldom do containers need these types of privileges to function properly.  You can reject pods with containers configured to run as privileged by creating a [pod security policy](https://kubernetes.io/docs/concepts/policy/pod-security-policy/).  You can think of a pod security policy as a set of requirements that pods have to meet before they can be created.  If you elect to use pod security policies, you will need to create a role binding that allows service accounts to read your pod security policies. 

When you provision an EKS cluster, a pod security policy called `eks.privileged` is automatically created.  The manifest for that policy appears below: 

```yaml
apiVersion: extensions/v1beta1
kind: PodSecurityPolicy
metadata:
  annotations:
    kubernetes.io/description: privileged allows full unrestricted access to pod features,
      as if the PodSecurityPolicy controller was not enabled.
    seccomp.security.alpha.kubernetes.io/allowedProfileNames: '*'
  labels:
    eks.amazonaws.com/component: pod-security-policy
    kubernetes.io/cluster-service: "true"
  name: eks.privileged
spec:
  allowPrivilegeEscalation: true
  allowedCapabilities:
  - '*'
  fsGroup:
    rule: RunAsAny
  hostIPC: true
  hostNetwork: true
  hostPID: true
  hostPorts:
  - max: 65535
    min: 0
  privileged: true
  runAsUser:
    rule: RunAsAny
  seLinux:
    rule: RunAsAny
  supplementalGroups:
    rule: RunAsAny
  volumes:
  - '*'
```

This PSP allows an authenticated user to run privileged containers across all namespaces within the cluster.  While this may seem overly permissive at first, there are certain applications/plug-ins such as the AWS VPC CNI and kube-proxy that have to run as privileged because they are responsible for configuring the host’s network settings. Furthermore, this policy provides backward compatibility with earlier versions of Kubernetes that lacked support for pod security policies.    

The binding shown below is what binds the ClusterRole `eks:podsecuritypolicy:privileged` to the `system:authenticated` RBAC group. 

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  annotations: 
    kubernetes.io/description: Allow all authenticated users to create privileged
  labels:
    eks.amazonaws.com/component: pod-security-policy
    kubernetes.io/cluster-service: "true"
  name: eks:podsecuritypolicy:authenticated
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: eks:podsecuritypolicy:privileged
subjects:
- apiGroup: rbac.authorization.k8s.io
  kind: Group
  name: system:authenticated
```

Lastly, the ClusterRole below allow all bindings that reference it to use the `eks.privileged` PodSecurityPolicy.

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  labels:
    eks.amazonaws.com/component: pod-security-policy
    kubernetes.io/cluster-service: "true"
  name: eks:podsecuritypolicy:privileged
rules:
- apiGroups:
  - policy
  resourceNames:
  - eks.privileged
  resources:
  - podsecuritypolicies
  verbs:
  - use
``` 

As a best practice we recommend that you scope the binding for privileged pods to service accounts within a particular namespace, e.g. kube-system, and limiting access to that namespace.  For all other serviceaccounts/namespaces, we recommend implementing a more restrictive policy such as this: 

```yaml
apiVersion: policy/v1beta1
kind: PodSecurityPolicy
metadata:
    name: restricted
    annotations:
    seccomp.security.alpha.kubernetes.io/allowedProfileNames: 'docker/default,runtime/default'
    apparmor.security.beta.kubernetes.io/allowedProfileNames: 'runtime/default'
    seccomp.security.alpha.kubernetes.io/defaultProfileName:  'runtime/default'
    apparmor.security.beta.kubernetes.io/defaultProfileName:  'runtime/default'
spec:
    privileged: false
    # Required to prevent escalations to root.
    allowPrivilegeEscalation: false
    # This is redundant with non-root + disallow privilege escalation,
    # but we can provide it for defense in depth.
    requiredDropCapabilities:
    - ALL
    # Allow core volume types.
    volumes:
    - 'configMap'
    - 'emptyDir'
    - 'projected'
    - 'secret'
    - 'downwardAPI'
    # Assume that persistentVolumes set up by the cluster admin are safe to use.
    - 'persistentVolumeClaim'
    hostNetwork: false
    hostIPC: false
    hostPID: false
    runAsUser:
    # Require the container to run without root privileges.
    rule: 'MustRunAsNonRoot'
    seLinux:
    # This policy assumes the nodes are using AppArmor rather than SELinux.
    rule: 'RunAsAny'
    supplementalGroups:
    rule: 'MustRunAs'
    ranges:
        # Forbid adding the root group.
        - min: 1
        max: 65535
    fsGroup:
    rule: 'MustRunAs'
    ranges:
        # Forbid adding the root group.
        - min: 1
        max: 65535
    readOnlyRootFilesystem: false
```

This policy prevents pods from running as privileged or escalating privileges.  It also restricts the types of volumes that can be mounted and the root supplemental groups that can be added. 

!!! attention 
    Fargate is a launch type that enables you to run "serverless" container(s) where the containers of a pod are run on infrastructure that AWS manages. With Fargate, you cannot run a privileged container or configure your pod to use hostNetwork or hostPort.

### Do not run processes in containers as root
All containers run as root by default.  This could be problematic if an attacker is able to exploit a vulnerability in the application and get shell access to the running container.  You can mitigate this risk a variety of ways.  First, by removing the shell from the container image.  Second, adding the USER directive to your Dockerfile or running the containers in the pod as a non-root user.  The Kubernetes podSpec includes a set of fields under `spec.securityContext`, that allow to let you specify the user and/or group to run your application as.  These fields are `runAsUser` and `runAsGroup` respectively.  You can mandate the use of these fields by creating a pod security policy.  See https://kubernetes.io/docs/concepts/policy/pod-security-policy/#users-and-groups for further information on this topic. 

### Never run Docker in Docker or mount the socket in the container
While this conveniently lets you to build/run images in Docker containers, you're basically relinquishing complete control of the node to the process running in the container. If you need to build container images on Kubernetes use [Kaniko](https://github.com/GoogleContainerTools/kaniko), [buildah](https://github.com/containers/buildah), [img](https://github.com/genuinetools/img), or a build service like [CodeBuild](https://docs.aws.amazon.com/codebuild/latest/userguide/welcome.html) instead. 

### Restrict the use of hostPath or if hostPath is necessary restrict which prefixes can be used and configure the volume as read-only
`hostPath` is a volume that mounts a directory from the host directly to the container.  Rarely will pods need this type of access, but if they do, you need to be aware of the risks.  By default pods that run as root will have write access to the file system exposed by hostPath.  This could allow an attacker to modify the kubelet settings, create symbolic links to directories or files not directly exposed by the hostPath, e.g. /etc/shadow, install ssh keys, read secrets mounted to the host, and other malicious things. To mitigate the risks from hostPath, configure the `spec.containers.volumeMounts` as `readOnly`, for example: 

```yaml
volumeMounts:
- name: hostPath-volume
    readOnly: true
    mountPath: /host-path
```

You should also use a pod security policy to restrict the directories that can be used by `hostPath` volumes.  For example the following PSP excerpt only allows paths that begin with `/foo`.  It will prevent containers from traversing the host file system from outside the prefix: 

```yaml
allowedHostPaths:
# This allows "/foo", "/foo/", "/foo/bar" etc., but
# disallows "/fool", "/etc/foo" etc.
# "/foo/../" is never valid.
- pathPrefix: "/foo"
    readOnly: true # only allow read-only mounts
```

### Set requests and limits for each container to avoid resource contention and DoS attacks
A pod without requests or limits can theoretically consume all of the resources available on a host.  As additional pods are scheduled onto a node, the node may experience CPU or memory pressure which can cause the Kubelet to terminate or evict pods from the node.  While you can’t prevent this from happening all together, setting requests and limits will help minimize resource contention and mitigate the risk from poorly written applications that consume an excessive amount of resources. 

The `podSpec` allows you to specify requests and limits for CPU and memory.  CPU is considered a compressible resource because it can be oversubscribed.  Memory is incompressible, i.e. it cannot be shared among multiple containers.  

When you specify _requests_ for CPU or memory, you’re essentially designating the amount of _memory_ that containers are guaranteed to get.  Kubernetes aggregates the requests of all the containers in a pod to determine which node to schedule the pod onto.  If a container exceeds the requested amount of memory it may be subject to termination if there’s memory pressure on the node. 

_Limits_ are the maximum amount of CPU and memory resources that a container is allowed to consume and directly corresponds to the `memory.limit_in_bytes` value of the cgroup created for the container.  A container that exceeds the memory limit will be OOM killed. If a container exceeds its CPU limit, it will be throttled. 

Kubernetes uses three Quality of Service (QoS) classes to prioritize the workloads running on a node.  These include: guaranteed, burstable, and best effort.  If limits and requests are not set, the pod is configured as burstable (lowest priority).  Burstable pods are the first to get killed when there is insufficient memory.  If limits are set on _all_ containers within the pod, or if the requests and limits are set to the same values, the pod is configured as guaranteed (highest priority).  Guaranteed pods will not be killed unless they exceed their configured memory limits. If the limits and requests are configured with different values, or one container within the pod sets limits and the others don’t or have limits set for different resources, the pods are configured as burstable (medium priority). These pods have some resource guarantees, but can be killed once they exceed their requested memory. Be aware that requests doesn’t actually affect the `memory_limit_in_bytes` value of the cgroup; the cgroup limit is set to the amount of memory available on the host. Nevertheless, setting the requests value too low could cause the pod to be targeted for termination by the kubelet if the node undergoes memory pressure. 

For additional information about resource QoS, please refer to the [Kubernetes documentation](https://github.com/kubernetes/community/blob/master/contributors/design-proposals/node/resource-qos.md).

You can force the use of requests and limits by setting a [resource quota](https://kubernetes.io/docs/concepts/policy/resource-quotas/) on a namespace or by creating a [limit range](https://kubernetes.io/docs/concepts/policy/limit-range/).  A resource quota allows you to specify the total amount of resources, e.g. CPU and RAM, allocated to a namespace.  When it’s applied to a namespace, it forces you to specify requests and limits for all containers deployed into that namespace. By contrast, limit ranges give you more granular control of the allocation of resources. With limit ranges you can min/max for CPU and memory resources per pod or per container within a namespace.  You can also use them to set default request/limit values if none are provided.

### Do not allow privileged escalation
Privileged escalation allows a process to change the security context under which its running.  Sudo is a good example of this as are binaries with the SUID or SGID bit.  Privileged escalation is basically a way for users to execute a file with the permissions of another user or group.  You can prevent a container from privileged escalation by implementing a pod security policy that sets `allowPriviledgedEscalation` to `false` or by setting `securityContext.allowPrivilegedEscalation` in the `podSpec`.  

## Tools
+ [kube-psp-advisor](https://github.com/sysdiglabs/kube-psp-advisor) is a tool that makes it easier to create K8s Pod Security Policies (PSPs) from either a live K8s environment or from a single .yaml file containing a pod specification (Deployment, DaemonSet, Pod, etc).
