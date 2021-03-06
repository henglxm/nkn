import boto3
import json
import sys
import time
import os
import base64
from dotenv import load_dotenv

load_dotenv(verbose=True)


def main():
    """TODO: Docstring for main.
    :returns: TODO

    """
    access = os.getenv('AWS_ACCESS_KEY')
    secret = os.getenv('AWS_SECRET_ACCESS')
    count = int(os.getenv('AWS_LAUNCH_COUNT'))
    instane_type = os.getenv('INSTANCE_TYPE')
    region = os.getenv('AWS_REGION')
    ami = os.getenv('AWS_AMI')
    nkn_path = os.getenv('ARM_NKN_PATH')
    wallet = os.getenv('WALLET')

    print('钱包地址 : ' + wallet)
    print('钱包地址 : ' + wallet)
    print('钱包地址 : ' + wallet)
    print("")

    param = None
    try:
        param = sys.argv[1] if sys.argv[1] else None
    except Exception as e:
        pass
    if param and param == 'getip':
        get_ip(access=access, secret=secret, region=region)
        return False
    if param and param == 'init':
        instane_type = os.getenv('INIT_TYPE')
        ami = os.getenv('INIT_AMI')
        nkn_path = os.getenv('AMD_NKN_PATH')
        count = 1
        f = open("init.txt", "r+")
        lines = f.readlines()
        i = 1
        for line in lines:
            access = line[0:line.find(' ')]
            secret = line[line.find(' ') + 1:].strip('\n')
            group_id = create_security_group(access=access,
                                             secret=secret,
                                             region=region)
            client = boto3.client('ec2',
                                  aws_access_key_id=access,
                                  aws_secret_access_key=secret,
                                  region_name=region)
            subnets = client.describe_subnets()
            instances = create_instances(
                group_id=group_id,
                access=access,
                secret=secret,
                count=count,
                instane_type=instane_type,
                region=region,
                nkn_path=nkn_path,
                wallet=wallet,
                subnet_id=subnets['Subnets'][1]['SubnetId'],
                ami=ami)
            for instance in instances:
                print('请等待3秒...')
                time.sleep(3)
                desc = client.describe_instances(Filters=[
                    {
                        'Name': 'instance-type',
                        'Values': [
                            instane_type,
                        ]
                    },
                ])
                for ins in desc['Reservations'][0]['Instances']:
                    print(
                        str(i) + '   ' + region + '   ' + '   ' +
                        ins['InstanceId'] + '   ' + ins['PublicIpAddress'] +
                        '   ' + ins['InstanceType'] + '   ' +
                        str(ins['LaunchTime']))
            i = i + 1
        return False

    if param and param == 'termination':
        termination(access=access, secret=secret, region=region)
        return False

    for param in sys.argv:
        if param.find('--') != -1 and param[0:2] == '--' and param.find(
                '=') != -1:
            key = param[2:param.find('=')].strip()
            value = param[param.find('=') + 1:].strip()
            if key == 'access':
                access = value
            if key == 'secret':
                secret = value
            if key == 'count':
                count = value
            if key == 'type':
                instane_type = value
            if key == 'region':
                region = value
            if key == 'ami':
                ami = value

    f = open("apikey.txt", "r+")
    lines = f.readlines()
    i = 1
    for line in lines:
        access = line[0:line.find(' ')]
        secret = line[line.find(' ') + 1:].strip('\n')
        print(access + ' ... ' + secret)
        client = boto3.client('ec2',
                              aws_access_key_id=access,
                              aws_secret_access_key=secret,
                              region_name=region)
        subnets = client.describe_subnets()
        group_id = create_security_group(access=access,
                                         secret=secret,
                                         region=region)
        instances = create_instances(
            group_id=group_id,
            access=access,
            secret=secret,
            count=count,
            instane_type=instane_type,
            region=region,
            nkn_path=nkn_path,
            wallet=wallet,
            subnet_id=subnets['Subnets'][1]['SubnetId'],
            ami=ami)
        print('ec2 created')
        time.sleep(30)
        client = boto3.client('ec2',
                              aws_access_key_id=access,
                              aws_secret_access_key=secret,
                              region_name=region)
        desc = client.describe_instances(Filters=[
            {
                'Name': 'instance-type',
                'Values': [
                    instane_type,
                ]
            },
        ])
        for ins in desc['Reservations'][0]['Instances']:
            print(
                str(i) + '   ' + region + '   ' + '   ' + ins['InstanceId'] +
                '   ' + ins['PublicIpAddress'] + '   ' + ins['InstanceType'] +
                '   ' + str(ins['LaunchTime']))
            i = i + 1
    print('==========================')


