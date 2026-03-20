# 抖音视频下载器

一个基于 Python 的抖音视频下载工具，支持从抖音链接中提取视频并提供下载功能。

## 功能特性

- 支持抖音短链接和完整链接
- 自动解析短链接
- 优先选择高清 HD 版本下载
- 支持自定义输出目录
- 生成视频信息描述文件
- 提供下载进度条
- 包含网络请求重试机制
- 详细的日志记录

## 依赖项

- Python 3.6+
- requests
- beautifulsoup4
- tqdm

## 安装依赖

使用 `requirements.txt` 文件安装依赖：

```bash
pip install -r requirements.txt
```

## 使用方法

### 基本用法

```bash
python douyin_downloader.py <抖音视频链接>
```

### 指定输出目录

```bash
python douyin_downloader.py <抖音视频链接> --output <输出目录路径>
# 或
python douyin_downloader.py <抖音视频链接> -o <输出目录路径>
```

## 示例

### 下载抖音视频到默认目录

```bash
python douyin_downloader.py https://v.douyin.com/KqkNll9Dn3g/
```

### 下载抖音视频到指定目录

```bash
python douyin_downloader.py https://v.douyin.com/KqkNll9Dn3g/ --output D:\Downloads
```

## 输出文件

程序会在指定的输出目录下创建以下文件：

- `output/<视频ID>/<视频ID>.mp4` - 下载的视频文件
- `output/<视频ID>/<视频ID>_info.json` - 视频信息描述文件，包含标题、时长、视频ID、原始链接等信息

## 视频信息描述文件格式

```json
{
  "title": "视频标题",
  "duration": "视频时长",
  "tiktok_id": "视频ID",
  "original_url": "原始抖音链接"
}
```

## 注意事项

- 本工具仅用于个人学习和研究，请勿用于商业用途
- 请遵守抖音平台的相关规定
- 视频下载速度取决于网络状况
- 部分视频可能因版权或其他原因无法下载

## 故障排除

- **网络请求错误**：可能是网络连接问题，程序会自动重试 3 次
- **未找到视频数据**：可能是链接无效或视频已被删除
- **未找到合适的视频下载链接**：可能是网站结构变更，需要更新代码

## 许可证

MIT
