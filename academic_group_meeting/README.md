# academic_group_meeting · 简约学术组会

这是可直接被 ppt-master 使用的模板工作区。使用时提供本目录路径；不要只提供内部 templates 文件夹。

- templates/：10个可复用SVG与设计规范。
- images/：校徽及完整校名标识。
- exports/简约学术组会_版式示例.pptx：用于手工编辑的示例演示文稿。
- exports/academic_group_meeting_template_preview.pptx：通用占位符预览。
- exports/版式总览.png：全套视觉预览。

手工使用：复制所需正文页，替换标题、图表和解释；页尾改为实际论文来源。背景色带和校徽在“视图—幻灯片母版”中编辑。章节导航需按实际章节调整高亮及文字颜色；当前示例正文高亮方法设计。图表区域为通用object槽，插入图片/图表后移除提示文字。参考文献条目是格式示例，使用时替换为真实条目。

AI使用：优先左文右图；宽幅图用上图下文；比较用双栏；特殊内容用自由页。先读取 templates/design_spec.md，保持本模板的配色、字体、标识与导航规则。不要为每页新增装饰或强制填满留白。

完整安装与使用提示词见[仓库 README](../README.md#使用-ppt-master-应用模板)。

字体与导出：制作前确认中文字体可用；交付前检查实际 PPTX 导出的 PDF。中文缺字和意外换行的处理方法见[字体渲染与导出修复](../docs/font-rendering.md)。仓库提供字体检测与 PDF 导出脚本，以及针对 ppt-master 6.8.0 的可选宽度补丁。SVG 预览正常并不代表 Office/LibreOffice 的排版一定相同。

模板及改编贡献依 [CC BY-NC-SA 4.0](../LICENSE) 分享；校徽、校名等第三方素材的来源与权利范围见 [THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md)。
