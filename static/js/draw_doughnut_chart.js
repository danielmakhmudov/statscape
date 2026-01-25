document.addEventListener('DOMContentLoaded', function() {
    const labels = JSON.parse(document.getElementById('chart_labels').textContent);
    const values = JSON.parse(document.getElementById('chart_values').textContent);
    const hours = JSON.parse(document.getElementById('chart_hours').textContent);

    const palette = [
    '#4ade80','#22c55e','#16a34a','#15803d','#facc15',
    '#fb923c','#f97316','#ef4444','#8b5cf6','#6366f1','#94a3b8'
    ];

    const ctx = document.getElementById('playtime-doughnut');
    new Chart(ctx, {
    type: 'doughnut',
    data: {
        labels,
        datasets: [{
        data: values,
        backgroundColor: labels.map((_, i) => palette[i % palette.length]),
        borderWidth: 1,
        }]
    },
    options: {
        plugins: {
        legend: { position: 'right' },
        tooltip: {
            callbacks: {
                label: (context) => {
                const hoursValue = hours[context.dataIndex];
                return `${context.parsed}%(${hoursValue}h)`;
            }
            }
        }
        }
    }
    });
});