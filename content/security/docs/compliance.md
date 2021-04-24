# Compliance
Compliance is a shared responsibility between AWS and the consumers of its services. Generally speaking, AWS is responsible for “security of the cloud” whereas its users are responsible for “security in the cloud.” The line that delineates what AWS and its users are responsible for will vary depending on the service. For example, with Fargate, AWS is responsible for managing the physical security of its data centers, the hardware, the virtual infrastructure (Amazon EC2), and the container runtime (Docker). Users of Fargate are responsible for securing the container image and their application. Knowing who is responsible for what is an important consideration when running workloads that must adhere to compliance standards.

The following table shows the compliance programs with which the different container services conform.

| Compliance Program | Amazon ECS Orchestrator | Amazon EKS Orchestrator| ECS Fargate | Amazon ECR |
| ------------------ |:----------:|:----------:|:-----------:|:----------:|
| PCI DSS Level 1	| 1 | 1 | 1 | 1 |
| HIPAA Eligible	| 1 | 1	| 1	| 1 |
| SOC I | 1 | 1 | 1 | 1 |
| SOC II | 1 |	1 |	1 |	1 |
| SOC III |	1 |	1 |	1 |	1 |
| ISO 27001:2013 | 1 | 1 | 1 | 1 |
| ISO 9001:2015 | 1 | 1 | 1 | 1 |
| ISO 27017:2015 |	1 |	1 |	1 |	1 |
| ISO 27018:2019 |	1 |	1 |	1 |	1 |
| IRAP | 1 | 1 | 1 | 1 |
| FedRAMP Moderate (East/West) | 1 | 1 | 0 | 1 |
| FedRAMP High (GovCloud) | 1 | 1 | 0 | 1 |
| DOD CC SRG | 1 |	DISA Review (IL5) |	0 |	1 |
| HIPAA BAA | 1 | 1 | 1 | 1 |
| MTCS | 1 | 1 | 0 | 1 |
| C5 | 1 | 1 | 0 | 1 |
| K-ISMS | 1 | 1 | 0 | 1 |
| ENS High | 1 | 1 | 0 | 1 |
| OSPAR | 1 | 1 | 0 | 1 | 
| HITRUST CSF | 1 | 1 | 1 | 1 |

Compliance status changes over time. For the latest status, always refer to [https://aws.amazon.com/compliance/services-in-scope/](https://aws.amazon.com/compliance/services-in-scope/). 

For futher information about cloud accreditation models and best practices, see the AWS whitepaper, [Accreditation Models for Secure Cloud Adoption](https://d1.awsstatic.com/whitepapers/accreditation-models-for-secure-cloud-adoption.pdf) 

## Shifting Left
The concept of shifting left involves catching policy violations and errors earlier in the software development lifecycle. From a security perspective, this can be very beneficial. A developer, for example, can fix issues with their configuration before their application is deployed to the cluster. Catching mistakes like this earlier will help prevent configurations that violate your policies from being deployed.

### Policy
Policy can be thought of as a set of rules for governing behaviors, i.e. behaviors that are allowed or those that are prohibited. For example, you may have a policy that says that all Dockerfiles should include a USER directive that causes the container to run as a non-root user. As a document, a policy like this can be hard to discover and enforce. It may also become outdated as your requirements change.

## Recommendations

### Use Open Policy Agent (OPA) or Alcide's sKan to detect policy violations before deployment

[OPA](https://www.openpolicyagent.org/) is open source policy engine that's part of CNCF. It's used for making policy decisions and can be run a variety of different ways, e.g. as a language library or a service. OPA policies are written in a Domain Specific Language (DSL) called Rego. While it is often run as part of a Kubernetes Dynamic Admission Controller, OPA can also be incorporated into your CI/CD pipeline. This allows developers to get feedback about their configuration earlier in the release cycle which can subsequently help them resolve issues before they get to production. A collection of common OPA policies can be found in the GitHub [repository](https://github.com/aws/aws-eks-best-practices/tree/master/policies/opa) for this project.

+ [Conftest](https://github.com/open-policy-agent/conftest) is built on top of OPA and it provides a developer focused experience for testing Kubernetes configuration. 
+ [sKan](https://github.com/alcideio/skan) is powered by OPA and is "tailor made" to check whether their Kubernetes configuration files are compliant with security and operational best practices.

## Tools and resources
+ [kube-bench](https://github.com/aquasecurity/kube-bench)
+ [docker-bench-security](https://github.com/docker/docker-bench-security)
+ [actuary](https://github.com/diogomonica/actuary)
+ [AWS Inspector](https://aws.amazon.com/inspector/)
+ [Kubernetes Security Review](https://github.com/kubernetes/community/blob/master/sig-security/security-audit-2019/findings/Kubernetes%20Final%20Report.pdf) A 3rd party security assessment of Kubernetes 1.13.4 (2019)
