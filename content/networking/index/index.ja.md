# Amazon EKS ネットワークのベストプラクティスガイド

クラスタとアプリケーションを効率的に運用するためには、Kubernetesのネットワークを理解することが重要です。 クラスタネットワークとも呼ばれるPodネットワークは、Kubernetesネットワークの中心です。 Kubernetesはクラスターネットワーク用に[Container Network Interface](https://github.com/containernetworking/cni)（CNI）プラグインをサポートしています。

Amazon EKSは、Kubernetes Podネットワークを実装するための[Amazon Virtual Private Cloud (VPC)](https://docs.aws.amazon.com/vpc/latest/userguide/what-is-amazon-vpc.html) CNIプラグインを公式にサポートしています。 VPC CNIはAWS VPCとのネイティブ統合を提供し、アンダーレイモードで動作します。 アンダーレイモードでは、Pod とホストは同じネットワークレイヤーに配置され、ネットワーク名前空間を共有します。 PodのIPアドレスはクラスタとVPCの観点から一貫しています。

このガイドでは、Kubernetesクラスタネットワークの文脈で[Amazon VPC Container Network Interface](https://github.com/aws/amazon-vpc-cni-k8s)[(VPC CNI)]を紹介します。 VPC CNIはEKSがサポートするデフォルトのネットワークプラグインであるため、本ガイドの焦点となります。 VPC CNI は、さまざまなユースケースをサポートするために高度に設定可能です。 本ガイドでは、VPC CNI の様々なユースケース、動作モード、サブコンポーネント、および推奨事項に関する専用セクションを設けています。

Amazon EKSはアップストリームのKubernetesを実行し、Kubernetes適合性が認証されています。 代替CNIプラグインを使用することはできますが、本ガイドでは代替CNIを管理するための推奨事項は記載していません。 代替CNIを効果的に管理するためのパートナーやリソースのリストについては、 [EKS Alternate CNI](https://docs.aws.amazon.com/eks/latest/userguide/alternate-cni-plugins.html) のドキュメントを確認してください。

## Kubernetes ネットワークモデル

Kubernetesはクラスタネットワークに以下の要件を設定しています。

* 同じノードでスケジュールされているPodは、NAT（Network Address Translation）を使用せずに他のPodと通信できる必要があります。 
* 特定のノードで実行されているすべてのシステムデーモン（ [kubelet](https://kubernetes.io/docs/concepts/overview/components/)などのバックグラウンドプロセス）は、同じノードで実行されているPodと通信できる必要があります。 
* [host network](https://docs.docker.com/network/host/)を使用するPodは、NATを使用せずに他のすべてのノードのすべてのPodと通信できる必要があります。

Kubernetesが互換性のあるネットワーク実装に期待することの詳細については、[Kubernetesネットワークモデル]((https://kubernetes.io/docs/concepts/services-networking/#the-kubernetes-network-model) )を参照してください。 次の図は、Podネットワーク名前空間とホストネットワーク名前空間の関係を示しています。

![illustration of host network and 2 pod network namespaces](image.png)
## Container Networking Interface (CNI)

Kubernetesは、Kubernetesのネットワークモデルを実装するためのCNI仕様とプラグインをサポートしています。CNIは、[仕様]((https://github.com/containernetworking/cni/blob/main/SPEC.md))（現在のバージョンは1.0.0）と、コンテナ内のネットワークインターフェイスを設定するためのプラグインを記述するためのライブラリ、およびサポートされる多数のプラグインで構成されます。 CNI は、コンテナのネットワーク接続性と、コンテナが削除されたときに割り当てられたリソースを削除することだけに関係します。

CNIプラグインは、kubeletに`--network-plugin=cni`コマンドラインオプションを渡すことで有効になります。kubeletは`--cni-conf-dir`（デフォルトは/etc/cni/net.d）からファイルを読み取り、そのファイルのCNI設定を使用して各Podのネットワークを設定します。CNI設定ファイルはCNI仕様（最小バージョンv0.4.0）と一致する必要があり、設定で参照される必要のあるCNIプラグインは`--cni-bin-dir`ディレクトリ（デフォルトは/opt/cni/bin）に存在している必要があります。ディレクトリ内に複数のCNI設定ファイルがある場合、*kubeletは辞書順で最初に来る設定ファイルを使用します*。


## Amazon Virtual Private Cloud (VPC) CNI

AWSが提供するVPC CNIは、EKSクラスターのデフォルトのネットワーキングアドオンです。EKSクラスターをプロビジョニングする際には、VPC CNIアドオンがデフォルトでインストールされます。VPC CNIはKubernetesワーカーノード上で実行されます。VPC CNIアドオンには、CNIバイナリとIPアドレス管理（ipamd）プラグインが含まれています。CNIは、VPCネットワークからPodにIPアドレスを割り当てます。ipamdは、各Kubernetesノードに対してAWS Elastic Networking Interface（ENI）を管理し、IPのウォームプールを維持します。VPC CNIは、ENIとIPアドレスの事前割り当てのための構成オプションを提供します。Podの起動時間を高速化するためのENIとIPアドレスのプリアロケーションについては、[Amazon VPC CNI](../vpc-cni/index.md)を参照してください。

Amazon EKSでは、クラスターを作成する際に少なくとも2つのアベイラビリティーゾーンのサブネットを指定することを推奨しています。Amazon VPC CNIは、ノードのサブネットからPodにIPアドレスを割り当てます。EKSクラスターを展開する前に、利用可能なIPアドレスのためにサブネットを確認することを強くお勧めします。EKSクラスターを展開する前に、[VPCとサブネット](../subnets/index.md)の推奨事項をご確認ください。

Amazon VPC CNIは、ノードのプライマリENIに接続されたサブネットからENIとセカンダリIPアドレスのウォームプールを割り当てます。このVPC CNIのモードは「[セカンダリIPモード](../vpc-cni/index.md)」と呼ばれます。IPアドレスの数、つまりPodの数（Podの密度）は、インスタンスタイプによって定義されるENIの数とENIごとのIPアドレス（制限）によって決まります。セカンダリモードはデフォルトであり、小規模なクラスターや小さいインスタンスタイプに適しています。Podの密度の課題に直面している場合は、[プレフィックスモード](../prefix-mode/index_linux.md)を使用することを検討してください。また、ENIにプレフィックスを割り当てることで、Podのための利用可能なIPアドレスを増やすこともできます。

Amazon VPC CNIは、AWS VPCとネイティブに統合されており、Kubernetesクラスターの構築において既存のAWS VPCネットワーキングとセキュリティのベストプラクティスを適用することができます。これには、VPCフローログ、VPCルーティングポリシー、ネットワークトラフィックの分離のためのセキュリティグループの使用が含まれます。デフォルトでは、Amazon VPC CNIはノードのプライマリENIに関連付けられたセキュリティグループをPodに適用します。異なるネットワークルールをPodに割り当てたい場合は、[Pod用のセキュリティグループ](../sgpp/index.md)を有効にすることを検討してください。

デフォルトでは、VPC CNIはPodにIPアドレスをプライマリENIに割り当てます。大規模なクラスターで数千のワークロードを実行する場合、IPv4アドレスの不足が発生することが一般的です。AWS VPCでは、IPv4 CIDRブロックの枯渇を回避するために、[セカンダリCIDRを割り当てる](https://docs.aws.amazon.com/vpc/latest/userguide/configure-your-vpc.html#add-cidr-block-restrictions)ことができます。AWS VPC CNIを使用して、Podに異なるサブネットCIDR範囲を使用することもできます。これはVPC CNIの「[カスタムネットワーキング](../custom-networking/index.md)」と呼ばれる機能です。EKSと一緒に100.64.0.0/10および198.19.0.0/16のCIDR（CG-NAT）を使用するためにカスタムネットワーキングを使用することを検討してください。これにより、PodがVPCのRFC1918 IPアドレスを消費しなくなる環境を作成することができます。

カスタムネットワーキングはIPv4アドレスの枯渇問題に対処するための1つのオプションですが、運用上のオーバーヘッドが発生します。この問題を解決するために、IPv6クラスターを使用することをお勧めします。特に、VPCのIPv4アドレススペースが完全に枯渇した場合は、[IPv6クラスターへの移行](../ipv6/index.md)をお勧めします。組織のIPv6サポート計画を評価し、IPv6への投資がより長期的な価値を持つかどうかを検討してください。

EKSのIPv6サポートは、限られたIPv4アドレススペースによって引き起こされるIP枯渇問題を解決することに焦点を当てています。IPv4の枯渇に関する顧客の問題に対応するため、EKSはIPv6のみのPodをデュアルスタックのPodよりも優先的に扱います。つまり、PodはIPv4リソースにアクセスできる場合がありますが、VPC CIDR範囲からIPv4アドレスは割り当てられません。VPC CNIは、PodにIPv6アドレスをAWS管理のVPC IPv6 CIDRブロックから割り当てます。

## サブネット計算機

このプロジェクトには、[サブネット計算機のExcelドキュメント](../subnet-calc/subnet-calc.xlsx)が含まれています。この計算機ドキュメントは、指定されたワークロードのIPアドレス消費を、`WARM_IP_TARGET`や`WARM_ENI_TARGET`などの異なるENI構成オプションでシミュレートします。ドキュメントには、ウォームENIモード用の最初のシートとウォームIPモード用の2番目のシートが含まれています。これらのモードについての詳細については、[VPC CNIガイダンス](../vpc-cni/index.md)を参照してください。

入力:
- サブネットCIDRサイズ
- ウォームENIターゲット *または* ウォームIPターゲット
- インスタンスのリスト
    - タイプ、数、およびインスタンスごとにスケジュールされるワークロードの数

出力:
- ホストされるポッドの総数
- 消費されるサブネットIPの数
- 残りのサブネットIPの数
- インスタンスレベルの詳細
    - インスタンスごとのウォームIP/ENIの数
    - インスタンスごとのアクティブIP/ENIの数
