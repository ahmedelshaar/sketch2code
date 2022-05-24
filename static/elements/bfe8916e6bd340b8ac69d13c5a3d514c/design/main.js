const labels = [
    'January',
    'February',
    'March',
    'April',
    'May',
    'June',
];

const data = {
    labels: labels,
    datasets: [{
        label: 'My First dataset',
        backgroundColor:  [
            'rgb(255, 99, 132)',
            'rgb(75, 192, 192)',
            'rgb(255, 205, 86)',
            'rgb(201, 203, 207)',
            'rgb(54, 162, 235)'
          ],
        data: [0, 10, 5, 2, 20, 30, 45],
    }]
};

const config = {
    type: 'polarArea',
    data: data,
    options: {}
};

const myChart = new Chart(
    document.getElementById('myChart'),
    config
);