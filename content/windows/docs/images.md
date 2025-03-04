---
redirect: https://docs.aws.amazon.com/eks/latest/best-practices/windows-images.html
---


!!! info "We've Moved to the AWS Docs! 🚀"
    This content has been updated and relocated to improve your experience. 
    Please visit our new site for the latest version:
    [AWS EKS Best Practices Guide](https://docs.aws.amazon.com/eks/latest/best-practices/windows-images.html) on the AWS Docs

    Bookmarks and links will continue to work, but we recommend updating them for faster access in the future.

---

# Container image scanning

Image Scanning is an automated vulnerability assessment feature that helps improve the security of your application’s container images by scanning them for a broad range of operating system vulnerabilities.

Currently, the Amazon Elastic Container Registry (ECR) is only able to scan Linux container image for vulnerabilities. However; there are third-party tools which can be integrated with an existing CI/CD pipeline for Windows container image scanning.

* [Anchore](https://anchore.com/blog/scanning-windows-container-images/)
* [PaloAlto Prisma Cloud ](https://docs.paloaltonetworks.com/prisma/prisma-cloud/prisma-cloud-admin-compute/vulnerability_management/windows_image_scanning.html)
* [Trend Micro - Deep Security Smart Check](https://www.trendmicro.com/en_us/business/products/hybrid-cloud/smart-check-image-scanning.html)

To learn more about how to integrate these solutions with Amazon Elastic Container Repository (ECR), check:

* [Anchore, scanning images on Amazon Elastic Container Registry (ECR)](https://anchore.com/blog/scanning-images-on-amazon-elastic-container-registry/)
* [PaloAlto, scanning images on Amazon Elastic Container Registry (ECR)](https://docs.paloaltonetworks.com/prisma/prisma-cloud/prisma-cloud-admin-compute/vulnerability_management/registry_scanning0/scan_ecr.html)
* [TrendMicro, scanning images on Amazon Elastic Container Registry (ECR)](https://cloudone.trendmicro.com/docs/container-security/sc-about/)
