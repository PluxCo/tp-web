let delayed = [false, false];

let timeline_labels = [];
let timeline_values_ignored = [];
let timeline_values_correct = [];
let timeline_values_incorrect = [];

for (const timelineKey of config.timeline) {
    timeline_labels.push(timelineKey[0])
    timeline_values_correct.push(timelineKey[1])
    timeline_values_incorrect.push(timelineKey[2])
    timeline_values_ignored.push(timelineKey[3])
}

let dataset = [];
for (let i = 1; i < config.bar_data[2]; i++) {
    const a = {
        type: 'bar',
        label: 'Level ' + i.toString(),
        data: config.bar_data[1][i],
        backgroundColor: colorize_bars((i - 1) / (config.bar_data[2] - 1)),
    }
    dataset.push(Object.create(a))
}

function colorize_bars(heat) {
    const first_color = [253, 200, 48];
    const second_color = [243, 115, 53];
    const r = first_color[0] + heat * (second_color[0] - first_color[0]);
    const g = first_color[1] + heat * (second_color[1] - first_color[1]);
    const b = first_color[2] + heat * (second_color[2] - first_color[2]);
    const a = 1;

    return 'rgba(' + r + ',' + g + ',' + b + ',' + a + ')';
}

new Chart(
    document.getElementById('QuestionChart'),
    {
        data: {
            labels: config.bar_data[0],
            datasets: dataset,
        },
        options: {
            locale: 'en-US',
            maintainAspectRatio: false,
            scales: {
                y: {
                    grid: {
                        display: true,
                        color: "rgba(104,157,61,0.2)"
                    },
                    ticks: {
                        callback: (value, index, values) => {
                            return `${value} %`
                        }
                    },
                    grace: '5%',
                },
                x: {
                    grid: {
                        display: false
                    },
                }
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            let label = context.dataset.label || '';
                            if (label) {
                                label += ': ';
                            }
                            if (context.parsed.y !== null) {
                                label += `${context.parsed.y} %`;
                            }
                            return label;
                        }
                    }
                }
            },
            animation: {
                onComplete: () => {
                    delayed[0] = true;
                },
                delay: (context) => {
                    let delay = 0;
                    if (context.type === 'data' && context.mode === 'default' && !delayed[0]) {
                        delay = context.dataIndex * 300 + context.datasetIndex * 100;
                    }
                    return delay;
                },
            }
        }
    }
);

new Chart(
    document.getElementById('Timeline'),
    {
        data: {
            labels: timeline_labels,
            datasets: [
                {
                    type: 'line',
                    label: 'Ignored',
                    data: timeline_values_ignored,
                    backgroundColor: "rgba(176,176,176,0.2)",
                    borderColor: "rgb(194,194,194)",
                    hoverBackgroundColor: "rgba(185,185,185,0.4)",
                    hoverBorderColor: "rgb(180,180,180)",
                },
                {
                    type: 'line',
                    label: 'Correct',
                    data: timeline_values_correct,
                    backgroundColor: "rgba(123,185,72,0.2)",
                    borderColor: "rgb(122,204,81)",
                    hoverBackgroundColor: "rgba(138,196,76,0.4)",
                    hoverBorderColor: "rgb(136,187,73)",
                },
                {
                    type: 'line',
                    label: 'Incorrect',
                    data: timeline_values_incorrect,
                    backgroundColor: "rgba(185,72,72,0.2)",
                    borderColor: "rgb(204,81,81)",
                    hoverBackgroundColor: "rgba(196,76,76,0.4)",
                    hoverBorderColor: "rgb(187,73,73)",
                }
            ]
        },
        options: {
            locale: 'en-US',
            maintainAspectRatio: false,
            elements: {
                point: {
                    pointStyle: false
                }
            },
            scales: {
                x: {
                    type: 'time',
                    grid: {
                        display: true,
                        color: "rgba(104,157,61,0.2)",
                    },
                    ticks: {
                        maxTicksLimit: 6,
                    }
                },
                y: {
                    stacked: false,
                    grid: {
                        display: true,
                        color: "rgba(104,157,61,0.2)",
                    },
                    beginAtZero: true,
                    grace: '40%'
                }
            }
        }
    }
);

let heatmap_grid = [];
let heatmap_data = [];

for (let i = 0; i < config.bar_data[0].length; i++) {
    heatmap_data.push([]);
    for (let j = 0; j < config.bar_data[2]; j++) {
        if (j > 0) {
            heatmap_grid.push([i, j]);
        }
        heatmap_data[i].push(config.bar_data[1][j][i]);
    }
}

function colorize_heatmap(opaque, context) {
    const value = context.raw;
    const x = value[0];
    const y = value[1];
    const heat = heatmap_data[x][y] / 100;
    const first_color = [255, 247, 184];
    const second_color = [92, 178, 112];
    const r = first_color[0] + heat * (second_color[0] - first_color[0]);
    const g = first_color[1] + heat * (second_color[1] - first_color[1]);
    const b = first_color[2] + heat * (second_color[2] - first_color[2]);

    const a = 0.8;

    return 'rgba(' + r + ',' + g + ',' + b + ',' + a + ')';
}

new Chart(document.getElementById('Heatmap'), {
    type: 'scatter',
    data: {
        datasets: [{
            data: heatmap_grid,
            pointStyle: 'rect',
            pointRadius: 30,
            pointHoverRadius: 35
        }]
    },
    options: {
        maintainAspectRatio: false,
        scales: {
            x: {
                ticks: {
                    callback: function (val, index) {
                        return config.bar_data[0][val];
                    },
                },
                grid: {
                    display: true,
                    offset: true
                },
                min: -0.5,
                max: config.bar_data[0].length,
            },
            y: {
                title: {
                    display: true,
                    text: "Level",
                },
                grid: {
                    display: true,
                    offset: true
                },
                ticks: {
                    callback: function (val, index) {
                        if (val > 0) {
                            return val;
                        }
                    },
                    maxTicksLimit: config.bar_data[2] + 1
                },
                min: 0,
                max: config.bar_data[2],
            }
        },
        plugins: {
            legend: {
                display: false
            },
            tooltip: {
                callbacks: {
                    label: function (context) {
                        let label = '';
                        if (context.parsed.y !== null) {
                            label += config.bar_data[1][context.parsed.y][context.parsed.x] + '%';
                        }
                        return label;
                    }
                }
            },
        },
        elements: {
            point: {
                backgroundColor: colorize_heatmap.bind(null, false),
                borderColor: colorize_heatmap.bind(null, true),
            }
        },
        animation: {
            onComplete: () => {
                delayed[1] = true;
            },
            delay: (context) => {
                let delay = 0;
                if (context.type === 'data' && context.mode === 'default' && !delayed[1]) {
                    delay = context.dataIndex * 30 + context.datasetIndex * 10;
                }
                return delay;
            },
        }
    }
});