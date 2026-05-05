from pathlib import Path
import shutil
import subprocess
import textwrap


ROOT = Path(r"E:\CTpath-master")
SRC = ROOT / "附件6：重庆邮电大学本科毕业设计（论文）写作参考模板 (2).doc"
DST = ROOT / "附件6：重庆邮电大学本科毕业设计（论文）写作参考模板 (2)-润色版.doc"
TXT = ROOT / "_tmp_polished_text.txt"
PDF = ROOT / "_tmp_polished_preview.pdf"
PNG_DIR = ROOT / "_tmp_polished_pages"
PS1 = ROOT / "_tmp_polish_doc.ps1"


REPLACEMENTS = [
    (
        "我向学院呈交的论文《                                    》，是本人在指导教师的指导下，独立进行研究工作所取得的成果。",
        "本人向学院提交的论文《                                    》，是在指导教师指导下独立完成研究工作所形成的成果。",
    ),
    (
        "除文中已经注明引用的内容外，本论文不含任何其他个人或集体已经发表或撰写过的作品成果。",
        "除文中已明确注明引用的内容外，本论文不包含任何其他个人或集体已经发表或撰写的作品成果。",
    ),
    (
        "对本文的研究做出重要贡献的个人和集体，均已在文中以明确方式标明并致谢。",
        "凡对本研究作出重要贡献的个人和集体，均已在文中以明确方式标明并致谢。",
    ),
    (
        "本人完全意识到本声明的法律结果由本人承担。",
        "本人已充分知悉本声明可能产生的法律责任，并愿意承担相应后果。",
    ),
    (
        "本人完全了解重庆邮电大学有权保留、使用学位论文纸质版和电子版的规定，即学校有权向国家有关部门或机构送交论文，允许论文被查阅和借阅等。",
        "本人已充分了解重庆邮电大学关于保留和使用学位论文纸质版、电子版的相关规定，即学校有权向国家有关部门或机构送交论文，并允许论文被查阅和借阅。",
    ),
    (
        "本人授权重庆邮电大学可以公布本学位论文的全部或部分内容，可编入有关数据库或信息系统进行检索、分析或评价，可以采用影印、缩印、扫描或拷贝等复制手段保存、汇编本学位论文。",
        "本人授权重庆邮电大学公布本学位论文的全部或部分内容，并将其编入有关数据库或信息系统，用于检索、分析或评价；学校亦可采用影印、缩印、扫描、复制等方式保存和汇编本学位论文。",
    ),
    (
        "毕业设计是本科教学过程最后阶段的一种总结性实践教学环节。",
        "毕业设计是本科教学培养过程最后阶段的重要总结性实践环节。",
    ),
    (
        "通过毕业设计，学生可以综合应用所学的各种理论知识和技能，进行全面、系统、严格的技术及基本能力的练习。",
        "通过毕业设计，学生能够综合运用所学理论知识与专业技能，接受较为全面、系统、严格的工程实践和基本能力训练。",
    ),
    (
        "为了提高毕业设计论文的质量，做到论文在内容和格式上的规范化与统一化，特制作本模板。",
        "为提升毕业设计（论文）质量，促进论文内容与格式的规范统一，特制定本模板。",
    ),
    (
        "论文摘要是论文内容不加注释和评论的简短陈述，应以第三人称陈述，用语力求简洁、准确。",
        "论文摘要是对论文内容不加注释和评论的简要陈述，宜采用第三人称表述，语言应简洁、准确。",
    ),
    (
        "中文摘要字数原则上为400-600字，英文摘要应与中文内容一致。",
        "中文摘要原则上控制在400-600字，英文摘要应与中文摘要内容保持一致。",
    ),
    (
        "摘要是学位论文的浓缩，应具有独立性和自含性，即是一篇完整的短文，不阅读论文的全文，就能获得必要的信息。",
        "摘要是学位论文的浓缩，应具有独立性和自含性；即使不阅读全文，读者也应能够从摘要中获得必要信息。",
    ),
    (
        "摘要内容应尽可能包括原论文的主要信息，包括研究工作的目的意义、主要问题、研究内容、研究方法、研究结果、主要结论，供读者确定有无必要阅读全文，也供文摘汇编等二次文献采用。",
        "摘要内容应尽可能涵盖论文的主要信息，包括研究目的与意义、主要问题、研究内容、研究方法、研究结果和主要结论，以便读者判断是否需要阅读全文，也便于文摘汇编等二次文献采用。",
    ),
    (
        "摘要要用文字表达，不用图、表、化学结构式、公式、非公知公用的符号和术语。",
        "摘要应以文字表述为主，一般不使用图、表、化学结构式、公式以及非公知公用的符号和术语。",
    ),
    (
        "关键词是为了文献标引工作从论文中选取出来用以表示全文主题内容信息的单词或术语。",
        "关键词是为文献标引而从论文中选取的、能够反映全文主题内容的词语或术语。",
    ),
    (
        "自定义3-5个关键词，按外延由大到小排列，建议采用EI标准检索词，关键词间用分号分开。",
        "关键词一般设置3-5个，按外延由大到小排列；建议优先采用EI标准检索词，关键词之间用分号分隔。",
    ),
    (
        "Abstract is a brief statement of the thesis without notes and comments, which should be stated in the third person with concise and accurate language in 600-800 Chinese characters and less than 700 words in foreign languages.",
        "The abstract is a concise statement of the thesis without notes or commentary. It should be written in the third person, use clear and accurate language, and remain consistent with the Chinese abstract.",
    ),
    (
        "The writing of an abstract should follow these principles:",
        "The abstract should follow these principles:",
    ),
    (
        "Abstract should generally state out clearly the purpose, significance, problem, methods, results, main conclusion and its significance, creative achievements and new insights of the research program, and the results and conclusions should be emphasized.",
        "It should clearly present the purpose, significance, research problem, methods, results, main conclusions, creative contributions and new insights of the study, with appropriate emphasis on the results and conclusions.",
    ),
    (
        "Abstract should be independent and self contained, which can offer the necessary information without reading the full text.",
        "It should be independent and self-contained, providing the necessary information without requiring readers to consult the full text.",
    ),
    (
        "It is the miniature and abbreviation of a thesis, which contains the thesis's main points, views and conclusions in a short and clear way.",
        "It is a compact representation of the thesis, presenting the main points, views and conclusions briefly and clearly.",
    ),
    (
        "Abstract is a complete short essay with data and conclusion, which can be adopted and referred to independently.",
        "It should function as a complete short passage, including essential data and conclusions where appropriate, and should be usable as an independent reference.",
    ),
    (
        "Abstract should include main information of the original thesis as far as possible for the reader to determine whether to read the full text, which can also be applied for secondary sources.",
        "It should include the thesis's key information so that readers can decide whether to read the full text and so that secondary sources can cite or index it accurately.",
    ),
    (
        "Abstract should be written in words without any appended drawings and photos.",
        "It should be written in prose and should not include appended drawings or photographs.",
    ),
    (
        "Unless there is no alternative way available, abstract should be presented without graphs, tables, chemical structural equations, non-public common symbols and terminology, subscripts, and other special symbols.",
        "Unless strictly necessary, it should avoid graphs, tables, chemical structural formulas, uncommon symbols or terminology, subscripts and other special symbols.",
    ),
    (
        "It is the best policy to highlight the key points clearly with less data tables.",
        "The preferred approach is to highlight key points clearly while minimizing tabular data.",
    ),
    (
        "Keywords are words or terms selected from the thesis for literature indexing to represent the topic information entry.",
        "Keywords are words or terms selected from the thesis for literature indexing and should represent the core topic information.",
    ),
    (
        "Generally, a thesis should have 3-5 keywords, which should be arranged from broad to narrow entry according to the principle of epitaxial order.",
        "A thesis generally includes 3-5 keywords, arranged from broader to narrower concepts.",
    ),
    (
        "EI standard retrieval words are recommended.",
        "EI-standard retrieval terms are recommended where applicable.",
    ),
    (
        "The keywords should be separated by a semicolon and there is no punctuation after the last word.",
        "Keywords should be separated by semicolons, with no punctuation after the final keyword.",
    ),
    (
        "If possible, it is better to use the standard words from Chinese Thesauri and other dictionaries of the same type.",
        "Where possible, use standardized terms from Chinese Thesauri or comparable controlled vocabularies.",
    ),
    (
        "Abstract should be centered in bold-3 word size.",
        "The heading “Abstract” should be centered and set in bold size-3 type.",
    ),
    (
        "The content and the key words are written in Chinese song typeface, English Times New Roman, small-four word size and 1.5 spaced.",
        "The abstract body and keywords should use Chinese Song typeface for Chinese text and Times New Roman for English text, in small-four size with 1.5 line spacing.",
    ),
    (
        "绪论（也称引言）简要说明研究工作的目的、范围、相关领域国内外研究现状、研究目标、研究设想和内容、研究和实验方法、预期结果和意义，以及论文的章节安排等。",
        "绪论（也称引言）应简要说明研究工作的目的、范围、相关领域国内外研究现状、研究目标、研究思路与内容、研究方法或实验方法、预期结果与意义，以及论文的章节安排等。",
    ),
    (
        "力求言简意赅，不要与摘要雷同，也不要叙述教科书中的知识。",
        "表述应力求言简意赅，避免与摘要重复，也不宜展开叙述教科书式常识。",
    ),
    (
        "本模板主要参照",
        "本模板主要参考",
    ),
    (
        "部分范例来自",
        "部分示例参考",
    ),
    (
        "分类号指中图分类号，是指采用",
        "分类号通常指中图分类号，是采用",
    ),
    (
        "分门别类地组织文献，所获取的分类代号。",
        "分门别类组织文献后形成的分类代号。",
    ),
    (
        "论文中文题名是以最恰当、最简明的词语，反映学位论文最重要的特定内容的逻辑组合。",
        "论文中文题名应以恰当、简明的词语，准确反映学位论文最重要的特定内容及其逻辑关系。",
    ),
    (
        "题名应恰当简洁，一般不超过25个字。",
        "题名应恰当、简洁，中文题名一般不超过25个字。",
    ),
    (
        "写出论文的主要工作内容，并逐一介绍每章的内容安排。",
        "本节应概述论文的主要工作内容，并逐章说明全文结构安排。",
    ),
    (
        "学士学位论文应能表明作者确已较好地掌握了本门学科的基础理论、专门知识和基本技能，并从事科学研究工作或独立担负专门技术工作的初步能力。",
        "学士学位论文应能够表明作者已较好掌握本学科的基础理论、专门知识和基本技能，并具备从事科学研究或独立承担专门技术工作的初步能力。",
    ),
    (
        "论文的文字表述应实事求是、客观真切、合乎逻辑、层次分明、简练可读。",
        "论文文字表述应实事求是、客观准确、逻辑清晰、层次分明、简练可读。",
    ),
    (
        "凡引用他人观点、方案、资料、数据、图表等，无论是纸质或电子版，均应详加注释。",
        "凡引用他人观点、方案、资料、数据或图表等内容，无论来源为纸质版还是电子版，均应准确注明出处。",
    ),
    (
        "论文由前置部分、主体部分和附录部分构成。",
        "论文通常由前置部分、主体部分和附录部分构成。",
    ),
    (
        "主体部分包括引文、正文、结论、致谢、参考文献等；",
        "主体部分包括引言、正文、结论、致谢、参考文献等；",
    ),
    (
        "论文应根据内容的相对独立性划分各章，每章的内容精简后可作为期刊论文发表，各章的顺序安排应考虑论文内容的逻辑性。",
        "论文应根据内容的相对独立性划分章节，章节顺序应符合论文内容的逻辑展开。",
    ),
    (
        "由于研究工作涉及的学科、选题、研究方法、工作进程、结果表达方式等有很大差异，对正文内容不作统一规定，但正文应对研究内容及成果进行较全面、客观的理论阐述，应着重指出研究内容中的创新、改进与实际应用之处。",
        "由于研究工作在学科方向、选题内容、研究方法、工作进程和结果表达方式等方面差异较大，正文内容不宜作统一规定；但正文应对研究内容及成果进行全面、客观的理论阐述，并重点说明研究中的创新、改进与实际应用价值。",
    ),
    (
        "国家标准GB7713-87规定：",
        "国家标准GB7713-87曾规定：",
    ),
    (
        "一般教科书中有的知识，在引言中不要赘述。",
        "一般教科书中已有的基础知识，不宜在引言中赘述。",
    ),
    (
        "引言的目的是给出作者进行本项工作的原因，希望达到的目的。",
        "引言的目的在于说明作者开展本项工作的原因及希望达到的目标。",
    ),
    (
        "让对这一领域并不特别熟悉的读者能够了解进行这方面研究的意义，前人已达到的水平，已解决和尚待解决的问题，引出要研究的内容，介绍通过研究取得的成果和主要创新之处。",
        "使对该领域不甚熟悉的读者也能了解研究意义、前人已达到的水平、已解决和尚待解决的问题，并自然引出本文的研究内容、研究成果和主要创新之处。",
    ),
    (
        "原来存在的问题，提出了什么要求，说明这项研究的意义",
        "原有问题、现实需求以及本研究的意义",
    ),
    (
        "对于存在的问题，前人进行过怎样的研究，介绍其大概情形",
        "围绕相关问题，概述前人研究的主要情况",
    ),
    (
        "考察了前人的研究之后，发现了什么欠缺，还可以介绍自己研究的动机",
        "在梳理前人研究的基础上，指出其不足，并说明本研究的动机",
    ),
    (
        "写作目的和涉及的范围，研究结果的适用范围，研究者有什么建议，研究的新特点是什么",
        "论文写作目的、研究范围、结果适用范围、研究建议及创新特点",
    ),
    (
        "引用从具体数值计算出的数据，介绍研究的经过和结果",
        "结合必要的具体数据，概述研究过程和主要结果",
    ),
    (
        "除了要注重论文结构的规范性，规范的注释、图表、公式和计量单位格式同样是论文质量的基本保证。",
        "除论文结构规范外，注释、图表、公式和计量单位格式的规范性同样是论文质量的重要保障。",
    ),
    (
        "注释是正文中为了不中断或割离连贯的叙述语言而对文中某些内容",
        "注释是在不打断正文连贯叙述的前提下，对文中某些内容",
    ),
]

