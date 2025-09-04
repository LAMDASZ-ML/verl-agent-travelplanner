import sys
import time
import requests
import subprocess

url = "https://box.nju.edu.cn/api/v2.1/via-repo-token/download-link/?path=%2Ftest_model.zip"

headers = {
    "accept": "application/json",
    "authorization": "Token 6f52999c420787e9ea3bfd2e8aff17cf31daddca",
}

response = requests.get(url, headers=headers)

download_link_str = response.text
print(download_link_str)
time.sleep(3)  # 等待1秒，确保输出被打印
# 根据下载链接下载文件并计时
start_time = time.time()


# wget时传入token
token = "6f52999c420787e9ea3bfd2e8aff17cf31daddca"
output_file = "test_model.zip"
cmd = [
    "wget",
    f"--header=Authorization: Token {token}",
    "-O",
    output_file,
    download_link_str,  # URL 放在最后，避免和参数冲突
]

cmd = " ".join(cmd)  # 将命令列表转换为字符串
subprocess.run(cmd, check=True, shell=True)
end_time = time.time()
download_time = end_time - start_time
print(f"Download completed in {download_time:.2f} seconds.")
