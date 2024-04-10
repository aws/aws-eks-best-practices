# 容器映像掃描

映像掃描是一種自動化漏洞評估功能,可透過掃描廣泛的作業系統漏洞,協助提高應用程式容器映像的安全性。

目前,Amazon Elastic Container Registry (ECR) 僅能掃描 Linux 容器映像的漏洞。不過,有第三方工具可與現有的 CI/CD 管線整合,用於 Windows 容器映像掃描。

* [Anchore](https://anchore.com/blog/scanning-windows-container-images/)
* [PaloAlto Prisma Cloud ](https://docs.paloaltonetworks.com/prisma/prisma-cloud/prisma-cloud-admin-compute/vulnerability_management/windows_image_scanning.html)
* [Trend Micro - Deep Security Smart Check](https://www.trendmicro.com/en_us/business/products/hybrid-cloud/smart-check-image-scanning.html)

若要進一步瞭解如何將這些解決方案與 Amazon Elastic Container Repository (ECR) 整合,請查看:

* [Anchore,在 Amazon Elastic Container Registry (ECR) 上掃描映像](https://anchore.com/blog/scanning-images-on-amazon-elastic-container-registry/)
* [PaloAlto,在 Amazon Elastic Container Registry (ECR) 上掃描映像](https://docs.paloaltonetworks.com/prisma/prisma-cloud/prisma-cloud-admin-compute/vulnerability_management/registry_scanning0/scan_ecr.html)
* [TrendMicro,在 Amazon Elastic Container Registry (ECR) 上掃描映像](https://cloudone.trendmicro.com/docs/container-security/sc-about/)