COMMENTS = [
    ("《学位论文编写规则》（GB/T7713.1-2006", "请核对学校当前执行的论文编写标准是否仍为 GB/T 7713.1-2006，或是否已有新版/校内补充规定。"),
    ("《文后参考文献著录规则》（GB/T7714-2005", "请核对参考文献著录规则是否应更新为学校当前采用的版本。GB/T 7714-2015 已广泛使用。"),
    ("http://www.33tt.com/tools/ztf", "请核对该中图分类号查询网址是否仍可访问且适合作为正式模板引用。"),
    ("http://lib.jzit.edu.cn/sjk/tsflf/index.htm", "请核对该查询网址是否仍有效；若失效，建议改用学校图书馆或权威分类法查询入口。"),
    ("采用1999年出版的第四版《中图法》", "请核对当前是否仍要求使用第四版《中图法》；该说法可能与现行版本或学校要求不一致。"),
    ("国家标准GB7713-87曾规定", "请核对是否仍需引用 GB7713-87；该标准表述可能已被后续论文编写规则替代。"),
    ("全文共分为5章", "此处看起来是示例结构，请根据实际论文章数更新。"),
    ("部分示例参考《障碍环境中Swarm突现计算模型研究及行为控制》", "请确认该示例来源是否仍保留，或替换为更贴合本科毕业设计的示例。"),
]


