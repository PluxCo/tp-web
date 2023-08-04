let delayed;

let timeline_labels = [];
let timeline_values_ignored = [];
let timeline_values_correct = [];
let timeline_values_incorrect = [];

for (const timelineKey of config.timeline) {
    timeline_labels.push(timelineKey[0])
    timeline_values_ignored.push(timelineKey[1])
    timeline_values_correct.push(timelineKey[2])
    timeline_values_incorrect.push(timelineKey[3])
}

let dataset = [];
for (let i = 0; i < config.bar_data[2]; i++) {
    const a = {
        type: 'bar',
        label: 'Level ' + (i + 1).toString(),
        data: config.bar_data[1][i],
        // backgroundColor: "rgba(123,185,72,0.2)",
        // borderColor: "rgb(122,204,81)",
        // borderWidth: 2,
        // hoverBackgroundColor: "rgba(138,196,76,0.4)",
        // hoverBorderColor: "rgb(136,187,73)",
    }
    dataset.push(Object.create(a))
}

new Chart(
    document.getElementById('QuestionChart'),
    {
        data: {
            labels: config.bar_data[0],
            datasets: dataset
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
                },
                colorschemes: {
                    scheme: 'brewer.Paired12'
                }
            },
            animation: {
                onComplete: () => {
                    delayed = true;
                },
                delay: (context) => {
                    let delay = 0;
                    if (context.type === 'data' && !delayed) {
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
                }
            }
        }
    }
);