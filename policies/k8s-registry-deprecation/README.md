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

## Sigstore/policy-controller

By default, the Sigstore policy-controller requires to label every namespace where a container image policy wants to be enforced. For these labeled namespaces, the policy-controller will reject any container image that does not match any of the existing policies. 

These are the default settings although the policy-controller allows to configure a different behavior such as warning when an image does not match any policy, or to enforce policies on all namespaces. To do so, you just need to apply the following commands when installing the policy-controller on your cluster:

```shell
cat > values.yaml <<EOF
policywebhook:
  configData:
    no-match-policy: warn
webhook:
  namespaceSelector:
    matchExpressions:
      - key: policy.sigstore.dev/exclude
        operator: NotIn
        values: ["true"]
EOF
```

The `values.yaml` file sets a namespace selector for the webhook to only label namespaces that we want to exclude from the admission verifications. It also configures the policy-controller to warn whenever a container image does not match any policy with `no-match-policy: warn`.

For its installation, we recommend using the [helm chart](https://github.com/sigstore/helm-charts/tree/main/charts/policy-controller):

```shell
helm install policy-controller -n cosign-system sigstore/policy-controller --devel --create-namespace --values=values.yaml

kubectl label ns cosign-system policy.sigstore.dev/exclude=true
```