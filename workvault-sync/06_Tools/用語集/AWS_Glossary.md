# AWS用語ノート

作成日: 2026-10-01

## 略語索引

|略語|正式名称|このノートの関連項目|
|---|---|---|
|AWS|Amazon Web Services|Amazon Web Services|
|AZ|Availability Zone|アベイラビリティーゾーン|
|IAM|Identity and Access Management|AWS Identity and Access Management|
|VPC|Virtual Private Cloud|仮想プライベートクラウド|
|EC2|Elastic Compute Cloud|Amazon Elastic Compute Cloud|
|S3|Simple Storage Service|Amazon Simple Storage Service|
|EBS|Elastic Block Store|Amazon Elastic Block Store|
|RDS|Relational Database Service|Amazon Relational Database Service|
|API|Application Programming Interface|Amazon API Gateway|
|DNS|Domain Name System|ドメインネームシステム|
|TLS|Transport Layer Security|Transport Layer Security|
|MFA|Multi-Factor Authentication|多要素認証|
|RTO|Recovery Time Objective|復旧時間目標|
|RPO|Recovery Point Objective|復旧時点目標|
|HA|High Availability|高可用性|

サービス名など略語ではない名称は、その名称を記載した。


対象: AWS基礎から構築・運用の主要領域。特定の資格試験の全出題範囲を対象としたものではない。

説明中の略語は、原則として最初の登場時に正式名称を併記し、関連する正式名称の項目を索引として収録した。具体例は「自作例」と明記したものに限る。料金や無料枠は時点・地域・条件で変わるため、本文では断定しない。

## 1. Amazon Web Services

正式名称: Amazon Web Services (AWS)
意味: Amazonが提供するクラウドサービス群。サーバー、ストレージ、データベースなどをネットワーク経由で利用する。

## 2. クラウド責任分担モデル

正式名称: AWS Shared Responsibility Model
意味: AWSはクラウド基盤の安全性を担い、利用者は選んだサービスに応じてデータ、設定、認証、アプリケーションを管理する。

## 3. リージョン

正式名称: AWS Region
意味: 地理的に分離されたAWSの提供地域。リージョン間の複製や転送は自動ではない。

## 4. アベイラビリティーゾーン

正式名称: Availability Zone (AZ)
意味: 1つのリージョン内の独立した場所。サブネットは1つのAZに属するため、障害分散では複数AZへ配置する。

## 5. エッジロケーション

正式名称: AWS edge location
意味: 利用者に近い場所でコンテンツ配信や名前解決などを処理する拠点。リージョンやAZとは役割が異なる。

## 6. ローカルゾーン

正式名称: AWS Local Zones
意味: 大都市など利用者に近い場所へ一部の計算・保存資源を置く仕組み。

## 7. ウェーブレングスゾーン

正式名称: AWS Wavelength Zones
意味: 通信事業者の5Gネットワーク近くで低遅延処理を行う配置場所。

## 8. サービスレベルアグリーメント

正式名称: Service Level Agreement (SLA)
意味: サービス可用性などについてAWSが定める契約上の水準。設計上の可用性を保証するものではない。

## 9. 認証

正式名称: authentication
意味: 利用者やサービスが誰であるかを確認すること。認可とは別である。

## 10. 認可

正式名称: authorization
意味: 認証された主体がどの操作を許されるかを判定すること。

## 11. AWS Identity and Access Management

正式名称: AWS Identity and Access Management (IAM)
意味: AWS資源への認証・認可を管理するサービス。ポリシーはJSON文書である。

## 12. IAMユーザー

正式名称: IAM user
意味: AWSアカウント内の恒久的な識別子。人の通常利用は短期認証情報やIAMロールを優先する。

## 13. IAMグループ

正式名称: IAM user group
意味: IAMユーザーをまとめ、共通のアイデンティティベースポリシーを適用する単位。

## 14. IAMロール

正式名称: IAM role
意味: 一時的な認証情報を得るためのIAMアイデンティティ。人、AWSサービス、別アカウントなどが引き受ける。

## 15. 信頼ポリシー

正式名称: role trust policy
意味: IAMロールを誰が引き受けられるかを定めるリソースベースポリシー。権限そのものを付与するポリシーではない。

## 16. アイデンティティベースポリシー

