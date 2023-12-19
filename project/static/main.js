// custom javascript

(function() {
  console.log('Sanity Check!');
})();

function handleClick() {
  fetch('/slice_video', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ url : fileList.value,
                           start_frame : 35,
                           end_frame : 250}),
  })
  .then(response => response.json())
  .then(data => {
    getStatus(data.task_id)
  })
}

function handleDetectClick() {
    fetch('/run_yolo', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ url : fileList.value,
                               confidence : 0.25})
    })
    .then(response => response.json())
    .then(data => {
        console.log(data); // Print the JSON response for debugging
        getStatus(data.task_id);
    })
    .catch(error => console.error(error)); // Handle any errors during the fetch request
}

function getStatus(taskID) {
  fetch(`/tasks/${taskID}`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json'
    },
  })
  .then(response => response.json())
  .then(res => {
    console.log(res)
    const html = `
      <tr>
        <td>${taskID}</td>
        <td>${res.task_status}</td>
        <td>${res.task_result}</td>
      </tr>`;
    const newRow = document.getElementById('tasks').insertRow(0);
    newRow.innerHTML = html;

    const taskStatus = res.task_status;
    if (taskStatus === 'SUCCESS' || taskStatus === 'FAILURE') return false;
    setTimeout(function() {
      getStatus(res.task_id);
    }, 1000);
  })
  .catch(err => console.log(err));
}

const fileNames = ['file1.txt', 'file2.txt', 'file3.txt'];

const fileList = document.getElementById('file-list');

fetch('/video_files')
  .then(response => response.json())
  .then(data => {
    data.forEach(fileName => {
      const option = document.createElement('option');
      option.value = fileName;
      option.text = fileName;
      fileList.add(option);
    });
  })
  .catch(error => console.error(error));

function selectFile() {
  const selectedFile = fileList.value;
  if (selectedFile) {
    console.log(`You selected ${selectedFile}`);
  }
}

const resultFileList = document.getElementById('results-file-list');

fetch('/result_files')
  .then(response => response.json())
  .then(data => {
    data.forEach(fileName => {
      const listItem = document.createElement('li');
      listItem.textContent = fileName;
      listItem.addEventListener('click', () => selectFile(fileName));
      resultFileList.appendChild(listItem);
    });
  })
  .catch(error => console.error(error));

/*
function selectFile(selectedFile) {
  console.log(`You selected ${selectedFile}`);
}

fileNames.forEach(fileName => {
  const option = document.createElement('option');
  option.value = fileName;
  option.text = fileName;
  fileList.add(option);
});

function selectFile() {
  const selectedFile = fileList.value;
  if (selectedFile) {
    console.log(`You selected ${selectedFile}`);
  }
}
*/