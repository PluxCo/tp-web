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
        document.getElementById('edit_button').setAttribute('disabled', '');
        document.getElementById('delete_button').setAttribute('disabled', '');
    } else {
        table.rows('.selected').nodes().each((row) => row.classList.remove('selected'));
        classList.add('selected');
        document.getElementById('edit_button').removeAttribute('disabled');
        document.getElementById('delete_button').removeAttribute('disabled');
    }

    let row = table.rows('.selected')[0][0]
    let formated_options = ""
    for (const option of dataSet[row].options) {
        formated_options += option + "\n";
    }
    document.getElementById('question-id').setAttribute('value', dataSet[row].id)
    document.getElementById('question-text').textContent = dataSet[row].text
    document.getElementById('question-subject').setAttribute('value', dataSet[row].subject)
    document.getElementById('question-options').textContent = formated_options
    document.getElementById('question-answer').setAttribute('value', dataSet[row].answer)
    document.getElementById('question-level').setAttribute('value', dataSet[row].level)
    document.getElementById('question-article').setAttribute('value', dataSet[row].article)

    $("#question-groups").selectpicker("val", dataSet[row].groups[0]);
    document.getElementById('question-id-delete').setAttribute('value', dataSet[row].id)

});

document.querySelector('#delete-btn').addEventListener('click', function () {
    table.row('.selected').remove().draw(false);
    const id = table.rows('.selected').nodes()[0].cells[0].innerText;

    document.getElementById('edit_button').setAttribute('disabled', '');
    document.getElementById('delete_button').setAttribute('disabled', '');
});