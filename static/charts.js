new Chart(
    document.getElementById('QuestionChart'),
    {
        data: {
            labels: config.bar_labels,
            datasets: [
                {
                    type: 'bar',
                    label: 'Questions answered correctly',
                    data: config.bar_values,
                    backgroundColor: "rgba(123,185,72,0.2)",
                    borderColor: "rgb(122,204,81)",
                    borderWidth: 2,
                    hoverBackgroundColor: "rgba(138,196,76,0.4)",
                    hoverBorderColor: "rgb(136,187,73)",
                }
            ]
        },
        options: {
            locale: 'ru-RU',
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
                    max: 100
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
            }
        }
    }
);

new Chart(
    document.getElementById('Timeline'),
    {
        data: {
            labels: config.timeline_labels,
            datasets: [
                {
                    type: 'line',
                    label: 'Ignored',
                    data: config.timeline_values_ignored,
                    backgroundColor: "rgba(176,176,176,0.2)",
                    borderColor: "rgb(194,194,194)",
                    hoverBackgroundColor: "rgba(185,185,185,0.4)",
                    hoverBorderColor: "rgb(180,180,180)",
                },
                {
                    type: 'line',
                    label: 'Correct',
                    data: config.timeline_values_correct,
                    backgroundColor: "rgba(123,185,72,0.2)",
                    borderColor: "rgb(122,204,81)",
                    hoverBackgroundColor: "rgba(138,196,76,0.4)",
                    hoverBorderColor: "rgb(136,187,73)",
                },
                {
                    type: 'line',
                    label: 'Incorrect',
                    data: config.timeline_values_incorrect,
                    backgroundColor: "rgba(185,72,72,0.2)",
                    borderColor: "rgb(204,81,81)",
                    hoverBackgroundColor: "rgba(196,76,76,0.4)",
                    hoverBorderColor: "rgb(187,73,73)",
                }
            ]
        },
        options: {
            locale: 'ru-RU',
            maintainAspectRatio: false,
            elements: {
                point: {
                    pointStyle: false
                }
            },
            scales: {
                x: {
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