# 演示项目：绿萝黄叶排查（svg 路线，S 纯排版）

一套 5 页的演示，展示 svg 路线下 S 页的排版效果。内容是演示用的通用知识，不代表任何账号。

| 页 | 版式 | 风格 |
|---|---|---|
| P01 | L15 纯字排大字报（封面 C01） | V11 |
| P02 | L05 步骤流程 | V03 |
| P03 | L23 多列对比表 | V03 |
| P04 | L24 对错示范 | V03 |
| P05 | L35 总结尾页 | V03 |

![预览](preview.jpg)

## 自己重新渲染

页面 HTML 引用 `../../render/base.css`。在仓库根目录运行：

```bash
cp skills/image-passage/assets/css/base.css examples/demo/render/
python3 skills/image-passage/scripts/fetch_fonts.py
python3 skills/image-passage/scripts/render_page.py examples/demo/pages/P0*/page.html --out-dir /tmp/demo-out
```

`render/tokens.css` 由下面的命令生成（风格锁精确版）：

```bash
python3 skills/image-passage/scripts/palette.py tokens --out examples/demo/render/tokens.css \
  --bg 暖米白 --surface 纯白 --text 炭灰 --primary 鼠尾草绿 --accent 珊瑚橙 --highlight 奶油黄 \
  --font-title noto-sans-sc --font-body noto-sans-sc --font-hand lxgw-wenkai
```
