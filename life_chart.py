import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from datetime import datetime

def generate_high_quality_life_chart(birth_date_str: str, weeks_per_year=52, total_years=70):
    """
    Генерирует график жизни:
    - Прожитые недели – синий (#1f77b4),
    - Остальные – светло-серые (#cccccc).
    В графике отсутствуют подписи по осям (числа слева и сверху),
    заголовок: "70 лет жизни в неделях".
    """
    birth_date = datetime.strptime(birth_date_str, "%d.%m.%Y")
    today = datetime.today()
    
    total_days = (today - birth_date).days
    weeks_lived = total_days // 7
    total_weeks = weeks_per_year * total_years

    # Размер изображения оптимизирован для Telegram
    fig, ax = plt.subplots(figsize=(8, 12), dpi=150)
    ax.set_xlim(0, weeks_per_year)
    ax.set_ylim(0, total_years)
    ax.invert_yaxis()
    ax.set_facecolor("#f0f0f0")  # светлый фон

    # Рисуем квадраты
    for week in range(total_weeks):
        x = week % weeks_per_year
        y = week // weeks_per_year
        facecolor = '#1f77b4' if week < weeks_lived else '#cccccc'
        rect = patches.Rectangle((x, y), 1, 1, linewidth=0.2, edgecolor='white', facecolor=facecolor)
        ax.add_patch(rect)

    # Убираем подписи осей
    ax.set_xticks([])
    ax.set_yticks([])

    # Заголовок
    ax.set_title("70 лет жизни в неделях", fontsize=16, fontname="Arial", color='black', pad=20)

    # Убираем рамки для чистого вида
    for spine in ax.spines.values():
        spine.set_visible(False)

    image_path = "life_chart.png"
    plt.savefig(image_path, bbox_inches='tight')
    plt.close()
    return image_path, weeks_lived