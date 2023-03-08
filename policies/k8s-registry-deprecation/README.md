As part of an effort to help the Kubernetes community with the impending registry freeze, mentioned in this [blog post](https://kubernetes.io/blog/2023/02/06/k8s-gcr-io-freeze-announcement/), we wrote the following example Gatekeeper and Kyverno policies for this effort. 

The Gatekeeper and Kyverno policies are used to detect the use of container images that use the now deprecated, soon to be frozen, `k8s.gcr.io` container image registry.

The policies are based on examples I found in the respective Gatekeeper and Kyverno policy libraries.

- [Gatekeeper](https://open-policy-agent.github.io/gatekeeper-library/website/)
- [Kyverno](https://kyverno.io/policies/)

Policies should work for the following resources:
- Pod
- Deployment
- DaemonSet
- Job
- StatefulSet
- ReplicaSet

And the following containers:
- containers
- initContainers
- ephemeralContainers

The policies are set to enforce mode, by can be set to warn/audit modes.


