# Pod Security

Pods have a variety of different settings that can strengthen or weaken your overall security posture.  As a Kubernetes practitioner your chief concern should be preventing a process that’s running in a container from escaping the isolation boundaries of container runtime and gaining access to the underlying host.

### Linux Capabilities

The processes that run within a container run under the context of the \[Linux\] root user by default.  Although the actions of root within a container are partially constrained by the set of Linux capabilities that the container runtime assigns to the containers, these default privileges could allow an attacker to escalate their privileges and/or gain access to sensitive information bound to the host, including Secrets and ConfigMaps.  Below is a list of the default capabilities assigned to containers.  For additional information about each capability, see [http://man7.org/linux/man-pages/man7/capabilities.7.html](http://man7.org/linux/man-pages/man7/capabilities.7.html).

`CAP_AUDIT_WRITE, CAP_CHOWN, CAP_DAC_OVERRIDE, CAP_FOWNER, CAP_FSETID, CAP_KILL, CAP_MKNOD, CAP_NET_BIND_SERVICE, CAP_NET_RAW, CAP_SETGID, CAP_SETUID, CAP_SETFCAP, CAP_SETPCAP, CAP_SYS_CHROOT`

!!! info 
    
    EC2 and Fargate pods are assigned the aforementioned capabilities by default. Additionally, Linux capabilities can only be dropped from Fargate pods. 

Pods that are run as privileged, inherit _all_ of the Linux capabilities associated with root on the host. This should be avoided if possible.

### Node Authorization

All Kubernetes worker nodes use an authorization mode called [Node Authorization](https://kubernetes.io/docs/reference/access-authn-authz/node/). Node Authorization authorizes all API requests that originate from the kubelet and allows nodes to perform the following actions: 

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

## Pod Security Solutions

### Pod Security Policy (PSP)

In the past, [Pod Security Policy (PSP)](https://kubernetes.io/docs/concepts/policy/pod-security-policy/) resources were used to specify a set of requirements that pods had to meet before they could be created. PSPs were used, in conjunction with Kubernetes [Role Based Access Control (RBAC)](https://kubernetes.io/docs/reference/access-authn-authz/rbac/), to apply levels of access to work loads via role assumption.

As of Kubernetes version 1.21, PSP have been deprecated. They are scheduled for removal in Kubernetes version 1.25. 

!!! attention
    [PSPs are deprecated](https://kubernetes.io/blog/2021/04/06/podsecuritypolicy-deprecation-past-present-and-future/) in Kubernetes version 1.21. You will have until version 1.25 or roughly 2 years to transition to an alternative. This [document](https://github.com/kubernetes/enhancements/blob/master/keps/sig-auth/2579-psp-replacement/README.md#motivation) explains the motivation for this deprecation.

### Migrating to a new pod security solution

Since PSPs are scheduled to be removed and are no longer under active development, cluster administrators and operators must replace those security controls. Two solutions can fill this need:

+ Policy-as-code (PAC) solutions from the Kubernetes ecosystem
+ Kubernetes [Pod Security Standards (PSS)](https://kubernetes.io/docs/concepts/security/pod-security-standards/)

Both the PAC and PSS solutions can coexist with PSP; they can be used in clusters before PSP is removed. This reduces friction when migrating from PSP. Please see this [document](https://kubernetes.io/docs/tasks/configure-pod-container/migrate-from-psp/) when considering migrating from PSP to PSS.

### Policy-as-code (PAC)

Policy-as-code (PAC) solutions provide guardrails to guide cluster users, and prevent unwanted behaviors, through prescribed and automated controls. PAC uses [Kubernetes Admission Controllers](https://kubernetes.io/docs/reference/access-authn-authz/admission-controllers/) to intercept the Kubernetes API server request flow, and mutate and validate request payloads, based on policies written and stored as code. Mutation and validation happens before the API server request results in a change to the cluster. PAC solutions use policies to match and act on API server request payloads, based on taxonomy and values.

There are several open source PAC solutions available for Kubernetes. These solutions are not part of the Kubernetes project; they are sourced from the Kubernetes ecosystem. Some PAC solutions are listed below.

+ [Open Policy Agent (OPA)](https://www.openpolicyagent.org/)
+ [OPA/Gatekeeper](https://open-policy-agent.github.io/gatekeeper/website/docs/)
+ [Kyverno](https://kyverno.io/)
+ [Kubewarden](https://www.kubewarden.io/)
+ [jsPolicy](https://www.jspolicy.com/)

For further information about PAC solutions and how to help you select the appropriate solution for your needs, see the links below.

+ [Policy-based countermeasures for Kubernetes – Part 1](https://aws.amazon.com/blogs/containers/policy-based-countermeasures-for-kubernetes-part-1/)
+ [Policy-based countermeasures for Kubernetes – Part 2](https://aws.amazon.com/blogs/containers/policy-based-countermeasures-for-kubernetes-part-2/)

### Pod Security Standards (PSS) and Pod Security Admission (PSA)

In response to the PSP deprecation and the ongoing need to control pod security out-of-the-box, with a native Kubernetes solution, the Kubernetes [Auth Special Interest Group](https://github.com/kubernetes/community/tree/master/sig-auth) created the [Pod Security Standards (PSS)](https://kubernetes.io/docs/concepts/security/pod-security-standards/) and [Pod Security Admission (PSA)](https://kubernetes.io/docs/concepts/security/pod-security-admission/). The PSA effort includes an [admission controller webhook project](https://github.com/kubernetes/pod-security-admission#pod-security-admission) that implements the controls defined in the PSS. This admission controller approach resembles that used in the PAC solutions.

According to the Kubernetes documentation, the PSS _"define three different policies to broadly cover the security spectrum. These policies are cumulative and range from highly-permissive to highly-restrictive."_ 

These policies are defined as:

+ **Privileged:** Unrestricted (unsecure) policy, providing the widest possible level of permissions. This policy allows for known privilege escalations. It is the absence of a policy. This is good for applications such as logging agents, CNIs, storage drivers, and other system wide applications that need privileged access.
+ **Baseline:** Minimally restrictive policy which prevents known privilege escalations. Allows the default (minimally specified) Pod configuration. The baseline policy prohibits use of hostNetwork, hostPID, hostIPC, hostPath, hostPort, the inability to add Linux capabilities, along with several other restrictions. Controls are: `AppArmor, Capabilities, Host Namespaces, HostPath Volumes, Host Ports, Privileged Containers, proc mount type, SELinux, Sysctls`

+ **Restricted:** Heavily restricted policy, following current Pod hardening best practices.  This policy inherits from the baseline and adds further restrictions such as the inability to run as root or a root-group. Restricted policies may impact an application's ability to function. They are primarily targeted at running security critical applications. Controls are: `non-root users, non-root groups, Privilege Escalation, Seccomp, Volume Types`

These policies define [profiles for pod execution](https://kubernetes.io/docs/concepts/security/pod-security-standards/#profile-details), arranged into three levels of privileged vs. restricted access.

To implement the controls defined by the PSS, PSA operates in three modes:

+ **enforce:** Policy violations will cause the pod to be rejected.
+ **audit:** Policy violations will trigger the addition of an audit annotation to the event recorded in the audit log, but are otherwise allowed.
+ **warn:**	Policy violations will trigger a user-facing warning, but are otherwise allowed.

These modes and the profile (restriction) levels are configured at the Kubernetes Namespace level, using labels, as seen in the below example.

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: policy-test
  labels:
    pod-security.kubernetes.io/enforce: restricted
```

When used independently, these operational modes have different responses that result in different user experiences. The _enforce_ mode will prevent pods from being created if respective podSpecs violate the configured restriction level. However, in this mode, non-pod Kubernetes objects that create pods, such as Deployments, will not be prevented from being applied to the cluster, even if the podSpec therein violates the applied PSS. In this case the Deployment will be applied, while the pod(s) will be prevented from being applied.

This is a difficult user experience, as there is no immediate indication that the successfully applied Deployment object belies failed pod creation. The offending podSpecs will not create pods. Inspecting the Deployment resource will expose the message from the failed pod(s), as seen below.

```yaml
...
    - lastTransitionTime: "2022-01-20T01:02:08Z"
      lastUpdateTime: "2022-01-20T01:02:08Z"
      message: 'pods "test-688f68dc87-tw587" is forbidden: violates PodSecurity "restricted:latest":
        allowPrivilegeEscalation != false (container "test" must set securityContext.allowPrivilegeEscalation=false),
        unrestricted capabilities (container "test" must set securityContext.capabilities.drop=["ALL"]),
        runAsNonRoot != true (pod or container "test" must set securityContext.runAsNonRoot=true),
        seccompProfile (pod or container "test" must set securityContext.seccompProfile.type
        to "RuntimeDefault" or "Localhost")'
      reason: FailedCreate
      status: "True"
      type: ReplicaFailure
...
```

In both the _audit_ and _warn_ modes, the pod restrictions do not prevent violating pods from being created and started. However, in these modes audit annotations and warnings are triggered, respectively, when pods, as well as objects that create pods, contain podSpecs with violations, as seen below.

```bash
Warning: would violate PodSecurity "restricted:latest": allowPrivilegeEscalation != false (container "test" must set securityContext.allowPrivilegeEscalation=false), unrestricted capabilities (container "test" must set securityContext.capabilities.drop=["ALL"]), runAsNonRoot != true (pod or container "test" must set securityContext.runAsNonRoot=true), seccompProfile (pod or container "test" must set securityContext.seccompProfile.type to "RuntimeDefault" or "Localhost")
deployment.apps/test created
```

The PSA _audit_ and _warn_ modes are useful when introducing the PSS without negatively impacting cluster operations.

The PSA operational modes are not mutually exclusive, and can be used in a cumulative manner. As seen below, the multiple modes can be configured in a single namespace.

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: policy-test
  labels:
    kubernetes.io/metadata.name: policy-test
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/warn: restricted
```

In the above example, the user-friendly warnings and audit annotations are provided when applying Deployments, while the enforce of violations are also provided at the pod level. In fact multiple PSA labels can use different profile levels, as seen below.

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: policy-test
  labels:
    kubernetes.io/metadata.name: policy-test
    pod-security.kubernetes.io/enforce: baseline
    pod-security.kubernetes.io/warn: restricted
```

In the above example, PSA is configured to allow the creation of all pods that satisfy the _baseline_ profile level, and then _warn_ on pods (and objects that create pods) that violate the _restricted_ profile level. This is a useful approach to determine the possible impacts when changing from the _baseline_ to _restricted_ profiles.

PSA uses _Exemptions_ to exclude enforcement of violations against pods that would have otherwise been applied. These exemptions are seen below.

+ **Usernames:** requests from users with an exempt authenticated (or impersonated) username are ignored.
+ **RuntimeClassNames:** pods and workload resources specifying an exempt runtime class name are ignored.
+ **Namespaces:** pods and workload resources in an exempt namespace are ignored.

!!! Attention 
    
    As of Kubernetes versions _1.22_ and _1.23_, the Pod Security Admission feature is _alpha_ and _beta_ status, respectively. At least until GA, the current admission controller webhook can be configured from [these instructions](https://github.com/kubernetes/pod-security-admission/tree/master/webhook).

### Choosing between policy-as-code and Pod Security Standards

The Pod Security Standards (PSS) were developed to replace the Pod Security Policy (PSP), by providing a solution that was native to Kubernetes and did not require non-native solutions from the Kubernetes ecosystem. That being said, policy-as-code (PAC) solutions are considerably more flexible. 

The following list of Pros and Cons is designed help you make a more informed decision about your pod security solution.

**Policy-as-code (as compared to Pod Security Standards)**

Pros:

  + More flexible and more granular (down to attributes of resources if need be)
  + Not just focused on pods, can be used against different resources and actions
  + Not just applied at the namespace level
  + More mature than the Pod Security Standards
  + Decisions can be based on anything in the API server request payload, as well as existing cluster resources and external data (solution dependent)
  + Supports mutating API server requests before validation
  + Generates policies and resources (solution dependent)
  + Can be used to shift left, into CICD pipelines, before making calls to the Kubernetes API server (solution dependent)
  + Can be used to implement behaviors that are not necessarily security related, such as best practices, organizational standards, etc.
  + Can be used in non-Kubernetes use cases (solution dependent)
  + Because of flexibility, the user experience can be tuned to users' needs

Cons:

  + Not part of native Kubernetes
  + More complex to learn, configure, and support
  + Policy authoring may require new skills/languages/capabilities

**Pod Security Admission (as compared to policy-as-code)**

Pros:

  + Built into native Kubernetes
  + Simpler to configure
  + No new languages to use or policies to author

Cons:

  + Not as flexible or granular as policy-as-code
  + Only 3 levels of restrictions
  + Primarily focused on pods

#### Summary
If you currently do not have a pod security solution, beyond PSP, and your required pod security posture fits the model defined in the Pod Security Standards (PSS), then an easier path may be to adopt the PSS, in lieu of a policy-as-code solution. However, if your pod security posture does not fit the PSS model, or you envision adding additional controls, beyond that defined by PSS, then a policy-as-code solution would seem a better fit.

## Recommendations

### Restrict the containers that can run as privileged

As mentioned, containers that run as privileged inherit all of the Linux capabilities assigned to root on the host.  Seldom do containers need these types of privileges to function properly.  There are multiple methods that can be used to restrict the permissions and capabilities of containers.

!!! Attention 
    
    Fargate is a launch type that enables you to run "serverless" container(s) where the containers of a pod are run on infrastructure that AWS manages. With Fargate, you cannot run a privileged container or configure your pod to use hostNetwork or hostPort.

### Do not run processes in containers as root

All containers run as root by default.  This could be problematic if an attacker is able to exploit a vulnerability in the application and get shell access to the running container.  You can mitigate this risk a variety of ways.  First, by removing the shell from the container image.  Second, adding the USER directive to your Dockerfile or running the containers in the pod as a non-root user.  The Kubernetes podSpec includes a set of fields, under `spec.securityContext`, that let you specify the user and/or group under which to run your application.  These fields are `runAsUser` and `runAsGroup` respectively.  

To enforce the use of the `spec.securityContext`, and its associated elements, within the Kubernetes podSpec, policy-as-code or Pod Security Standards can be added to clusters. These solutions allow you to write and/or use policies or profiles that can validate inbound Kubernetes API server request payloads, before they are persisted into etcd. Furthermore, policy-as-code solutions can mutate inbound requests, and in some cases, generate new requests.

### Never run Docker in Docker or mount the socket in the container

While this conveniently lets you to build/run images in Docker containers, you're basically relinquishing complete control of the node to the process running in the container. If you need to build container images on Kubernetes use [Kaniko](https://github.com/GoogleContainerTools/kaniko), [buildah](https://github.com/containers/buildah), [img](https://github.com/genuinetools/img), or a build service like [CodeBuild](https://docs.aws.amazon.com/codebuild/latest/userguide/welcome.html) instead. 

!!! Tip
    Kubernetes clusters used for CICD processing, such as building container images, should be isolated from clusters running more generalized workloads.

### Restrict the use of hostPath or if hostPath is necessary restrict which prefixes can be used and configure the volume as read-only

`hostPath` is a volume that mounts a directory from the host directly to the container.  Rarely will pods need this type of access, but if they do, you need to be aware of the risks.  By default pods that run as root will have write access to the file system exposed by hostPath.  This could allow an attacker to modify the kubelet settings, create symbolic links to directories or files not directly exposed by the hostPath, e.g. /etc/shadow, install ssh keys, read secrets mounted to the host, and other malicious things. To mitigate the risks from hostPath, configure the `spec.containers.volumeMounts` as `readOnly`, for example: 

```yaml
volumeMounts:
- name: hostPath-volume
    readOnly: true
    mountPath: /host-path
```

You should also use policy-as-code solutions to restrict the directories that can be used by `hostPath` volumes, or prevent `hostPath` usage altogether.  You can use the Pod Security Standards _Baseline_ or _Restricted_ policies to prevent the use of `hostPath`.

For further information about the dangers of privileged escalation, read Seth Art's blog [Bad Pods: Kubernetes Pod Privilege Escalation](https://labs.bishopfox.com/tech-blog/bad-pods-kubernetes-pod-privilege-escalation).

### Set requests and limits for each container to avoid resource contention and DoS attacks

A pod without requests or limits can theoretically consume all of the resources available on a host.  As additional pods are scheduled onto a node, the node may experience CPU or memory pressure which can cause the Kubelet to terminate or evict pods from the node.  While you can’t prevent this from happening all together, setting requests and limits will help minimize resource contention and mitigate the risk from poorly written applications that consume an excessive amount of resources. 

The `podSpec` allows you to specify requests and limits for CPU and memory.  CPU is considered a compressible resource because it can be oversubscribed.  Memory is incompressible, i.e. it cannot be shared among multiple containers.  

When you specify _requests_ for CPU or memory, you’re essentially designating the amount of _memory_ that containers are guaranteed to get.  Kubernetes aggregates the requests of all the containers in a pod to determine which node to schedule the pod onto.  If a container exceeds the requested amount of memory it may be subject to termination if there’s memory pressure on the node. 

_Limits_ are the maximum amount of CPU and memory resources that a container is allowed to consume and directly corresponds to the `memory.limit_in_bytes` value of the cgroup created for the container.  A container that exceeds the memory limit will be OOM killed. If a container exceeds its CPU limit, it will be throttled. 

Kubernetes uses three Quality of Service (QoS) classes to prioritize the workloads running on a node.  These include: 

+ guaranteed
+ burstable
+ best-effort

If limits and requests are not set, the pod is configured as _best-effort_ (lowest priority).  Best-effort pods are the first to get killed when there is insufficient memory.  If limits are set on _all_ containers within the pod, or if the requests and limits are set to the same values and not equal to 0, the pod is configured as _guaranteed_ (highest priority).  Guaranteed pods will not be killed unless they exceed their configured memory limits. If the limits and requests are configured with different values and not equal to 0, or one container within the pod sets limits and the others don’t or have limits set for different resources, the pods are configured as _burstable_ (medium priority). These pods have some resource guarantees, but can be killed once they exceed their requested memory. 

!!! attention
    Requests don't affect the `memory_limit_in_bytes` value of the container's cgroup; the cgroup limit is set to the amount of memory available on the host. Nevertheless, setting the requests value too low could cause the pod to be targeted for termination by the kubelet if the node undergoes memory pressure. 

| Class | Priority | Condition | Kill Condition |
| :-- | :-- | :-- | :-- |
| Guaranteed | highest | limit = request != 0  | Only exceed memory limits |
| Burstable  | medium  | limit != request != 0 | Can be killed if exceed request memory |
| Best-Effort| lowest  | limit & request Not Set | First to get killed when there's insufficient memory |

For additional information about resource QoS, please refer to the [Kubernetes documentation](https://github.com/kubernetes/community/blob/master/contributors/design-proposals/node/resource-qos.md).

You can force the use of requests and limits by setting a [resource quota](https://kubernetes.io/docs/concepts/policy/resource-quotas/) on a namespace or by creating a [limit range](https://kubernetes.io/docs/concepts/policy/limit-range/).  A resource quota allows you to specify the total amount of resources, e.g. CPU and RAM, allocated to a namespace.  When it’s applied to a namespace, it forces you to specify requests and limits for all containers deployed into that namespace. By contrast, limit ranges give you more granular control of the allocation of resources. With limit ranges you can min/max for CPU and memory resources per pod or per container within a namespace.  You can also use them to set default request/limit values if none are provided.

Policy-as-code solutions can be used enforce requests and limits. or to even create the resource quotas and limit ranges when namespaces are created.

### Do not allow privileged escalation

Privileged escalation allows a process to change the security context under which its running.  Sudo is a good example of this as are binaries with the SUID or SGID bit.  Privileged escalation is basically a way for users to execute a file with the permissions of another user or group.  You can prevent a container from using privileged escalation by implementing a policy-as-code mutating policy that sets `allowPrivilegeEscalation` to `false` or by setting `securityContext.allowPrivilegeEscalation` in the `podSpec`. Policy-as-code policies can also be used to prevent API server requests from succeeding if incorrect settings are detected. Pod Security Standards can also be used to prevent pods from using privilege escalation.

### Disable ServiceAccount token mounts

For pods that do not need to access the Kubernetes API, you can disable the
automatic mounting of a ServiceAccount token on a pod spec, or for all pods that
use a particular ServiceAccount.

!!! attention
    Disabling ServiceAccount mounting does not prevent a pod from having network
    access to the Kubernetes API. To prevent a pod from having any network
    access to the Kubernetes API, you will need to modify the [EKS cluster
    endpoint access][eks-ep-access] and use
    [NetworkPolicy](../network/#network-policy) to block pod access

[eks-ep-access]: https://docs.aws.amazon.com/eks/latest/userguide/cluster-endpoint.html

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: pod-no-automount
spec:
  automountServiceAccountToken: false
```

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: sa-no-automount
automountServiceAccountToken: false
```

### Disable service discovery

For pods that do not need to lookup or call in-cluster services, you can
reduce the amount of information given to a pod. You can set the Pod's DNS
policy to not use CoreDNS, and not expose services in the pod's namespace as
environment variables. See the [Kubernetes docs on environment
variables][k8s-env-var-docs] for more information on service links. The default
value for a pod's DNS policy is "ClusterFirst" which uses in-cluster DNS, while
the non-default value "Default" uses the underlying node's DNS resolution. See
the [Kubernetes docs on Pod DNS policy][dns-policy] for more information.

[k8s-env-var-docs]: https://kubernetes.io/docs/concepts/services-networking/service/#environment-variables
[dns-policy]: https://kubernetes.io/docs/concepts/services-networking/dns-pod-service/#pod-s-dns-policy

!!! attention
    Disabling service links and changing the pod's DNS policy does not prevent a
    pod from having network access to the in-cluster DNS service. An attacker
    can still enumerate services in a cluster by reaching the in-cluster DNS
    service. (ex: `dig SRV *.*.svc.cluster.local @$CLUSTER_DNS_IP`) To prevent
    in-cluster service discovery, use [NetworkPolicy](../network/#network-policy)
    to block pod access

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: pod-no-service-info
spec:
    dnsPolicy: Default # "Default" is not the true default value
    enableServiceLinks: false
```

### Configure your images with read-only root file system

Configuring your images with a read-only root file system prevents an attacker from overwriting a binary on the file system that your application uses. If your application has to write to the file system, consider writing to a temporary directory or attach and mount a volume. You can enforce this by setting the pod's SecurityContext as follows:

```yaml
...
securityContext:
  readOnlyRootFilesystem: true
...
``` 

Policy-as-code and Pod Security Standards can be used to enforce this behavior.

## Tools and Resources

+ [open-policy-agent/gatekeeper-library: The OPA Gatekeeper policy library](https://github.com/open-policy-agent/gatekeeper-library) a library of OPA/Gatekeeper policies that you can use as a substitute for PSPs.
+ [Kyverno Policy Library](https://kyverno.io/policies/)
+ A collection of common OPA and Kyverno [policies](https://github.com/aws/aws-eks-best-practices/tree/master/policies) for EKS.
+ [Policy based countermeasures: part 1](https://aws.amazon.com/blogs/containers/policy-based-countermeasures-for-kubernetes-part-1/)
+ [Policy based countermeasures: part 2](https://aws.amazon.com/blogs/containers/policy-based-countermeasures-for-kubernetes-part-2/)
