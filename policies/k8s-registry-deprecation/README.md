As part of an effort to help the Kubernetes community with the impending registry freeze, mentioned in this [blog post](https://kubernetes.io/blog/2023/02/06/k8s-gcr-io-freeze-announcement/), we wrote the following example Gatekeeper, Kyverno and Sigstore policies for this effort. 

The Gatekeeper, Kyverno and Sigstore policies are used to detect the use of container images that use the now deprecated, soon to be frozen, `k8s.gcr.io` container image registry.

The policies are based on examples I found in the respective Gatekeeper and Kyverno policy libraries.

- [Gatekeeper](https://open-policy-agent.github.io/gatekeeper-library/website/)
- [Kyverno](https://kyverno.io/policies/)
- [Sigstore/policy-controller](https://github.com/sigstore/policy-controller): The [sigstore/policy-controller](https://github.com/sigstore/helm-charts/tree/main/charts/policy-controller) is an admission controller that enforces image policies on a cluster on verifiable supply-chain metadata.

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