正式名称: identity-based policy
意味: ユーザー、グループ、ロールに付け、操作と対象への許可・拒否を記述するポリシー。

## 17. リソースベースポリシー

正式名称: resource-based policy
意味: S3バケットなど資源に付け、誰がどの操作をできるかを記述するポリシー。

## 18. 明示的拒否

正式名称: explicit deny
意味: 適用されるポリシーの1つでも拒否すると許可を上書きする規則。

## 19. 暗黙的拒否

正式名称: implicit deny
意味: 許可が明示されていない要求は原則として拒否される状態。

## 20. 権限境界

正式名称: permissions boundary
意味: IAMユーザーやロールに付与できる最大権限を定める上限。単独では権限を付与しない。

## 21. サービスコントロールポリシー

正式名称: service control policy (SCP)
意味: AWS Organizationsのアカウントや組織単位に対する最大権限の制御。許可を付与するものではない。

## 22. セッションポリシー

正式名称: session policy
意味: 一時セッションで有効な権限をさらに制限するポリシー。

## 23. 最小権限

正式名称: principle of least privilege
意味: 業務に必要な操作と対象だけを許可する設計原則。

## 24. Amazon Resource Name

正式名称: Amazon Resource Name (ARN)
意味: AWS資源を一意に識別する文字列。例は自作例: arn:aws:s3:::example-bucket。

## 25. JavaScript Object Notation

正式名称: JavaScript Object Notation (JSON)
意味: IAMポリシーなどで使う構造化テキスト形式。

## 26. 多要素認証

正式名称: multi-factor authentication (MFA)
意味: パスワード以外の要素も使う認証。特にルートユーザーで重要。

## 27. ルートユーザー

正式名称: AWS account root user
意味: AWSアカウント作成時の最上位主体。日常作業には使わず強固に保護する。

## 28. AWS Organizations

正式名称: AWS Organizations
意味: 複数AWSアカウントを組織単位で管理し、統合請求やSCPを使うサービス。

## 29. AWS Control Tower

正式名称: AWS Control Tower
意味: 複数アカウントの標準構成、ガードレール、統制を組織的に整えるサービス。

## 30. 仮想プライベートクラウド

正式名称: Amazon Virtual Private Cloud (VPC)
意味: AWS内に論理的に分離したネットワークを作るサービス。

## 31. サブネット

正式名称: subnet
意味: VPCのIP範囲を分割した単位。必ず単一AZに属し、public/privateは経路設定による分類である。

## 32. パブリックサブネット

正式名称: public subnet
意味: ルートテーブルがインターネットゲートウェイへの経路を持つサブネット。配置しただけで公開到達できるわけではない。

## 33. プライベートサブネット

正式名称: private subnet
意味: 直接のインターネットゲートウェイ経路を持たないサブネット。外向き通信にNATゲートウェイを使う場合がある。

## 34. CIDR

正式名称: Classless Inter-Domain Routing (CIDR)
意味: IPアドレス範囲を10.0.0.0/16のように表す方法。自作例: VPCを10.0.0.0/16で設計する。

## 35. ルートテーブル

正式名称: route table
意味: 宛先IP範囲ごとの次の転送先を定め、サブネットに関連付ける設定。

## 36. インターネットゲートウェイ

正式名称: internet gateway (IGW)
意味: VPCとインターネット間の通信を可能にする接続先。経路、公開IP、許可設定がそろって初めて到達する。

## 37. NATゲートウェイ

正式名称: NAT gateway
意味: private subnetの資源から外部へ出る通信を変換するマネージドサービス。通常はpublic subnetに置く。

## 38. セキュリティグループ

正式名称: security group (SG)
意味: 仮想ネットワークインターフェイスに適用する状態保持型の仮想ファイアウォール。受信ルールへの戻り通信は自動的に許可される。

## 39. ネットワークアクセスコントロールリスト

正式名称: network access control list (NACL)
意味: サブネット単位の状態を保持しない通信フィルター。受信・送信を個別に許可し、番号順で評価する。

## 40. VPCエンドポイント

正式名称: VPC endpoint
意味: VPCから対応AWSサービスへ、インターネットを経由せず接続する仕組み。ゲートウェイ型とインターフェイス型がある。

## 41. VPCピアリング

