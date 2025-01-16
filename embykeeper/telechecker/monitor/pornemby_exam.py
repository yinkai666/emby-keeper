import asyncio
from io import BytesIO
import random
import re

import httpx
from pyrogram.types import Message
from PIL import Image
import numpy as np

from embykeeper.utils import show_exception

from ..lock import pornemby_alert
from ._base import Monitor

class _PornembyExamResultMonitor(Monitor):
    name = "Pornemby 科举答案"
    chat_keyword = r"问题\d*：(.*?)\n+答案为：([ABCD])\n+([A-Z-\d]+)"
    additional_auth = ["pornemby_pack"]
    allow_edit = True

    async def on_trigger(self, message: Message, key, reply):
        self.log.info(f"本题正确答案为 {key[1]} ({key[2]}).")

class _PornembyExamAnswerMonitor(Monitor):
    name = "Pornemby 科举"
    chat_user = [
        "pornemby_question_bot",
        "PronembyTGBot2_bot",
        "PronembyTGBot3_bot",
        "PornembyBot",
        "Porn_Emby_Bot",
        "Porn_Emby_Script",
    ]
    chat_keyword = r"问题\d*：根据以上封面图，猜猜是什么番号？"
    additional_auth = ["pornemby_pack"]
    
    async def get_cover_image(self, code: str):
        # 先获取 content_id
        detail_url = f"https://r18.dev/videos/vod/movies/detail/-/dvd_id={code.lower()}/json"
        try:
            if self.proxy:
                proxy = f"{self.proxy['scheme']}://"
                if self.proxy.get("username"):
                    proxy += f"{self.proxy['username']}:{self.proxy['password']}@"
                proxy += f"{self.proxy['hostname']}:{self.proxy['port']}"
            else:
                proxy = None
            # 使用 httpx 创建异步客户端
            async with httpx.AsyncClient(
                http2=True,
                proxy=proxy,
                verify=False,
                follow_redirects=True,
            ) as client:
                # 获取 content_id
                response = await client.get(detail_url)
                if response.status_code != 200:
                    self.log.warning(f"获取影片详情失败: 网址访问错误: {detail_url} ({response.status_code}).")
                    return None
                detail_json = response.json()
                content_id = detail_json.get('content_id')
                if not content_id:
                    self.log.warning(f"获取影片详情失败: 无法获取 content_id: {detail_url}")
                    return None
                
                # 获取封面图片 URL
                combined_url = f"https://r18.dev/videos/vod/movies/detail/-/combined={content_id}/json"
                response = await client.get(combined_url)
                if response.status_code != 200:
                    self.log.warning(f"获取封面详情失败: 网址访问错误: {combined_url} ({response.status_code}).")
                    return None
                combined_json = response.json()
                jacket_url = combined_json.get('jacket_thumb_url')
                if not jacket_url:
                    self.log.warning(f"获取封面详情失败: 无法获取封面URL: {combined_url}")
                    return None
                
                # 下载封面图片
                img_response = await client.get(jacket_url)
                if img_response.status_code == 200:
                    return BytesIO(img_response.content)
                else:
                    self.log.warning(f"获取封面图片失败: 网址访问错误: {jacket_url} ({img_response.status_code}).")
                    return None
                
        except Exception as e:
            self.log.warning(f"获取封面图片失败: {e.__class__.__name__}: {str(e)}")
            show_exception(e)
            return None

    def compare_images(self, img1_bytes: BytesIO, img2_bytes: BytesIO) -> float:
        try:
            img1 = Image.open(img1_bytes).convert('RGB').resize((100, 100))
            img2 = Image.open(img2_bytes).convert('RGB').resize((100, 100))
            
            arr1 = np.array(img1)
            arr2 = np.array(img2)
            mse = np.mean((arr1 - arr2) ** 2)
            
            similarity = 1 / (1 + mse)
            return similarity
        except Exception as e:
            self.log.debug(f"图片比较失败: {e}")
            return 0

    async def on_trigger(self, message: Message, key, reply):
        if not message.photo or not message.reply_markup:
            return
        if pornemby_alert.get(self.client.me.id, False):
            self.log.info(f"由于风险急停不作答.")
            return
        if random.random() > self.config.get("possibility", 1.0):
            self.log.info(f"由于概率设置不作答.")
            return
        
        question_photo = await message.download(in_memory=True)
        
        codes = []
        for row in message.reply_markup.inline_keyboard:
            for button in row:
                if button.text:
                    codes.append(button.text)
                    
        async def get_cover_with_timeout(code):
            try:
                return code, await asyncio.wait_for(self.get_cover_image(code), timeout=10)
            except (asyncio.TimeoutError, Exception) as e:
                self.log.debug(f"获取 {code} 封面超时或失败")
                return code, None
        
        cover_tasks = [get_cover_with_timeout(code) for code in codes]
        covers = await asyncio.gather(*cover_tasks)
        max_similarity = -1
        best_code = None
        for code, cover in covers:
            if cover is None:
                continue
            question_photo.seek(0)
            cover.seek(0)
            similarity = self.compare_images(question_photo, cover)
            self.log.debug(f"番号 {code} 相似度: {similarity:.4f}")
            if similarity > max_similarity:
                max_similarity = similarity
                best_code = code
        if best_code:
            self.log.info(f"选择相似度最高的番号: {best_code} (相似度: {max_similarity:.4f})")
            for row in message.reply_markup.inline_keyboard:
                for button in row:
                    if button.text == best_code:
                        await message.click(button.text)
                        return
        else:
            self.log.warning("未找到匹配的封面图片")

class PornembyExamMonitor:
    class PornembyExamResultMonitor(_PornembyExamResultMonitor):
        chat_name = "Pornemby"

    class PornembyExamAnswerMonitor(_PornembyExamAnswerMonitor):
        chat_name = "Pornemby"
