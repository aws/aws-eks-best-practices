This folder contains example Gatekeeper and Kyverno policies to detect the use of container images that use the now deprecated, soon to be frozen, `k8s.gcr.io` container image registry.

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