正式名称: VPC peering connection
意味: 2つのVPCを私設接続する機能。推移的ルーティングは提供しない。

## 42. AWS Transit Gateway

正式名称: AWS Transit Gateway
意味: 多数のVPCやオンプレミスネットワークをハブとして接続するサービス。

## 43. AWS Site-to-Site VPN

正式名称: AWS Site-to-Site VPN
意味: オンプレミスとVPCを暗号化トンネルで接続するサービス。

## 44. AWS Direct Connect

正式名称: AWS Direct Connect
意味: AWSと利用者拠点を専用接続で結ぶサービス。インターネット経由ではないが暗号化を自動提供するとは限らない。

## 45. Amazon Route 53

正式名称: Amazon Route 53
意味: DNS、ドメイン登録、ヘルスチェック、ルーティングを提供するサービス。

## 46. ドメインネームシステム

正式名称: Domain Name System (DNS)
意味: example.comのような名前をIPアドレスなどへ対応付ける仕組み。

## 47. DNSレコード

正式名称: DNS resource record
意味: 名前、種類、値、TTLなどを持つ名前解決の設定。A、AAAA、CNAME、Aliasなどがある。

## 48. Route 53 Resolver

正式名称: Route 53 Resolver
意味: VPC内のDNS問い合わせを解決し、転送ルールで外部DNSとの連携も行う機能。

## 49. Amazon Elastic Compute Cloud

正式名称: Amazon Elastic Compute Cloud (Amazon EC2)
意味: 仮想サーバーを起動し、OSやアプリケーションを利用者が管理するサービス。

## 50. Amazon Machine Image

正式名称: Amazon Machine Image (AMI)
意味: EC2インスタンス起動時のOS、ソフトウェア、設定のテンプレート。

## 51. EC2インスタンスタイプ

正式名称: Amazon EC2 instance type
意味: 仮想CPU、メモリ、ネットワークなどの性能組合せ。

## 52. Elastic IPアドレス

正式名称: Elastic IP address
意味: AWSアカウントに割り当て、インスタンスなどへ関連付ける固定IPv4アドレス。

## 53. Amazon Elastic Block Store

正式名称: Amazon Elastic Block Store (Amazon EBS)
意味: EC2用の永続ブロックストレージ。通常は単一AZの資源で、スナップショットは別の保存形態である。

## 54. Amazon Elastic File System

正式名称: Amazon Elastic File System (Amazon EFS)
意味: 複数AZのEC2などから同時利用できる伸縮自在なファイルストレージ。

## 55. Amazon FSx

正式名称: Amazon FSx
意味: Windows File Server、Lustre、NetApp ONTAP、OpenZFSなどのファイルシステムをマネージド提供するサービス群。

## 56. Amazon EC2 Auto Scaling

正式名称: Amazon EC2 Auto Scaling
意味: EC2インスタンスの台数を需要やヘルスチェックに応じて増減し、指定した最低・最大・希望台数を保つ。

## 57. Elastic Load Balancing

正式名称: Elastic Load Balancing (ELB)
意味: 複数のターゲットへ受信通信を分散するサービス群。

## 58. Application Load Balancer

正式名称: Application Load Balancer (ALB)
意味: HTTP/HTTPSのリクエストをパスやホスト名などでルーティングするロードバランサー。

## 59. Network Load Balancer

正式名称: Network Load Balancer (NLB)
意味: TCP、TLS、UDPなどの接続を高性能・低遅延で分散するロードバランサー。

## 60. AWS Lambda

正式名称: AWS Lambda
意味: サーバーをプロビジョニングせず、イベントに応じてコードを実行するサービス。実行時間や同時実行数などの制約がある。

## 61. コンテナ

正式名称: container
意味: アプリケーションと依存関係を隔離して実行するパッケージ。仮想マシンとは異なり通常はホストカーネルを共有する。

## 62. Amazon Elastic Container Registry

正式名称: Amazon Elastic Container Registry (Amazon ECR)
意味: コンテナイメージを保存・管理するレジストリ。

## 63. Amazon Elastic Container Service

正式名称: Amazon Elastic Container Service (Amazon ECS)
意味: コンテナをタスクやサービスとして実行・管理するオーケストレーションサービス。

## 64. Amazon Elastic Kubernetes Service