def ps_quote(text: str) -> str:
    return "'" + text.replace("'", "''") + "'"


def build_ps() -> str:
    replacement_items = "\n".join(
        f"  @{{ Old = {ps_quote(old)}; New = {ps_quote(new)} }}"
        for old, new in REPLACEMENTS
    )
    comment_items = "\n".join(
        f"  @{{ Needle = {ps_quote(needle)}; Note = {ps_quote(note)} }}"
        for needle, note in COMMENTS
    )
    return textwrap.dedent(
        rf"""
        $ErrorActionPreference = 'Stop'
        $docPath = '{DST}'
        $txtPath = '{TXT}'
        $pdfPath = '{PDF}'
        $replacements = @(
        {replacement_items}
        )
        $comments = @(
        {comment_items}
        )

        $word = New-Object -ComObject Word.Application
        $word.Visible = $false
        $word.DisplayAlerts = 0
        $summary = @()
        try {{
          $doc = $word.Documents.Open($docPath, $false, $false)
          $doc.TrackRevisions = $false

          foreach ($item in $replacements) {{
            $range = $doc.Content
            $find = $range.Find
            $find.ClearFormatting()
            $find.Replacement.ClearFormatting()
            $find.Text = $item.Old
            $find.Replacement.Text = $item.New
            $find.Forward = $true
            $find.Wrap = 1
            $find.MatchCase = $false
            $find.MatchWholeWord = $false
            $find.MatchWildcards = $false
            $count = 0
            while ($find.Execute($item.Old, $false, $false, $false, $false, $false, $true, 1, $false, $item.New, 2)) {{
              $count += 1
              if ($count -gt 200) {{ break }}
            }}
            if ($count -gt 0) {{
              $summary += ("replace`t" + $count + "`t" + $item.Old)
            }}
          }}

          foreach ($item in $comments) {{
            $range = $doc.Content
            $find = $range.Find
            $find.ClearFormatting()
            $find.Text = $item.Needle
            $find.Forward = $true
            $find.Wrap = 0
            $find.MatchCase = $false
            $find.MatchWholeWord = $false
            $find.MatchWildcards = $false
            if ($find.Execute()) {{
              $doc.Comments.Add($range, $item.Note) | Out-Null
              $summary += ("comment`t1`t" + $item.Needle)
            }} else {{
              $summary += ("comment`t0`t" + $item.Needle)
            }}
          }}

          $doc.Save()
          $doc.SaveAs2($txtPath, 2)
          $doc.ExportAsFixedFormat($pdfPath, 17)
          $doc.Close($false)
        }} finally {{
          $word.Quit()
        }}
        $summary | Set-Content -LiteralPath '{ROOT / "_tmp_polish_summary.tsv"}' -Encoding UTF8
        """
    )


