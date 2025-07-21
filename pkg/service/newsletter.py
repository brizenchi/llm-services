import logging
from typing import List, Dict, Any
from pkg.repository.passage_repository import PassageRepository
from pkg.repository.passage_summaries_repository import PassageSummariesRepository
from pkg.repository.folder_summaries_repository import FolderSummariesRepository
from pkg.repository.folder_views_repository import FolderViewsRepository
from pkg.core.mailer.mail_factory import EmailFactory
from pkg.repository.folders import FoldersRepository
from pkg.repository.newsletter_logs import NewsletterLogsRepository
from pkg.constants.newsletter import REFLECTION_MAP, LANGUAGE_MAP

from pkg.repository.newsletter_html import NewsletterHtmlRepository
from pkg.repository.newsletter_text import NewsletterTextRepository
from pkg.repository.newsletter_wechat import NewsletterWechatRepository
import re
from collections import Counter
from datetime import datetime
import json
import asyncio
from pkg.core.llm.llm_aggrator import LLMAggrator
logger = logging.getLogger(__name__)

class NewsletterService:
    def __init__(self):
        # 获取不同数据源的实例
        self.passage_repo = PassageRepository()
        self.passage_summaries_repo = PassageSummariesRepository()
        self.folder_summaries_repo = FolderSummariesRepository()
        self.folder_views_repo = FolderViewsRepository()
        self.email_client = EmailFactory.get_instance()
        self.newsletter_logs_repo = NewsletterLogsRepository()
        self.newsletter_text_repo = NewsletterTextRepository()
        self.newsletter_html_repo = NewsletterHtmlRepository()
        self.newsletter_wechat_repo = NewsletterWechatRepository()
        self.llm_aggrator = LLMAggrator()
        self.folders_repo = FoldersRepository()
    
    async def generate_text_report(self, language: str, folder_id: int, date: str = "2025-03-01"):
        if await self.newsletter_text_repo.query_newsletter_text(date, language, folder_id):
            logger.info(f"Found cached newsletter text for {date}")
            return
        summary = await self.folder_summaries_repo.query_summary(language, folder_id, date, date)
        if len(summary) > 0:
            logger.info(f"Found cached summary for folder {folder_id}")
            summary = json.loads(summary[0]['summary'])
        else:
            logger.info(f"No cached summary found, generating new summary for folder {folder_id}")
            passage_list = await self.passage_repo.fetch_passages_by_date(folder_id, 1000, date=date)
            if len(passage_list) == 0:
                logger.info(f"No passages found for folder {folder_id} on date {date}")
                return
            top_news = await self._filter_top_news(folder_id, language=language, passage_list=passage_list, date=date)
            summary = await self._generate_folder_summary(folder_id, language=language, top_news=top_news, passage_list=passage_list, date=date)

        # 生成 HTML 报告
        text_report = await self._format_ai_report_to_text(language,folder_id, summary,date)

        try:
            await self.newsletter_text_repo.save_newsletter_text(date, language, folder_id, text_report)
        except Exception as e:
            logger.error(f"Failed to save newsletter text: {str(e)}")
            raise RuntimeError(f"Error saving newsletter text: {str(e)}") from e

    async def generate_seo_keywords(self,folder_id: str, date: str = "2025-03-01", language: str="en", passage_list: List[Dict[str, Any]]=[]):
        messages = [
    {
        "role": "system",
        "content": f"""You are a seo expert, {language}
"""
    },
    {
        "role": "user",
        "content": f"""
        
Return Format:
{{
    "keywords": ["keyword1","keywords2"]
    "long_tail_keywords":["long_tail_keyword1","long_tail_keyword2"]
}}

Original News:
{passage_list}
"""
    }
]

        # 获取响应并验证JSON格式
        response = await self.llm_aggrator.generate_response(messages)
        
        # 验证JSON格式并返回Python对象
        try:
            pattern = r"```json\s*([\s\S]*?)\s*```"
            match = re.search(pattern, response)
            json_data = {}
            if match:
                json_str = match.group(1).strip()
                # 尝试直接 loads
                try:
                    json_data = json.loads(json_str)
                except json.JSONDecodeError:
                    # 如果失败，尝试去掉多余的转义
                    json_str_fixed = json_str.replace('\\"', '"').replace('\\n', '').replace('\\\\', '\\')
                    json_data = json.loads(json_str_fixed)
                
                # 找到对应的文章并添加link
                passage_dict = {str(p['id']): p for p in passage_list}
                for article in json_data['passageList']:
                    article_id = str(article['id'])
                    if article_id in passage_dict:
                        article['link'] = passage_dict[article_id].get('link', '')
                        article['image_url'] = passage_dict[article_id].get('image_url', '')
                
            await self.folder_summaries_repo.save_summary(language,folder_id,  json.dumps(json_data, ensure_ascii=False, indent=2), date, date)
            return json_data
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON format in response: {e}")
            raise
        except ValueError as e:
            logger.error(f"Validation error: {e}")
            raise

    # async def generate_wechat_summary(self, language: str, folder_id: int, date: str = "2025-03-01"):
    #     """Generate Wechat summary for newsletter content.
    #     """
    #     passage_list = 
    #     top_news = await self._filter_top_news(folder_id, language=language, passage_list=passage_list, date=date)
    #     folder_summary = await self._generate_folder_summary(folder_id, language=language,top_news=top_news, passage_list=passage_list, date=date)
                

    #     return text_report
    
    async def generate_wechat_report(self, language: str, date: str = "2025-03-01"):
        try:
            report = {}
            folder_ids = await self.folders_repo.get_folder_ids(type="wechat")
            for folder_id in folder_ids:
                
                # 获取文章列表
                passage_list = await self.passage_repo.fetch_passages_by_date(folder_id, 1000,date=date)
                if len(passage_list) == 0:
                    continue
                top_news = await self._filter_top_news(folder_id, language=language, passage_list=passage_list, date=date)
                folder_summary = await self._generate_wechat_summary(folder_id, language=language,top_news=top_news, passage_list=passage_list, date=date)
                
                report[folder_id] = {
                    "passage_list": passage_list,
                    "folder_summary": folder_summary,
                    # "viewpoint": viewpoint
                }
            
                await self._format_ai_report_to_wechat(language,folder_id,date,report)
            
        except Exception as e:
            logger.error(f"Error in generate_newsletter: {e}")
            raise
        finally:
            # 确保关闭连接
            try:
                await self.email_client.close()
            except Exception as e:
                logger.error(f"Error closing email client: {e}")

    async def _format_ai_report_to_wechat(self, language: str,folder_id:str, date:str, report: Dict[str, Any]):
        try:
            if await self.newsletter_wechat_repo.query_newsletter_wechat(date, language, folder_id):
                logger.info(f"Found cached newsletter html for {date}")
                return
                
            text = ''
            for folder_id, folder_data in report.items():
                try:
                    folder_summary = folder_data['folder_summary']
                    if 'passageList' in folder_summary:
                        for i, passage in enumerate(folder_summary['passageList'], 1):
                            text += f"{i}、{passage['summary']}\n"
                except KeyError as e:
                    logger.error(f"Missing required key in folder data: {e}")
                    continue
                    
            await self.newsletter_wechat_repo.save_newsletter_wechat(date, language, folder_id, text)
            return text
            
        except Exception as e:
            logger.error(f"Error formatting wechat report: {e}")
            raise
    async def generate_html_report(self, language: str, folder_id: int, date: str = "2025-03-01"):
        """Generate HTML report for newsletter content.
        
        Args:
            language: Language code for the report
            folder_id: ID of the folder to generate report for
            date: Date string in YYYY-MM-DD format
            
        Returns:
            str: Generated HTML report
            
        Raises:
            ValueError: If invalid parameters are provided
            IOError: If there are file system related errors
            RuntimeError: If there are errors generating the report content
        """
        if await self.newsletter_html_repo.query_newsletter_html(date, language, folder_id):
            logger.info(f"Found cached newsletter html for {date}")
            return
        if not language or not folder_id:
            raise ValueError("Language and folder_id are required")

        # 首先获取文章列表
        passage_list = await self.passage_repo.fetch_passages_by_date(folder_id, 1000, date=date)
        if len(passage_list) == 0:
            logger.info(f"No passages found for folder {folder_id} on date {date}")
            return

        # 然后尝试获取或生成摘要
        summary = await self.folder_summaries_repo.query_summary(language, folder_id, date, date)
        if len(summary) > 0:
            logger.info(f"Found cached summary for folder {folder_id}")
            summary = json.loads(summary[0]['summary'])
        else:
            logger.info(f"No cached summary found, generating new summary for folder {folder_id}")
            top_news = await self._filter_top_news(folder_id, language=language, passage_list=passage_list, date=date)
            summary = await self._generate_folder_summary(folder_id, language=language, top_news=top_news, passage_list=passage_list, date=date)

        # 生成 HTML 报告
        
        html_report = self._format_ai_report_to_seo_html(folder_id, date, language, summary, passage_list)

        try:
            await self.newsletter_html_repo.save_newsletter_html(date, language, folder_id, html_report)
        except Exception as e:
            logger.error(f"Failed to save newsletter HTML: {str(e)}")
            raise RuntimeError(f"Error saving newsletter HTML: {str(e)}") from e

        return html_report
    
    async def generate_newsletter(self,language: str, batch_size: int = 1000, date: str = "2025-03-01", folder_ids: List[int] = [], email: str = "kuniseichi@gmail.com"):
        """从多个数据源处理文章并生成专业报告"""
        try:
            report = {}
            if len(folder_ids) == 0:
                folder_ids = await self.folders_repo.get_folder_ids(type="deeper")
            
            # 1. 并发获取所有文件夹的文章列表
            passage_list_tasks = [
                self.passage_repo.fetch_passages_by_date(folder_id, batch_size, date=date)
                for folder_id in folder_ids
            ]
            passage_lists = await asyncio.gather(*passage_list_tasks)
            
            # 过滤掉没有文章的文件夹
            valid_folders = []
            folder_passage_map = {}
            
            for folder_id, passage_list in zip(folder_ids, passage_lists):
                if len(passage_list) > 0:
                    valid_folders.append(folder_id)
                    folder_passage_map[folder_id] = passage_list
                else:
                    logger.info(f"No passages found for folder {folder_id} on date {date}")
            
            if not valid_folders:
                logger.info(f"No content found for any folders on date {date}")
                return
            
            # 2. 并发获取所有有效文件夹的 top_news
            top_news_tasks = [
                self._filter_top_news(
                    folder_id, 
                    language=language, 
                    passage_list=folder_passage_map[folder_id], 
                    date=date
                )
                for folder_id in valid_folders
            ]
            top_news_results = await asyncio.gather(*top_news_tasks)
            
            # 3. 并发获取所有文件夹的 folder_summary
            folder_summary_tasks = [
                self._generate_folder_summary(
                    folder_id,
                    language=language,
                    top_news=top_news,
                    passage_list=folder_passage_map[folder_id],
                    date=date
                )
                for folder_id, top_news in zip(valid_folders, top_news_results)
            ]
            folder_summary_results = await asyncio.gather(*folder_summary_tasks)
            
            # 4. 构建最终报告数据
            for i, folder_id in enumerate(valid_folders):
                report[folder_id] = {
                    "passage_list": folder_passage_map[folder_id],
                    "folder_summary": folder_summary_results[i],
                }
            
            # 5. 使用原有的函数生成 HTML
            html_report = None
            try:
                html_report = self._format_ai_report_to_html(language, report)
            except Exception as e:
                logger.error(f"生成HTML报告失败: {e}")
                return

            # 发送邮件
            max_retries = 3
            retry_count = 0
            
            while retry_count < max_retries:
                try:
                    success = await self.email_client.send_email(
                        to_addrs=[email],
                        subject='Deeper AI Newsletter',
                        body=html_report,
                        html=True
                    )
                    if success:
                        logger.info("Email sent successfully")
                        await self.newsletter_logs_repo.save_newsletter_log(email, "success")
                        break
                    else:
                        retry_count += 1
                        if retry_count < max_retries:
                            logger.warning(f"Failed to send email, retrying ({retry_count}/{max_retries})")
                            await asyncio.sleep(1)  # 等待1秒后重试
                        else:
                            logger.error("Failed to send email after all retries")
                            await self.newsletter_logs_repo.save_newsletter_log(email, "failed")
                            raise Exception("Failed to send email after all retries")
                except Exception as e:
                    retry_count += 1
                    if retry_count < max_retries:
                        logger.warning(f"Error sending email: {e}, retrying ({retry_count}/{max_retries})")
                        await asyncio.sleep(1)  # 等待1秒后重试
                    else:
                        logger.error(f"Error sending email after all retries: {e}")
                        await self.newsletter_logs_repo.save_newsletter_log(email, str(e))
                        raise
            
            return html_report
            
        except Exception as e:
            logger.error(f"Error in generate_newsletter: {e}")
            raise
        finally:
            # 确保关闭连接
            try:
                await self.email_client.close()
            except Exception as e:
                logger.error(f"Error closing email client: {e}")

    async def _generate_single_summary(self) -> str:
        """生成专业报告"""
        try:
            
            MAX_CHARS_PER_PASSAGE = 500  # 单篇最大字符数

            summaries = []
            # Create tasks list for concurrent processing
            tasks = []
            batch_size = 100
            date = datetime.now().strftime("%Y-%m-%d")
            passage_list = []
            for folder_id in range(1, 7):
                passage_list.extend(await self.passage_repo.fetch_unsummaried_passages(folder_id, batch_size,date=date))

            for passage in passage_list:
                
                # total_chars = len(passage['content']) + len(passage['title']) + len(passage['description'])
                passage['content'] = re.sub(r'\n+', '\n', re.sub(r'<[^>]+>', '', passage.get('content', '')))
                passage['description'] = re.sub(r'<[^>]+>', '', passage.get('description', ''))
                
                tasks.append(self._summarize_single_passage(passage, MAX_CHARS_PER_PASSAGE))

            # Wait for all tasks to complete

            results = await asyncio.gather(*tasks)

            summaries.extend(results)
            # 3. 智能分组并递归总结
            # final_summaries = await self._smart_group_summarize(summaries)

            # 4. 生成最终报告
            return results

        except Exception as e:
            logger.error(f"Error in _generate_summary: {e}")
            raise
