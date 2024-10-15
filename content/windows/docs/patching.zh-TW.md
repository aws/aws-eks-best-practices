# 修補 Windows 伺服器和容器

修補 Windows Server 是 Windows 管理員的標準管理任務。可以使用不同的工具來完成,例如 Amazon System Manager - Patch Manager、WSUS、System Center Configuration Manager 等等。然而,Amazon EKS 叢集中的 Windows 節點不應被視為普通的 Windows 伺服器。它們應被視為不可變的伺服器。簡而言之,避免更新現有節點,只需根據新的更新 AMI 啟動新節點即可。

使用 [EC2 Image Builder](https://aws.amazon.com/image-builder/) 您可以通過創建配方和添加組件來自動化 AMI 構建。

以下示例顯示了 **組件**,其中包括 AWS 預先構建的 (Amazon 管理) 組件以及您創建的組件 (由我擁有)。請特別注意名為 **update-windows** 的 Amazon 管理組件,它會在通過 EC2 Image Builder 管道生成 AMI 之前更新 Windows Server。

![](./images/associated-components.png)

EC2 Image Builder 允許您基於 Amazon 管理的公共 AMI 構建 AMI,並根據您的業務需求對其進行自定義。然後,您可以將這些 AMI 與啟動模板關聯,從而將新的 AMI 與 EKS 節點組創建的自動伸縮組關聯。完成後,您可以開始終止現有的 Windows 節點,新節點將根據新的更新 AMI 啟動。

## 推送和拉取 Windows 映像
Amazon 發佈了包含兩個緩存 Windows 容器映像的 EKS 優化 AMI。

    mcr.microsoft.com/windows/servercore
    mcr.microsoft.com/windows/nanoserver

![](./images/images.png)

緩存映像會根據主 OS 的更新而更新。當 Microsoft 發佈直接影響 Windows 容器基礎映像的新 Windows 更新時,該更新將作為普通 Windows 更新在主 OS 上啟動。保持環境的最新狀態可以在節點和容器級別提供更安全的環境。

Windows 容器映像的大小會影響推送/拉取操作,從而導致容器啟動時間緩慢。[緩存 Windows 容器映像](https://aws.amazon.com/blogs/containers/speeding-up-windows-container-launch-times-with-ec2-image-builder-and-image-cache-strategy/) 允許在 AMI 構建創建過程中發生昂貴的 I/O 操作 (文件提取),而不是在容器啟動時。因此,所有必需的映像層都將在 AMI 上提取,並準備就緒以供使用,從而加快 Windows 容器啟動並開始接受流量的時間。在推送操作期間,只有構成您映像的層會被上傳到存儲庫。

以下示例顯示,在 Amazon ECR 上 **fluentd-windows-sac2004** 映像僅有 **390.18MB**。這是在推送操作期間上傳的量。

以下示例顯示將 [fluentd Windows ltsc](https://github.com/fluent/fluentd-docker-image/blob/master/v1.14/windows-ltsc2019/Dockerfile) 映像推送到 Amazon ECR 存儲庫。存儲在 ECR 中的層的大小為 **533.05MB**。

![](./images/ecr-image.png)

從 `docker image ls` 的輸出可以看到,fluentd v1.14-windows-ltsc2019-1 的大小為 **6.96GB**,但這並不意味著它下載和提取了那麼多數據。

實際上,在拉取操作期間只會下載和提取 **壓縮的 533.05MB**。

```bash
REPOSITORY                                                              TAG                        IMAGE ID       CREATED         SIZE
111122223333.dkr.ecr.us-east-1.amazonaws.com/fluentd-windows-coreltsc   latest                     721afca2c725   7 weeks ago     6.96GB
fluent/fluentd                                                          v1.14-windows-ltsc2019-1   721afca2c725   7 weeks ago     6.96GB
amazonaws.com/eks/pause-windows                                         latest                     6392f69ae6e7   10 months ago   255MB
```

大小列顯示映像的總大小為 6.96GB。細分如下:

* Windows Server Core 2019 LTSC 基礎映像 = 5.74GB
* Fluentd 未壓縮基礎映像 = 6.96GB
* 磁盤上的差異 = 1.2GB
* Fluentd [壓縮最終映像 ECR](https://docs.aws.amazon.com/AmazonECR/latest/userguide/repository-info.html) = 533.05MB

基礎映像已經存在於本地磁盤上,因此磁盤上的總量增加了 1.2GB。下次看到大小列中的 GB 數量時,不要太過擔心,很可能已經有 70% 以上是作為緩存容器映像存在於磁盤上。

## 參考
[使用 EC2 Image Builder 和映像緩存策略加快 Windows 容器啟動時間](https://aws.amazon.com/blogs/containers/speeding-up-windows-container-launch-times-with-ec2-image-builder-and-image-cache-strategy/)