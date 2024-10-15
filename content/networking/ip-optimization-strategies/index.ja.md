# IPアドレスの利用を最適化する

コンテナ化された環境は、アプリケーションのモダン化により急速に拡大しています。これにより、より多くのワーカーノードとポッドが展開されるようになりました。

[Amazon VPC CNI](../vpc-cni/)プラグインは、各ポッドにVPCのCIDRからIPアドレスを割り当てます。このアプローチにより、VPC Flow Logsやその他のモニタリングソリューションなどのツールを使用して、ポッドのアドレスを完全に把握することができます。ただし、ワークロードの種類によっては、ポッドによって多数のIPアドレスが消費される可能性があります。

AWSネットワーキングアーキテクチャを設計する際には、VPCおよびノードレベルでAmazon EKSのIP消費を最適化することが重要です。これにより、IP枯渇の問題を軽減し、ノードごとのポッド密度を向上させることができます。

このセクションでは、これらの目標を達成するのに役立つテクニックについて説明します。

## ノードレベルのIP消費を最適化する

[プレフィックスデリゲーション](https://docs.aws.amazon.com/eks/latest/userguide/cni-increase-ip-addresses.html)は、Amazon Virtual Private Cloud（Amazon VPC）の機能であり、IPv4またはIPv6のプレフィックスをAmazon Elastic Compute Cloud（Amazon EC2）インスタンスに割り当てることができます。これにより、ネットワークインターフェース（ENI）ごとのIPアドレス数が増え、ノードごとのポッド密度が向上し、コンピューティング効率が向上します。プレフィックスデリゲーションは、カスタムネットワーキングでもサポートされています。

詳細については、[Linuxノードでのプレフィックスデリゲーション](../prefix-mode/index_linux/)および[Windowsノードでのプレフィックスデリゲーション](../prefix-mode/index_windows/)のセクションを参照してください。

## IP枯渇を軽減する

クラスタが利用可能なすべてのIPアドレスを消費しないようにするために、VPCおよびサブネットのサイズを成長を考慮して設計することを強くお勧めします。

IPv6を採用することは、最初からこれらの問題を回避するための素晴らしい方法です。ただし、スケーラビリティのニーズが初期の計画を超える場合やIPv6を採用できない組織の場合は、VPCの設計を改善することを推奨します。Amazon EKSのお客様の間で最も一般的に使用されるテクニックは、VPCに非ルーティングのセカンダリCIDRを追加し、VPC CNIを構成してこの追加のIPスペースをポッドに割り当てることです。これは一般的に[カスタムネットワーキング](../custom-networking/)と呼ばれています。

Amazon VPC CNIでノードに割り当てられるIPのウォームプールを最適化するために使用できる変数と、IP枯渇を軽減するのに役立つ他のアーキテクチャパターンについて説明します。

### IPv6を使用する（推奨）

ネットワークアーキテクチャを選択する際の最初のオプションとして、IPv6を採用することを強くお勧めします。IPv6は非常に大きな総IPアドレススペースを提供し、クラスタ管理者はIPv4の制限を回避するための努力をせずにアプリケーションの移行とスケーリングに集中することができます。

Amazon EKSクラスタはIPv4とIPv6の両方をサポートしています。デフォルトでは、EKSクラスタはIPv4アドレススペースを使用します。クラスタ作成時にIPv6ベースのアドレススペースを指定すると、IPv6を使用できるようになります。IPv6のEKSクラスタでは、ポッドとサービスはIPv6アドレスを受け取りますが、**レガシーのIPv4エンドポイントがIPv6クラスタ上で実行されているサービスに接続できる能力を維持します**。クラスタ内のポッド間の通信は常にIPv6を使用します。VPC（/56）内では、IPv6サブネットのIPv6 CIDRブロックサイズは固定されており、/64です。これにより、約18京個のIPv6アドレス（2の64乗）を使用してEKS上での展開をスケーリングすることができます。

詳細については、[Running IPv6 EKS Clusters](../ipv6/)セクションを参照してください。実際の操作手順については、[Understanding IPv6 on Amazon EKS](https://catalog.workshops.aws/ipv6-on-aws/en-US)の[Understanding IPv6 on Amazon EKS](https://catalog.workshops.aws/ipv6-on-aws/en-US/lab-6)セクションを参照してください。

![EKS Cluster in IPv6 Mode, traffic flow](./ipv6.gif)


### IPv4クラスタでのIP消費の最適化

このセクションは、レガシーアプリケーションを実行している顧客や、まだIPv6に移行する準備ができていないお客様を対象としています。すべての組織に早急にIPv6に移行することを奨励していますが、IPv4（RFC1918）アドレススペースを使用してコンテナワークロードをスケーリングするための代替手法を検討する必要がある場合も認識しています。そのため、Amazon EKSクラスタでIPv4（RFC1918）アドレススペースの消費を最適化するためのアーキテクチャパターンについても説明します。

#### 成長を見越した計画

IP枯渇に対する最初の防衛策として、IPv4のVPCおよびサブネットのサイズを成長を見越して設計することを強くお勧めします。サブネットに十分な利用可能なIPアドレスがない場合、新しいポッドやノードを作成することはできません。

VPCとサブネットを構築する前に、必要なワークロードスケールから逆算することをお勧めします。たとえば、[eksctl](https://eksctl.io/)（EKS上でクラスタを作成および管理するためのシンプルなCLIツール）を使用してクラスタを構築する場合、デフォルトで/19のサブネットが作成されます。/19のネットマスクは、8000以上のアドレスを割り当てることができる多くのワークロードタイプに適しています。

!!! attention
    VPCとサブネットのサイズを決定する際には、ポッドやノード以外にもIPアドレスを消費する要素がいくつかある場合があります。たとえば、ロードバランサーやRDSデータベースなどのVPC内のサービスが該当します。
さらに、Amazon EKSは最大4つのエラスティックネットワークインターフェース（X-ENI）を作成し、コントロールプレーンへの通信を許可するために必要です（詳細は[こちら](../subnets/)を参照）。クラスタのアップグレード時には、Amazon EKSは新しいX-ENIを作成し、アップグレードが成功した場合には古いX-ENIを削除します。そのため、EKSクラスタに関連付けられたサブネットのために、少なくとも/28（16個のIPアドレス）のネットマスクを推奨します。

ネットワークの計画には、[サンプルのEKSサブネット計算機](../subnet-calc/subnet-calc.xlsx)スプレッドシートを使用することができます。このスプレッドシートは、ワークロードとVPC ENIの構成に基づいてIP使用状況を計算します。IP使用状況はIPv4サブネットと比較され、構成とサブネットのサイズがワークロードに十分であるかどうかを判断します。VPCのサブネットの利用可能なIPアドレスがなくなった場合は、VPCの元のCIDRブロックを使用して[新しいサブネットを作成](https://docs.aws.amazon.com/vpc/latest/userguide/working-with-subnets.html#create-subnets)することをおすすめします。また、[Amazon EKSはクラスタのサブネットとセキュリティグループの変更を許可](https://aws.amazon.com/about-aws/whats-new/2023/10/amazon-eks-modification-cluster-subnets-security/)するようになりました。

#### IPスペースを拡張する

RFC1918のIPスペースを枯渇させる前に、[カスタムネットワーキング](../custom-networking/)パターンを使用して、専用の追加のサブネット内でポッドをスケジュールすることで、ルーティング可能なIPを節約することができます。
カスタムネットワーキングでは、セカンダリCIDR範囲に有効なVPC範囲を使用できますが、RFC1918範囲よりも企業の設定で使用される可能性が低いCIDR（/16）を使用することをお勧めします。

詳細については、[カスタムネットワーキング](../custom-networking/)の専用セクションを参照してください。

![Custom Networking, traffic flow](./custom-networking.gif)

#### IPのウォームプールを最適化する

デフォルトの設定では、VPC CNIはウォームプール内のすべてのENI（および関連するIP）を保持します。特に大きなインスタンスタイプでは、これにより多数のIPが消費される場合があります。

クラスタのサブネットに利用可能なIPアドレスが制限されている場合、次のVPC CNI構成環境変数を注意深く検討してください。

* `WARM_IP_TARGET`
* `MINIMUM_IP_TARGET`
* `WARM_ENI_TARGET`

`MINIMUM_IP_TARGET`の値を、ノード上で実行される予定のポッド数に近づけるように設定することで、ポッドが作成されると、CNIはEC2 APIを呼び出さずにウォームプールからIPアドレスを割り当てることができます。

ただし、`WARM_IP_TARGET`の値を低く設定すると、EC2 APIへの追加の呼び出しが発生し、リクエストのスロットリングが発生する可能性があります。大規模なクラスタでは、リクエストのスロットリングを回避するために、`MINIMUM_IP_TARGET`と併用して使用してください。

これらのオプションを設定するには、`aws-k8s-cni.yaml`マニフェストをダウンロードして環境変数を設定します。現時点では、最新のリリースは[こちら](https://github.com/aws/amazon-vpc-cni-k8s/blob/master/config/master/aws-k8s-cni.yaml)にあります。構成値のバージョンがインストールされているVPC CNIのバージョンと一致しているかどうかを確認してください。

!!! Warning
    これらの設定はCNIを更新するとデフォルトにリセットされます。更新する前にCNIのバックアップを取得してください。更新が成功した後にこれらの設定を再適用する必要があるかどうかを確認するために、構成設定を確認してください。

既存のアプリケーションに対してダウンタイムなしでCNIパラメータを調整することができますが、スケーラビリティのニーズをサポートする値を選択する必要があります。バッチワークロードで作業している場合は、デフォルトの`WARM_ENI_TARGET`を更新して、ポッドのスケールニーズに合わせることをおすすめします。`WARM_ENI_TARGET`を高い値に設定することで、常に大規模なバッチワークロードを実行するために必要なウォームIPプールを維持し、データ処理の遅延を回避できます。

!!! warning
    IPアドレスの枯渇に対する推奨される対応策は、VPCの設計改善です。IPv6やセカンダリCIDRなどのソリューションを検討してください。ウォームIPの数を最小限に抑えるためのこれらの値の調整は、他のオプションが除外された後の一時的な解決策として考えてください。これらの値を誤って設定すると、クラスタの動作に支障をきたす可能性があります。

    **本番システムに変更を加える前に**、[このページ](https://github.com/aws/amazon-vpc-cni-k8s/blob/master/docs/eni-and-ip-target.md)の考慮事項を必ず確認してください。

#### IPアドレス在庫のモニタリング

上記で説明したソリューションに加えて、IP利用状況の可視化も重要です。[CNI Metrics Helper](https://docs.aws.amazon.com/eks/latest/userguide/cni-metrics-helper.html)を使用して、サブネットのIPアドレス在庫をモニタリングすることができます。利用可能なメトリクスの一部は以下の通りです：

* クラスタがサポートできるENIの最大数
* すでに割り当てられているENIの数
* 現在Podに割り当てられているIPアドレスの数
* 利用可能なIPアドレスの総数と最大数

また、[CloudWatchアラーム](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/AlarmThatSendsEmail.html)を設定して、IPアドレスが枯渇しているサブネットについて通知を受けることもできます。[CNI metrics helperのインストール手順](https://docs.aws.amazon.com/eks/latest/userguide/cni-metrics-helper.html)については、EKSユーザーガイドを参照してください。

!!! warning
    VPC CNIの`DISABLE_METRICS`変数がfalseに設定されていることを確認してください。

#### その他の考慮事項

Amazon EKSに固有ではない他のアーキテクチャパターンもIP枯渇の問題に役立つ場合があります。たとえば、[VPC間の通信の最適化](../subnets/#communication-across-vpcs)や[複数のアカウントでのVPCの共有](../subnets/#sharing-vpc-across-multiple-accounts)など、IPv4アドレスの割り当てを制限するための方法があります。

これらのパターンについて詳しくは、以下のリンクを参照してください：

* [大規模なAmazon VPCネットワークの設計](https://aws.amazon.com/blogs/networking-and-content-delivery/designing-hyperscale-amazon-vpc-networks/)
* [Amazon VPC Latticeを使用したセキュアなマルチアカウント・マルチVPC接続の構築](https://aws.amazon.com/blogs/networking-and-content-delivery/build-secure-multi-account-multi-vpc-connectivity-for-your-applications-with-amazon-vpc-lattice/)

