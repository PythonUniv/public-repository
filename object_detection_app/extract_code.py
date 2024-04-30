from typing import TextIO
from enum import Enum
import black.parsing
from selenium.webdriver import Chrome
from bs4 import BeautifulSoup
import black
from pygments import highlight
from pygments.lexers.python import PythonLexer
from pygments.formatters import HtmlFormatter


webdriver = Chrome()


class PygmentsStyle(str, Enum):
    default: str = 'default'
    bw: str = 'bw'
    staroffice: str = 'staroffice'
    

def get_extracted_page(
    url: str,
    file: TextIO,
    style: PygmentsStyle = PygmentsStyle.default,
    line_length: int | None = None
) -> None:
    
    webdriver.get(url)
    
    content = webdriver.page_source
    
    beautiful_soup = BeautifulSoup(content, 'html.parser')
    blocks = [block.find('code').get_text() for block in
              beautiful_soup.find_all('pre', {'class': 'language-python'})]
    
    if line_length is not None:
        blocks = format_blocks(blocks, line_length=line_length)
        
    entire_text = '\n\n\n### ### ### ### ### ### ### ###\n'.join(blocks)
    
    highlight(
        code=entire_text,
        lexer=PythonLexer(),
        formatter=HtmlFormatter(full=True, style=style),
        outfile=file
    )
    
      
def format_blocks(
    blocks: list[str],
    line_length: int = 80,
) -> list[str]:
    
    mode = black.Mode(
        line_length=line_length,
        string_normalization=True)
    
    formatted_blocks = []
    for block in blocks:
        try:    
            formatted_block = black.format_str(block, mode=mode)
            formatted_blocks.append(formatted_block)
        except black.parsing.InvalidInput:
            formatted_blocks.append(block) 
    return formatted_blocks
    
    
def get_title_from_url(
    url: str
) -> str:
    return url_title + '.html' if (url_title := url.split('/')[-1]) else 'blocks.html'
