import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

fig, ax = plt.subplots(1, 1, figsize=(14, 6))
ax.set_xlim(0, 14)
ax.set_ylim(0, 6)
ax.axis('off')

colors = {
    'csv': '#4ecdc4',
    'pg': '#45b7d1', 
    'dbt': '#f9ca24',
    'dash': '#eb4d4b'
}

boxes = [
    (1, 2.5, 'CSV Files', colors['csv'], ['customers.csv', 'orders.csv', 'order_items.csv']),
    (4.5, 2.5, 'PostgreSQL 17', colors['pg'], ['Raw tables', 'Staging views', 'Docker container']),
    (8, 2.5, 'dbt Models', colors['dbt'], ['stg_* (views)', 'dim_* (tables)', 'fact_order_items', '30 tests \u2713']),
    (11.5, 2.5, 'Evidence Dashboard', colors['dash'], ['Monthly Revenue', 'Top Products', 'Retention Cohort'])
]

for x, y, title, color, details in boxes:
    box = FancyBboxPatch((x-1.2, y-1), 2.4, 2, boxstyle="round,pad=0.1", 
                         facecolor=color, edgecolor='none', alpha=0.95)
    ax.add_patch(box)
    ax.text(x, y+0.3, title, ha='center', va='center', fontsize=14, fontweight='bold', color='white')
    for i, d in enumerate(details):
        ax.text(x, y-0.15 - i*0.3, d, ha='center', va='center', fontsize=9, color='white', alpha=0.95)

arrow_props = dict(arrowstyle='->', color='#6c757d', lw=2, shrinkA=5, shrinkB=5)
ax.annotate('', xy=(4.5-1.2, 2.5), xytext=(1+1.2, 2.5), arrowprops=arrow_props)
ax.annotate('', xy=(8-1.2, 2.5), xytext=(4.5+1.2, 2.5), arrowprops=arrow_props)
ax.annotate('', xy=(11.5-1.2, 2.5), xytext=(8+1.2, 2.5), arrowprops=arrow_props)

stages = [
    (1, 0.5, 'Stage 1', '#4ecdc4', 'Extract'),
    (4.5, 0.5, 'Stage 2', '#45b7d1', 'Load & Model'),
    (8, 0.5, 'Stage 3-4', '#f9ca24', 'Transform & Test'),
    (11.5, 0.5, 'Stage 5-6', '#eb4d4b', 'Visualize & Deploy')
]

for x, y, label, color, desc in stages:
    ax.text(x, y, label, ha='center', va='center', fontsize=12, fontweight='bold', color=color)
    ax.text(x, y-0.3, desc, ha='center', va='center', fontsize=9, color='#6c757d')

ax.text(7, 5.5, 'E-Commerce Data Warehouse Pipeline Architecture', ha='center', va='center', 
        fontsize=18, fontweight='bold', color='#1a1a2e')

plt.tight_layout()
plt.savefig('docs/architecture.png', dpi=200, bbox_inches='tight', facecolor='#f8f9fa')
plt.savefig('docs/architecture.svg', bbox_inches='tight', facecolor='#f8f9fa')
print("Architecture diagram saved!")
