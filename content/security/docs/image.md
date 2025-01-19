---
redirect: https://docs.aws.amazon.com/eks/latest/best-practices/image-security.html
---


!!! info "We've Moved to the AWS Docs! 🚀"
    This content has been updated and relocated to improve your experience. 
    Please visit our new site for the latest version:
    [AWS EKS Best Practices Guide](https://docs.aws.amazon.com/eks/latest/best-practices/image-security.html) on the AWS Docs

    Bookmarks and links will continue to work, but we recommend updating them for faster access in the future.

---

# Image security

You should consider the container image as your first line of defense against an attack. An insecure, poorly constructed image can allow an attacker to escape the bounds of the container and gain access to the host. Once on the host, an attacker can gain access to sensitive information or move laterally within the cluster or with your AWS account. The following best practices will help mitigate risk of this happening.

## Recommendations

### Create minimal images

Start by removing all extraneous binaries from the container image. If you’re using an unfamiliar image from Dockerhub, inspect the image using an application like [Dive](https://github.com/wagoodman/dive) which can show you the contents of each of the container’s layers. Remove all binaries with the SETUID and SETGID bits as they can be used to escalate privilege and consider removing all shells and utilities like nc and curl that can be used for nefarious purposes. You can find the files with SETUID and SETGID bits with the following command:

```bash
find / -perm /6000 -type f -exec ls -ld {} \;
```

To remove the special permissions from these files, add the following directive to your container image:

```docker
RUN find / -xdev -perm /6000 -type f -exec chmod a-s {} \; || true
```

Colloquially, this is known as de-fanging your image.

### Use multi-stage builds

Using multi-stage builds is a way to create minimal images. Oftentimes, multi-stage builds are used to automate parts of the Continuous Integration cycle. For example, multi-stage builds can be used to lint your source code or perform static code analysis. This affords developers an opportunity to get near immediate feedback instead of waiting for a pipeline to execute. Multi-stage builds are attractive from a security standpoint because they allow you to minimize the size of the final image pushed to your container registry. Container images devoid of build tools and other extraneous binaries improves your security posture by reducing the attack surface of the image. For additional information about multi-stage builds, see [Docker's multi-stage builds documentation](https://docs.docker.com/develop/develop-images/multistage-build/).

### Create Software Bill of Materials (SBOMs) for your container image

A “software bill of materials” (SBOM) is a nested inventory of the software artifacts that make up your container image.
SBOM is a key building block in software security and software supply chain risk management. [Generating, storing SBOMS in a central repository and scanning SBOMs for vulnerabilities](https://anchore.com/sbom/) helps address the following concerns:

- **Visibility**: understand what components make up your container image. Storing in a central repository allows SBOMs to be audited and scanned anytime, even post deployment to detect and respond to new vulnerabilities such as zero day vulnerabilities.
- **Provenance Verification**: assurance that existing assumptions of where and how an artifact originates from are true and that the artifact or its accompanying metadata have not been tampered with during the build or delivery processes.
- **Trustworthiness**: assurance that a given artifact and its contents can be trusted to do what it is purported to do, i.e. is suitable for a purpose. This involves judgement on whether the code is safe to execute and making informed decisions about the risks associated with executing the code. Trustworthiness is assured by creating an attested pipeline execution report along with attested SBOM and attested CVE scan report to assure the consumers of the image that this image is in-fact created through secure means (pipeline) with secure components.
- **Dependency Trust Verification**: recursive checking of an artifact’s dependency tree for trustworthiness and provenance of the artifacts it uses. Drift in SBOMs can help detect malicious activity including unauthorized, untrusted dependencies, infiltration attempts.

The following tools can be used to generate SBOM:

- [Amazon Inspector](https://docs.aws.amazon.com/inspector) can be used to [create and export SBOMs](https://docs.aws.amazon.com/inspector/latest/user/sbom-export.html).
- [Syft from Anchore](https://github.com/anchore/syft) can also be used for SBOM generation. For quicker vulnerability scans, the SBOM generated for a container image can be used as an input to scan. The SBOM and scan report are then [attested and attached](https://github.com/sigstore/cosign/blob/main/doc/cosign_attach_attestation.md) to the image before pushing the image to a central OCI repository such as Amazon ECR for review and audit purposes.

Learn more about securing your software supply chain by reviewing [CNCF Software Supply Chain Best Practices guide](https://project.linuxfoundation.org/hubfs/CNCF_SSCP_v1.pdf).

### Scan images for vulnerabilities regularly

Like their virtual machine counterparts, container images can contain binaries and application libraries with vulnerabilities or develop vulnerabilities over time. The best way to safeguard against exploits is by regularly scanning your images with an image scanner. Images that are stored in Amazon ECR can be scanned on push or on-demand (once during a 24 hour period). ECR currently supports [two types of scanning - Basic and Enhanced](https://docs.aws.amazon.com/AmazonECR/latest/userguide/image-scanning.html). Basic scanning leverages [Clair](https://github.com/quay/clair) an open source image scanning solution for no cost. [Enhanced scanning](https://docs.aws.amazon.com/AmazonECR/latest/userguide/image-scanning-enhanced.html) uses Amazon Inspector to provide automatic continuous scans for [additional cost](https://aws.amazon.com/inspector/pricing/). After an image is scanned, the results are logged to the event stream for ECR in EventBridge. You can also see the results of a scan from within the ECR console. Images with a HIGH or CRITICAL vulnerability should be deleted or rebuilt. If an image that has been deployed develops a vulnerability, it should be replaced as soon as possible.

Knowing where images with vulnerabilities have been deployed is essential to keeping your environment secure. While you could conceivably build an image tracking solution yourself, there are already several commercial offerings that provide this and other advanced capabilities out of the box, including:

- [Grype](https://github.com/anchore/grype)
- [Palo Alto - Prisma Cloud (twistcli)](https://docs.paloaltonetworks.com/prisma/prisma-cloud/prisma-cloud-admin-compute/tools/twistcli_scan_images)
- [Aqua](https://www.aquasec.com/)
- [Kubei](https://github.com/Portshift/kubei)
- [Trivy](https://github.com/aquasecurity/trivy)
- [Snyk](https://support.snyk.io/hc/en-us/articles/360003946917-Test-images-with-the-Snyk-Container-CLI)

A Kubernetes validation webhook could also be used to validate that images are free of critical vulnerabilities. Validation webhooks are invoked prior to the Kubernetes API. They are typically used to reject requests that don't comply with the validation criteria defined in the webhook. [This](https://aws.amazon.com/blogs/containers/building-serverless-admission-webhooks-for-kubernetes-with-aws-sam/) is an example of a serverless webhook that calls the ECR describeImageScanFindings API to determine whether a pod is pulling an image with critical vulnerabilities. If vulnerabilities are found, the pod is rejected and a message with list of CVEs is returned as an Event.

### Use attestations to validate artifact integrity

An attestation is a cryptographically signed “statement” that claims something - a “predicate” e.g. a pipeline run or the SBOM or the vulnerability scan report is true about another thing - a “subject” i.e. the container image.

Attestations help users to validate that an artifact comes from a trusted source in the software supply chain. As an example, we may use a container image without knowing all the software components or dependencies that are included in that image. However, if we trust whatever the producer of the container image says about what software is present, we can use the producer’s attestation to rely on that artifact. This means that we can proceed to use the artifact safely in our workflow in place of having done the analysis ourself.

- Attestations can be created using [AWS Signer](https://docs.aws.amazon.com/signer/latest/developerguide/Welcome.html) or [Sigstore cosign](https://github.com/sigstore/cosign/blob/main/doc/cosign_attest.md).
- Kubernetes admission controllers such as [Kyverno](https://kyverno.io/) can be used to [verify attestations](https://kyverno.io/docs/writing-policies/verify-images/sigstore/).
- Refer to this [workshop](https://catalog.us-east-1.prod.workshops.aws/workshops/49343bb7-2cc5-4001-9d3b-f6a33b3c4442/en-US/0-introduction) to learn more about software supply chain management best practices on AWS using open source tools with topics including creating and attaching attestations to a container image.

### Create IAM policies for ECR repositories

Nowadays, it is not uncommon for an organization to have multiple development teams operating independently within a shared AWS account. If these teams don't need to share assets, you may want to create a set of IAM policies that restrict access to the repositories each team can interact with. A good way to implement this is by using ECR [namespaces](https://docs.aws.amazon.com/AmazonECR/latest/userguide/Repositories.html#repository-concepts). Namespaces are a way to group similar repositories together. For example, all of the registries for team A can be prefaced with the team-a/ while those for team B can use the team-b/ prefix. The policy to restrict access might look like the following:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowPushPull",
      "Effect": "Allow",
      "Action": [
        "ecr:GetDownloadUrlForLayer",
        "ecr:BatchGetImage",
        "ecr:BatchCheckLayerAvailability",
        "ecr:PutImage",
        "ecr:InitiateLayerUpload",
        "ecr:UploadLayerPart",
        "ecr:CompleteLayerUpload"
      ],
      "Resource": [
        "arn:aws:ecr:<region>:<account_id>:repository/team-a/*"
      ]
    }
  ]
}
```

### Consider using ECR private endpoints

The ECR API has a public endpoint. Consequently, ECR registries can be accessed from the Internet so long as the request has been authenticated and authorized by IAM. For those who need to operate in a sandboxed environment where the cluster VPC lacks an Internet Gateway (IGW), you can configure a private endpoint for ECR. Creating a private endpoint enables you to privately access the ECR API through a private IP address instead of routing traffic across the Internet. For additional information on this topic, see [Amazon ECR interface VPC endpoints](https://docs.aws.amazon.com/AmazonECR/latest/userguide/vpc-endpoints.html).

### Implement endpoint policies for ECR

The default endpoint policy for allows access to all ECR repositories within a region. This might allow an attacker/insider to exfiltrate data by packaging it as a container image and pushing it to a registry in another AWS account. Mitigating this risk involves creating an endpoint policy that limits API access to ECR repositories. For example, the following policy allows all AWS principles in your account to perform all actions against your and only your ECR repositories:

```json
{
  "Statement": [
    {
      "Sid": "LimitECRAccess",
      "Principal": "*",
      "Action": "*",
      "Effect": "Allow",
      "Resource": "arn:aws:ecr:<region>:<account_id>:repository/*"
    }
  ]
}
```

You can enhance this further by setting a condition that uses the new `PrincipalOrgID` attribute which will prevent pushing/pulling of images by an IAM principle that is not part of your AWS Organization. See, [aws:PrincipalOrgID](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_condition-keys.html#condition-keys-principalorgid) for additional details.
We recommended applying the same policy to both the `com.amazonaws.<region>.ecr.dkr` and the `com.amazonaws.<region>.ecr.api` endpoints.
Since EKS pulls images for kube-proxy, coredns, and aws-node from ECR, you will need to add the account ID of the registry, e.g. `602401143452.dkr.ecr.us-west-2.amazonaws.com/*` to the list of resources in the endpoint policy or alter the policy to allow pulls from "*" and restrict pushes to your account ID. The table below reveals the mapping between the AWS accounts where EKS images are vended from and cluster region.

|Account Number |Region |
|--- |--- |
|602401143452 |All commercial regions except for those listed below |
|--- |--- |
|800184023465 |ap-east-1 - Asia Pacific (Hong Kong) |
|558608220178 |me-south-1 - Middle East (Bahrain) |
|918309763551 |cn-north-1 - China (Beijing) |
|961992271922 |cn-northwest-1 - China (Ningxia) |

For further information about using endpoint policies, see [Using VPC endpoint policies to control Amazon ECR access](https://aws.amazon.com/blogs/containers/using-vpc-endpoint-policies-to-control-amazon-ecr-access/).

### Implement lifecycle policies for ECR

The [NIST Application Container Security Guide](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-190.pdf) warns about the risk of "stale images in registries", noting that over time old images with vulnerable, out-of-date software packages should be removed to prevent accidental deployment and exposure.
Each ECR repository can have a lifecycle policy that sets rules for when images expire. The [AWS official documentation](https://docs.aws.amazon.com/AmazonECR/latest/userguide/LifecyclePolicies.html) describes how to set up test rules, evaluate them and then apply them. There are several [lifecycle policy examples](https://docs.aws.amazon.com/AmazonECR/latest/userguide/lifecycle_policy_examples.html) in the official docs that show different ways of filtering the images in a repository:

- Filtering by image age or count
- Filtering by tagged or untagged images
- Filtering by image tags, either in multiple rules or a single rule

???+ warning
    If the image for long running application is purged from ECR, it can cause an image pull errors when the application is redeployed or scaled horizontally. When using image lifecycle policies, be sure you have good CI/CD practices in place to keep deployments and the images that they reference up to date and always create [image] expiry rules that account for how often you do releases/deployments.

### Create a set of curated images

Rather than allowing developers to create their own images, consider creating a set of vetted images for the different application stacks in your organization. By doing so, developers can forego learning how to compose Dockerfiles and concentrate on writing code. As changes are merged into Master, a CI/CD pipeline can automatically compile the asset, store it in an artifact repository and copy the artifact into the appropriate image before pushing it to a Docker registry like ECR. At the very least you should create a set of base images from which developers to create their own Dockerfiles. Ideally, you want to avoid pulling images from Dockerhub because 1/ you don't always know what is in the image and 2/ about [a fifth](https://www.kennasecurity.com/blog/one-fifth-of-the-most-used-docker-containers-have-at-least-one-critical-vulnerability/) of the top 1000 images have vulnerabilities. A list of those images and their vulnerabilities can be found [here](https://vulnerablecontainers.org/).

### Add the USER directive to your Dockerfiles to run as a non-root user

As was mentioned in the pod security section, you should avoid running container as root. While you can configure this as part of the podSpec, it is a good habit to use the `USER` directive to your Dockerfiles. The `USER` directive sets the UID to use when running `RUN`, `ENTRYPOINT`, or `CMD` instruction that appears after the USER directive.

### Lint your Dockerfiles

Linting can be used to verify that your Dockerfiles are adhering to a set of predefined guidelines, e.g. the inclusion of the `USER` directive or the requirement that all images be tagged. [dockerfile_lint](https://github.com/projectatomic/dockerfile_lint) is an open source project from RedHat that verifies common best practices and includes a rule engine that you can use to build your own rules for linting Dockerfiles. It can be incorporated into a CI pipeline, in that builds with Dockerfiles that violate a rule will automatically fail.

### Build images from Scratch

Reducing the attack surface of your container images should be primary aim when building images. The ideal way to do this is by creating minimal images that are devoid of binaries that can be used to exploit vulnerabilities. Fortunately, Docker has a mechanism to create images from [`scratch`](https://docs.docker.com/develop/develop-images/baseimages/#create-a-simple-parent-image-using-scratch). With languages like Go, you can create a static linked binary and reference it in your Dockerfile as in this example:

```docker
############################
# STEP 1 build executable binary
############################
FROM golang:alpine AS builder# Install git.
# Git is required for fetching the dependencies.
RUN apk update && apk add --no-cache gitWORKDIR $GOPATH/src/mypackage/myapp/COPY . . # Fetch dependencies.
# Using go get.
RUN go get -d -v# Build the binary.
RUN go build -o /go/bin/hello

############################
# STEP 2 build a small image
############################
FROM scratch# Copy our static executable.
COPY --from=builder /go/bin/hello /go/bin/hello# Run the hello binary.
ENTRYPOINT ["/go/bin/hello"]
```

This creates a container image that consists of your application and nothing else, making it extremely secure.

### Use immutable tags with ECR

[Immutable tags](https://aws.amazon.com/about-aws/whats-new/2019/07/amazon-ecr-now-supports-immutable-image-tags/) force you to update the image tag on each push to the image repository. This can thwart an attacker from overwriting an image with a malicious version without changing the image's tags. Additionally, it gives you a way to easily and uniquely identify an image.

### Sign your images, SBOMs, pipeline runs and vulnerability reports

When Docker was first introduced, there was no cryptographic model for verifying container images. With v2, Docker added digests to the image manifest. This allowed an image’s configuration to be hashed and for the hash to be used to generate an ID for the image. When image signing is enabled, the Docker engine verifies the manifest’s signature, ensuring that the content was produced from a trusted source and no tampering has occurred. After each layer is downloaded, the engine verifies the digest of the layer, ensuring that the content matches the content specified in the manifest. Image signing effectively allows you to create a secure supply chain, through the verification of digital signatures associated with the image.

We can use [AWS Signer](https://docs.aws.amazon.com/signer/latest/developerguide/Welcome.html) or [Sigstore Cosign](https://github.com/sigstore/cosign), to sign container images, create attestations for SBOMs, vulnerability scan reports and pipeline run reports. These attestations assure the trustworthiness and integrity of the image, that it is in fact created by the trusted pipeline without any interference or tampering, and that it contains only the software components that are documented (in the SBOM) that is verified and trusted by the image publisher. These attestations can be attached to the container image and pushed to the repository.

In the next section we will see how to use the attested artifacts for audits and admissions controller verification.

### Image integrity verification using Kubernetes admission controller

We can verify image signatures, attested artifacts in an automated way before deploying the image to target Kubernetes cluster using [dynamic admission controller](https://kubernetes.io/blog/2019/03/21/a-guide-to-kubernetes-admission-controllers/) and admit deployments only when the security metadata of the artifacts comply with the admission controller policies.

For example we can write a policy that cryptographically verifies the signature of an image, an attested SBOM, attested pipeline run report, or attested CVE scan report. We can write conditions in the policy to check data in the report, e.g. a CVE scan should not have any critical CVEs. Deployment is allowed only for images that satisfy these conditions and all other deployments will be rejected by the admissions controller.

Examples of admission controller include:

- [Kyverno](https://kyverno.io/)
- [OPA Gatekeeper](https://github.com/open-policy-agent/gatekeeper)
- [Portieris](https://github.com/IBM/portieris)
- [Ratify](https://github.com/deislabs/ratify)
- [Kritis](https://github.com/grafeas/kritis)
- [Grafeas tutorial](https://github.com/kelseyhightower/grafeas-tutorial)
- [Voucher](https://github.com/Shopify/voucher)

### Update the packages in your container images

You should include RUN `apt-get update && apt-get upgrade` in your Dockerfiles to upgrade the packages in your images. Although upgrading requires you to run as root, this occurs during image build phase. The application doesn't need to run as root. You can install the updates and then switch to a different user with the USER directive. If your base image runs as a non-root user, switch to root and back; don't solely rely on the maintainers of the base image to install the latest security updates.

Run `apt-get clean` to delete the installer files from `/var/cache/apt/archives/`. You can also run `rm -rf /var/lib/apt/lists/*` after installing packages. This removes the index files or the lists of packages that are available to install. Be aware that these commands may be different for each package manager. For example:

```docker
RUN apt-get update && apt-get install -y \
    curl \
    git \
    libsqlite3-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*
```

## Tools and resources

- [Amazon EKS Security Immersion Workshop - Image Security](https://catalog.workshops.aws/eks-security-immersionday/en-US/12-image-security)
- [docker-slim](https://github.com/docker-slim/docker-slim) Build secure minimal images
- [dockle](https://github.com/goodwithtech/dockle) Verifies that your Dockerfile aligns with best practices for creating secure images
- [dockerfile-lint](https://github.com/projectatomic/dockerfile_lint) Rule based linter for Dockerfiles
- [hadolint](https://github.com/hadolint/hadolint) A smart dockerfile linter
- [Gatekeeper and OPA](https://github.com/open-policy-agent/gatekeeper) A policy based admission controller
- [Kyverno](https://kyverno.io/) A Kubernetes-native policy engine
- [in-toto](https://in-toto.io/) Allows the user to verify if a step in the supply chain was intended to be performed, and if the step was performed by the right actor
- [Notary](https://github.com/theupdateframework/notary) A project for signing container images
- [Notary v2](https://github.com/notaryproject/nv2)
- [Grafeas](https://grafeas.io/) An open artifact metadata API to audit and govern your software supply chain
- [NeuVector by SUSE](https://www.suse.com/neuvector/) open source, zero-trust container security platform, provides container, image and registry scanning for vulnerabilities, secrets and compliance.
