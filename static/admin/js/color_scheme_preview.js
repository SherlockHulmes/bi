/* 配色方案预览 - 在 select 下拉框旁显示颜色条 */
(function() {
    var colorSchemes = {
        'default': ['#3b82f6','#ef4444','#10b981','#f59e0b','#8b5cf6','#ec4899','#06b6d4','#84cc16','#f97316','#6366f1','#14b8a6','#e11d48'],
        'business': ['#475569','#64748b','#94a3b8','#0ea5e9','#8b5cf6','#d946ef','#059669','#eab308','#f97316','#0d9488','#7c3aed','#155e75'],
        'vibrant': ['#f43f5e','#a855f7','#06b6d4','#f97316','#22c55e','#3b82f6','#ec4899','#eab308','#14b8a6','#6366f1','#ef4444','#8b5cf6'],
        'morandi': ['#8b7355','#a69279','#6b8e6b','#c4a882','#7a6f8a','#5b7b7b','#9b8a76','#8fbc8f','#b8a088','#7b8e97','#a0a0a0','#c0a888'],
        'earth': ['#92400e','#854d0e','#3f6212','#1e3a5f','#7e22ce','#be185d','#b45309','#a16207','#4d7c0f','#155e75','#6b21a8','#9f1239'],
        'mint': ['#0d9488','#0891b2','#059669','#16a34a','#2563eb','#7c3aed','#f43f5e','#f97316','#eab308','#06b6d4','#8b5cf6','#ec4899']
    };

    function createPreview(selectEl) {
        // 移除旧预览
        var old = selectEl.parentElement.querySelector('.scheme-preview-bar');
        if (old) old.remove();

        var val = selectEl.value;
        if (val === 'custom' || !colorSchemes[val]) return;

        var colors = colorSchemes[val];
        var bar = document.createElement('div');
        bar.className = 'scheme-preview-bar';
        bar.style.cssText = 'display:flex;gap:2px;margin-top:4px;flex-wrap:wrap;';
        colors.forEach(function(c) {
            var dot = document.createElement('span');
            dot.style.cssText = 'display:inline-block;width:18px;height:18px;border-radius:3px;background:' + c + ';border:1px solid #e2e8f0;';
            dot.title = c;
            bar.appendChild(dot);
        });
        selectEl.parentElement.appendChild(bar);
    }

    function init() {
        var sel = document.getElementById('id_color_scheme');
        if (!sel) return;
        sel.addEventListener('change', function() { createPreview(sel); });
        // 也给 option 加颜色预览
        createPreview(sel);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();