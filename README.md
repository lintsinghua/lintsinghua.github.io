# 御舆 · 在线阅读网站

[在线阅读](https://lintsinghua.github.io/) · [书籍仓库](https://github.com/lintsinghua/claude-code-book)

## 自动发布

网站的 `main` 分支推送后，GitHub Actions 自动检查并部署到 GitHub Pages。工作流每 5 小时检查书籍仓库是否更新；两个仓库均无变化时跳过构建与部署。GitHub 定时任务可能排队，检查频率不等于严格的上线时限。也可以在 Actions 中手动运行 **Deploy book reader**。

发布前检查 Markdown 链接、Mermaid 语法和测试。检查失败时不替换线上版本。部署只使用 GitHub Actions 自带的权限，不需要额外的个人访问令牌。

## 内容与缓存

每次发布将正文和封面一起打包到带书籍版本号的路径中，页面不会混用不同版本的文件。`version.json` 记录书籍、网站和完整发布的版本。

页面打开时、切回标签页时以及每 60 秒检查一次新发布。检测到更新后，页面以新的版本参数刷新，保留当前章节与语言偏好。离线或版本检查失败时保留当前页面，待下次检查重试。这通过更新资源地址避开旧缓存，不依赖 GitHub Pages 提供 CDN 清除接口。

## 本地构建

需要 Python 3、Node.js 22 或更新版本，以及一份已检出的书籍仓库：

```sh
python3 -m unittest discover -s tests
node --test tests/test_reader.mjs
python3 scripts/build_site.py --book /path/to/claude-code-book --output /tmp/book-reader-preview
python3 -m http.server 8000 --directory /tmp/book-reader-preview
```

`index.html` 是构建模板，请预览生成目录。输出目录必须尚不存在。
