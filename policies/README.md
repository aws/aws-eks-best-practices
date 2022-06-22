This repository contains two separate examples. 

In the first (/kyverno and /opa) we have some example policies that are consistent between kyverno, OPA without Gatekeeper and OPA with Gatekeeper. These will help you see the differences on how to use these three tools.

In the second (/alternative-gatekeeper) we have another documented example of Gatekeeper-only policies that include those items in the legacy [Restricted legacy PSP template](https://kubernetes.io/docs/concepts/security/pod-security-standards/#restricted) as well as a few more important things that were not possible with PSPs but are with Gatekeeper (requiring cpu&memory limits, requiring readiness and liveness probes and blocking the use of the latest tag). The second example is intended as one that can be deployed as-is to existing clusters and excludes the kube-system namespace by default to not conflict with many add-ons that may be deployed there.
