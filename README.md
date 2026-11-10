# README

这里是清雨影的Blog。

对于我个人来说，是一份技术备忘录，对于读者来说，可以是随时查阅的工具站点。

我工作之余写各种开源软件，希望能给这个世界带来哪怕一点点的便利或者贡献，这个博客的目的也是一样的。

如果这个博客对你有帮助，或者你发现了错误，欢迎随时通过邮箱 nigel434ATgmail.com (请将AT替换为@，这么做是为了防止垃圾邮件) 联系我。

我很乐于看到我写的东西对读者有帮助，仅这一条就可以构成我写作的原始动力了。

## 关于转载

你可以转载任何你想转载的文章，但是请带上原地址。

## 源码

这个博客的源代码在：[TsingJyujing/blogs](https://github.com/TsingJyujing/blogs)。

目前不支持RSS订阅，但是你可以关注这个Github项目Commit的RSS。

---

## 环境与启动

安装 Git 和 Hugo **0.158.0 或更高版本**。主题通过 Git submodule 管理，克隆站点后先初始化主题，再启动预览；无需安装 Go 或 Node.js。

```sh
git submodule update --init --recursive
hugo server -D --bind 127.0.0.1
```

## 主题版本与定制

主题以 Git submodule 引入 [hugo-book](https://github.com/alex-shpak/hugo-book)，路径为 `themes/hugo-book/`，当前固定到 [v0.15.0](https://github.com/alex-shpak/hugo-book/releases/tag/v0.15.0)，提交 `027be3349d20785efeb93f6773872a35497d7258`，保留上游 MIT 许可证。父仓库记录具体提交，使每次克隆得到相同版本。

升级主题时，在项目根目录执行以下命令，将 `HUGO_BOOK_VERSION` 改为目标发布标签：

```sh
HUGO_BOOK_VERSION=v0.15.0
git -C themes/hugo-book fetch --tags
git -C themes/hugo-book switch --detach "$HUGO_BOOK_VERSION"
hugo --minify --panicOnWarning
git add themes/hugo-book
```

构建并检查首页、文章、公式和移动端导航后，提交父仓库中的主题指针；首次提交站点时，一并提交 `.gitmodules`。站点定制继续放在 `assets/styles/custom.css` 和 `layouts/` 中。