# Specify response language
    
    async def _summarize_single_passage(self, passage: Dict[str, Any], count: int=500) -> str:
        """Summarize a single article within 500 characters while maintaining cache"""
        try:
            logger.info(f"[Summary]Starting to summarize passage {passage['id']}, max chars: {count}")

            if passage['summary'] is not None and passage['summary'] != '':
                logger.info(f"[Summary]Found cached summary for passage {passage['id']}")
                return passage
            if len(passage['title']+passage['description']+passage['content']) < count:
                summary = passage['title'] + passage['description'] + passage['content']
            else:
                logger.info(f"[Summary]No cached summary for passage {passage['id']}, generating summary")
                system_prompt = f"You are a keyword extraction expert, skilled at distilling article key points. Please keep the summary within {count} characters."
                user_prompt = f"""
                Summarize the article in one word within {count} characters. Extract only facts and data, remove redundant words, and try to explain clearly in one sentence if possible.

                Article Title: {passage['title']}
                Content: {passage['description']}. {passage['content']}
                """
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
                logger.info(f"[Summary]Generating summary for passage {passage['id']}")
                summary = await self.llm_aggrator.generate_response(messages)
                logger.info(f"[Summary]Summary generated for passage {passage['id']}")

            passage["summary"] = summary
            # Save to cache
            logger.info(f"[Summary]Saving summary to cache for passage {passage['id']}")
            await self.passage_summaries_repo.save_summary([passage['id']], summary)
            logger.info(f"[Summary]Successfully saved summary to cache for passage {passage['id']}")
            
            return passage

        except Exception as e:
            logger.error(f"Error in _summarize_single_passage for passage {passage['id']}: {e}")
            raise
    async def _filter_top_news(self, folder_id: str, language: str, passage_list: List[Dict[str, Any]], date: str) -> List[Dict[str, Any]]:
        """生成最终总结，返回JSON格式"""
        try:
            if len(passage_list) == 0:
                return []
            folder_info = await self.folders_repo.get_folder_info(folder_id)
            folder_name = folder_info['name']

            cache_result = await self.folder_summaries_repo.query_summary(language,folder_id, date, date)
            if cache_result and len(cache_result) > 0:
                logger.info(f"Found cached final summary for date {date}")
                return json.loads(cache_result[0]['summary'])
            
            passages_text = '\n\n'.join([
                f"id:{passage['id']}, title:{passage.get('title', '')}."
                for passage in passage_list
            ])

            messages = [
                {"role": "system", "content": """You are a news curator, skilled at consolidating and organizing information from different sources.
"""},
                {"role": "user", "content": f"""
Based on the following news article points, please generate structured data:

Requirements:
1. Return in strict JSON format.
2. Deduplicate content by identifying articles that describe the same event or story, even if worded differently or from different sources. Represent each unique event/story only once.
3. Prioritize the 10 most impactful news stories, based on:
   - Frequency of mentions across sources (higher frequency indicates greater significance).
   - high relevance to {folder_name}
   - {folder_info['filter_prompt']}
4. For each unique event/story, select the article with the most comprehensive or authoritative source, or the one with the clearest title.
5. If multiple sources cover the same event, choose only one representative article to avoid redundancy.
Return Format:
{{
    "passageList": [
        {{
            "id": "Article ID",
            "title": "Article Title",
        }},{{
            "id": "Article ID", 
            "title": "Article Title",
        }}
}}

Original News:
{passages_text}
"""}
            ]

            # 获取响应并验证JSON格式
            response = await self.llm_aggrator.generate_response(messages)
            
            # 验证JSON格式并返回Python对象
            try:
                pattern = r"```json\s*([\s\S]*?)\s*```"
                match = re.search(pattern, response)
                json_data = {}
                if match:
                    json_str = match.group(1)
                    json_data = json.loads(json_str)
                    
                    # 找到对应的文章并添加link
                    passage_dict = {str(p['id']): p for p in passage_list}
                    for article in json_data['passageList']:
                        article_id = str(article['id'])
                        if article_id in passage_dict:
                            article['link'] = passage_dict[article_id].get('link', '')
                            article['image_url'] = passage_dict[article_id].get('image_url', '')
                    
                # await self.folder_summaries_repo.save_summary(language,folder_id,  json.dumps(json_data, ensure_ascii=False, indent=2), date, date)
                return json_data
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON format in response: {e}")
                raise
            except ValueError as e:
                logger.error(f"Validation error: {e}")
                raise
                
        except Exception as e:
            logger.error(f"Error in _generate_viewpoint: {e}")
            raise
        
    def fix_json_string(self,response):
        pattern = r"```json\s*([\s\S]*?)\s*```"
        match = re.search(pattern, response)
        json_data = {}
        if match:
            json_str = match.group(1).strip()
            
            # 修复不正确的转义：将 \\" 替换为 "
            fixed_json = json_str.replace('\\"', '"')
            
            # 使用更可靠的方法处理值中的未转义双引号
            # 先找到所有的键值对
            key_value_pattern = r'"([^"]+)"\s*:\s*"(.*?)"(?=\s*[,}])'
            
            def fix_value(match):
                key = match.group(1)
                value = match.group(2)
                # 如果值中包含未转义的双引号，进行转义
                escaped_value = value.replace('"', '\\"')
                return f'"{key}": "{escaped_value}"'
            
            # 替换所有匹配的键值对
            fixed_json = re.sub(key_value_pattern, fix_value, fixed_json)
            
            # 调试：输出修复后的字符串
            print(f"修复后字符串: {fixed_json}")
            
            # 尝试解析JSON
            try:
                json_data = json.loads(fixed_json)
            except json.JSONDecodeError as e:
                print(f"JSON解析失败: {e}, 修复后字符串: {fixed_json}")
                # 尝试进一步清理多余的反斜杠
                fixed_json = re.sub(r'\\{2,}', r'\\', fixed_json)
                try:
                    json_data = json.loads(fixed_json)
                except json.JSONDecodeError as e:
                    print(f"第二次JSON解析失败: {e}, 修复后字符串: {fixed_json}")
                    return {}
        
        return json_data

    async def _generate_folder_summary(self, folder_id: str, language: str, top_news: List[Dict[str, Any]], passage_list: List[Dict[str, Any]], date: str) -> List[Dict[str, Any]]:
        """生成最终总结，返回JSON格式"""
        try:
            if len(top_news) == 0:
                return []
            cache_result = await self.folder_summaries_repo.query_summary(language,folder_id, date, date)
            if cache_result and len(cache_result) > 0:
                logger.info(f"Found cached final summary for date {date}")
                return json.loads(cache_result[0]['summary'])
            
            if language not in LANGUAGE_MAP:
                language_prompt = "Adapt to the syntactic and stylistic norms of the target language, ensuring the tone matches high-quality journalistic writing in that language."
            else:
                language_prompt = LANGUAGE_MAP[language]['prompt']
            messages = [
    {
        "role": "system",
        "content": f"""You are a news curator, skilled at consolidating and organizing information from different sources. For each article, you will:
1. Visit and read the article link to understand the news content.
2. Analyze using the 5W1H framework (Who, What, When, Where, Why, How) to structure the information.
3. Generate a concise, fluent, and natural one-sentence summary that seamlessly incorporates the 5W1H elements without explicitly mentioning labels like '(Who)', '(What)', etc.
4. Ensure the summary is highly idiomatic and aligns with the syntactic, stylistic, and cultural conventions of the target language, emulating the tone and phrasing of native journalistic writing.
5. Provide the title and summary and viewpoint directly in the requested language within the `title` and `summary` and `viewpoint` fields, prioritizing conciseness, clarity, and native-like fluency over literal translations.
6. {language_prompt}
"""
    },
    {
        "role": "user",
        "content": f"""
Please visit each news article link and generate structured data:

Requirements:
1. Visit each article link and read the content.
2. Use the 5W1H framework (Who, What, When, Where, Why, How) to analyze each article, then summarize the content in a single, concise, and fluent sentence that incorporates all 5W1H elements without explicitly labeling them (e.g., avoid '(Who)', '(What)').
3. Ensure the summary is highly natural, idiomatic, and aligned with the target language's journalistic style, using phrasing that feels native and avoids literal translations of English sentence structures.
4. Provide the title and summary and viewpoint directly in the requested language (`{language}`) within the `title` and `summary` and `viewpoint` fields, prioritizing native-like fluency and conciseness.
5. {language_prompt}
6. Return in strict JSON format.

Return Format:
{{
    "passageList": [
        {{
            "id": "Article ID",
            "title": "Article Title in {language}",
            "summary": "Comprehensive, idiomatic summary in {language} based on 5W1H framework",
            "viewpoint": "Comprehensive, idiomatic viewpoint in {language} based on 5W1H framework"
        }},
        {{
            "id": "Article ID",
            "title": "Article Title in {language}",
            "summary": "Comprehensive, idiomatic summary in {language} based on 5W1H framework",
            "viewpoint": "Comprehensive, idiomatic viewpoint in {language} based on 5W1H framework"
        }}
    ]
}}

Original News:
{top_news}
"""
    }
]

            # 获取响应并验证JSON格式
            response = await self.llm_aggrator.generate_response(messages)
            
            # 验证JSON格式并返回Python对象
            try:
                json_data = self.fix_json_string(response)
                # 找到对应的文章并添加link
                passage_dict = {str(p['id']): p for p in passage_list}
                for article in json_data['passageList']:
                    article_id = str(article['id'])
                    if article_id in passage_dict:
                        article['link'] = passage_dict[article_id].get('link', '')
                        article['image_url'] = passage_dict[article_id].get('image_url', '')
                        article['feed_title'] = passage_dict[article_id].get('feed_title', '')
                        article['feed_homepage'] = passage_dict[article_id].get('feed_homepage', '')
                    
                await self.folder_summaries_repo.save_summary(language,folder_id,  json.dumps(json_data, ensure_ascii=False, indent=2), date, date)
                return json_data
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON format in response: {e}")
                raise
            except ValueError as e:
                logger.error(f"Validation error: {e}")
                raise
                
        except Exception as e:
            logger.error(f"Error in _generate_viewpoint: {e}")
            raise
    
    async def _generate_wechat_summary(self, folder_id: str, language: str, top_news: List[Dict[str, Any]], passage_list: List[Dict[str, Any]], date: str) -> List[Dict[str, Any]]:
        """生成最终总结，返回JSON格式"""
        try:
            if len(top_news) == 0:
                return []
            cache_result = await self.folder_summaries_repo.query_summary(language,folder_id, date, date)
            if cache_result and len(cache_result) > 0:
                logger.info(f"Found cached final summary for date {date}")
                return json.loads(cache_result[0]['summary'])
            
            if language not in LANGUAGE_MAP:
                language_prompt = "Adapt to the syntactic and stylistic norms of the target language, ensuring the tone matches high-quality journalistic writing in that language."
            else:
                language_prompt = LANGUAGE_MAP[language]['prompt']
            messages = [
    {
        "role": "system", 
        "content": f"""You are a news curator, skilled at consolidating and organizing information from different sources. For each article, you will:
1. Visit and read the article link to understand the news content.
2. Analyze using the 5W1H framework (Who, What, When, Where, Why, How) to structure the information.
3. Generate a concise, fluent, and natural one-sentence summary that seamlessly incorporates the 5W1H elements without explicitly mentioning labels like '(Who)', '(What)', etc.
4. Ensure the summary is highly idiomatic and aligns with the syntactic, stylistic, and cultural conventions of the target language, emulating the tone and phrasing of native journalistic writing.
5. Provide the title and summary and viewpoint directly in the requested language within the `title` and `summary` and `viewpoint` fields, prioritizing conciseness, clarity, and native-like fluency over literal translations.
6. {language_prompt}
7. Select only the 10 most important and impactful articles based on:
   - News value and significance
   - Timeliness and relevance
   - Impact on the industry/field
   - Reader interest and engagement potential
"""
    },
    {
        "role": "user",
        "content": f"""
Please visit each news article link, analyze the content, and select the 10 most important articles. For each selected article, generate structured data:

Requirements:
1. Visit each article link and read the content.
2. Select the 10 most important articles based on news value, timeliness, impact, and reader interest.
3. Use the 5W1H framework (Who, What, When, Where, Why, How) to analyze each selected article, then summarize the content in a single, concise, and fluent sentence that incorporates all 5W1H elements without explicitly labeling them (e.g., avoid '(Who)', '(What)').
4. Ensure the summary is highly natural, idiomatic, and aligned with the target language's journalistic style, using phrasing that feels native and avoids literal translations of English sentence structures.
5. Provide the title and summary and viewpoint directly in the requested language (`{language}`) within the `title` and `summary` and `viewpoint` fields, prioritizing native-like fluency and conciseness.
6. {language_prompt}
7. Return in strict JSON format.

Return Format:
{{
    "passageList": [
        {{
            "id": "Article ID",
            "title": "Article Title in {language}",
            "summary": "Comprehensive, idiomatic summary in {language} based on 5W1H framework",
            "viewpoint": "Comprehensive, idiomatic viewpoint in {language} based on 5W1H framework"
        }},
        {{
            "id": "Article ID",
            "title": "Article Title in {language}",
            "summary": "Comprehensive, idiomatic summary in {language} based on 5W1H framework",
            "viewpoint": "Comprehensive, idiomatic viewpoint in {language} based on 5W1H framework"
        }}
    ]
}}

Original News:
{top_news}
"""
    }
]

            # 获取响应并验证JSON格式
            response = await self.llm_aggrator.generate_response(messages)
            
            # 验证JSON格式并返回Python对象
            try:
                json_data = self.fix_json_string(response)
                # 找到对应的文章并添加link
                passage_dict = {str(p['id']): p for p in passage_list}
                for article in json_data['passageList']:
                    article_id = str(article['id'])
                    if article_id in passage_dict:
                        article['link'] = passage_dict[article_id].get('link', '')
                        article['image_url'] = passage_dict[article_id].get('image_url', '')
                        article['feed_title'] = passage_dict[article_id].get('feed_title', '')
                        article['feed_homepage'] = passage_dict[article_id].get('feed_homepage', '')
                    
                await self.folder_summaries_repo.save_summary(language,folder_id,  json.dumps(json_data, ensure_ascii=False, indent=2), date, date)
                return json_data
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON format in response: {e}")
                raise
            except ValueError as e:
                logger.error(f"Validation error: {e}")
                raise
                
        except Exception as e:
            logger.error(f"Error in _generate_viewpoint: {e}")
            raise

    async def _generate_viewpoint(self, folder_id: str, language: str, summary: List[Dict[str, Any]], date: str) -> str:
        """生成最终总结，返回JSON格式"""
        try:
            cache_result = await self.folder_views_repo.query_viewpoint(language,folder_id, date, date)
            if cache_result and len(cache_result) > 0:
                logger.info(f"Found cached final summary for date {date}")
                return cache_result[0]['viewpoint']
            
            passages_text = '\n\n'.join([
                f"title:{passage.get('title', '')}, summary:{passage.get('summary', '')}."
                for passage in summary
            ])
            if language not in LANGUAGE_MAP:
                language_prompt = "Adapt to the syntactic and stylistic norms of the target language, ensuring the tone matches high-quality journalistic writing in that language."
            else:
                language_prompt = LANGUAGE_MAP[language]['prompt']

            messages = [
    {
        "role": "system",
        "content": f"""You are a senior news analyst at Deeper AI, skilled at crafting concise, professional, and human-like news forecasts. As Deeper AI, you deliver content in a clear, objective, and engaging manner, synthesizing insights from multiple high-impact events. Your tasks include:
1. Providing a focused forecast analyzing future trends, emphasizing chain reactions and long-term impacts, supported by specific contextual insights.
2. Ensuring the tone is natural, professional, and free of robotic or overly formulaic phrasing, emulating high-quality journalistic writing.
3. When handling multiple news articles, prioritize geopolitically, economically, or socially significant events (e.g., Ukraine conflict, social movements), integrating relevant details and ignoring minor themes (e.g., consumer issues).
4. Ensure logical coherence when covering multiple events, connecting trends thematically (e.g., conflict and societal shifts).
5. {language_prompt}
Please respond in {language} language."""
    },
    {
        "role": "user",
        "content": f"""Based on the following news articles, generate a concise future forecast:

Requirements:
1. Analyze future trends based on multiple high-impact events (e.g., Ukraine conflict, social movements) in 100-120 words, highlighting chain reactions, long-term impacts, and Deeper AI's unique perspective on specific outcomes (e.g., war trends, societal shifts).
2. From multiple articles, prioritize geopolitically, economically, or socially significant events, integrating relevant details and ignoring minor themes (e.g., sports, consumer issues), ensuring logical coherence across events.
3. Avoid vague generalizations, citing specific contexts (e.g., energy markets, seasonal factors, policy shifts).
4. Use a professional, human-written tone that aligns with high-quality news reporting in {language}, ensuring clarity and natural phrasing.
5. {language_prompt}
News content:
{passages_text}"""
}
]

            # 获取响应并验证JSON格式
            response = await self.llm_aggrator.generate_response(messages)
            
            # 验证JSON格式
            try:
                await self.folder_views_repo.save_viewpoint(language,folder_id, response, date, date)
                return response
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON format in response: {e}")
                raise
            except ValueError as e:
                logger.error(f"Validation error: {e}")
                raise
                
        except Exception as e:
            logger.error(f"Error in _generate_viewpoint: {e}")
            raise

    # def generate_keyword():

    def generate_keyword_prompt(language_code, daily_news_topics, project_name="Deeper AI"):
        """
        Generate a language-specific prompt for AI keyword generation, incorporating daily news topics.
        
        Args:
            language_code (str): Language code (e.g., 'en', 'zh')
            daily_news_topics (list): List of daily news topics (e.g., ["AI regulation updates", "Web3 market crash"])
            project_name (str): Name of the project (default: 'Deeper AI')
        
        Returns:
            str: Formatted prompt for the specified language
        """
        if language_code not in LANGUAGE_MAP:
            raise ValueError(f"Unsupported language code: {language_code}")
        
        lang_info = LANGUAGE_MAP[language_code]
        language_name = lang_info["language_name"]
        market = lang_info["market"]
        keyword_example = lang_info["keyword_example"]
        
        # Format daily news topics for inclusion in the prompt
        news_topics_str = ", ".join(daily_news_topics) if daily_news_topics else "latest trending topics"
        
        prompt = (
            f"Generate a list of SEO-optimized keywords for a news aggregation and newsletter website named '{project_name}', "
            f"targeting the {market}. The website uses AI to aggregate and deliver news on global politics, financial markets, "
            f"technology, business, startups, AI, and Web3, with custom theme subscription features. Today's news includes {news_topics_str}. "
            f"Return the keywords in {language_name} in a JSON array format, like {keyword_example}. Focus on keywords that highlight "
            f"'{project_name}' branding, its AI-driven news aggregation, custom subscription features, and today's news topics. Include "
            f"a mix of high-traffic core keywords, long-tail keywords, and subscription-related terms relevant to the specified topics "
            f"and audience. Ensure the keywords are concise, relevant, and aligned with search trends in the {market}. Avoid generic terms "
            f"and prioritize keywords with strong search intent."
        )
        
        return prompt

    async def _format_ai_report_to_text(self, language: str,folder_id: str, report: Dict[str, Any],date: str) -> str:
        """将JSON格式的报告转换为文本格式"""
        date_str = datetime.strptime(date, "%Y-%m-%d").strftime("%Y年%m月%d日")
        section_title = REFLECTION_MAP.get(str(folder_id), {}).get(language, 'General News')
        folder_info = await self.folders_repo.get_folder_info(folder_id)
        folder_name = folder_info['name']

        lang_config = LANGUAGE_MAP.get(language, LANGUAGE_MAP["en"])
        translations = lang_config["translations"]
        seo_title_template = lang_config["seo_title_template"]
        

        date_format = lang_config["date_format"]

        # 格式化日期
        date_obj = datetime.strptime(date, "%Y-%m-%d")
        date_str = date_obj.strftime(date_format)


        text_report = f"{seo_title_template.format(date=date_str)}"
        text_report += f" ({translations['curated_by']} https://deeperai.net)\n"
        text_report += f"{section_title} (https://deeperai.net/digest/{language}/{folder_name}/{date}.html)\n\n"
        
        # Add summaries from report
        for i, passage in enumerate(report['passageList'], 1):
            text_report += f"{i}. {passage['summary']}\n"

        return text_report
    


    def extract_keywords(self,text: str) -> List[str]:
        # 简单分词，转换为小写，移除标点
        words = re.findall(r'\b\w+\b', text.lower())
        # 停用词列表
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to',
            'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be',
            'this', 'that', 'these', 'those', 'has', 'have', 'had'
        }
        # 过滤停用词，保留长度 > 3 的词
        filtered_words = [word for word in words if word not in stop_words and len(word) > 3]
        # 计算词频，取前 5 个高频词
        word_counts = Counter(filtered_words)
        return [word for word, _ in word_counts.most_common(5)]
    
    def _format_ai_report_to_seo_html(self, folder_id: str, date: str, language: str, summary: Dict[str, Any], passage_list: List[Dict[str, Any]]) -> str:
        """将JSON格式的报告转换为美观的、SEO优化的HTML格式，动态提取关键词并支持国际化"""
        try:
            # 验证输入
            if not summary or not isinstance(summary, dict) or 'passageList' not in summary:
                raise ValueError("Invalid summary format: 'passageList' missing or empty")

            # 获取语言配置，默认为英语
            lang_config = LANGUAGE_MAP.get(language, LANGUAGE_MAP["en"])
            date_format = lang_config["date_format"]
            translations = lang_config["translations"]
            seo_title_template = lang_config["seo_title_template"]

            # 格式化日期
            date_obj = datetime.strptime(date, "%Y-%m-%d")
            date_str = date_obj.strftime(date_format)
            # 为 URL 生成标准化的日期格式 (YYYY-MM-DD)
            url_date_str = date_obj.strftime("%Y-%m-%d")

            # 收集所有标题和摘要以提取关键词
            all_text = ""
            for passage in summary['passageList']:
                title = passage.get('title', '')
                summary_text = passage.get('summary', '')
                all_text += f"{title} {summary_text} "

            # 提取动态关键词
            dynamic_keywords = self.extract_keywords(all_text)[:5]  # 限制动态关键词数量
            # 核心关键词
            core_keywords = ["AI news", "Web3", "cryptocurrency", "Deeper AI"]
            # 日期相关关键词
            date_keywords = [f"{date_str} news digest"]
            # 合并关键词
            keywords = core_keywords + date_keywords + dynamic_keywords
            keywords_str = ", ".join(keywords)

            # 格式化新闻条目的HTML
            news_html = ""
            event_html = ""
            for passage in summary['passageList']:
                passage_info = next((item for item in passage_list if str(item['id']) == passage['id']), None)
                if passage_info is None:
                    continue

                title = passage.get('title', 'No title available...')
                summary_text = passage.get('summary', 'No summary available...')
                link = passage.get('link', '#')
                feed_title = passage_info.get('feed_title', 'Unknown Source')
                feed_cover_image = passage_info.get('feed_cover_image', 'https://deeperai.net/static/default-author.png')
                image_url = passage.get('image_url', 'https://deeperai.net/static/placeholder-ai-web3.jpg')

                # 优化图像 alt 属性
                image_alt = f"{title} - {feed_title}"[:100]
                image_html = f"""
                    <div class="article-image">
                        <img src="{image_url}" alt="{image_alt}" loading="lazy" style="max-width: 100%; height: auto; border-radius: 5px;">
                    </div>
                """ if image_url else ""

                # 单条新闻HTML
                event_html += f"""
                    <article class="article-content" lang="{language}">
                        <div class="article-text">
                            <div class="author">
                                <div class="author-img-wrapper">
                                    <img class="author-img" src="{feed_cover_image}" alt="{feed_title} logo">
                                </div>
                                <a class="author-pic" href="{passage_info.get('feed_homepage', '#')}">{feed_title}</a>
                            </div>
                            <h2 class="text-xl font-bold font-serif mb-2">
                                <a href="{link}">{title}</a>
                            </h2>
                            <p class="text-mono-dim mb-4">{summary_text}</p>
                        </div>
                        {image_html}
                    </article>
                """

            # 按文件夹ID生成section，使用语言适配的标题
            section_title = REFLECTION_MAP.get(str(folder_id), {}).get(language, 'General News')
            news_html += f"""
                <div class="section">
                    <h2 class="section-title">{section_title}</h2>
                    {event_html}
                </div>
            """

            # 动态标题和描述
            seo_title = seo_title_template.format(date=date_str)
            seo_description = f"Explore the {date_str} Deeper AI news digest, covering AI, Web3, and cryptocurrency. Curated with high-quality insights for global readers."

            # 添加 hreflang 标签，使用标准化的 URL 日期格式
            hreflang_tags = ""
            for lang_code in LANGUAGE_MAP:
                hreflang_tags += f'<link rel="alternate" hreflang="{lang_code}" href="https://deeperai.net/digest/ai/{lang_code}/{url_date_str}.html">\n'

            # 完整的HTML模板
            html = f"""
    <!DOCTYPE html>
    <html lang="{language}">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{seo_title}</title>
        <meta name="description" content="{seo_description}">
        <meta name="keywords" content="{keywords_str}">
        <meta name="author" content="Deeper AI">
        <meta name="robots" content="index, follow">
        <link rel="canonical" href="https://deeperai.net/digest/ai/{url_date_str}.html">
        {hreflang_tags}
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css">
        <link rel="icon" href="https://qny.brizen.top/logo.jpg">
        <style>
            body {{
                font-family: 'sohne', 'Helvetica Neue', Helvetica, Arial, sans-serif;
                background-color: #fff;
                color: #1a1a1a;
            }}
            .container {{
                margin: 0 auto;
                padding-left: 1rem;
                padding-right: 1rem;
            }}
            .header {{
                background-color: #fff;
                border-bottom: 1px solid #e0e0e0;
                padding: 16px 0;
                margin-bottom: 32px;
            }}
            .nav-link {{
                color: #1a1a1a;
                font-size: 16px;
                padding: 8px 16px;
                transition: color 0.3s;
            }}
            .nav-link:hover {{
                color: #666;
            }}
            .section-title {{
                font-family: 'Georgia', serif;
                font-size: 24px;
                font-weight: bold;
                color: #000;
                text-transform: uppercase;
                margin-bottom: 20px;
                border-bottom: 1px solid #e0e0e0;
                padding-bottom: 10px;
            }}
            .article-content {{
                display: grid;
                grid-template-columns: 1fr 250px;
                gap: 24px;
                margin-bottom: 32px;
                align-items: start;
                border-bottom: 1px solid #e0e0e0;
                padding-bottom: 24px;
            }}
            .article-content:last-child {{
                border-bottom: none;
            }}
            .article-image img {{
                max-width: 100%;
                height: auto;
                border-radius: 5px;
            }}
            .article-text {{
                line-height: 1.6;
            }}
            .article-text a {{
                color: #000;
                text-decoration: none;
                transition: text-decoration 0.3s;
            }}
            .article-text a:hover {{
                text-decoration: underline;
            }}
            .author {{
                display: flex;
                align-items: center;
                font-size: 14px;
                color: #666;
                margin-bottom: 8px;
            }}
            .author-img-wrapper {{
                display: inline-block;
                vertical-align: middle;
                margin-right: 8px;
            }}
            .author-img {{
                border-radius: 50%;
                height: 20px;
                width: 20px;
            }}
            .author-pic {{
                color: #666;
                text-decoration: none;
            }}
            .author-pic:hover {{
                text-decoration: underline;
            }}
            .text-mono-dim {{
                color: #666;
            }}
            .btn-home {{
                background-color: #1a1a1a;
                color: #fff;
                padding: 12px 24px;
                border-radius: 8px;
                text-decoration: none;
                transition: background-color 0.3s;
            }}
            .btn-home:hover {{
                background-color: #333;
            }}
            @media (max-width: 768px) {{
                .article-content {{
                    grid-template-columns: 1fr 200px;
                    gap: 16px;
                }}
            }}
            @media (max-width: 640px) {{
                .article-content {{
                    grid-template-columns: 1fr;
                }}
                .article-image {{
                    margin-top: 16px;
                    order: 2;
                }}
                .article-text {{
                    order: 1;
                }}
            }}
        </style>
        <script type="application/ld+json">
            {{
                "@context": "https://schema.org",
                "@type": "NewsArticle",
                "headline": "{seo_title}",
                "description": "{seo_description}",
                "keywords": "{keywords_str}",
                "publisher": {{
                    "@type": "Organization",
                    "name": "Deeper AI",
                    "url": "https://deeperai.net"
                }},
                "mainEntityOfPage": {{
                    "@type": "WebPage",
                    "@id": "https://deeperai.net/digest/ai/{url_date_str}.html"
                }},
                "datePublished": "{date_obj.isoformat()}Z"
            }}
        </script>
    </head>
    <body>
        <header class="header">
            <div class="container flex justify-between items-center">
                <h1 class="text-2xl font-bold font-serif">
                    <a href="https://deeperai.net/" class="hover:text-gray-600">DeeperAI</a>
                </h1>
                <nav class="flex space-x-4">
                    <a href="https://deeperai.net/" class="nav-link">{translations["home"]}</a>
                </nav>
            </div>
        </header>

        <main class="container">
            <section class="newsletter-content bg-mono-card p-6 rounded-lg shadow-lg">
                <h1 class="section-title">{seo_title}</h1>
                <p class="text-mono-dim mb-4">{translations["curated_by"]}</p>
                {news_html}
                <div class="text-center">
                    <a href="https://deeperai.net/" class="btn-home inline-block">
                        {translations["back_to_home"]}
                    </a>
                </div>
            </section>
        </main>

        <footer class="bg-gray-900 text-white py-4 mt-8">
            <div class="container text-center">
                <p>{translations["footer_copyright"]}</p>
                <p><a href="https://deeperai.net/" class="text-gray-400 hover:text-gray-300">{translations["visit_homepage"]}</a></p>
            </div>
        </footer>
    </body>
    </html>
            """
            return html

        except Exception as e:
            logger.error(f"Error formatting report to HTML: {e}", exc_info=True)
            return f"<pre>Error: {str(e)}\nInput: {summary}</pre>"
        
    def _format_ai_report_to_html(self, language: str, report: Dict[str, Any]) -> str:
        """将JSON格式的报告转换为美观的HTML格式"""
        try:
            # 格式化数据一瞥的HTML
            news_html = ""
            for folder_id in report:
                event_html = ""
                if not report or not isinstance(report, dict):
                    continue
                folder_summary = report[folder_id].get('folder_summary', {})
                # 如果 folder_summary 是 list 或为空，跳过
                if not isinstance(folder_summary, dict) or 'passageList' not in folder_summary:
                    continue
                for passage in folder_summary['passageList']:
                    passage_info = next((item for item in report[folder_id]['passage_list'] if str(item['id']) == passage['id']), None)
                    if passage_info is None:
                        continue
                    title = passage.get('title', 'No title available...')
                    summary = passage.get('summary', 'No summary available...')
                    
                    # 处理图像
                    image_html = ""
                    if passage_info.get('image_url') and passage_info['image_url'] != "":
                        image_html = f"""
                            <div style="width: 200px; height: auto; float: right; margin-left: 15px; border-radius: 5px;">
                                <img src="{passage_info['image_url']}" alt="{self._clean_text(title)}" style="width: 200px; height: auto; border-radius: 5px; display: block;">
                            </div>
                        """
                    else:
                        image_html = ""

                    # 单个事件HTML
                    event_html += f"""
                        <div style="margin-bottom: 30px; padding-bottom: 20px; border-bottom: 1px solid #e0e0e0; display: flex; flex-wrap: wrap; align-items: center; gap: 15px; font-family: 'Arial', sans-serif; color: #1a1a1a;">
                            <div style="flex: 1; min-width: 0;">
                                <div style="font-size: 14px; color: #666666; margin-bottom: 8px;">
                                    <div style="display: inline-block; vertical-align: middle;">
                                        <img src="{passage_info['feed_cover_image']}" alt="" style="display: block; border-radius: 50%; height: 20px; width: 20px;">
                                    </div>
                                    <a href="{passage_info['feed_homepage']}" style="color: #000000; font-weight: 400; font-size: 13px; line-height: 20px; margin-left: 3px; text-decoration: none;">{self._clean_text(passage_info['feed_title'])}</a>
                                </div>
                                <div style="font-family: 'Georgia', serif; font-size: 22px; font-weight: bold; color: #000000; margin-bottom: 8px;">
                                    <a href="{passage_info['link']}" style="color: #000000; text-decoration: none;">{self._clean_text(title)}</a>
                                </div>
                                <div style="font-size: 16px; color: #333333; margin-bottom: 10px;">{self._clean_text(summary)}</div>
                            </div>
                            {image_html}
                        </div>
                    """
                
                # 每个section的HTML
                section_title = REFLECTION_MAP.get(str(folder_id), {}).get(language, "Section Title")
                news_html += f"""
                    <div style="margin-bottom: 40px;">
                        <div style="font-family: 'Georgia', serif; font-size: 24px; font-weight: bold; color: #000000; text-transform: uppercase; margin-bottom: 20px; border-bottom: 1px solid #e0e0e0; padding-bottom: 10px;">
                            {self._clean_text(section_title)}
                        </div>
                        {event_html}
                    </div>
                """

            # HTML模板（所有CSS内联）
            html = f"""
            <!DOCTYPE html>
            <html lang="{language}">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Deeper AI Digest</title>
            </head>
            <body style="font-family: sohne,'Helvetica Neue',Helvetica,Arial,sans-serif; line-height: 1.6; max-width: 700px; margin: 0 auto; padding: 30px; background-color: #ffffff; color: #1a1a1a;">
                <div style="background: #f0f0f0; padding: 50px; width: 600px; margin: auto;">
                    <div style="text-align: left; margin-bottom: 40px;">
                        <div style="font-family: 'Georgia', serif; font-size: 48px; font-weight: bold; color: #000000; margin-bottom: 10px;">Deeper AI Digest</div>
                    </div>
                    {news_html}
                </div>
            </body>
            </html>
            """
            
            return html

        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON report: {e}")
            return f"<pre>Error parsing JSON report: {e}</pre>"
        except Exception as e:
            logger.error(f"Error formatting report to HTML: {e}", exc_info=True)
            return f"<pre>Error formatting report to HTML: {e}</pre>"
    def _clean_text(self, text: str) -> str:
        """清理文本中的特殊字符和转义字符"""
        if not text:
            return ""
            
        # 1. 处理转义字符
        text = text.replace("\\'", "'")  # 处理转义的单引号
        text = text.replace('\\"', '"')  # 处理转义的双引号
        text = text.replace('\\n', '<br>')  # 将换行转换为HTML换行
        
        # 2. 处理特殊引号
        replacements = {
            "'": "'",    # 弯引号 -> 直引号
            """: '"',    # 弯双引号 -> 直双引号
            """: '"',    # 弯双引号 -> 直双引号
            "–": "-",    # en dash -> 连字符
            "—": "-",    # em dash -> 连字符
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
            
        return text

