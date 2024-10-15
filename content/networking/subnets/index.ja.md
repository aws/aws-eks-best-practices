# VPC と サブネットに関する考慮事項

EKSクラスターの運用には、Kubernetesネットワーキングに加えて、AWS VPCネットワーキングの知識が必要です。

VPCまたは既存のVPCにクラスターをデプロイする前に、EKSコントロールプレーンの通信メカニズムを理解することをお勧めします。

EKSと一緒に使用するためにVPCとサブネットを設計する際には、[クラスターVPCの考慮事項](https://docs.aws.amazon.com/eks/latest/userguide/network_reqs.html)と[Amazon EKSセキュリティグループの考慮事項](https://docs.aws.amazon.com/eks/latest/userguide/sec-group-reqs.html)を参照してください。

## 概要

### EKSクラスターアーキテクチャ

EKSクラスターは2つのVPCで構成されています：

* KubernetesコントロールプレーンをホストするAWS管理のVPC。このVPCはカスタマーアカウントに表示されません。
* Kubernetesノードをホストするカスタマー管理のVPC。ここでコンテナが実行され、クラスターで使用されるロードバランサーなどの他のカスタマー管理のAWSインフラストラクチャも含まれます。このVPCはカスタマーアカウントに表示されます。クラスターを作成する前に、カスタマー管理のVPCを作成する必要があります。eksctlは、VPCを指定しない場合にVPCを作成します。

カスタマーVPCのノードは、AWS VPC内の管理APIサーバーエンドポイントに接続する必要があります。これにより、ノードはKubernetesコントロールプレーンに登録し、アプリケーションポッドを実行するためのリクエストを受け取ることができます。

ノードは、EKSコントロールプレーンに(a) EKSパブリックエンドポイントまたは(b) EKSが管理するクロスアカウントの[Elastic Network Interface](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-eni.html)（X-ENI）を介して接続します。クラスターが作成されると、少なくとも2つのVPCサブネットを指定する必要があります。EKSは、クラスター作成時に指定された各サブネットにX-ENIを配置します（クラスターサブネットとも呼ばれます）。Kubernetes APIサーバーは、これらのクロスアカウントENIを使用して、カスタマー管理のクラスターVPCサブネットに展開されたノードと通信します。

![general illustration of cluster networking, including load balancer, nodes, and pods.](./image.png)

ノードが起動すると、EKSブートストラップスクリプトが実行され、Kubernetesノードの設定ファイルがインストールされます。各インスタンスの起動時に、コンテナランタイムエージェントであるkubeletとKubernetesノードエージェントが起動されます。

ノードは、kubeletがKubernetesクラスターエンドポイントに接続することで登録されます。kubeletは、VPC外のパブリックエンドポイントまたはVPC内のプライベートエンドポイントのいずれかと接続を確立します。 kubeletは、APIの指示を受け取り、定期的にエンドポイントに対してステータスの更新とハートビートを提供します。

### EKSコントロールプレーンの通信

EKSには、クラスターエンドポイントへのアクセスを制御する2つの方法があります。エンドポイントアクセス制御を使用すると、エンドポイントがパブリックインターネットから到達可能か、VPCを介してのみ到達可能かを選択できます。パブリックエンドポイント（デフォルト）、プライベートエンドポイント、または両方を同時に有効にすることができます。 

クラスターAPIエンドポイントの構成によって、ノードがコントロールプレーンと通信するための経路が決まります。エンドポイントの設定は、いつでもEKSコンソールまたはAPIを介して変更できます。

#### パブリックエンドポイント

これは新しいAmazon EKSクラスターのデフォルトの動作です。クラスターのパブリックエンドポイントのみが有効になっている場合、クラスター内から発信されるKubernetes APIリクエスト（ワーカーノードとコントロールプレーンの通信など）は、VPCを離れずにAmazonのネットワークを経由せずに外部に出ます。ノードがコントロールプレーンに接続するためには、ノードにパブリックIPアドレスとインターネットゲートウェイへのルートまたはNATゲートウェイへのルートが必要です。

#### パブリックエンドポイントとプライベートエンドポイント

パブリックエンドポイントとプライベートエンドポイントの両方が有効になっている場合、VPC内からのKubernetes APIリクエストは、VPC内のX-ENIを介してコントロールプレーンに通信します。クラスターAPIサーバーはインターネットからアクセスできます。

#### プライベートエンドポイント

プライベートエンドポイントのみが有効になっている場合、インターネットからクラスターのAPIサーバーにアクセスすることはできません。クラスターのAPIサーバーへのすべてのトラフィックは、クラスターのVPC内または接続されたネットワークからのみ行われる必要があります。ノードはVPC内のX-ENIを介してAPIサーバーと通信します。クラスター管理ツールはプライベートエンドポイントへのアクセス権を持っている必要があります。[Amazon VPC外からプライベートAmazon EKSクラスターエンドポイントに接続する方法について詳しくはこちらをご覧ください。](https://aws.amazon.com/premiumsupport/knowledge-center/eks-private-cluster-endpoint-vpc/)

クラスターのAPIサーバーエンドポイントは、パブリックDNSサーバーによってVPC内のプライベートIPアドレスに解決されます。以前は、VPC内からのみエンドポイントにアクセスできました。

### VPCの設定

Amazon VPCはIPv4およびIPv6のアドレッシングをサポートしています。Amazon EKSはデフォルトでIPv4をサポートしています。VPCにはIPv4 CIDRブロックが関連付けられている必要があります。VPCに複数のIPv4 [Classless Inter-Domain Routing](http://en.wikipedia.org/wiki/CIDR_notation)（CIDR）ブロックと複数のIPv6 CIDRブロックをオプションで関連付けることもできます。VPCを作成する際には、VPCのためのIPv4 CIDRブロックを指定する必要があります。指定できるブロックサイズは、`/16`プレフィックス（65,536個のIPアドレス）から`/28`プレフィックス（16個のIPアドレス）の間です。

新しいVPCを作成する場合、単一のIPv6 CIDRブロックをアタッチすることができます。既存のVPCを変更する場合は最大5つのIPv6 CIDRブロックをアタッチできます。IPv6 CIDRブロックのプレフィックス長は/44から/60の間で、IPv6サブネットのプレフィックス長は/44から/64の間である必要があります。IPv6アドレスプールからIPv6 CIDRブロックをリクエストすることもできます。詳細については、VPCユーザーガイドの[VPC CIDRブロック](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-cidr-blocks.html)セクションを参照してください。

Amazon EKSクラスターはIPv4とIPv6の両方をサポートしています。デフォルトでは、EKSクラスターはIPv4 IPを使用します。クラスター作成時にIPv6を指定すると、IPv6クラスターを有効にすることができます。IPv6クラスターにはデュアルスタックVPCとサブネットが必要です。

Amazon EKSは、クラスター作成時に少なくとも2つのサブネットを指定することをお勧めします。指定したサブネットはクラスターサブネットとして知られています。クラスターを作成すると、Amazon EKSは指定したサブネットに最大4つのクロスアカウント（x-accountまたはx-ENI）ENIを作成します。x-ENIは常に展開され、ログの配信、exec、およびプロキシなどのクラスター管理トラフィックに使用されます。詳細な[VPCおよびサブネットの要件](https://docs.aws.amazon.com/eks/latest/userguide/network_reqs.html#network-requirements-subnets)については、EKSユーザーガイドを参照してください。

Kubernetesワーカーノードはクラスターサブネットで実行できますが、推奨されません。[クラスターアップグレード](https://aws.github.io/aws-eks-best-practices/upgrades/#verify-available-ip-addresses)中にAmazon EKSはクラスターサブネットに追加のENIをプロビジョニングします。クラスターがスケールアウトすると、ワーカーノードとポッドはクラスターサブネットの利用可能なIPを消費する可能性があります。したがって、利用可能なIPが十分にあることを確認するために、/28ネットマスクを持つ専用のクラスターサブネットを使用することを検討してください。

Kubernetesワーカーノードはパブリックまたはプライベートサブネットのいずれかで実行できます。サブネットがパブリックかプライベートかは、サブネット内のトラフィックが[インターネットゲートウェイ](https://docs.aws.amazon.com/vpc/latest/userguide/VPC_Internet_Gateway.html)を介してルーティングされるかどうかによって決まります。パブリックサブネットは、インターネットゲートウェイを介してインターネットへのルートテーブルエントリを持っていますが、プライベートサブネットは持っていません。

ノードに到達する他の場所から発信されるトラフィックは*イングレス*と呼ばれます。ノードから出発しネットワークを離れるトラフィックは*エグレス*と呼ばれます。パブリックまたはElastic IPアドレス（EIP）を持つノードは、インターネットゲートウェイを介してVPCの外部からイングレスを許可します。プライベートサブネットには通常、[NATゲートウェイ](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-nat-gateway.html)が含まれており、ノードへのイングレストラフィックはVPC内からのみ許可されますが、ノードからのトラフィックはVPCを離れることができます（エグレス）。

IPv6の世界では、すべてのアドレスがインターネットルーティング可能です。ノードとポッドに関連付けられたIPv6アドレスはパブリックです。プライベートサブネットは、[egress-onlyインターネットゲートウェイ（EIGW）](https://docs.aws.amazon.com/vpc/latest/userguide/egress-only-internet-gateway.html)を使用してサポートされており、アウトバウンドトラフィックを許可しながらすべての着信トラフィックをブロックします。IPv6サブネットの実装に関するベストプラクティスについては、[VPCユーザーガイド](https://docs.aws.amazon.com/vpc/latest/userguide/VPC_Scenario2.html)を参照してください。



### 3つの異なる方法でVPCとサブネットを設定できます：

#### パブリックサブネットのみを使用する


同じパブリックサブネット内で、ノードとイングレスリソース（ロードバランサなど）が作成されます。パブリックサブネットに[`kubernetes.io/role/elb`](http://kubernetes.io/role/elb)のタグを付けて、インターネットに面したロードバランサを構築します。この構成では、クラスターエンドポイントをパブリック、プライベート、または両方（パブリックとプライベート）に設定することができます。

#### プライベートサブネットとパブリックサブネットの使用

ノードはプライベートサブネットに作成され、イングレスリソースはパブリックサブネットにインスタンス化されます。クラスターエンドポイントへのアクセスをパブリック、プライベート、または両方に設定することができます。クラスターエンドポイントの構成に応じて、ノードのトラフィックはNATゲートウェイまたはENIを介して入力されます。

#### プライベートサブネットのみを使用する

ノードとイングレスの両方がプライベートサブネットに作成されます。内部ロードバランサを構築するために、[`kubernetes.io/role/internal-elb`](http://kubernetes.io/role/internal-elb:1)のサブネットタグを使用します。クラスターのエンドポイントにアクセスするには、VPN接続が必要です。EC2およびすべてのAmazon ECRおよびS3リポジトリに対して[AWS PrivateLink](https://docs.aws.amazon.com/vpc/latest/userguide/endpoint-service.html)を有効にする必要があります。クラスターのプライベートエンドポイントのみを有効にする必要があります。プライベートクラスターをプロビジョニングする前に、[EKSプライベートクラスターの要件](https://docs.aws.amazon.com/eks/latest/userguide/private-clusters.html)を確認することをおすすめします。


### VPC間の通信

複数のVPCとそれらのVPCに展開された別々のEKSクラスターが必要なシナリオは多々あります。

[Amazon VPC Lattice](https://aws.amazon.com/vpc/lattice/)を使用すると、VPCピアリング、AWS PrivateLink、AWS Transit Gatewayなどのサービスによる追加の接続性を必要とせずに、複数のVPCとアカウント間のサービスを一貫して安全に接続できます。詳細は[こちら](https://aws.amazon.com/blogs/networking-and-content-delivery/build-secure-multi-account-multi-vpc-connectivity-for-your-applications-with-amazon-vpc-lattice/)をご覧ください。

Amazon VPC LatticeはIPv4およびIPv6のリンクローカルアドレススペースで動作し、重複するIPv4アドレスを持つサービス間の接続性を提供します。運用効率を考慮して、重複するIP範囲を持つVPCが含まれる場合は、ネットワークを適切に設計する必要があります。[Private NAT Gateway](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-nat-gateway.html#nat-gateway-basics)またはカスタムネットワーキングモードのVPC CNIと[トランジットゲートウェイ](https://docs.aws.amazon.com/whitepapers/latest/aws-vpc-connectivity-options/aws-transit-gateway.html)を組み合わせて、EKS上のワークロードを統合し、重複するCIDRの課題を解決しながらルーティング可能なRFC1918 IPアドレスを保持することをおすすめします。

[AWS PrivateLink](https://docs.aws.amazon.com/vpc/latest/privatelink/privatelink-share-your-services.html)（エンドポイントサービスとも呼ばれる）を使用すると、サービスプロバイダとしての役割を果たし、独立したアカウントのカスタマーVPCとKubernetesサービスおよびイングレス（ALBまたはNLB）を共有したい場合に利用できます。

### 複数のアカウントでのVPCの共有

多くの企業は、AWS組織内の複数のAWSアカウント間でネットワーク管理を効率化し、コストを削減し、セキュリティを向上させる手段として、共有Amazon VPCを採用しています。AWSリソースアクセスマネージャー（RAM）を使用して、個々のAWSアカウント、組織単位（OU）、またはAWS組織全体と共有できるサポートされている[AWSリソース](https://docs.aws.amazon.com/ram/latest/userguide/shareable.html)を安全に共有します。

AWS RAMを使用して、別のAWSアカウントから共有VPCサブネットにAmazon EKSクラスター、管理ノードグループ、およびその他のサポートするAWSリソース（ロードバランサ、セキュリティグループ、エンドポイントなど）をデプロイできます。以下の図は、このシナリオの例の高レベルアーキテクチャを示しています。これにより、ネットワーキングの構成（VPC、サブネットなど）を中央のネットワーキングチームが制御し、アプリケーションまたはプラットフォームチームがそれぞれのAWSアカウントにAmazon EKSクラスターをデプロイできるようになります。このシナリオの完全な手順については、[githubリポジトリ](https://github.com/aws-samples/eks-shared-subnets)を参照してください。

#### 共有サブネットを使用する際の考慮事項

* Amazon EKSクラスターとワーカーノードは、同じVPCに属する共有サブネット内に作成できます。Amazon EKSは複数のVPCにまたがるクラスターの作成をサポートしていません。

* Amazon EKSは、Kubernetesコントロールプレーンとクラスターのワーカーノード間のトラフィックを制御するためにAWS VPCセキュリティグループ（SG）を使用します。セキュリティグループは、ワーカーノード間および他のVPCリソース、および外部IPアドレス間のトラフィックを制御するためにも使用されます。カスタムセキュリティグループを使用する場合、これらのセキュリティグループをアプリケーション/参加者アカウントに作成する必要があります。ポッドに使用する予定のセキュリティグループも参加者アカウントに配置されていることを確認してください。セキュリティグループ内のインバウンドおよびアウトバウンドルールを設定して、セントラルVPCアカウントに配置されたセキュリティグループとの間で必要なトラフィックを許可できます。

* Amazon EKSクラスターが存在する参加者アカウント内でIAMロールと関連するポリシーを作成してください。これらのIAMロールとポリシーは、Amazon EKSによって管理されるKubernetesクラスター、およびFargateで実行されるノードとポッドに必要な権限を付与するために必要です。これらの権限により、Amazon EKSが他のAWSサービスに対してあなたの代わりに呼び出しを行うことができます。

* k8sのポッドからAmazon S3バケット、DynamodbテーブルなどのAWSリソースへのクロスアカウントアクセスを許可するために、次のアプローチを使用できます：
    * **リソースベースのポリシーアプローチ**：AWSサービスがリソースベースのポリシーをサポートしている場合、適切なリソースベースのポリシーを追加して、kubernetesポッドに割り当てられたIAMロールへのクロスアカウントアクセスを許可できます。このシナリオでは、OIDCプロバイダ、IAMロール、および許可ポリシーがアプリケーションアカウントに存在します。リソースベースのポリシーをサポートするAWSサービスを見つけるには、[IAMで動作するAWSサービス](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_aws-services-that-work-with-iam.html)を参照し、リソースベースの列にYesがあるサービスを探します。

    * **OIDCプロバイダのアプローチ**：OIDCプロバイダ、IAMロール、許可ポリシー、およびトラストポリシーなどのIAMリソースは、リソースが存在する他の参加者AWSアカウントに作成されます。これらのロールは、アプリケーションアカウントのKubernetesポッドに割り当てられ、クロスアカウントリソースにアクセスできるようにします。このアプローチの詳細な手順については、[Kubernetesサービスアカウント用のクロスアカウントIAMロール](https://aws.amazon.com/blogs/containers/cross-account-iam-roles-for-kubernetes-service-accounts/)ブログを参照してください。

* Amazon Elastic Load Balancer（ELB）リソース（ALBまたはNLB）をデプロイして、k8sポッドへのトラフィックをアプリケーションアカウントまたはセントラルネットワーキングアカウントにルーティングできます。セントラルネットワーキングアカウントでELBリソースをデプロイする詳細な手順については、[クロスアカウントロードバランサを介したAmazon EKSポッドの公開](https://aws.amazon.com/blogs/containers/expose-amazon-eks-pods-through-cross-account-load-balancer/)の手順を参照してください。このオプションは、ロードバランサリソースのセキュリティ構成に対するセントラルネットワーキングアカウントの完全な制御を提供します。

* Amazon VPC CNIの`カスタムネットワーキング機能`を使用する場合、各`ENIConfig`を作成するために、セントラルネットワーキングアカウントの物理的なAZとAZ名のランダムなマッピングを使用する必要があります。

### セキュリティグループ

[*セキュリティグループ*](https://docs.aws.amazon.com/vpc/latest/userguide/VPC_SecurityGroups.html)は、関連付けられているリソースに到達および出発するトラフィックを制御します。Amazon EKSはセキュリティグループを使用して、[コントロールプレーンとノード間の通信](https://docs.aws.amazon.com/eks/latest/userguide/sec-group-reqs.html)を管理します。クラスターを作成すると、Amazon EKSは`eks-cluster-sg-my-cluster-uniqueID`という名前のセキュリティグループを作成します。EKSはこれらのセキュリティグループを管理されたENIとノードに関連付けます。デフォルトのルールでは、クラスターとノード間のすべてのトラフィックを自由に流すことができ、すべてのアウトバウンドトラフィックを任意の宛先に許可します。

クラスターを作成する際に独自のセキュリティグループを指定することもできます。独自のセキュリティグループを指定する場合は、[セキュリティグループの推奨事項](https://docs.aws.amazon.com/eks/latest/userguide/sec-group-reqs.html)を参照してください。

## 推奨事項

### マルチAZデプロイを検討してください

AWSリージョンは、低遅延、高スループット、高い冗長性のネットワーキングで接続された複数の物理的に分離された可用性ゾーン（AZ）を提供します。可用性ゾーンを使用すると、中断することなく可用性ゾーン間で自動的にフェイルオーバーするアプリケーションを設計および運用することができます。Amazon EKSは、EKSクラスターを複数の可用性ゾーンにデプロイすることを強くお勧めします。クラスターを作成する際には、少なくとも2つの可用性ゾーンにサブネットを指定することを検討してください。


Kubeletがノード上で自動的にノードオブジェクトにラベルを追加します。例えば、[`topology.kubernetes.io/region=us-west-2`や`topology.kubernetes.io/zone=us-west-2d`](http://topology.kubernetes.io/region=us-west-2,topology.kubernetes.io/zone=us-west-2d)などです。Podのトポロジースプレッド制約とノードラベルを組み合わせて使用することをおすすめします。これにより、KubernetesスケジューラはPodをより良い可用性で配置し、相関障害がワークロード全体に影響を与えるリスクを減らすことができます。ノードセレクターやAZスプレッド制約の例については、[ノードへの割り当て](https://kubernetes.io/docs/concepts/scheduling-eviction/assign-pod-node/#nodeselector)を参照してください。

ノードを作成する際には、サブネットや可用性ゾーンを指定することができます。サブネットが設定されていない場合、ノードはクラスターサブネットに配置されます。EKSのマネージドノードグループは、利用可能な容量に基づいてノードを複数の可用性ゾーンに自動的に分散させます。[Karpenter](https://karpenter.sh/)は、ワークロードがトポロジースプレッド制約を定義している場合、指定された可用性ゾーンにノードをスケーリングします。

AWS Elastic Load Balancerは、KubernetesクラスターのAWS Load Balancer Controllerによって管理されます。これは、Kubernetesのイングレスリソースに対してApplication Load Balancer（ALB）をプロビジョニングし、タイプがLoadbalancerのKubernetesサービスに対してNetwork Load Balancer（NLB）をプロビジョニングします。Elastic Load Balancerコントローラは、サブネットを検出するために[タグ](https://aws.amazon.com/premiumsupport/knowledge-center/eks-vpc-subnet-discovery/)を使用します。ELBコントローラは、イングレスリソースを正常にプロビジョニングするために、少なくとも2つの可用性ゾーン（AZ）が必要です。地理的な冗長性と信頼性のために、少なくとも2つのAZにサブネットを設定することを検討してください。

### プライベートサブネットにノードを展開する

EKS上でKubernetesワークロードを展開するためには、プライベートサブネットとパブリックサブネットの両方を含むVPCが理想的です。少なくとも2つのパブリックサブネットと2つのプライベートサブネットを2つの異なる可用性ゾーンに設定することを検討してください。パブリックサブネットの関連するルートテーブルには、インターネットゲートウェイへのルートが含まれています。PodはNATゲートウェイを介してインターネットとやり取りすることができます。プライベートサブネットでは、ロードバランサーなどのイングレスリソースがインスタンス化され、プライベートサブネット上で動作するPodにトラフィックがルーティングされます。

厳密なセキュリティとネットワークの分離が必要な場合は、プライベート専用モードを検討してください。この構成では、AWSリージョンのVPC内の異なる可用性ゾーンに3つのプライベートサブネットが展開されます。サブネットに展開されたリソースはインターネットにアクセスすることはできず、インターネットもサブネット内のリソースにアクセスすることはできません。Kubernetesアプリケーションが他のAWSサービスにアクセスするためには、PrivateLinkインターフェースやゲートウェイエンドポイントを設定する必要があります。AWS Load Balancer Controllerを使用してトラフィックをPodにリダイレクトするために、内部ロードバランサーを設定することもできます。プライベートサブネットは、コントロールプレーンにノードが登録されるためにはタグ（[`kubernetes.io/role/internal-elb: 1`](http://kubernetes.io/role/internal-elb)）が設定されている必要があります。クラスターエンドポイントはプライベートモードに設定する必要があります。完全な要件と考慮事項については、[プライベートクラスターガイド](https://docs.aws.amazon.com/eks/latest/userguide/private-clusters.html)を参照してください。

### クラスターエンドポイントのパブリックモードとプライベートモードを検討する

Amazon EKSでは、パブリックのみ、パブリックとプライベート、プライベートのみのクラスターエンドポイントモードを提供しています。デフォルトのモードはパブリックのみですが、クラスターエンドポイントをパブリックとプライベートのモードで構成することをおすすめします。このオプションにより、クラスターのVPC内でのKubernetes API呼び出し（ノードとコントロールプレーン間の通信など）は、プライベートVPCエンドポイントを利用し、トラフィックはクラスターのVPC内に留まります。一方、クラスターAPIサーバーはインターネットからアクセスできるようになります。ただし、パブリックエンドポイントを使用できるCIDRブロックを制限することを強くおすすめします。[CIDRブロックを制限する方法など、パブリックおよびプライベートエンドポイントアクセスの構成方法について詳しくはこちらをご覧ください。](https://docs.aws.amazon.com/eks/latest/userguide/cluster-endpoint.html#modify-endpoint-access)

セキュリティグループの設定には注意が必要です。Amazon EKSはカスタムセキュリティグループの使用をサポートしています。ただし、カスタムセキュリティグループはノードとKubernetesコントロールプレーン間の通信を許可する必要があります。組織がオープンな通信を許可しない場合は、[ポート要件](https://docs.aws.amazon.com/eks/latest/userguide/sec-group-reqs.html)を確認し、ルールを手動で設定してください。

EKSは、クラスター作成時に提供するカスタムセキュリティグループを管理されたインターフェース（X-ENI）に適用しますが、ノードに直ちに関連付けません。ノードグループを作成する際には、[カスタムセキュリティグループを手動で関連付ける](https://eksctl.io/usage/schema/#nodeGroups-securityGroups)ことを強くおすすめします。ノードの自動スケーリング時にKarpenterノードテンプレートがカスタムセキュリティグループを検出するために、[securityGroupSelectorTerms](https://karpenter.sh/docs/concepts/nodeclasses/#specsecuritygroupselectorterms)を有効にすることも検討してください。

ノード間の通信トラフィックを許可するためにセキュリティグループを作成することを強くおすすめします。ブートストラッププロセス中、ノードはクラスターエンドポイントにアクセスするために出力インターネット接続性が必要です。オンプレミス接続やコンテナレジストリへのアクセスなど、外部へのアクセス要件を評価し、適切なルールを設定してください。本番環境に変更を加える前に、開発環境で接続を注意深く確認することを強くおすすめします。

各可用性ゾーン（AZ）にNATゲートウェイを展開することで、プライベートサブネット（IPv4およびIPv6）にノードを展開する場合、ゾーンに依存しないアーキテクチャを確保し、クロスAZの費用を削減することができます。各AZのNATゲートウェイは冗長性を持って実装されます。

プライベートサブネットへのアクセスを持つEC2インスタンスを使用して、AWS Cloud9はプライベートサブネットで安全に実行できるWebベースのIDEです。Cloud9インスタンスでは、イネスアクセスを使用せずにエグレスも無効にすることができます。[Cloud9を使用してプライベートクラスターやサブネットにアクセスする方法について詳しくはこちらをご覧ください。](https://aws.amazon.com/blogs/security/isolating-network-access-to-your-aws-cloud9-environments/)

![illustration of AWS Cloud9 console connecting to no-ingress EC2 instance.](./image-2.jpg)