正式名称: Amazon Elastic Kubernetes Service (Amazon EKS)
意味: Kubernetesクラスターの制御プレーンをAWSが管理するサービス。

## 65. AWS Fargate

正式名称: AWS Fargate
意味: ECSやEKSのコンテナを、EC2インスタンスを利用者が管理せず実行する技術。

## 66. Amazon Simple Storage Service

正式名称: Amazon Simple Storage Service (Amazon S3)
意味: バケット内のオブジェクトを保存するオブジェクトストレージ。バケット作成時にリージョンを選び、後から変更できない。

## 67. S3オブジェクト

正式名称: Amazon S3 object
意味: データ本体、メタデータ、キーで構成される保存単位。

## 68. S3バケット

正式名称: Amazon S3 bucket
意味: オブジェクトを格納するコンテナ。名前空間上の単位で、作成時にリージョンを指定する。

## 69. S3オブジェクトキー

正式名称: Amazon S3 object key
意味: バケット内でオブジェクトを識別する名前。photos/a.jpgのような文字列で、実際のフォルダーではない。

## 70. S3ストレージクラス

正式名称: Amazon S3 storage class
意味: アクセス頻度、可用性、保存場所、料金特性を選ぶ分類。S3 Standard、Standard-IA、One Zone-IA、Intelligent-Tiering、Glacier各クラスなどがある。

## 71. S3 Intelligent-Tiering

正式名称: S3 Intelligent-Tiering
意味: アクセスパターンに応じて対象階層を自動移動するストレージクラス。料金条件は最新の公式料金表で確認する。

## 72. S3 Glacier

正式名称: S3 Glacier storage classes
意味: 低頻度データのアーカイブ向けストレージクラス群。取り出し時間と料金がクラスごとに異なる。

## 73. S3ライフサイクル

正式名称: S3 Lifecycle
意味: オブジェクトを別クラスへ移行したり期限後に削除したりするルール。

## 74. S3バージョニング

正式名称: S3 Versioning
意味: 同じキーの複数版を保持する機能。削除時は削除マーカーとなり、版ごとに保存量が生じる。

## 75. S3強い整合性

正式名称: Amazon S3 strong read-after-write consistency
意味: オブジェクトのPUT、上書き、DELETE後の読み取りと一覧が、成功応答後に最新状態を返すモデル。バケット設定の伝播とは別である。

## 76. S3レプリケーション

正式名称: S3 Replication
意味: オブジェクトを同一リージョンまたは別リージョンのバケットへ非同期複製する機能。自動的に全バケットが複製されるわけではない。

## 77. Amazon Relational Database Service

正式名称: Amazon Relational Database Service (Amazon RDS)
意味: リレーショナルデータベースのセットアップ、バックアップ、パッチ適用などを管理するサービス。

## 78. Amazon Aurora

正式名称: Amazon Aurora
意味: MySQL互換またはPostgreSQL互換のリレーショナルデータベースエンジン。Amazon RDSのDB instance deploymentやMulti-AZ DB clusterとは異なる、共有ストレージを使うクラスター型のサービス。Auroraのリーダーで読み取りを分散する設計と、RDS Multi-AZの構成を混同しない。

## 79. RDS Multi-AZ DB instance deployment

正式名称: Amazon RDS Multi-AZ DB instance deployment
意味: 主DBインスタンスと別AZのスタンバイDBインスタンスを組み合わせる高可用性構成。通常のスタンバイは同期複製され、利用者の読み取り接続を受ける読み取りレプリカではない。障害時のフェイルオーバー先であり、読み取りスケール用途と混同しない。
例: 読み取り負荷を分散したい場合は、要件に合うAmazon RDSのリードレプリカを別途検討する。

## 80. RDS Multi-AZ DB cluster

正式名称: Amazon RDS Multi-AZ DB cluster
意味: ライターDBインスタンスと2つの読み取り可能なスタンバイDBインスタンスを、3つのAZに配置するRDSの構成。高可用性に加え読み取りキャパシティを提供するが、対象エンジン・リージョン・機能条件を現行公式ドキュメントで確認する。従来のDB instance deploymentのスタンバイとは別の構成である。
例: 「Multi-AZならスタンバイを読める」と一般化せず、DB instance deploymentかDB clusterかを構成名で確認する。

