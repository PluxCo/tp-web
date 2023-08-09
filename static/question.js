// let config_table = {
//     data: dataSet,
//     columns: [
//         {
//             "data": 'id',
//             title: "#"
//         },
//         {
//             "data": 'text',
//             title: "Text"
//         },
//         {
//             "data": 'subject',
//             title: "Subject"
//         },
//         {
//             "data": 'options',
//             title: "Options",
//             width: '30%'
//         },
//         {
//             "data": 'answer',
//             title: "Answer index"
//         },
//         {
//             "data": 'groups',
//             title: "Groups"
//         },
//         {
//             "data": 'level',
//             title: "Difficulty"
//         },
//         {
//             "data": 'article',
//             title: "Article",
//             render: function (data, type, row) {
//                 if (row.article === "none") {
//                     return 'none'
//                 }
//                 return '<a href="' + row.article + '" target="_new">' + data + '</a>';
//             }
//         }
//     ],
// }

const table = new DataTable('#table', {columns: [{}, {}, {}, {width: "30%"}, {}, {}, {}, {}]});


table.on('click', 'tbody tr', (e) => {
    let classList = e.currentTarget.classList;

    if (classList.contains('selected')) {
        classList.remove('selected');
        document.getElementById('edit_button').disabled = true;
        document.getElementById('delete_button').disabled = true;
    } else {
        table.rows('.selected').nodes().each((row) => row.classList.remove('selected'));
        classList.add('selected');
        document.getElementById('edit_button').disabled = false;
        document.getElementById('delete_button').disabled = false;
    }
    let row_id = table.rows('.selected')[0][0];
    document.getElementById('question-id-delete').value = dataSet[row_id].id;
});

document.querySelector('#delete-btn').addEventListener('click', function () {
    let row = table.rows('.selected');
    row.remove().draw(false);
    const id = table.rows('.selected').nodes()[0].cells[0].innerText;

    document.getElementById('edit_button').disabled = true;
    document.getElementById('delete_button').disabled = true;
});

document.querySelector('#edit_button').addEventListener('click', function () {
    let row_id = table.rows('.selected')[0][0]
    let formated_options = ""
    for (const option of dataSet[row_id].options) {
        formated_options += option + "\n";
    }
    document.getElementById('question-id').value = dataSet[row_id].id
    document.getElementById('question-text').value = dataSet[row_id].text
    document.getElementById('question-subject').value = dataSet[row_id].subject
    document.getElementById('question-options').value = formated_options
    document.getElementById('question-answer').value = dataSet[row_id].answer
    document.getElementById('question-level').value = dataSet[row_id].level
    document.getElementById('question-article').value = dataSet[row_id].article
    $("#question-groups").selectpicker("val", dataSet[row_id].groups[0]);
})