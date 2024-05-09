import re
from pathlib import Path
import asyncio
from datetime import datetime, date, timedelta, timezone
from typing import Any, Iterable
import aiohttp
from difflib import SequenceMatcher
from dotenv import dotenv_values
from pydantic import BaseModel, Field, field_validator
from apify_client import ApifyClientAsync


environment_values = dotenv_values()

apify_key = environment_values['APIFY_KEY']
serper_key = environment_values['SERPER_KEY']


async_client = ApifyClientAsync(token=apify_key)


class FoundWebSource(BaseModel):
    text: str
    searched_by_text: str
    query_url: str
    website_link: str
    index: int
    website_title: str | None = None
    website_description: str | None = None
    website_text: str | None = None
    source_score: float | None = None
    website_date: str | date | None = None
    searched_at: datetime = Field(default_factory=datetime.now)
    
    @field_validator('website_date', mode='after')
    def validate_website_date(
        cls,
        value
    ) -> date | None:
        
        if isinstance(value, str):
            value = cls.website_date_str_to_datetime(value)
        return value
        
    @staticmethod
    def website_date_str_to_datetime(
        string_date: str
    ) -> date:
        
        month_to_number = {
            'Jan': 1,
            'Feb': 2,
            'Mar': 3,
            'Apr': 4,
            'May': 5,
            'Jun': 6,
            'Jul': 7,
            'Aug': 8,
            'Sep': 9,
            'Oct': 10,
            'Nov': 11,
            'Dec': 12
        }
        
        if 'hours' in string_date:
            return date.today()
        elif 'day' in string_date:
            return date.today() - timedelta(int(re.search(r'\d+', string_date).group(0)))
        elif found := re.search(r'(\w{3}) (\d{1,2}), (\d{4})', string=string_date):
            month, day, year = month_to_number[found.group(1)], int(found.group(2)), int(found.group(3))
            return date(year=year, month=month, day=day)
        else:
            raise ValueError(f'\'{string_date}\' cannot be converted to date.')
        

class FoundWebSources(BaseModel):
    sources: list[FoundWebSource]
    

class FindTextSources:
    
    def __init__(
        self,
        apify_key: str,
        serper_key: str
    ):
        
        self.async_client = ApifyClientAsync(token=apify_key)
        self.serper_key = serper_key
    
    async def bing_search(
        self,
        texts: str | list[str],
        max_number_results: int = 10
    ) -> list[dict]:
        
        texts = self._to_list_if_single(texts)
        
        run_input = {
            'queries': texts,
            "resultPerPage": max_number_results,
            'marketCode': "en-US"
        }
        
        call = await self.async_client.actor('YahzVjUHQsxjW5b4I').call(run_input=run_input)
        
        return [item async for item in self.async_client.dataset(call['defaultDatasetId']).iterate_items()]

    async def get_website_content_serper(
        self,
        url: str,
        timeout: float | None = 6000
    ) -> dict | None:
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url='https://scrape.serper.dev',
                params={'url': url},
                headers={'X-API-KEY': self.serper_key, 'Content-Type': 'application/json'},
                timeout=timeout
            ) as request:
                return await request.json() if request.ok else None
            
    @staticmethod
    def duplicate_score(
        text_1: str,
        text_2: str
    ) -> float:
        return SequenceMatcher(a=text_1, b=text_2).ratio()
    
    @classmethod
    def source_score(
        cls,
        searched_text_source: str,
        website_text: str,
        patch_size: int = 380,
        minimum_comparison_patch: int = 140
    ) -> float:
        
        return max(
            cls.duplicate_score(
                searched_text_source[idx_source: idx_source + patch_size],
                website_text[idx_website_text: idx_website_text + patch_size]
            )
                   for idx_source in range(0, len(searched_text_source) - minimum_comparison_patch, patch_size)
                   for idx_website_text in range(0, len(website_text) - minimum_comparison_patch, patch_size)
        )
        
    @staticmethod
    def _to_list_if_single(
        value: Any
    ) -> Iterable[Any]:
        
        value = [value] if isinstance(value, (int, str, float, bytes, dict)) else value
        return value
    
    async def find_text_source(
        self,
        text: str,
        max_number_results: int = 10
    ) -> FoundWebSources:
        
        searched = (await self.bing_search(
            texts=text,
            max_number_results=max_number_results
        ))[0]
        
        searched_by_text = searched.get('keyword')
        query_url = searched.get('url')
        pages = searched.get('pages')

        done, pending = await asyncio.wait(
            [asyncio.create_task(self.get_website_content_serper(url=page.get('link')), name=str(idx))
             for idx, page in enumerate(pages)]
        )
        
        pages_content = []
        
        for task in done:
            pages_content.append((int(task.get_name()), task.result()))
            
        for task in pending:
            pages_content.append((int(task.get_name()), None))
            task.cancel()    
        
        pages_content.sort(key=lambda i: i[0])
        
        text_web_sources = []
        for (page, (index, page_content)) in zip(pages, pages_content):
            if page_content is None:
                website_text = None
                source_score = None
            else:
                website_text = page_content.get('text')
                source_score = self.source_score(text, website_text)
            
            text_web_source = FoundWebSource(
                text=text,
                searched_by_text=searched_by_text,
                query_url=query_url,
                website_link=page.get('link'),
                website_title=page.get('title'),
                website_description=page.get('desc'),
                website_text=website_text,
                website_date=page.get('date'),
                index=index,
                source_score=source_score
            )
            text_web_sources.append(text_web_source)
        return FoundWebSources(sources=text_web_sources)


if __name__ == '__main__':
    find_text_sources = FindTextSources(apify_key=apify_key, serper_key=serper_key)
    sources = asyncio.run(find_text_sources.find_text_source(text=input('Text:\n'))) 
    open(Path(__file__).parent / 'sources.json', 'wb').write(sources.model_dump_json(indent=4).encode())
