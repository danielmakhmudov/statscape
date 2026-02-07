document.addEventListener('DOMContentLoaded', function() {
    const labels = JSON.parse(document.getElementById('chart_labels').textContent);
    const values = JSON.parse(document.getElementById('chart_values').textContent);
    const hours = JSON.parse(document.getElementById('chart_hours').textContent);

    const palette = [
        '#34d399', '#38bdf8', '#a78bfa', '#fb923c', '#22d3ee',
        '#fbbf24', '#4ade80', '#0ea5e9', '#84cc16', '#f97316',
        '#06b6d4', '#facc15'
    ];

    function darkenHex(hex, factor) {
        const n = hex.slice(1);
        const r = Math.round(parseInt(n.substr(0, 2), 16) * factor);
        const g = Math.round(parseInt(n.substr(2, 2), 16) * factor);
        const b = Math.round(parseInt(n.substr(4, 2), 16) * factor);
        return '#' + [r, g, b].map(x => ('0' + Math.min(255, x).toString(16)).slice(-2)).join('');
    }

    const ctx = document.getElementById('playtime-doughnut');
    new Chart(ctx, {
    type: 'doughnut',
    data: {
        labels,
        datasets: [{
        data: values,
        backgroundColor: function(context) {
            const chart = context.chart;
            const ctx2d = chart.ctx;
            if (!chart.chartArea) return palette[context.dataIndex % palette.length];
            const a = chart.chartArea;
            const gradient = ctx2d.createLinearGradient(0, a.top, 0, a.bottom);
            const base = palette[context.dataIndex % palette.length];
            gradient.addColorStop(0, base);
            gradient.addColorStop(1, darkenHex(base, 0.55));
            return gradient;
        },
        borderWidth: 0,
        }]
    },
    options: {
        plugins: {
        legend: {
            position: 'right',
            borderWidth: 0,
            labels: {
                useBorder: false,
                boxWidth: 24,
                boxHeight: 10,
                padding: 12
            }
        },
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