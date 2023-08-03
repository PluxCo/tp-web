const bubble_chart_canvas = document.getElementById('TimeLine');

const bubble_chart = new Chart(
    bubble_chart_canvas,
    {
        type: 'bubble',
        data: {
            datasets: [
                {
                    label: 'Questions answered correctly',
                    data: config.timeline_data_correct,
                    backgroundColor: "rgba(123,185,72,0.2)",
                    borderColor: "rgb(122,204,81)",
                    hoverBackgroundColor: "rgba(138,196,76,0.4)",
                    hoverBorderColor: "rgb(136,187,73)",
                },
                {
                    label: 'Questions answered incorrectly',
                    data: config.timeline_data_incorrect,
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
            scales: {
                y: {
                    grid: {
                        display: true,
                        color: "rgba(104,157,61,0.2)"
                    },
                    display: false,
                    grace: '5%'
                },
                x: {
                    type: 'time',
                    ticks: {
                        major: {
                            enabled: true
                        },
                        autoSkip: true,
                        autoSkipPadding: 50,
                        maxRotation: 0,
                    },
                    grid: {
                        display: true
                    }
                }
            },
            plugins: {
                legend: {
                    position: 'bottom'
                },
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            let date = new Date(context.parsed.x).toString().split(' ')
                            let label = date[1] + ' ' + date[2] + ': '
                            if (context.parsed.y !== null) {
                                label += config.id_to_name[context.parsed.y];
                            }
                            return label;
                        }
                    }
                },
                zoom: {
                    pan: {
                        enabled: true,
                        mode: 'xy',
                        modifierKey: 'ctrl',
                    },
                    zoom: {
                        mode: 'xy',
                        drag: {
                            enabled: true,
                            borderColor: 'rgb(54, 162, 235)',
                            borderWidth: 1,
                            backgroundColor: 'rgba(54, 162, 235, 0.3)'
                        }
                    }
                }
            }
        }
    }
)

bubble_chart_canvas.onclick = (evt) => {
    const res = bubble_chart.getElementsAtEventForMode(evt, 'nearest', {intersect: true}, true);

    if (res.length === 0) {
        return;
    }

    window.location.href = "/statistic/" + bubble_chart.data.datasets[res[0].datasetIndex].data[res[0].index].y;
};

var manager = new Hammer.Manager(bubble_chart_canvas);

var DoubleTap = new Hammer.Tap({
    event: 'doubletap',
    taps: 2
});

manager.add(DoubleTap);

manager.on('doubletap', function (e) {
    bubble_chart.resetZoom();
});
