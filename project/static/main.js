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

let myNewChart = null;

function handlePlotClick() {
  const subdir = document.getElementById('results-file-list').value;  // Get the selected subdir
  fetch(`/result_contents?subdir=${encodeURIComponent(subdir)}`) // fetch('/result_contents?subdir=artifacts12/labels')
  .then(response => response.json())
  .then(results => {
    // console.log(results);
    // Extract data
    const data = results.map(result => {
      // console.log(result)
      const x = result.sample;
      const y = result.score;
      return { x, y };
    });
    
    console.log(myNewChart)
    if (myNewChart) {
      myNewChart.destroy();
    }
    // Create chart
    const ctx = document.getElementById('myChart').getContext('2d');
    myNewChart = new Chart(ctx, {
      type: 'scatter',
      data: {
        datasets: [{
          data,
          backgroundColor: 'rgba(0, 123, 255, 0.5)',
          borderColor: 'rgba(0, 123, 255, 1)',
        }],
      },
      options: {
        scales: {
          x: { beginAtZero: true },
          y: { beginAtZero: true },
        },
      },
    });  
  })
  .catch(error => console.error(error));
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
    const taskResult = res.task_result ? res.task_result.status : 'No result';
    const html = `
      <tr>
        <td>${taskID}</td>
        <td>${res.task_status}</td>
        <td>${res.task_status === 'SUCCESS' ? res.task_result : taskResult}</td>
      </tr>`;

    const table = document.getElementById('tasks');
    console.log("Table length = " + table.rows.length);
    // If the table has 5 or more rows, remove the last one
    if (table.rows.length >= 5) {
      table.deleteRow(-1);
    }
    // Insert the new row at the top of the table
    const newRow = table.insertRow(0);
    newRow.classList.add('table-row');
    newRow.innerHTML = html;
  
    const taskStatus = res.task_status;
    if (taskStatus === 'SUCCESS' || taskStatus === 'FAILURE') return false;
    setTimeout(function() {
      getStatus(res.task_id);
    }, 1000);
  })
  .catch(err => console.log(err));
}

const fileList = document.getElementById('file-list');

fetch('/video_files')
  .then(response => response.json())
  .then(data => {
    // console.log(data);
    data.forEach(fileName => {
      const option = document.createElement('option');
      option.value = fileName;
      option.text = fileName;
      // console.log(option);
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
    // console.log(data);
    data.forEach(fileName => {
      // console.log(fileName);
      const result_option = document.createElement('option');
      result_option.value = fileName;
      result_option.text = fileName;
      // console.log(result_option)
      resultFileList.add(result_option);
    });
  })
  .catch(error => console.error(error));

  function selectResultsFile() {
    const selectedFile = resultFileList.value;
    if (selectedFile) {
      console.log(`You selected ${selectedFile}`);
    }
  }