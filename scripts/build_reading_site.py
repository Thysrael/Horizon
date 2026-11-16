"""Render Horizon's Markdown digests as a small static reading-list website."""

import argparse
import html
import json
import re
import shutil
from pathlib import Path

import markdown


def page(title: str, body: str, *, date: str = "") -> str:
    title = html.escape(title)
    eyebrow = f"本期候选 · {date}" if date else "READ SLOWLY, KEEP WHAT MATTERS"
    return f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} · Jam's Reading List</title><meta name="description" content="一些值得认真读，也值得以后重读的文章。">
<link rel="stylesheet" href="/style.css"><link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Ctext y='.9em' font-size='56'%3E📖%3C/text%3E%3C/svg%3E"></head>
<body><div class="wrap"><header class="brand"><a class="wordmark" href="/">Jam's Reading List</a><a class="small" href="/archive/">往期清单 ↗</a></header>
<main><p class="eyebrow">{eyebrow}</p><h1>{title}</h1>
<p class="intro">一些值得认真读，也值得以后重读的文章。先看看推荐理由，再决定打开原文、读一读，或者收进自己的阅读清单。</p>
{body}</main><footer>这是候选阅读清单，模型推荐仅供参考。收录由我自己决定。<br>由 <a href="https://github.com/Thysrael/Horizon">Horizon</a> 整理 · <a href="https://github.com/fullstackjam/horizon">源码与订阅配置</a></footer></div></body></html>'''


def build(summaries: Path, output: Path, state: Path) -> int:
    output.mkdir(parents=True, exist_ok=True)
    (output / "archive").mkdir(exist_ok=True)
    (output / "summaries").mkdir(exist_ok=True)
    shutil.copyfile("site/style.css", output / "style.css")
    (output / "CNAME").write_text("horizon.fullstackjam.com\n")
    (output / ".nojekyll").touch()
    entries = []
    for source in sorted(summaries.glob("horizon-*-zh.md"), reverse=True):
        match = re.fullmatch(r"horizon-(\d{4}-\d{2}-\d{2})-zh\.md", source.name)
        if not match:
            continue
        date = match[1]
        text = source.read_text(encoding="utf-8")
        text = text.replace("&\\#x27;", "'")
        text = re.sub(r"(\*\*[^\n]+\*\*)\n(?=1\. )", r"\1\n\n", text)
        text = re.sub(r"\A# [^\n]+\n", "", text)
        text = re.sub(r"从 (\d+) 条内容中筛选出 (\d+) 条重要资讯。", r"从 \1 篇候选中选出 \2 篇值得读的文章。", text)
        body = '<article>' + markdown.markdown(text, extensions=["extra", "sane_lists"]) + '</article>'
        rendered = page("给自己留一点阅读时间", body, date=date)
        (output / "archive" / f"{date}.html").write_text(rendered, encoding="utf-8")
        shutil.copyfile(source, output / "summaries" / source.name)
        entries.append((date, rendered))
    if entries:
        (output / "index.html").write_text(entries[0][1], encoding="utf-8")
    else:
        (output / "index.html").write_text(page("给自己留一点阅读时间", '<p class="empty">第一期正在准备中。</p>'), encoding="utf-8")
    links = ''.join(f'<li><time>{date}</time><a href="/archive/{date}.html">查看本期阅读清单 →</a></li>' for date, _ in entries)
    (output / "archive" / "index.html").write_text(page("往期阅读清单", f'<ul class="archive">{links}</ul>'), encoding="utf-8")
    if state.exists():
        json.loads(state.read_text())
        shutil.copyfile(state, output / "last-run.json")
    print(f"Built {len(entries)} reading lists in {output}")
    return len(entries)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--summaries", type=Path, default=Path("data/summaries"))
    parser.add_argument("--output", type=Path, default=Path("public"))
    parser.add_argument("--state", type=Path, default=Path("data/last-run.json"))
    args = parser.parse_args()
    build(args.summaries, args.output, args.state)
