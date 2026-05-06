"""
stitcher.py — 图片纵向拼接模块

将指定文件夹内的图片按文件名排序后，从上到下拼接成一张长图。
典型用途：拼接聊天记录截图。
"""

import os
import logging
from typing import Optional, List

from PIL import Image

logger = logging.getLogger(__name__)

# 支持打开的图像扩展名（小写）
IMAGE_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".bmp",
    ".gif",
    ".tiff",
    ".tif",
    ".webp",
}


def _is_image_file(filename: str) -> bool:
    """检查文件名是否为支持的图片格式"""
    _, ext = os.path.splitext(filename)
    return ext.lower() in IMAGE_EXTENSIONS


def _normalize_image(img: Image.Image) -> Image.Image:
    """
    将图像统一为 RGB 模式。

    - RGBA / PA：用 alpha 通道与白色背景合成，保留视觉内容。
    - P / 其他非 RGB：直接转换。
    """
    if img.mode in ("RGBA", "PA"):
        if img.mode == "PA":
            img = img.convert("RGBA")
        background = Image.new("RGB", img.size, (255, 255, 255))
        background.paste(img, mask=img.getchannel("A"))
        return background
    elif img.mode == "P":
        return img.convert("RGB")
    elif img.mode != "RGB":
        return img.convert("RGB")
    return img


def stitch_folder(
    folder_path: str,
    output_path: Optional[str] = None,
    *,
    common_width: Optional[int] = None,
    align: str = "center",
    background_color: str = "white",
) -> str:
    """
    将 *folder_path* 目录下所有图片按文件名排序后纵向拼接为一张长图。

    Parameters
    ----------
    folder_path : str
        存放待拼接图片的文件夹路径。
    output_path : str, optional
        输出文件路径。若为 None，自动在 *folder_path* 同级目录下生成
        ``{folder_name}_stitched.png``。
    common_width : int, optional
        统一宽度（像素）。若为 None，则使用所有图片中的最大宽度。
    align : str, optional
        对齐方式：``"center"``（居中）、``"left"``（左对齐）、
        ``"right"``（右对齐）。默认 ``"center"``。
    background_color : str, optional
        拼接时填充空白区域的颜色，默认为 ``"white"``。

    Returns
    -------
    str
        输出文件的绝对路径。

    Raises
    ------
    FileNotFoundError
        *folder_path* 不存在。
    ValueError
        文件夹中没有可识别的图片文件，或 *align* 参数无效。
    """
    if not os.path.isdir(folder_path):
        raise FileNotFoundError(f"文件夹不存在: {folder_path}")

    _ALIGN_OPTIONS = ("left", "center", "right")
    if align not in _ALIGN_OPTIONS:
        raise ValueError(f"align 必须是 {_ALIGN_OPTIONS} 之一，收到: {align!r}")

    # 收集所有图片文件，按文件名排序
    filenames = sorted(
        f for f in os.listdir(folder_path)
        if _is_image_file(f)
    )

    if not filenames:
        raise ValueError(f"文件夹 '{folder_path}' 中没有找到支持的图片文件。"
                         f" 支持: {', '.join(sorted(IMAGE_EXTENSIONS))}")

    logger.info("找到 %d 个图片文件: %s", len(filenames), filenames)

    # 打开所有图片，统一模式
    images: List[Image.Image] = []
    for fn in filenames:
        path = os.path.join(folder_path, fn)
        try:
            img = Image.open(path)
            img = _normalize_image(img)
            images.append(img)
        except Exception as exc:
            logger.warning("跳过文件 '%s': %s", fn, exc)

    if not images:
        raise ValueError(f"无法打开 '{folder_path}' 中的任何图像文件。")

    # 确定统一宽度
    if common_width is None:
        common_width = max(img.width for img in images)

    # 计算总高度
    total_height = sum(img.height for img in images)

    # 创建空白画布
    canvas = Image.new("RGB", (common_width, total_height), background_color)

    # 偏移映射表（align 已在入口校验过）
    _x_offsets = {
        "left":   0,
        "center": lambda cw, iw: (cw - iw) // 2,
        "right":  lambda cw, iw: cw - iw,
    }

    # 逐张粘贴
    y_offset = 0
    for img in images:
        x_offset = _x_offsets[align]
        x_val = x_offset(common_width, img.width) if callable(x_offset) else x_offset
        canvas.paste(img, (x_val, y_offset))
        y_offset += img.height

    # 确定输出路径
    if output_path is None:
        folder_basename = os.path.basename(os.path.normpath(folder_path))
        output_path = os.path.join(
            os.path.dirname(os.path.abspath(folder_path)),
            f"{folder_basename}_stitched.png",
        )

    # 确保目录存在
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    canvas.save(output_path)
    logger.info("拼接完成，已保存至: %s", output_path)

    return os.path.abspath(output_path)
