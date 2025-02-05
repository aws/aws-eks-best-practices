---
redirect: https://docs.aws.amazon.com/eks/latest/best-practices/compliance.html
---


!!! info "We've Moved to the AWS Docs! 🚀"
    This content has been updated and relocated to improve your experience. 
    Please visit our new site for the latest version:
    [AWS EKS Best Practices Guide](https://docs.aws.amazon.com/eks/latest/best-practices/compliance.html) on the AWS Docs

    Bookmarks and links will continue to work, but we recommend updating them for faster access in the future.

---

# Compliance

Compliance is a shared responsibility between AWS and the consumers of its services. Generally speaking, AWS is responsible for “security of the cloud” whereas its users are responsible for “security in the cloud.” The line that delineates what AWS and its users are responsible for will vary depending on the service. For example, with Fargate, AWS is responsible for managing the physical security of its data centers, the hardware, the virtual infrastructure (Amazon EC2), and the container runtime (Docker). Users of Fargate are responsible for securing the container image and their application. Knowing who is responsible for what is an important consideration when running workloads that must adhere to compliance standards.

The following table shows the compliance programs with which the different container services conform.

| Compliance Program | Amazon ECS Orchestrator | Amazon EKS Orchestrator| ECS Fargate | Amazon ECR |
| ------------------ |:----------:|:----------:|:-----------:|:----------:|
| PCI DSS Level 1 | 1 | 1 | 1 | 1 |
| HIPAA Eligible | 1 | 1 | 1 | 1 |
| SOC I | 1 | 1 | 1 | 1 |
| SOC II | 1 | 1 | 1 | 1 |
| SOC III | 1 | 1 | 1 | 1 |
| ISO 27001:2013 | 1 | 1 | 1 | 1 |
| ISO 9001:2015 | 1 | 1 | 1 | 1 |
| ISO 27017:2015 | 1 | 1 | 1 | 1 |
| ISO 27018:2019 | 1 | 1 | 1 | 1 |
| IRAP | 1 | 1 | 1 | 1 |
| FedRAMP Moderate (East/West) | 1 | 1 | 0 | 1 |
| FedRAMP High (GovCloud) | 1 | 1 | 0 | 1 |
| DOD CC SRG | 1 | DISA Review (IL5) | 0 | 1 |
| HIPAA BAA | 1 | 1 | 1 | 1 |
| MTCS | 1 | 1 | 0 | 1 |
| C5 | 1 | 1 | 0 | 1 |
| K-ISMS | 1 | 1 | 0 | 1 |
| ENS High | 1 | 1 | 0 | 1 |
| OSPAR | 1 | 1 | 0 | 1 |
| HITRUST CSF | 1 | 1 | 1 | 1 |

Compliance status changes over time. For the latest status, always refer to [https://aws.amazon.com/compliance/services-in-scope/](https://aws.amazon.com/compliance/services-in-scope/).

For further information about cloud accreditation models and best practices, see the AWS whitepaper, [Accreditation Models for Secure Cloud Adoption](https://d1.awsstatic.com/whitepapers/accreditation-models-for-secure-cloud-adoption.pdf)

## Shifting Left

The concept of shifting left involves catching policy violations and errors earlier in the software development lifecycle. From a security perspective, this can be very beneficial. A developer, for example, can fix issues with their configuration before their application is deployed to the cluster. Catching mistakes like this earlier will help prevent configurations that violate your policies from being deployed.

### Policy as Code

Policy can be thought of as a set of rules for governing behaviors, i.e. behaviors that are allowed or those that are prohibited. For example, you may have a policy that says that all Dockerfiles should include a USER directive that causes the container to run as a non-root user. As a document, a policy like this can be hard to discover and enforce. It may also become outdated as your requirements change. With Policy as Code (PaC) solutions, you can automate security, compliance, and privacy controls that detect, prevent, reduce, and counteract known and persistent threats. Furthermore, they give you mechanism to codify your policies and manage them as you do other code artifacts. The benefit of this approach is that you can reuse your DevOps and GitOps strategies to manage and consistently apply policies across fleets of Kubernetes clusters. Please refer to [Pod Security](https://aws.github.io/aws-eks-best-practices/security/docs/pods/#pod-security) for information about PaC options and the future of PSPs.

### Use policy-as-code tools in pipelines to detect violations before deployment

- [OPA](https://www.openpolicyagent.org/) is an open source policy engine that's part of the CNCF. It's used for making policy decisions and can be run a variety of different ways, e.g. as a language library or a service. OPA policies are written in a Domain Specific Language (DSL) called Rego. While it is often run as part of a Kubernetes Dynamic Admission Controller as the [Gatekeeper](https://github.com/open-policy-agent/gatekeeper) project, OPA can also be incorporated into your CI/CD pipeline. This allows developers to get feedback about their configuration earlier in the release cycle which can subsequently help them resolve issues before they get to production. A collection of common OPA policies can be found in the GitHub [repository](https://github.com/aws/aws-eks-best-practices/tree/master/policies/opa) for this project.
- [Conftest](https://github.com/open-policy-agent/conftest) is built on top of OPA and it provides a developer focused experience for testing Kubernetes configuration.
- [Kyverno](https://kyverno.io/) is a policy engine designed for Kubernetes. With Kyverno, policies are managed as Kubernetes resources and no new language is required to write policies. This allows using familiar tools such as kubectl, git, and kustomize to manage policies. Kyverno policies can validate, mutate, and generate Kubernetes resources plus ensure OCI image supply chain security. The [Kyverno CLI](https://kyverno.io/docs/kyverno-cli/) can be used to test policies and validate resources as part of a CI/CD pipeline. All the Kyverno community policies can be found on the [Kyverno website](https://kyverno.io/policies/), and for examples using the Kyverno CLI to write tests in pipelines, see the [policies repository](https://github.com/kyverno/policies).

## Tools and resources

- [Amazon EKS Security Immersion Workshop - Regulatory Compliance](https://catalog.workshops.aws/eks-security-immersionday/en-US/10-regulatory-compliance)
- [kube-bench](https://github.com/aquasecurity/kube-bench)
- [docker-bench-security](https://github.com/docker/docker-bench-security)
- [AWS Inspector](https://aws.amazon.com/inspector/)
- [Kubernetes Security Review](https://github.com/kubernetes/community/blob/master/sig-security/security-audit-2019/findings/Kubernetes%20Final%20Report.pdf) A 3rd party security assessment of Kubernetes 1.13.4 (2019)
- [NeuVector by SUSE](https://www.suse.com/neuvector/) open source, zero-trust container security platform, provides compliance reporting and custom compliance checks
