import requests
from bs4 import BeautifulSoup
import json
import os
import re
import logging
from tqdm import tqdm
from urllib.parse import urlparse, parse_qs

def setup_logger():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger

logger = setup_logger()

def validate_douyin_url(url):
    pattern = r'https?://(www\.)?douyin\.com/video/\d+|https?://v\.douyin\.com/[a-zA-Z0-9]+'
    return re.match(pattern, url) is not None

def download_douyin_video(douyin_url, output_dir=os.getcwd()):
    try:
        # 验证抖音链接
        if not validate_douyin_url(douyin_url):
            logger.error("无效的抖音视频链接")
            return False
        
        # 解析短链接
        if "v.douyin.com" in douyin_url:
            logger.info(f"解析短链接: {douyin_url}")
            response = requests.get(douyin_url, allow_redirects=True, timeout=10)
            douyin_url = response.url
            logger.info(f"解析后的链接: {douyin_url}")
        
        # 发送请求到 TikVideo API
        api_url = "https://tikvideo.app/api/ajaxSearch"
        data = {
            "q": douyin_url,
            "lang": "zh-cn",
            "cftoken": ""
        }
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Origin": "https://tikvideo.app",
            "Referer": "https://tikvideo.app/zh-cn/download-douyin-video",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36 Edg/146.0.0.0",
            "X-Requested-With": "XMLHttpRequest"
        }
        
        logger.info(f"发送请求到 TikVideo API: {api_url}")
        response = requests.post(api_url, data=data, headers=headers, timeout=30)
        response.raise_for_status()
        response_json = response.json()
        
        if response_json.get("status") != "ok":
            logger.error("API 请求失败")
            return False
        
        # 解析 HTML 内容
        html_content = response_json.get("data", "")
        soup = BeautifulSoup(html_content, "html.parser")
        
        # 提取视频信息
        video_data = soup.find("div", class_="video-data")
        if not video_data:
            logger.error("未找到视频数据")
            return False
        
        # 提取标题和时长
        title = video_data.find("h3").text.strip()
        duration = video_data.find("p").text.strip()
        
        # 提取封面图
        thumbnail = video_data.find("img").get("src")
        
        # 提取下载链接
        download_links = []
        dl_actions = video_data.find_all("a", class_="tik-button-dl")
        for link in dl_actions:
            href = link.get("href")
            text = link.text.strip()
            download_links.append({"text": text, "url": href})
        
        # 提取视频 ID
        tiktok_id = soup.find("input", id="TikTokId").get("value")
        
        # 生成输出目录
        output_dir = os.path.join(output_dir, "output", tiktok_id)
        os.makedirs(output_dir, exist_ok=True)
        
        # 保存视频信息到描述文件
        video_info = {
            "title": title,
            "duration": duration,
            "thumbnail": thumbnail,
            "download_links": download_links,
            "tiktok_id": tiktok_id,
            "original_url": douyin_url
        }
        
        info_file = os.path.join(output_dir, f"{tiktok_id}_info.json")
        with open(info_file, "w", encoding="utf-8") as f:
            json.dump(video_info, f, ensure_ascii=False, indent=2)
        logger.info(f"视频信息已保存到: {info_file}")
        
        # 下载视频
        # 优先选择高清HD版本的下载链接
        video_url = None
        # 先查找高清版本
        for link in download_links:
            if "HD" in link["text"] or "hd" in link["text"]:
                video_url = link["url"]
                logger.info("选择高清HD版本下载链接")
                break
        # 如果没有高清版本，选择直接的视频下载链接
        if not video_url:
            for link in download_links:
                if any(domain in link["url"] for domain in ["douyinvod.com", "zjcdn.com"]):
                    video_url = link["url"]
                    logger.info("选择标准清晰度版本下载链接")
                    break
        
        if not video_url:
            logger.error("未找到合适的视频下载链接")
            return False
        
        # 下载视频文件
        video_filename = os.path.join(output_dir, f"{tiktok_id}.mp4")
        logger.info(f"开始下载视频: {title}")
        logger.info(f"视频链接: {video_url}")
        
        # 下载视频并显示进度条，添加重试机制
        max_retries = 3
        for retry in range(max_retries):
            try:
                # 发送请求并获取视频大小
                video_response = requests.get(video_url, stream=True, timeout=60)
                video_response.raise_for_status()
                total_size = int(video_response.headers.get('content-length', 0))
                
                # 下载视频并显示进度条
                with open(video_filename, "wb") as f:
                    with tqdm(total=total_size, unit='B', unit_scale=True, unit_divisor=1024, desc=title) as pbar:
                        for chunk in video_response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                                pbar.update(len(chunk))
                break
            except requests.exceptions.RequestException as e:
                logger.warning(f"下载失败，尝试重试 ({retry+1}/{max_retries}): {str(e)}")
                if retry == max_retries - 1:
                    logger.error(f"下载失败，已达到最大重试次数: {str(e)}")
                    return False
        
        logger.info(f"视频下载完成: {video_filename}")
        
        return True
    
    except requests.exceptions.RequestException as e:
        logger.error(f"网络请求错误: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"发生错误: {str(e)}")
        return False

import argparse

def get_video_info(douyin_url):
    try:
        # 验证抖音链接
        if not validate_douyin_url(douyin_url):
            logger.error("无效的抖音视频链接")
            return None
        
        # 解析短链接
        if "v.douyin.com" in douyin_url:
            logger.info(f"解析短链接: {douyin_url}")
            response = requests.get(douyin_url, allow_redirects=True, timeout=10)
            douyin_url = response.url
            logger.info(f"解析后的链接: {douyin_url}")
        
        # 发送请求到 TikVideo API
        api_url = "https://tikvideo.app/api/ajaxSearch"
        data = {
            "q": douyin_url,
            "lang": "zh-cn",
            "cftoken": ""
        }
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Origin": "https://tikvideo.app",
            "Referer": "https://tikvideo.app/zh-cn/download-douyin-video",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36 Edg/146.0.0.0",
            "X-Requested-With": "XMLHttpRequest"
        }
        
        logger.info(f"发送请求到 TikVideo API: {api_url}")
        response = requests.post(api_url, data=data, headers=headers, timeout=30)
        response.raise_for_status()
        response_json = response.json()
        
        logger.info(f"API 响应状态: {response_json.get('status')}")
        logger.info(f"API 响应数据长度: {len(response_json.get('data', ''))}")
        
        if response_json.get("status") != "ok":
            logger.error(f"API 请求失败: {response_json.get('msg', '未知错误')}")
            return None
        
        # 解析 HTML 内容
        html_content = response_json.get("data", "")
        soup = BeautifulSoup(html_content, "html.parser")
        
        # 提取视频信息
        video_data = soup.find("div", class_="video-data")
        if not video_data:
            # 尝试查找其他可能的视频数据容器
            alternative_containers = ["video-info", "download-container", "content"]
            for container in alternative_containers:
                video_data = soup.find("div", class_=container)
                if video_data:
                    logger.info(f"找到替代视频数据容器: {container}")
                    break
            
            if not video_data:
                logger.error("未找到视频数据")
                # 打印部分 HTML 内容以便调试
                logger.debug(f"HTML 内容预览: {html_content[:500]}...")
                return None
        
        # 提取标题和时长
        title = video_data.find("h3").text.strip()
        duration = video_data.find("p").text.strip()
        
        # 提取封面图
        thumbnail = video_data.find("img").get("src")
        
        # 提取视频 ID
        tiktok_id = soup.find("input", id="TikTokId").get("value")
        
        # 构建视频信息
        video_info = {
            "title": title,
            "duration": duration,
            "thumbnail": thumbnail,
            "tiktok_id": tiktok_id,
            "original_url": douyin_url
        }
        
        # 打印视频信息
        logger.info("\n视频信息:")
        logger.info(f"标题: {title}")
        logger.info(f"时长: {duration}")
        logger.info(f"视频ID: {tiktok_id}")
        logger.info(f"封面图: {thumbnail}")
        
        return video_info
    
    except requests.exceptions.RequestException as e:
        logger.error(f"网络请求错误: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"发生错误: {str(e)}")
        return None



def save_video_info_to_md(video_info, output_file):
    """将视频信息保存到 Markdown 文件"""
    try:
        # 构建 Markdown 内容
        md_content = f"# 抖音视频信息\n\n"
        
        # 添加标题
        md_content += f"## 标题\n{video_info.get('title', '')}\n\n"
        
        # 添加视频信息
        md_content += f"## 视频信息\n"
        md_content += f"- 视频ID: {video_info.get('tiktok_id', '')}\n"
        md_content += f"- 时长: {video_info.get('duration', '')}\n"
        md_content += f"- 原始链接: [{video_info.get('original_url', '')}]({video_info.get('original_url', '')})\n\n"
        
        # 保存封面图到本地
        local_thumbnail_path = None
        if video_info.get('thumbnail'):
            # 获取输出目录
            directory = os.path.dirname(output_file)
            if not directory:
                directory = os.getcwd()
            
            # 创建输出目录
            os.makedirs(directory, exist_ok=True)
            
            # 生成封面图文件名
            thumbnail_filename = f"{video_info.get('tiktok_id', 'thumbnail')}_cover.jpg"
            local_thumbnail_path = os.path.join(directory, thumbnail_filename)
            
            # 下载封面图
            logger.info(f"开始下载封面图: {video_info.get('thumbnail')}")
            try:
                response = requests.get(video_info.get('thumbnail'), timeout=30)
                response.raise_for_status()
                with open(local_thumbnail_path, 'wb') as f:
                    f.write(response.content)
                logger.info(f"封面图已保存到: {local_thumbnail_path}")
            except Exception as e:
                logger.warning(f"下载封面图失败: {str(e)}")
                local_thumbnail_path = None
        
        # 添加封面图
        if local_thumbnail_path:
            # 使用相对路径指向本地封面图
            relative_thumbnail_path = os.path.basename(local_thumbnail_path)
            md_content += f"## 封面图\n![封面图]({relative_thumbnail_path})\n\n"
        elif video_info.get('thumbnail'):
            # 如果下载失败，仍使用原始链接
            md_content += f"## 封面图\n![封面图]({video_info.get('thumbnail')})\n\n"
        
        # 保存到文件
        directory = os.path.dirname(output_file)
        if directory:
            os.makedirs(directory, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        logger.info(f"视频信息已保存到 Markdown 文件: {output_file}")
        return True
    except Exception as e:
        logger.error(f"保存 Markdown 文件时发生错误: {str(e)}")
        return False

if __name__ == "__main__":
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="抖音视频下载器")
    parser.add_argument("url", help="抖音视频链接")
    parser.add_argument("--output", "-o", default=os.getcwd(), help="输出目录，默认为当前工作目录")
    parser.add_argument("--info", action="store_true", help="仅获取视频信息，不下载视频")
    parser.add_argument("--output-md", help="将视频信息输出到指定的 Markdown 文件")
    args = parser.parse_args()
    
    # 根据参数执行相应操作
    if args.info:
        video_info = get_video_info(args.url)
        if video_info and args.output_md:
            save_video_info_to_md(video_info, args.output_md)
    else:
        download_douyin_video(args.url, args.output)