def main() -> None:
    if not SRC.exists():
        raise FileNotFoundError(SRC)
    shutil.copy2(SRC, DST)
    PS1.write_text(build_ps(), encoding="utf-8-sig")
    subprocess.run(
        ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(PS1)],
        check=True,
    )
    print(f"revised={DST} size={DST.stat().st_size}")
    print(f"text_export={TXT} size={TXT.stat().st_size}")
    print(f"pdf_export={PDF} size={PDF.stat().st_size}")
    PNG_DIR.mkdir(exist_ok=True)
    try:
        import fitz  # type: ignore

        pdf_doc = fitz.open(PDF)
        for page_index in range(min(3, pdf_doc.page_count)):
            page = pdf_doc.load_page(page_index)
            pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5), alpha=False)
            out = PNG_DIR / f"page-{page_index + 1}.png"
            pix.save(out)
            print(f"png_export={out} size={out.stat().st_size}")
        pdf_doc.close()
    except Exception as exc:
        print(f"png_export_failed={type(exc).__name__}: {exc}")
    summary_path = ROOT / "_tmp_polish_summary.tsv"
    summary = summary_path.read_text(encoding="utf-8-sig", errors="replace")
    print(summary.encode("gb18030", errors="replace").decode("gb18030"))


if __name__ == "__main__":
    main()
