# Pod Security Contexts
**Pod Security Policies (PSP)** and **Pod Security Standards (PSS)** are two main ways of enforcing security in Kubernetes. Note that PodSecurityPolicy is deprecated as of Kubernetes v1.21, and will be removed in v1.25 and Pod Security Standard (PSS) is the Kubernetes recommended approach for enforcing security going forward.

A Pod Security Policy (PSP) is a native solution in Kubernetes to implement security policies. PSP is a cluster-level resource that controls security-sensitive aspects of the Pod specification. Using Pod Security Policy you can define a set of conditions that Pods must meet to be accepted by the cluster.
The PSP feature has been available from the early days of Kubernetes and is designed to block misconfigured pods from being created on a given cluster.

For more information on Pod Security Policies please reference the Kubernetes [documentation](https://kubernetes.io/docs/concepts/policy/pod-security-policy/). According to the [Kubernetes deprecation policy](https://kubernetes.io/docs/reference/using-api/deprecation-policy/), older versions will stop getting support nine months after the deprecation of the feature.

On the other hand, Pod Security Standards (PSS) which is the recommended security approach and typically implemented using Security Contexts are defined as part of the Pod and container specifications in the Pod manifest. PSS is the official standard that the Kubernetes project team has defined to address the security-related best practices for Pods. It defines policies such as baseline (minimally restrictive, default), privileged (unrestrictive) and restricted (most restrictive).

We recommend starting with the baseline profile. PSS baseline profile provides a solid balance between security and potential friction, requiring a minimal list of exceptions, it serves as a good starting point for workload security. If you are currently using PSPs we recommend switching to PSS. More details on the PSS policies can be found in the Kubernetes [documentation](https://kubernetes.io/docs/concepts/security/pod-security-standards/). These policies can be enforced with several tools including those from [OPA](https://www.openpolicyagent.org/), [Kyverno](https://kyverno.io/) and [Datree](https://hub.datree.io/built-in-rules). For example, both [Datree](https://hub.datree.io/built-in-rules/rules/#EKS) and [Kyverno](https://kyverno.io/policies/pod-security/) provides the full collection of PSS policies.

Security context settings allow one to give privileges to select processes, use program profiles to restrict capabilities to individual programs, allow privilege escalation, filter system calls, among other things.

Windows pods in Kubernetes have some limitations and differentiators from standard Linux-based workloads when it comes to security contexts.

Windows uses a Job object per container with a system namespace filter to contain all processes in a container and provide logical isolation from the host. There is no way to run a Windows container without the namespace filtering in place. This means that system privileges cannot be asserted in the context of the host, and thus privileged containers are not available on Windows.

The following `windowsOptions` are the only documented [Windows Security Context options](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.20/#windowssecuritycontextoptions-v1-core) while the rest are general [Security Context options](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.21/#securitycontext-v1-core (https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.21/#securitycontext-v1-core))

For a list of security context attributes that are supported in Windows vs linux, please refer to the official documentation [here](https://kubernetes.io/docs/setup/production-environment/windows/_print/#v1-container).

The Pod specific settings are applied to all containers. If unspecified, the options from the PodSecurityContext will be used. If set in both SecurityContext and PodSecurityContext, the value specified in SecurityContext takes precedence.

For example, runAsUserName setting for Pods and containers which is a Windows option is a rough equivalent of the Linux-specific runAsUser setting and in the following manifest, the pod specific security context is applied to all containers

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: run-as-username-pod-demo
spec:
  securityContext:
    windowsOptions:
      runAsUserName: "ContainerUser"
  containers:
  - name: run-as-username-demo
    ...
  nodeSelector:
    kubernetes.io/os: windows
```

Whereas in the following, the container level security context overrides the pod level security context.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: run-as-username-container-demo
spec:
  securityContext:
    windowsOptions:
      runAsUserName: "ContainerUser"
  containers:
  - name: run-as-username-demo
    ..
    securityContext:
        windowsOptions:
            runAsUserName: "ContainerAdministrator"
  nodeSelector:
    kubernetes.io/os: windows
```

Examples of acceptable values for the runAsUserName field: ContainerAdministrator, ContainerUser, NT AUTHORITY\NETWORK SERVICE, NT AUTHORITY\LOCAL SERVICE

It is generally a good idea to run your containers with ContainerUser for Windows pods. The users are not shared between the container and host but the ContainerAdministrator does have additional privileges with in the container. Note that, there are username [limitations](https://kubernetes.io/docs/tasks/configure-pod-container/configure-runasusername/#windows-username-limitations) to be aware of.

A good example of when to use ContainerAdministrator is to set PATH. You can use the USER directive to do that, like so:

```bash
USER ContainerAdministrator
RUN setx /M PATH "%PATH%;C:/your/path"
USER ContainerUser
```

Also note that, secrets are written in clear text on the node's volume (as compared to tmpfs/in-memory on linux). This means you have to do two things

* Use file ACLs to secure the secrets file location
* Use volume-level encryption using [BitLocker](https://docs.microsoft.com/en-us/windows/security/information-protection/bitlocker/bitlocker-how-to-deploy-on-windows-server)