def create_security_group(access, secret, region):
    """TODO: Docstring for create_security_group.
    :arg1: TODO
    :returns: TODO
    """
    # print('创建安全组...')
    client = boto3.client('ec2',
                          aws_access_key_id=access,
                          aws_secret_access_key=secret,
                          region_name=region)
    security_group = client.create_security_group(GroupName='nkn' +
                                                  str(time.time()),
                                                  Description="nkn")
    client.authorize_security_group_ingress(CidrIp='0.0.0.0/0',
                                            IpProtocol='tcp',
                                            FromPort=0,
                                            ToPort=65535,
                                            GroupId=security_group['GroupId'])
    group_id = security_group['GroupId']
    # print('安全组创建成功, ID ： ' + group_id)
    return group_id


def create_instances(group_id, access, secret, count, instane_type, region,
                     nkn_path, ami, subnet_id, wallet):
    """TODO: Docstring for create_instance.
    :returns: TODO

    """
    # print('创建ec2 ... ： ')

    ec2 = boto3.resource('ec2',
                         aws_access_key_id=access,
                         aws_secret_access_key=secret,
                         region_name=region)
    instances = ec2.create_instances(ImageId=ami,
                                     InstanceType=instane_type,
                                     MaxCount=int(count),
                                     MinCount=int(count),
                                     Monitoring={'Enabled': False},
                                     SecurityGroupIds=[group_id],
                                     SubnetId=subnet_id,
                                     UserData=get_user_data(nkn_path, wallet))
    # InstanceMarketOptions={
    # 'MarketType': 'spot',
    # 'SpotOptions': {
    # 'SpotInstanceType': 'persistent',
    # 'InstanceInterruptionBehavior':
    # 'stop'
    # }
    # })
    # print('ec2 创建成功')
    return instances


def get_user_data(nkn_path, wallet):
    """TODO: Docstring for get_user_data.
    :returns: TODO

    """
    userdata = """#!/bin/bash
sleep 2m
sudo -i
systemctl stop nkn-commercial
cd %(nkn_path)s
rm wallet.json
rm wallet.pswd
echo 123123 | sudo tee wallet.pswd
./nknc wallet -c --password=123123
cd ../../
./nkn-commercial -b %(wallet)s install"""

    userdata = userdata % dict(nkn_path=nkn_path, wallet=wallet)

    bytestring = userdata.encode(encoding='utf-8')
    return base64.encodebytes(bytestring)


def termination(access, secret, region):
    f = open("termination.txt", "r+")
    lines = f.readlines()
    ids = ""
    i = 1
    for line in lines:
        ec2 = boto3.resource('ec2',
                             aws_access_key_id=access,
                             aws_secret_access_key=secret,
                             region_name=region)
        instance = ec2.Instance(line.rstrip('\n'))
        print(instance.terminate())


def get_ip(access, secret, region):
    """TODO: Docstring for get_ip.
    :returns: TODO

    """
    f = open("ids.txt", "r+")
    lines = f.readlines()
    ids = ""
    i = 1
    for line in lines:
        ids = line.rstrip('\n')
        client = boto3.client('ec2',
                              aws_access_key_id=access,
                              aws_secret_access_key=secret,
                              region_name=region)
        desc = client.describe_instances(InstanceIds=[ids])
        ids = []
        for instance in desc['Reservations']:
            print(
                str(i) + '   ' + region + '   ' + '   ' +
                instance['Instances'][0]['InstanceId'] + '   ' +
                instance['Instances'][0]['PublicIpAddress'] + '   ' +
                instance['Instances'][0]['InstanceType'] + '   ' +
                str(instance['Instances'][0]['LaunchTime']))
            i = i + 1


if __name__ == "__main__":
    proxy = os.getenv('PROXY')
    if proxy is not None:
        os.environ["HTTP_PROXY"] = proxy
        os.environ["HTTPS_PROXY"] = proxy

    main()
