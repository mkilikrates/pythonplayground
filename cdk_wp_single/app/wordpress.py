import os
from aws_cdk import (
    Duration,
    RemovalPolicy,
    Stack,
    CfnOutput,
    Fn,
    cloudformation_include,
    aws_s3 as s3,
    aws_kms as kms,
    aws_ec2 as ec2,
    aws_rds as rds,
    aws_efs as efs,
    aws_ecr_assets as ecr_assets,
    aws_ecs as ecs,
    aws_logs as log,
    aws_iam as iam,
    aws_elasticloadbalancingv2 as elbv2,
    # aws_sqs as sqs,
)
from constructs import Construct

class WordpressStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # KMS
        qualifier = os.getenv('WORDPRESS_QUALIFIER')
        region = os.getenv('AWS_REGION')
        db_user = os.getenv('WORDPRESS_DB_USER')
        myipv4 = os.getenv('MY_IPv4') # export MY_IPv4=$(curl -4 ifconfig.co/)
        # myipv6 = os.getenv('MY_IPv6') # export MY_IPv6=$(curl -6 ifconfig.co/)
        self.kms_key = kms.Key(
            scope=self,
            id=f"KMS{qualifier}",
            alias=qualifier,
            description=f"Wordpress {qualifier}",
            enabled=True,
            enable_key_rotation=True,
            key_usage=kms.KeyUsage.ENCRYPT_DECRYPT,
            key_spec=kms.KeySpec.SYMMETRIC_DEFAULT,
            pending_window=Duration.days(7)
        )
        CfnOutput(
            scope=self,
            id=f"KMSARN{qualifier}",
            value=self.kms_key.key_arn
        )

        self.bucket = s3.Bucket(
            scope=self, 
            id=f"BUCKET{qualifier}",
            bucket_name=f"{qualifier}",
            access_control=s3.BucketAccessControl.BUCKET_OWNER_FULL_CONTROL,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            encryption=s3.BucketEncryption.KMS,
            encryption_key=self.kms_key,
            enforce_ssl=True,
            bucket_key_enabled=True,
            object_ownership=s3.ObjectOwnership.BUCKET_OWNER_ENFORCED,
            public_read_access=False,
            versioned=False
        )
        CfnOutput(
            scope=self,
            id=f"BUCKETNAME{qualifier}",
            value=self.bucket.bucket_name
        )

        # import default vpc
        self.vpc = ec2.Vpc.from_lookup(
            scope=self,
            id='DEFAULT-VPC',
            is_default=True
        )
        CfnOutput(
            scope=self,
            id=f"VPCID{qualifier}",
            value=self.vpc.vpc_id
        )
        azlist = self.vpc.availability_zones
        i = 256
        self.privsublst = []
        for az in azlist:
            i = i - 1
            privsub=ec2.PrivateSubnet(
                scope=self, 
                id=f"PrivSubnet{az}",
                availability_zone=az,
                cidr_block=Fn.select(
                    i,
                    Fn.cidr(
                        ip_block=self.vpc.vpc_cidr_block,
                        count=256,
                        size_mask="8"
                    )
                ),
                vpc_id=self.vpc.vpc_id,
                map_public_ip_on_launch=False
            )
            self.privsublst.append(privsub)
        
        #
        # log for db
        #
        self.kms_key.grant_encrypt_decrypt(iam.ServicePrincipal(f"logs.{region}.amazonaws.com"))
        dblog_group=log.LogGroup(
            scope=self,
            id=f"{qualifier}WPServerlessLogs",
            log_group_name="/aws/rds/cluster/wpserverlessdb/error",
            retention=log.RetentionDays.ONE_WEEK,
            encryption_key=self.kms_key,
            removal_policy=RemovalPolicy.DESTROY
        )
        dblog_group.grant_write((iam.ServicePrincipal(f"logs.{region}.amazonaws.com")))

        self.database = rds.ServerlessCluster(
            scope=self, 
            id=f"{qualifier}WPServerlessDB",
            engine=rds.DatabaseClusterEngine.AURORA_MYSQL,
            cluster_identifier="wpserverlessdb",
            default_database_name=f"{qualifier}DB",
            vpc=self.vpc,
            vpc_subnets=ec2.SubnetSelection(subnets=self.privsublst),#ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_ISOLATED, one_per_az=True),
            scaling=rds.ServerlessScalingOptions(
                auto_pause=Duration.minutes(10)
            ),
            deletion_protection=True,
            backup_retention=Duration.days(7),
            removal_policy=RemovalPolicy.DESTROY,
            credentials=rds.Credentials.from_generated_secret(
                username=db_user,
                secret_name=f"{qualifier}WPServerlessDBSecret",
                encryption_key=self.kms_key
            ),
            storage_encryption_key=self.kms_key
        )
        self.database.node.add_dependency(dblog_group)

        CfnOutput(
            scope=self,
            id=f"{qualifier}WPServerlessClusterName",
            value=self.database.cluster_identifier
        )
        CfnOutput(
            scope=self,
            id=f"{qualifier}WPServerlessClusterEndpoing",
            value=self.database.cluster_endpoint.hostname
        )
        CfnOutput(
            scope=self,
            id=f"{qualifier}WPServerlessDBSecretPath",
            value=self.database.secret.secret_name
        )

        self.file_system = efs.FileSystem(
            scope=self, 
            id=f"{qualifier}WProotFS",
            vpc=self.vpc,
            performance_mode=efs.PerformanceMode.GENERAL_PURPOSE,
            throughput_mode=efs.ThroughputMode.BURSTING,
            kms_key=self.kms_key,
            vpc_subnets=ec2.SubnetSelection(subnets=self.privsublst),#ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_ISOLATED, one_per_az=True),
            encrypted=True,
            file_system_policy=iam.PolicyDocument(
                statements=[
                    iam.PolicyStatement(
                        actions=[
                            "elasticfilesystem:ClientWrite", 
                            "elasticfilesystem:ClientMount",
                            "elasticfilesystem:DescribeMountTargets"
                        ],
                        effect=iam.Effect.ALLOW,
                        principals=[iam.AnyPrincipal()],
                        resources=["*"],
                        conditions={
                            "Bool": {
                                "elasticfilesystem:AccessedViaMountTarget": "true"
                            },
                            "StringEquals": {
                                "aws:SourceAccount" : f"{os.getenv('AWS_ACCOUNT')}"
                            }
                        }
                    )
                ]
            )
        )
        fsaccesspoint= self.file_system.add_access_point(f"{qualifier}WPAccessPoint")

        # docker context directory
        docker_context_path = os.path.dirname(__file__) + "../../src"

        # upload images to ecr
        nginx_image = ecr_assets.DockerImageAsset(
            scope=self, 
            id=f"{qualifier}Nginx",
            asset_name=f"{qualifier}Nginx",
            directory=docker_context_path,
            file="Docker.nginx",
        )

        wordpress_image = ecr_assets.DockerImageAsset(
            scope=self, 
            id=f"{qualifier}WP",
            asset_name=f"{qualifier}WP",
            directory=docker_context_path,
            file="Docker.wordpress",
        )

        #
        # log for db
        #
        ecsexeclog_group=log.LogGroup(
            scope=self,
            id=f"{qualifier}ECSClusterExecLogs",
            log_group_name="ECSClusterExecLogs",
            retention=log.RetentionDays.ONE_WEEK,
            encryption_key=self.kms_key,
            removal_policy=RemovalPolicy.DESTROY
        )
        ecsexeclog_group.grant_write((iam.ServicePrincipal(f"logs.{region}.amazonaws.com")))

        self.cluster = ecs.Cluster(
            scope=self, 
            id='ComputeResourceProvider',
            vpc=self.vpc,
            enable_fargate_capacity_providers=True,
            execute_command_configuration=ecs.ExecuteCommandConfiguration(
                kms_key=self.kms_key,
                log_configuration=ecs.ExecuteCommandLogConfiguration(
                    cloud_watch_log_group=ecsexeclog_group,
                    cloud_watch_encryption_enabled=True,
                    s3_bucket=self.bucket,
                    s3_encryption_enabled=True,
                    s3_key_prefix="exec-command-output"
                ),
                logging=ecs.ExecuteCommandLogging.OVERRIDE
            )
        )

        wordpress_volume = ecs.Volume(
            name=f"{qualifier}WProot",
            efs_volume_configuration=ecs.EfsVolumeConfiguration(
                file_system_id=self.file_system.file_system_id,
                transit_encryption="ENABLED",
                authorization_config=ecs.AuthorizationConfig(
                    access_point_id=fsaccesspoint.access_point_id,
                    iam="ENABLED"
                )
            )
        )

        task_role = iam.Role(
            self,
            f"TaskRole-{qualifier}-Wordpress",
            role_name=f"{qualifier}WordpressTaskRole",
            assumed_by=iam.ServicePrincipal(
                "ecs-tasks.amazonaws.com"
            ),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AmazonECSTaskExecutionRolePolicy"
                ),
            ]
        )

        event_task = ecs.FargateTaskDefinition(
            self, 
            f"{qualifier}WordpressTask",
            volumes=[wordpress_volume],
            task_role=task_role
        )

        #
        # grant access to kms key used on secrets, logs, db and s3
        #
        self.kms_key.grant_encrypt_decrypt(task_role)
        task_exec_role = event_task.obtain_execution_role()
        self.kms_key.grant_encrypt_decrypt(task_exec_role)
        self.bucket.grant_read_write(
            identity=task_exec_role,
            objects_key_pattern=[
                f"{qualifier}WProot/",
                f"{self.bucket.bucket_arn}/{qualifier}WProot/*"
            ]
        )
        self.file_system.grant_read_write(event_task.task_role)

        #
        # logs
        #
        log_group=log.LogGroup(
            self,
            f"{qualifier}WPLogs",
            log_group_name=f"{qualifier}WP",
            retention=log.RetentionDays.ONE_WEEK,
            encryption_key=self.kms_key,
            removal_policy=RemovalPolicy.DESTROY
        )

        #
        # webserver
        #
        nginx_container = event_task.add_container(
            "Nginx",
            image=ecs.ContainerImage.from_docker_image_asset(nginx_image),
            logging=ecs.LogDrivers.aws_logs(
                mode=ecs.AwsLogDriverMode.NON_BLOCKING,
                log_group=log_group,
                stream_prefix='nginx'
            )
        )

        nginx_container.add_port_mappings(
            ecs.PortMapping(container_port=80)
        )

        nginx_container_volume_mount_point = ecs.MountPoint(
            read_only=True,
            container_path="/var/www/html",
            source_volume=wordpress_volume.name
        )
        nginx_container.add_mount_points(nginx_container_volume_mount_point)

        #
        # application server
        #
        app_container = event_task.add_container(
            "Php",
            environment={
                'WORDPRESS_DB_HOST': self.database.cluster_endpoint.hostname,
                'WORDPRESS_TABLE_PREFIX': 'wp_'
            },
            secrets={
                'WORDPRESS_DB_USER':
                    ecs.Secret.from_secrets_manager(self.database.secret, field="username"),
                'WORDPRESS_DB_PASSWORD':
                    ecs.Secret.from_secrets_manager(self.database.secret, field="password"),
                'WORDPRESS_DB_NAME':
                    ecs.Secret.from_secrets_manager(self.database.secret, field="dbname"),
            },
            image=ecs.ContainerImage.from_docker_image_asset(wordpress_image),
            logging=ecs.LogDrivers.aws_logs(
                mode=ecs.AwsLogDriverMode.NON_BLOCKING,
                log_group=log_group,
                stream_prefix='wordpress'
            )
        )
        app_container.add_port_mappings(
            ecs.PortMapping(container_port=9000)
        )

        container_volume_mount_point = ecs.MountPoint(
            read_only=False,
            container_path="/var/www/html",
            source_volume=wordpress_volume.name
        )
        app_container.add_mount_points(container_volume_mount_point)

        #
        # create service
        #
        self.wordpress_service = ecs.FargateService(
            self, f"{qualifier}WPService",
            task_definition=event_task,
            platform_version=ecs.FargatePlatformVersion.VERSION1_4,
            cluster=self.cluster,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC, one_per_az=True),
            assign_public_ip=True
        )
        #
        # scaling
        #
        scaling = self.wordpress_service.auto_scale_task_count(
            min_capacity=1,
            max_capacity=5
        )
        scaling.scale_on_cpu_utilization(
            "CpuScaling",
            target_utilization_percent=85,
            scale_in_cooldown=Duration.seconds(120),
            scale_out_cooldown=Duration.seconds(30),
        )

        #
        # ALB
        #
        self.load_balancer = elbv2.ApplicationLoadBalancer(
            self, "ExternalEndpoint",
            vpc=self.vpc,
            internet_facing=True,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
        )

        CfnOutput(
            self, "ExternalLBDNSName",
            value=self.load_balancer.load_balancer_dns_name
        )

        #
        # security groups update
        #
        self.database.connections.allow_default_port_from(self.wordpress_service, f"wordpress {qualifier} access to db")
        self.file_system.connections.allow_default_port_from(self.wordpress_service)

        #
        # access from ALB to Service
        #
        self.wordpress_service.connections.allow_from(
            other=self.load_balancer,
            port_range=ec2.Port.tcp(80)
        )

        http_listener = self.load_balancer.add_listener(
            "HttpListener",
            port=80,
            open=False
        )

        http_listener.add_targets(
            f"{qualifier}HttpServiceTarget",
            protocol=elbv2.ApplicationProtocol.HTTP,
            targets=[self.wordpress_service],
            health_check=elbv2.HealthCheck(healthy_http_codes="200,301,302")
        )
        #
        # access from Internet to ALB
        #
        http_listener.connections.allow_default_port_from(
            other=ec2.Peer.ipv4(f"{myipv4}/32"),
            description="Internet access from my ipv4"
        )

        self.host = ec2.BastionHostLinux(
            scope = self,
            id = f"Bastion{qualifier}",
            vpc = self.vpc,
            subnet_selection=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
            instance_type=ec2.InstanceType.of(
                instance_class=ec2.InstanceClass.BURSTABLE3,
                instance_size=ec2.InstanceSize.MICRO
            ),
            machine_image=ec2.MachineImage.latest_amazon_linux2(
                edition=ec2.AmazonLinuxEdition.STANDARD,
            ),
            block_devices=[
                ec2.BlockDevice(
                    device_name="/dev/xvda",
                    volume=ec2.BlockDeviceVolume.ebs(
                        volume_size=10,
                        encrypted=True,
                        volume_type=ec2.EbsDeviceVolumeType.GP3,
                        kms_key=self.kms_key,
                        delete_on_termination=True,
                    ),
                )
            ],
        )
        self.host.instance.role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name(
                "AmazonSSMManagedInstanceCore"
            )
        )
        self.host.instance.role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name(
                "AmazonSSMPatchAssociation"
            )
        )
        self.host.instance.role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name(
                "AdministratorAccess"
            )
        )
        self.file_system.connections.allow_default_port_from(self.host)
        self.host.instance.user_data.add_commands(
            "yum check-update -y",
            "yum upgrade -y",
            "yum install -y amazon-efs-utils",
            "yum install -y nfs-utils",
            "file_system_id_1=" + self.file_system.file_system_id,
            "efs_mount_point_1=/mnt/efs/fs1", "mkdir -p \"${efs_mount_point_1}\"",
            "test -f \"/sbin/mount.efs\" && echo \"${file_system_id_1}:/ ${efs_mount_point_1} efs defaults,_netdev,tls,iam\" >> /etc/fstab || \" + \"echo \"${file_system_id_1}.efs." + region + ".amazonaws.com:/ ${efs_mount_point_1} nfs4 nfsvers=4.1,rsize=1048576,wsize=1048576,hard,timeo=600,retrans=2,noresvport,_netdev 0 0\" >> /etc/fstab",
            "mount -a -t efs,nfs4 defaults"
        )

        http_listener.connections.allow_default_port_from(self.host)
        self.database.connections.allow_default_port_from(self.host)

        self.bucket.grant_read_write(
            identity=self.host.instance.role,
            objects_key_pattern=[
                f"{self.bucket.bucket_arn}/*"
            ]
        )
        self.file_system.grant_read_write(self.host.instance.role)