## 80. RDSリードレプリカ

正式名称: Amazon RDS read replica
意味: 主インスタンスから非同期複製する読み取り専用コピー。読み取りスケールと障害復旧に使えるが、Multi-AZの同期スタンバイとは別物。

## 81. Amazon DynamoDB

正式名称: Amazon DynamoDB
意味: サーバー管理を要しないキーバリュー・ドキュメントデータベース。パーティションキー設計が重要。

## 82. DynamoDBパーティションキー

正式名称: DynamoDB partition key
意味: 項目を論理パーティションへ分散するキー。偏りは性能に影響する。

## 83. DynamoDBグローバルセカンダリインデックス

正式名称: DynamoDB global secondary index (GSI)
意味: 主キーとは異なるキーで検索するためのインデックス。

## 84. Amazon ElastiCache

正式名称: Amazon ElastiCache
意味: Redis OSSやMemcached互換のインメモリデータストアを管理するサービス。

## 85. Amazon Redshift

正式名称: Amazon Redshift
意味: 分析クエリ向けのクラウドデータウェアハウス。オンライン取引処理向けの一般的なリレーショナルデータベースとは目的が異なる。

## 86. Amazon CloudFront

正式名称: Amazon CloudFront
意味: エッジロケーションからウェブコンテンツやAPI応答を配信するコンテンツ配信ネットワーク。

## 87. AWS WAF

正式名称: AWS WAF
意味: ウェブアプリケーションのHTTP/HTTPS要求をルールで検査・制御するサービス。

## 88. AWS Shield

正式名称: AWS Shield
意味: 分散サービス妨害攻撃からAWS資源を保護するマネージドサービス群。

## 89. Amazon Cognito

正式名称: Amazon Cognito
意味: ウェブ・モバイルアプリの利用者サインアップ、サインイン、アクセストークン発行を提供するサービス。

## 90. AWS Secrets Manager

正式名称: AWS Secrets Manager
意味: データベース認証情報などの秘密を保存・取得し、ローテーションを支援するサービス。

## 91. AWS Key Management Service

正式名称: AWS Key Management Service (AWS KMS)
意味: 暗号化に使う暗号鍵の作成、管理、利用制御を行うサービス。鍵ポリシーとIAM権限の両方を確認する。

## 92. 暗号化

正式名称: encryption
意味: 鍵を使い、データを読めない形式へ変換すること。保管時と通信時を分けて設計する。

## 93. Transport Layer Security

正式名称: Transport Layer Security (TLS)
意味: 通信相手の認証と通信内容の暗号化を行うプロトコル。

## 94. Amazon Simple Queue Service

正式名称: Amazon Simple Queue Service (Amazon SQS)
意味: メッセージをキューに保持し、受信側が取り出す疎結合なサービス。標準キューとFIFOキューがある。

## 95. Amazon Simple Notification Service

正式名称: Amazon Simple Notification Service (Amazon SNS)
意味: トピックから複数の購読先へ通知を配信する発行・購読サービス。

## 96. Amazon EventBridge

正式名称: Amazon EventBridge
意味: イベントバスでイベントを受け、ルールに一致するターゲットへルーティングするサービス。旧CloudWatch Events。

## 97. AWS Step Functions

正式名称: AWS Step Functions
意味: 状態機械として複数処理、分岐、再試行、エラー処理を可視化・実行するサービス。

## 98. Amazon API Gateway

正式名称: Amazon API Gateway
意味: REST、HTTP、WebSocket APIの作成、公開、認証、制限、監視を行うサービス。

## 99. Amazon CloudWatch

正式名称: Amazon CloudWatch
意味: メトリクス、ログ、アラーム、ダッシュボード、イベントを用いた監視サービス。

## 100. AWS CloudTrail

正式名称: AWS CloudTrail
意味: AWS API操作や管理イベントを記録し、監査や調査に使うサービス。CloudWatchの性能メトリクスとは目的が異なる。

## 101. AWS Config

正式名称: AWS Config
意味: AWS資源の設定履歴を記録し、ルールにより望ましい設定か評価するサービス。

## 102. AWS Systems Manager

正式名称: AWS Systems Manager
意味: EC2などのノードを可視化し、パッチ、パラメータ、コマンド実行、セッションを管理するサービス。

