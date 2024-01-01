let socket = io();

window.onload = function () {
    new bootstrap.Modal("#question_modal");
    document.querySelectorAll(".question_stat").forEach(function (question_stat) {
        question_stat.addEventListener("click", function (event) {
            document.querySelector("#question_modal").querySelectorAll(".datable").forEach(function (datable) {
                datable.innerHTML = "";
                datable.classList.add("placeholder", "col-5");
            });
            bootstrap.Modal.getInstance("#question_modal").show();

            document.querySelector("#planquestionform-question_id").value = event.currentTarget.dataset.question;

            socket.emit("get_question_stat", {
                person_id: document.querySelector("#person").dataset.person,
                question_id: parseInt(event.currentTarget.dataset.question)
            });
        });

        let lastHue = 120 * question_stat.dataset.lastPoints;
        let lastAlpha = question_stat.dataset.answeredCount > 0 ? 100 : 0;
        question_stat.style.backgroundColor = `hsl(${lastHue}deg 30% 90% / ${lastAlpha}%)`;
    });
};

socket.on("question_info", function (data) {
    let modal = document.querySelector("#question_modal");

    modal.querySelector(".q_text").innerHTML = data.question.text;
    modal.querySelector(".q_groups").innerHTML = data.question.groups.map((g) => g.name).join(", ");
    modal.querySelector(".q_level").innerHTML = data.question.level;
    modal.querySelector(".q_correct").innerHTML = data.question.options ? data.question.options[data.question.answer - 1] : data.question.answer;

    let answers_tbl = modal.querySelector(".q_answers");
    answers_tbl.innerHTML = "";
    console.log(data)
    data.answers.forEach(function (answer) {
        let tr_style = "";
        switch (answer.state) {
            case "CORRECT":
                tr_style = "table-success";
                break;
            case "INCORRECT":
                tr_style = "table-warning";
                break;
            case "IGNORED":
                tr_style = "table-info";
                break;
            case "NOT_ANSWERED":
                tr_style = "table-secondary";
                break;
        }
        answers_tbl.innerHTML += `<tr class="${tr_style}">
                                    <td>${data.question.options ? data.question.options[answer.person_answer - 1] : answer.person_answer}</td>
                                    <td>${answer.points}</td>
                                    <td>${answer.ask_time}</td>
                                    <td>${answer.answer_time}</td>
                                  </tr>`;
    });

    modal.querySelectorAll(".datable").forEach(function (datable) {
        datable.classList.remove("placeholder", "col-5");
    });

});

let subjects = new Set(config.bar_data.map(l => l.subject));
let levels = new Set(config.bar_data.map(l => l.level));

let heatmapData = {
    datasets: [{
        data: [],
        backgroundColor(context) {
            const value = context.dataset.data[context.dataIndex].v;
            const hue = value / 100 * 120;
            return `hsl(${hue}deg 70% 50%)`;
        },
        borderWidth: 1,
        width: ({chart}) => (chart.chartArea || {}).width / subjects.size - 1,
        height: ({chart}) => (chart.chartArea || {}).height / levels.size - 1
    }]
};

const barsData = {
    labels: Array.from(subjects),
    datasets: []
};

for (const u of config.bar_data) {
    if (u.answered_count != 0) {
        heatmapData.datasets[0].data.push({x: u.subject, y: u.level, v: u.points / u.answered_count * 100});
    }
}

for (let level of levels) {
    let data = []

    for (let subject of subjects) {
        let info = config.bar_data.find((value, index, array) => (value.level == level && value.subject == subject));
        if (info === undefined) {
            data.push(0);
        } else {
            data.push(info.points / info.answered_count * 100);
        }
    }

    barsData.datasets.push({data: data, label: level});
}

const heatmapConfig = {
    type: 'matrix',
    data: heatmapData,
    options: {
        plugins: {
            legend: false,
            tooltip: {
                callbacks: {
                    title(context) {
                        return `${context[0].raw.v}%`;
                    },
                    label(context) {
                        const v = context.dataset.data[context.dataIndex];
                        return [`Subject: ${v.x}`, `Level: ${v.y}`, `Knowledge: ${v.v}%`];
                    }
                }
            }
        },
        scales: {
            x: {
                type: 'category',
                ticks: {
                    display: true
                },
                grid: {
                    display: false
                }
            },
            y: {
                reverse: false,
                offset: true,
                ticks: {
                    stepSize: 1
                },
                grid: {
                    display: false
                }
            }
        },
        onClick(ev, context) {
            // TODO: expanding accordion on click
            console.log(context);
        }
    }
};

const barsConfig = {
    type: 'bar',
    data: barsData,
    options: {
        scales: {
            y: {
                beginAtZero: true
            }
        }
    },
};

let heatmap = new Chart(document.getElementById('Heatmap'), heatmapConfig);
let bars = new Chart(document.getElementById("QuestionChart"), barsConfig);
