"""JavaScript脚本"""


def get_hexagram_click_script(hexagram_names: list) -> str:
    """生成卦象点击的JavaScript - 设置URL参数触发页面刷新"""
    if not hexagram_names:
        return ""

    names_json = '|'.join(hexagram_names)

    return f'''
    <script>
        const hexagramNames = "{names_json}".split("|");

        // Find all hexagram tags and add click listeners
        setTimeout(function() {{
            hexagramNames.forEach(function(name) {{
                var tags = document.querySelectorAll('.hexagram-tag[data-hexagram="' + name + '"]');
                tags.forEach(function(tag) {{
                    tag.style.cursor = 'pointer';
                    tag.addEventListener('click', function(e) {{
                        e.stopPropagation();
                        var url = new URL(window.location);
                        url.searchParams.set('show_hex', name);
                        window.location.href = url.toString();
                    }});
                }});
            }});
        }}, 500);
    </script>
    '''
