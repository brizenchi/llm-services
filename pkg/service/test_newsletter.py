import sys
from pathlib import Path
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict
import json
import re

# 设置项目根目录到 Python 路径
project_root = str(Path(__file__).parent.parent.parent.absolute())
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 现在导入项目模块
from pkg.repository.user_newsletter_repository import UserNewsletterRepository
from pkg.repository.user_folders_repository import UserFoldersRepository
from pkg.repository.user_repository import UserRepository
from pkg.constants.newsletter import LANGUAGE_MAP
from pkg.service.newsletter import NewsletterService

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 配置 SQL 日志
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
logging.getLogger('sqlalchemy.pool').setLevel(logging.DEBUG)
logging.getLogger('sqlalchemy.dialects.mysql').setLevel(logging.INFO)

logger = logging.getLogger(__name__)

# 模拟文章数据
MOCK_PASSAGES = [
    {
        "id": 1,
        "title": "AI 技术突破：新型语言模型超越人类表现",
        "description": "最新研究显示，新一代AI模型在多项测试中超越人类水平",
        "content": """
        <p>在最新的研究中，研究人员开发的新一代语言模型在多个基准测试中取得突破性进展。
        该模型不仅在传统的语言理解任务上表现出色，还在推理和创造性任务中展现出惊人的能力。
        然而，部分专家对此持谨慎态度，认为仍需要更多实际应用验证。</p>
        """,
        "category": "技术创新",
        "source": "科技日报",
        "publish_time": "2024-03-15 10:00:00"
    },
    {
        "id": 2,
        "title": "全球气候变化加速，各国加强减排承诺",
        "description": "最新气候报告显示全球变暖速度超预期，各国承诺加强减排措施",
        "content": """
        <p>联合国最新气候报告指出，全球平均气温上升速度较此前预测更快。
        报告显示，若不采取更严格的减排措施，到2050年全球温升可能超过2°C。</p>
        """,
        "category": "环境",
        "source": "环球时报",
        "publish_time": "2024-03-14 14:30:00"
    }
]

async def test_generate_html_report():
    languages = LANGUAGE_MAP.keys()
    folder_ids = range(1, 9)  # 1 to 6
    start_date = datetime(2025, 3, 13)
    end_date = datetime.now()
    service = NewsletterService()

    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.strftime("%Y-%m-%d")
        
        for language in languages:
            for folder_id in folder_ids:
                logger.info(f"Generating report for date: {date_str}, language: {language}, folder: {folder_id}")
                try:
                    await service.generate_html_report(
                        language=language,
                        folder_id=folder_id,
                        date=date_str
                    )
                except Exception as e:
                    logger.error(f"Error generating report: {str(e)}")
                    
        current_date += timedelta(days=1)
        
async def test_generate_wechat_report():
    languages = ["zh"]
    service = NewsletterService()
    for language in languages:
        formated_text = await service.generate_wechat_report(language=language, date="2025-05-22")
        print(formated_text)

async def test_generate_text_report():
    languages = ["zh"]
    folder_ids = range(1, 9)  # 1 to 6
    start_date = datetime(2025, 4, 27)
    end_date = datetime(2025, 4, 27)
    service = NewsletterService()

    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.strftime("%Y-%m-%d")
        
        for language in languages:
            for folder_id in folder_ids:
                logger.info(f"Generating report for date: {date_str}, language: {language}, folder: {folder_id}")
                try:
                    await service.generate_text_report(
                        language=language,
                        folder_id=folder_id,
                        date=date_str
                    )
                except Exception as e:
                    logger.error(f"Error generating report: {str(e)}")
                    
        current_date += timedelta(days=1)

async def test_batch_generate_newsletter():
    date = datetime.now().strftime("%Y-%m-%d")
    service = NewsletterService()
    user_newsletter_repository = UserNewsletterRepository()
    user_folders_repository = UserFoldersRepository()
    user_repository = UserRepository()
    members = await user_repository.fetch_newsletter_members()
    
    for member in members:
        user_newsletter = await user_newsletter_repository.fetch_user_newsletter(member['id'])
        if not user_newsletter:
            logger.info(f"Skipping member {member['id']} - no newsletter settings found")
            continue
            
        folder_list = await user_folders_repository.fetch_user_folders(member['id'])
        folder_ids = [folder['folder_id'] for folder in folder_list]
        # 确保 user_newsletter 是字典类型
        if isinstance(user_newsletter, list):
            if len(user_newsletter) > 0:
                user_newsletter = user_newsletter[0]
            else:
                logger.info(f"Skipping member {member['id']} - empty newsletter settings")
                continue
                
        await service.generate_newsletter(
            language=user_newsletter['language'],
            date=date,
            folder_ids=folder_ids,
            batch_size=1000,
            email=member['email']
        )

async def test_newsletter_service():
    """测试 NewsletterService"""
    try:
        logger.info("开始测试 NewsletterService...")
        
        # 创建服务实例
        service = NewsletterService()
        # 替换为 mock repository
        
        # 测试处理新闻简报
        # Loop through dates from March 8 to April 17
       
        report = await service.generate_newsletter(
            "zh",
            batch_size=1000, 
            date="2025-06-13",
            folder_ids=[1,2,3,4,5,6,7,8],
            email="kuniseichi@gmail.com"
        )
            
        # 验证结果
        assert report is not None
        
        logger.info(f"生成的报告长度: {len(report)} 字符")
        logger.info("报告预览:")
        logger.info("-" * 50)
        logger.info(report[:500] + "...")
        logger.info("-" * 50)
        
        logger.info("测试完成!")
        return report
        
    except Exception as e:
        logger.error(f"测试失败: {e}", exc_info=True)
        raise



response = '''```json
{
  "key": "This is a "test" string"
}
```'''


if __name__ == "__main__":
    # 运行测试
    asyncio.run(test_newsletter_service())