## 103. AWS CloudFormation

正式名称: AWS CloudFormation
意味: テンプレートでAWS資源を宣言し、スタックとして作成・更新・削除するサービス。

## 104. AWS Cloud Development Kit

正式名称: AWS Cloud Development Kit (AWS CDK)
意味: プログラミング言語でインフラを定義し、CloudFormationテンプレートを生成する開発ツール。

## 105. Terraform

正式名称: Terraform
意味: HashiCorpが提供する複数クラウド対応のInfrastructure as Codeツール。AWS固有サービスではなく、CloudFormationやCDKと競合・併用し得る。

## 106. Infrastructure as Code

正式名称: Infrastructure as Code (IaC)
意味: インフラ設定をコードで宣言・レビュー・再現する運用方式。

## 107. AWS Billing

正式名称: AWS Billing and Cost Management
意味: 利用料金、請求、支払い、コスト配分を管理する領域。無料枠は条件・時期・サービスで変わるため断定しない。

## 108. AWS Budgets

正式名称: AWS Budgets
意味: コストや利用量の予算を設定し、しきい値通知やアクションを行うサービス。

## 109. AWS Cost Explorer

正式名称: AWS Cost Explorer
意味: 過去・現在のコストと利用量を期間、サービス、アカウントなどで分析する機能。

## 110. Savings Plans

正式名称: AWS Savings Plans
意味: 一定の利用コミットメントに対して対象計算利用の料金割引を受ける購入モデル。適用範囲は種類ごとに異なる。

## 111. リザーブドインスタンス

正式名称: Amazon EC2 Reserved Instances
意味: 条件・期間へのコミットメントでEC2利用料金の割引を受けるモデル。予約したサーバーそのものを保持する機能ではない。

## 112. スポットインスタンス

正式名称: Amazon EC2 Spot Instances
意味: AWSの未使用EC2容量を割引で利用するモデル。中断され得るため中断耐性のある処理向け。

## 113. AWS Amplify

正式名称: AWS Amplify
意味: ウェブ・モバイルアプリの認証、API、データ、ホスティングなどの開発を簡略化するツール・サービス群。

## 114. Amazon Lightsail

正式名称: Amazon Lightsail
意味: 仮想サーバー、マネージドデータベース、ネットワークなどを予測しやすい構成で始める簡易クラウドサービス。

## 115. AWS Backup

正式名称: AWS Backup
意味: 対応AWSサービスのバックアップを一元的に設定、保護、監査するサービス。バックアップがあれば復旧目標を満たすとは限らない。

## 116. 災害復旧

正式名称: disaster recovery (DR)
意味: 障害・災害で利用不能になったシステムを別資源や別リージョンで復旧する計画と実装。

## 117. 復旧時間目標

正式名称: Recovery Time Objective (RTO)
意味: 障害発生からサービスを復旧させるまで許容する時間。

## 118. 復旧時点目標

正式名称: Recovery Point Objective (RPO)
意味: 障害時に失ってよいデータの時間幅。

## 119. 高可用性

正式名称: high availability (HA)
意味: 障害が起きてもサービス提供を継続しやすくする構成。Multi-AZ DB instance deploymentのスタンバイは通常読み取り接続を受けない。一方、Multi-AZ DB clusterには読み取り可能なスタンバイがあるため、構成種別を区別する。

## 120. アクティブ・パッシブ

正式名称: active/passive disaster recovery
意味: 通常は現用側を使い、障害時に待機側へ切り替える復旧方式。

## 121. フェイルオーバー

正式名称: failover
意味: 障害時に処理先を待機系などへ切り替えること。切替時間やデータ損失は設計による。

## 122. オブザーバビリティ

正式名称: observability
意味: メトリクス、ログ、トレースなどから内部状態や原因を推定できる性質。

## 123. サービスクォータ

正式名称: AWS service quotas
意味: アカウントやリージョンごとの利用上限。設計前に確認し、引き上げ可能性も別途確認する。

## 124. AWSアカウント

正式名称: AWS account
意味: AWS利用の請求・資源・権限の境界。組織では複数アカウントを分離して管理する。

## 125. 組織単位

正式名称: organizational unit (OU)
意味: AWS Organizationsでアカウントをまとめ、ポリシーを適用する階層単位。

