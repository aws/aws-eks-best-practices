This repository contains two separate examples.

In the first (/kyverno and /opa) we have some example policies that are consistent between Kyverno, OPA without Gatekeeper, and OPA with Gatekeeper. These will help you see the differences on how to use these three tools.

In the second (/alternative-gatekeeper) we have another documented example of Gatekeeper-only policies that include those items in the legacy [Restricted legacy PSP template](https://kubernetes.io/docs/concepts/security/pod-security-standards/#restricted) as well as a few more important things that were not possible with PSPs but are with Gatekeeper (requiring cpu&memory limits, requiring readiness and liveness probes and blocking the use of the latest tag). The second example is intended as one that can be deployed as-is to existing clusters and excludes the kube-system namespace by default to not conflict with many add-ons that may be deployed there.

In /datree, you will find many examples of Datree's built-in rules for EKS such as pod and network security best practices, multi-tanency, requiring readiness and liveness probes, and blocking use of the latest tag.

Datree's policy can be used by simply installing [Datree](https://github.com/datreeio/datree) and enabling monitoring with its built-in rules for EKS. You can find additional policies included in Datree's built-in policy for EKS in the [Datree documentation](https://hub.datree.io/) as well as information on how to get started with Datree.
