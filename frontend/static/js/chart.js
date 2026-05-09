/**
 * TDOA Chart Utilities
 * Chart.js wrapper untuk TDOA visualization
 */

const ChartUtils = {
    /**
     * Default chart config
     */
    defaultOptions: {
        responsive: true,
        maintainAspectRatio: true,
        plugins: {
            legend: {
                position: 'top'
            }
        },
        scales: {
            y: {
                beginAtZero: true
            }
        }
    },
    
    /**
     * Create line chart
     */
    createLineChart(canvas, label, data, options = {}) {
        const config = {
            type: 'line',
            data: {
                labels: Array.from({length: data.length}, (_, i) => i),
                datasets: [{
                    label: label,
                    data: data,
                    borderColor: '#667eea',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: { ...this.defaultOptions, ...options }
        };
        
        return new Chart(canvas, config);
    },
    
    /**
     * Create bar chart
     */
    createBarChart(canvas, labels, datasets, options = {}) {
        const config = {
            type: 'bar',
            data: {
                labels: labels,
                datasets: datasets.map((dataset, idx) => ({
                    label: dataset.label,
                    data: dataset.data,
                    backgroundColor: [
                        '#667eea',
                        '#764ba2',
                        '#f093fb',
                        '#4facfe'
                    ][idx % 4]
                }))
            },
            options: { ...this.defaultOptions, ...options }
        };
        
        return new Chart(canvas, config);
    },
    
    /**
     * Create scatter chart
     */
    createScatterChart(canvas, label, points, options = {}) {
        const config = {
            type: 'scatter',
            data: {
                datasets: [{
                    label: label,
                    data: points,
                    backgroundColor: '#667eea',
                    borderColor: '#667eea'
                }]
            },
            options: { ...this.defaultOptions, ...options }
        };
        
        return new Chart(canvas, config);
    }
};