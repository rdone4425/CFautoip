import json
import time
import requests
import subprocess

# 从本地文件读取配置
with open("/root/CFautoip/config.json", "r", encoding='utf-8') as file:
    config_data = json.load(file)

# 从配置数据中提取值
auth_email = config_data["auth_email"]
auth_key = config_data["auth_key"]
zone_name = config_data["zone_name"]
record_name = config_data["record_name"]
set_url_config = config_data["set_url_config"]
record_count = config_data["record_count"]  # 从配置文件中读取record_count的值
record_type = config_data["record_type"]

def fastwork():
    print('从 https://api.ipify.org 获取公共 IP 地址')
    ip_data = subprocess.check_output(['curl', 'https://api.ipify.org?format=json']).decode('utf-8')
    ip_list = [json.loads(ip_data)["ip"]]
    print(ip_list)
    return ip_list

def get_current_dns_ip(zone_identifier, record_name_with_count):
    response = requests.get(
        f"https://api.cloudflare.com/client/v4/zones/{zone_identifier}/dns_records?type={record_type}&name={record_name_with_count}",
        headers={
            "X-Auth-Email": auth_email,
            "X-Auth-Key": auth_key,
            "Content-Type": "application/json"
        })
    record_data = response.json()

    if "result" in record_data and len(record_data["result"]) > 0:
        return record_data["result"][0]["content"]
    else:
        return None

def create_dns_record(zone_identifier, record_name_with_count, ip_address):
    payload = {
        "type": record_type,
        "name": record_name_with_count,
        "content": ip_address,
        "ttl": 60,
        "proxied": False
    }
    response = requests.post(
        f"https://api.cloudflare.com/client/v4/zones/{zone_identifier}/dns_records",
        headers={
            "X-Auth-Email": auth_email,
            "X-Auth-Key": auth_key,
            "Content-Type": "application/json"
        }, json=payload)
    result = response.json()
    return result

if __name__ == '__main__':
    if set_url_config == 2:
        ip_list = fastwork()
    else:
        raise RuntimeError('请输入正确set_url_config配置')

    # 获取到的公共 IP 地址在 ip_list 中
    public_ip = ip_list[0]  # 这里假设你只关心第一个 IP 地址

    print(f"你的IP地址是：{public_ip}")
    print("欢迎关注telegram：https://t.me/notetoday")
    response = requests.get(f"https://api.cloudflare.com/client/v4/zones?name={zone_name}", headers={
        "X-Auth-Email": auth_email,
        "X-Auth-Key": auth_key,
        "Content-Type": "application/json"
    })
    zone_data = response.json()

    if "result" in zone_data and len(zone_data["result"]) > 0:
        zone_identifier = zone_data["result"][0]["id"]
        print(f"zone_id: {zone_identifier}")
    else:
        print("未找到匹配的区域")
        exit(1)

    # 处理同一 BGP 前缀下的 DNS 记录，使用不同的 IP 地址
    if record_count == 0:
        # 更新或创建前缀记录
        response = requests.get(
            f"https://api.cloudflare.com/client/v4/zones/{zone_identifier}/dns_records?type={record_type}&name={record_name}.{zone_name}",
            headers={
                "X-Auth-Email": auth_email,
                "X-Auth-Key": auth_key,
                "Content-Type": "application/json"
            })
        prefix_record_data = response.json()
        if "result" in prefix_record_data and len(prefix_record_data["result"]) > 0:
            # 前缀记录存在，更新 IP 地址
            prefix_record_id = prefix_record_data["result"][0]["id"]
            current_dns_ip = get_current_dns_ip(zone_identifier, f"{record_name}.{zone_name}")
            if current_dns_ip is None or current_dns_ip != ip_list[0]:
                # 如果记录不存在或 IP 不一致，执行更新操作
                payload = {
                    "type": record_type,
                    "name": f"{record_name}.{zone_name}",
                    "content": ip_list[0],  # 使用列表中的第一个IP地址
                    "ttl": 60,
                    "proxied": False
                }
                response = requests.put(
                    f"https://api.cloudflare.com/client/v4/zones/{zone_identifier}/dns_records/{prefix_record_id}",
                    headers={
                        "X-Auth-Email": auth_email,
                        "X-Auth-Key": auth_key,
                        "Content-Type": "application/json"
                    }, json=payload)
                result = response.json()
                print(f"{record_name}.{zone_name}域名地址更新为: {ip_list[0]}")
                print(f"更新结果：{result.get('success')}")
            else:
                print(f"{record_name}.{zone_name}域名地址与当前记录一致，无需更新")
        else:
            # 前缀记录不存在，创建新记录
            result = create_dns_record(zone_identifier, f"{record_name}.{zone_name}", ip_list[0])
            if result.get('success'):
                print(f"成功创建新的DNS记录: {record_name}.{zone_name}，IP地址为: {ip_list[0]}")
    else:
        for i in range(1, record_count + 1):  # 处理从1到record_count的记录
            record_name_with_count = f"{record_name}{i}.{zone_name}"

            response = requests.get(
                f"https://api.cloudflare.com/client/v4/zones/{zone_identifier}/dns_records?name={record_name_with_count}",
                headers={
                    "X-Auth-Email": auth_email,
                    "X-Auth-Key": auth_key,
                    "Content-Type": "application/json"
                })
            record_data = response.json()

            if "result" in record_data and len(record_data["result"]) > 0:
                record_id = record_data["result"][0]["id"]
                # 获取当前 DNS 记录的 IP 地址
                current_dns_ip = get_current_dns_ip(zone_identifier, record_name_with_count)
                if current_dns_ip is None or current_dns_ip != ip_list[i - 1]:
                    # 如果记录不存在或 IP 不一致，执行更新操作
                    payload = {
                        "type": record_type,
                        "name": record_name_with_count,
                        "content": ip_list[i - 1],  # 使用列表中的对应IP地址
                        "ttl": 60,
                        "proxied": False
                    }
                    response = requests.put(
                        f"https://api.cloudflare.com/client/v4/zones/{zone_identifier}/dns_records/{record_id}",
                        headers={
                            "X-Auth-Email": auth_email,
                            "X-Auth-Key": auth_key,
                            "Content-Type": "application/json"
                        }, json=payload)
                    result = response.json()
                    print(f"{record_name_with_count}域名地址更新为: {ip_list[i - 1]}")
                    print(f"更新结果：{result.get('success')}")
                else:
                    print(f"{record_name_with_count}域名地址与当前记录一致，无需更新")
            else:
                # 如果记录不存在，创建新记录
                result = create_dns_record(zone_identifier, record_name_with_count, ip_list[i - 1])
                if result.get('success'):
                    print(f"成功创建新的DNS记录: {record_name_with_count}，IP地址为: {ip_list[i - 1]}")

    print("处理完成。10秒自动关闭")
    time.sleep(10)