## 126. タグ

正式名称: AWS resource tag
意味: キーと値のメタデータ。所有者、環境、コスト配分などの識別に使う。

## 127. AWS Management Console

正式名称: AWS Management Console
意味: ブラウザーからAWS資源を操作するウェブ画面。

## 128. AWS Command Line Interface

正式名称: AWS Command Line Interface (AWS CLI)
意味: コマンドラインからAWS APIを呼び出すツール。

## 129. AWS SDK

正式名称: AWS Software Development Kit (AWS SDK)
意味: アプリケーションからAWSサービスを呼び出す言語別ライブラリ群。

## 130. 可用性

正式名称: availability
意味: 必要な時にサービスが利用できる性質。稼働率だけでなく復旧設計も関係する。

## 131. 耐障害性

正式名称: fault tolerance
意味: 部品の障害が起きても機能を継続できる性質。冗長化だけでなく切替設計を含む。

## 132. スケーラビリティ

正式名称: scalability
意味: 負荷やデータ量の増加に合わせて処理能力を拡張できる性質。

## 133. 水平スケーリング

正式名称: horizontal scaling
意味: サーバーやタスクの台数を増減して処理能力を変える方式。

## 134. 垂直スケーリング

正式名称: vertical scaling
意味: 1台のCPU、メモリなどを大きくして処理能力を変える方式。

## 135. サーバーレス

正式名称: serverless
意味: 利用者がサーバーのプロビジョニングや運用を直接管理せず、実行量などに応じてサービスを利用する方式。サーバーが存在しない意味ではない。

## 136. マネージドサービス

正式名称: managed service
意味: AWSが基盤の一部を運用し、利用者の管理負担を減らすサービス。設定、データ、権限はなお利用者責任になり得る。

## 137. Amazon EC2スナップショット

正式名称: Amazon EBS snapshot
意味: Amazon EBSボリュームのポイントインタイムバックアップ。復元時間やリージョン複製は別途設計する。

## 138. 起動テンプレート

正式名称: Amazon EC2 launch template
意味: EC2起動時のAMI、インスタンスタイプ、ネットワークなどの設定を再利用可能にする定義。

## 139. ターゲットグループ

正式名称: Elastic Load Balancing target group
意味: ロードバランサーがヘルスチェックと転送の対象にするインスタンス、IP、Lambdaなどの集合。

## 140. ヘルスチェック

正式名称: health check
意味: ターゲットやサービスが要求を処理できるかを定期的に確認する検査。

## 141. Amazon ECRイメージ

正式名称: Amazon Elastic Container Registry image
意味: コンテナ実行に必要なファイルをまとめた不変の成果物。タグ運用だけに依存せずダイジェストも考慮する。

## 142. ECSタスク

正式名称: Amazon ECS task
意味: ECSで1つ以上のコンテナを定義どおりに実行する単位。

## 143. Kubernetesポッド

正式名称: Kubernetes Pod
意味: Kubernetesで1つ以上の密接に連携するコンテナをまとめる最小実行単位。

## 144. S3マルチパートアップロード

正式名称: Amazon S3 multipart upload
意味: 大きなオブジェクトを複数部品に分けてアップロードする方式。中断した未完了部品の管理が必要。

## 145. S3オブジェクトロック

正式名称: S3 Object Lock
意味: 一定期間または無期限にオブジェクトの上書き・削除を防ぐ機能。規制対応のWORM用途に使う。

## 146. Amazon RDS自動バックアップ

正式名称: Amazon RDS automated backups
意味: 設定した保持期間内のバックアップやポイントインタイム復元を提供する機能。保持条件はエンジン等で異なる。

## 147. Amazon Auroraクラスター

正式名称: Amazon Aurora DB cluster
意味: 共有ストレージを使うAuroraのライター・リーダー構成。接続先やフェイルオーバー設計を確認する。

## 148. DynamoDBオンデマンド

正式名称: DynamoDB on-demand capacity mode
意味: キャパシティを事前にプロビジョニングせず、リクエストに応じて処理能力を管理するモード。料金条件は現行表を確認する。

## 149. DynamoDBプロビジョンド容量

