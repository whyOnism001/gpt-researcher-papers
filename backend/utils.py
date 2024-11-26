import aiofiles
import urllib
import mistune

# 异步将文本写入文件
async def write_to_file(filename: str, text: str) -> None:
    """异步地将文本以UTF-8编码写入文件。

    参数：
        filename (str): 要写入的文件名。
        text (str): 要写入的文本。
    """
    # 确保文本是字符串类型
    if not isinstance(text, str):
        text = str(text)

    # 将文本转换为UTF-8编码，替换任何有问题的字符
    text_utf8 = text.encode('utf-8', errors='replace').decode('utf-8')

    async with aiofiles.open(filename, "w", encoding='utf-8') as file:
        await file.write(text_utf8)

# 将文本写入Markdown文件并返回文件路径
async def write_text_to_md(text: str, filename: str = "") -> str:
    """将文本写入Markdown文件并返回文件路径。

    参数：
        text (str): 要写入Markdown文件的文本。

    返回：
        str: 生成的Markdown文件的文件路径。
    """
    file_path = f"outputs/{filename[:60]}.md"
    await write_to_file(file_path, text)
    return urllib.parse.quote(file_path)

# 将Markdown文本转换为PDF文件并返回文件路径
async def write_md_to_pdf(text: str, filename: str = "") -> str:
    """将Markdown文本转换为PDF文件并返回文件路径。

    参数：
        text (str): 要转换的Markdown文本。

    返回：
        str: 生成的PDF的编码文件路径。
    """
    file_path = f"outputs/{filename[:60]}.pdf"

    try:
        from md2pdf.core import md2pdf
        md2pdf(file_path,
               md_content=text,
               css_file_path="./frontend/pdf_styles.css",
               base_url=None)
        print(f"报告写入到 {file_path}")
    except Exception as e:
        print(f"将Markdown转换为PDF时出错：{e}")
        return ""

    encoded_file_path = urllib.parse.quote(file_path)
    return encoded_file_path

# 将Markdown文本转换为DOCX文件并返回文件路径
async def write_md_to_word(text: str, filename: str = "") -> str:
    """将Markdown文本转换为DOCX文件并返回文件路径。

    参数：
        text (str): 要转换的Markdown文本。

    返回：
        str: 生成的DOCX的编码文件路径。
    """
    file_path = f"outputs/{filename[:60]}.docx"

    try:
        from docx import Document
        from htmldocx import HtmlToDocx
        # 将报告Markdown转换为HTML
        html = mistune.html(text)
        # 创建一个文档对象
        doc = Document()
        # 将生成的html转换为文档格式
        HtmlToDocx().add_html_to_document(html, doc)

        # 将docx文档保存到文件路径
        doc.save(file_path)

        print(f"报告写入到 {file_path}")

        encoded_file_path = urllib.parse.quote(file_path)
        return encoded_file_path

    except Exception as e:
        print(f"将Markdown转换为DOCX时出错：{e}")
        return ""