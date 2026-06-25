"""自定义颜色选择器 Widget"""
from django import forms
from django.utils.safestring import mark_safe


class ColorPaletteWidget(forms.Widget):
    """多色板选择器：点击色块弹出取色器，自动拼接为HEX字符串"""

    DEFAULT_COLORS = [
        '#3b82f6', '#ef4444', '#10b981', '#f59e0b',
        '#8b5cf6', '#ec4899', '#06b6d4', '#84cc16',
        '#f97316', '#6366f1', '#14b8a6', '#e11d48',
    ]

    def __init__(self, num_colors=12, attrs=None):
        self.num_colors = num_colors
        super().__init__(attrs)

    def render(self, name, value, attrs=None, renderer=None):
        # value 是逗号分隔的HEX字符串
        colors = []
        if value:
            colors = [c.strip() for c in value.split(',') if c.strip()]
        # 补齐到 num_colors
        while len(colors) < self.num_colors:
            colors.append('#cccccc')
        colors = colors[:self.num_colors]

        input_id = attrs.get('id', name) if attrs else name

        html = f'<div class="color-palette-widget" id="{input_id}_palette">'
        for i, color in enumerate(colors):
            html += f'''
            <div class="color-swatch-wrap" data-idx="{i}">
                <input type="color" value="{color}" 
                    class="color-swatch-input" 
                    data-idx="{i}"
                    data-target="{input_id}"
                    onchange="updateColorValue(this)"
                    style="width:40px;height:40px;border:none;cursor:pointer;border-radius:6px;padding:0;">
                <span class="color-swatch-label" style="font-size:0.7rem;color:#64748b;display:block;text-align:center;margin-top:2px;">{color}</span>
            </div>
            '''
        html += '</div>'

        # 隐藏的文本输入框，存储实际值
        html += f'<input type="hidden" name="{name}" id="{input_id}" value="{value or ""}">'

        # JS
        html += '''
        <script>
        function updateColorValue(el) {
            var idx = el.dataset.idx;
            var targetId = el.dataset.target;
            var newColor = el.value;
            // 更新标签
            el.parentElement.querySelector('.color-swatch-label').textContent = newColor;
            // 拼接所有颜色
            var inputs = el.closest('.color-palette-widget').querySelectorAll('.color-swatch-input');
            var colors = [];
            inputs.forEach(function(inp) { colors.push(inp.value); });
            document.getElementById(targetId).value = colors.join(',');
        }
        </script>
        '''

        # CSS
        html += '''
        <style>
        .color-palette-widget { display: flex; flex-wrap: wrap; gap: 8px; padding: 8px 0; }
        .color-swatch-wrap { text-align: center; }
        .color-swatch-input { border: 2px solid #e2e8f0 !important; border-radius: 6px !important; }
        .color-swatch-input:hover { border-color: #3b82f6 !important; }
        </style>
        '''

        return mark_safe(html)