#!/usr/bin/env python3
"""Render PPTX with explicit local CJK font discovery (macOS/Linux).

Uses an isolated LibreOffice profile and temporary Fontconfig configuration;
does not install fonts, change the PPTX, or modify global font preferences.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from xml.etree import ElementTree as ET


CJK_FAMILIES = (
    'Microsoft YaHei', 'PingFang SC', 'Noto Sans CJK SC',
    'Source Han Sans SC', 'WenQuanYi Micro Hei',
)


def font_config(cache, cjk_family=None):
    root = ET.Element('fontconfig')
    for config in (
        '/etc/fonts/fonts.conf', '/opt/homebrew/etc/fonts/fonts.conf',
        '/usr/local/etc/fonts/fonts.conf',
    ):
        if Path(config).is_file():
            ET.SubElement(root, 'include', ignore_missing='yes').text = config
    for directory in (
        '/System/Library/Fonts', '/System/Library/Fonts/Supplemental',
        '/Library/Fonts', '~/Library/Fonts', '/usr/share/fonts',
        '/usr/local/share/fonts', '~/.local/share/fonts', '~/.fonts',
    ):
        path = Path(directory).expanduser()
        if path.is_dir():
            ET.SubElement(root, 'dir').text = str(path)
    ET.SubElement(root, 'cachedir').text = str(cache)
    if cjk_family and cjk_family != 'Microsoft YaHei':
        match = ET.SubElement(root, 'match', target='pattern')
        test = ET.SubElement(match, 'test', name='family', compare='eq')
        ET.SubElement(test, 'string').text = 'Microsoft YaHei'
        edit = ET.SubElement(match, 'edit', name='family', mode='prepend', binding='strong')
        ET.SubElement(edit, 'string').text = cjk_family
    return ET.tostring(root, encoding='unicode')


def choose_cjk(installed, requested=None):
    # fc-match silently substitutes missing families; require actual presence.
    names = {name.strip().casefold() for line in installed.splitlines()
             for name in line.split(',') if name.strip()}
    for family in ([requested] if requested else CJK_FAMILIES):
        if family.casefold() in names:
            return family
    wanted = requested or '、'.join(CJK_FAMILIES)
    raise ValueError(f'未发现支持中文的已安装字体：{wanted}。请先安装字体或使用 --cjk-font 指定。')


def run(command, env):
    return subprocess.run(command, env=env, check=True, text=True,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=180)


def render(args):
    source = args.pptx.expanduser().resolve()
    if not source.is_file() or source.suffix.lower() != '.pptx':
        raise ValueError(f'需要存在的 PPTX 文件：{source}')
    if sys.platform == 'win32':
        raise ValueError('此脚本面向 macOS/Linux；Windows 请在 PowerPoint 中安装所需字体后导出。')
    output_dir = args.output_dir.expanduser().resolve()
    target = output_dir / (source.stem + '.pdf')
    if target.exists() and not args.overwrite:
        raise ValueError(f'文件已存在：{target}；如需覆盖请加 --overwrite。')
    executables = {}
    for name, value in [('soffice', args.soffice), ('fc-list', 'fc-list'), ('fc-match', 'fc-match')]:
        executable = shutil.which(value)
        if not executable and name == 'soffice':
            app = Path('/Applications/LibreOffice.app/Contents/MacOS/soffice')
            if value == 'soffice' and app.is_file():
                executable = str(app)
        if not executable:
            raise ValueError(f'找不到 {value}；请安装 LibreOffice 与 Fontconfig，或检查 PATH。')
        executables[name] = executable
    with tempfile.TemporaryDirectory(prefix='ustc-ppt-render-') as tmp:
        temp = Path(tmp)
        config = temp / 'fonts.conf'
        config.write_text(font_config(temp / 'fontcache'), encoding='utf-8')
        env = dict(os.environ, FONTCONFIG_FILE=str(config))
        installed = run([executables['fc-list'], ':lang=zh', '--format=%{family}\n'], env).stdout
        family = choose_cjk(installed, args.cjk_font)
        config.write_text(font_config(temp / 'fontcache', family), encoding='utf-8')
        resolved = {}
        for name in ['Arial', 'Microsoft YaHei']:
            resolved[name] = run([executables['fc-match'], '--format=%{family}\n', name], env).stdout.strip()
        if family.casefold() not in {n.strip().casefold() for n in resolved['Microsoft YaHei'].split(',')}:
            raise ValueError(f'中文字体替换未生效：{resolved["Microsoft YaHei"]}')
        print(f'中文字体：{resolved["Microsoft YaHei"]}；英文字体：{resolved["Arial"]}', flush=True)
        staging = temp / 'output'
        staging.mkdir()
        command = [executables['soffice'], '-env:UserInstallation=' + (temp / 'profile').as_uri(),
                   '--headless', '--convert-to', 'pdf:impress_pdf_Export',
                   '--outdir', str(staging), str(source)]
        result = run(command, env)
        generated = staging / target.name
        if not generated.is_file() or generated.stat().st_size == 0:
            raise ValueError('LibreOffice 未生成 PDF：' + result.stdout + result.stderr)
        output_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(generated, target)
        report = {'input': str(source), 'output': str(target), 'requested_cjk': family,
                  'fontconfig_matches': resolved,
                  'note': '字体匹配为 Fontconfig 预检结果；仍需检查 PDF 的实际排版。'}
        target.with_suffix('.font-rendering.json').write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print(f'已导出：{target}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('pptx', type=Path)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--cjk-font', help='指定已安装且支持中文的字体；默认按模板后备顺序检测')
    parser.add_argument('--soffice', default='soffice', help='LibreOffice soffice 可执行文件路径')
    parser.add_argument('--overwrite', action='store_true')
    args = parser.parse_args()
    try:
        render(args)
    except (ValueError, OSError, subprocess.SubprocessError) as exc:
        print(f'导出失败：{exc}', file=sys.stderr)
        if isinstance(exc, subprocess.CalledProcessError):
            print((exc.stdout or '') + (exc.stderr or ''), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