正式名称: DynamoDB provisioned capacity mode
意味: 読み取り・書き込みキャパシティを設定し、必要なら自動スケーリングするモード。

## 150. Amazon CloudFrontオリジン

正式名称: Amazon CloudFront origin
意味: CloudFrontがコンテンツを取得するS3バケットやHTTPサーバーなどの元サービス。

## 151. AWS WAFウェブACL

正式名称: AWS WAF web access control list (web ACL)
意味: ウェブ要求を許可・ブロック・カウントするルールをまとめた設定。

## 152. AWS KMSカスタマーマネージドキー

正式名称: AWS KMS customer managed key
意味: 利用者がポリシー、ローテーション、無効化などを管理するKMS鍵。

## 153. SQS可視性タイムアウト

正式名称: Amazon SQS visibility timeout
意味: 受信中のメッセージを他の受信者から一時的に見えなくする期間。処理失敗時の再配信設計に関係する。

## 154. SNSトピック

正式名称: Amazon SNS topic
意味: 発行者がメッセージを送信し、複数の購読先へ配信する論理チャネル。

## 155. EventBridgeルール

正式名称: Amazon EventBridge rule
意味: イベントパターンまたはスケジュールに一致したイベントをターゲットへ送る設定。

## 156. CloudWatchメトリクス

正式名称: Amazon CloudWatch metric
意味: CPU使用率やエラー数などを時系列の数値として観測するデータ。

## 157. CloudTrail証跡

正式名称: AWS CloudTrail trail
意味: 指定したリージョンやイベントをログファイルとしてS3などへ継続配信する設定。

## 158. CloudFormationスタック

正式名称: AWS CloudFormation stack
意味: テンプレートから作られた関連資源の管理単位。削除時の保持設定に注意する。

## 159. AWS Pricing Calculator

正式名称: AWS Pricing Calculator
意味: 想定構成と利用量から料金見積もりを作るウェブツール。見積もりは実請求額を保証しない。

## 160. AWS Free Tier

正式名称: AWS Free Tier
意味: 条件付きで一部利用が無料または割引になる制度。対象、期間、リージョン、超過料金は現行公式情報を確認し、無条件の無料とは扱わない。

## 略語索引

|略語|正式名称|関連項目|
|---|---|---|
|AWS|Amazon Web Services|Amazon Web Services|
|AZ|Availability Zone|アベイラビリティーゾーン|
|IAM|Identity and Access Management|AWS Identity and Access Management|
|JSON|JavaScript Object Notation|JavaScript Object Notation|
|ARN|Amazon Resource Name|Amazon Resource Name|
|MFA|multi-factor authentication|多要素認証|
|VPC|Virtual Private Cloud|仮想プライベートクラウド|
|CIDR|Classless Inter-Domain Routing|CIDR|
|IGW|internet gateway|インターネットゲートウェイ|
|NAT|Network Address Translation|NATゲートウェイ|
|SG|security group|セキュリティグループ|
|NACL|network access control list|ネットワークアクセスコントロールリスト|
|DNS|Domain Name System|ドメインネームシステム|
|TLS|Transport Layer Security|Transport Layer Security|
|KMS|Key Management Service|AWS Key Management Service|
|SCP|service control policy|サービスコントロールポリシー|
|EBS|Elastic Block Store|Amazon Elastic Block Store|
|EFS|Elastic File System|Amazon Elastic File System|
|AMI|Amazon Machine Image|Amazon Machine Image|
|EC2|Elastic Compute Cloud|Amazon Elastic Compute Cloud|
|ALB|Application Load Balancer|Application Load Balancer|
|NLB|Network Load Balancer|Network Load Balancer|
|ELB|Elastic Load Balancing|Elastic Load Balancing|
|RDS|Relational Database Service|Amazon Relational Database Service|
|SQS|Simple Queue Service|Amazon Simple Queue Service|
|SNS|Simple Notification Service|Amazon Simple Notification Service|
|API|Application Programming Interface|Amazon API Gateway|
|CDK|Cloud Development Kit|AWS Cloud Development Kit|
|IaC|Infrastructure as Code|Infrastructure as Code|
|DR|disaster recovery|災害復旧|
|RTO|Recovery Time Objective|復旧時間目標|
|RPO|Recovery Point Objective|復旧時点目標|
|HA|high availability|高可用性|
