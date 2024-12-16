// Static script for rendering various charts using Chart.js

document.addEventListener('DOMContentLoaded', () => {

    // Skill Demand Chart
    fetch("/api/skill-demand")
        .then(response => response.json())
        .then(data => {
            const labels = data.map(item => item.skill);
            const counts = data.map(item => item.demand);

            const ctx = document.getElementById('skillDemandChart').getContext('2d');
            new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Top Skills in Demand',
                        data: counts,
                        backgroundColor: 'rgba(75, 192, 192, 0.2)',
                        borderColor: 'rgba(75, 192, 192, 1)',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: { display: true },
                        tooltip: { enabled: true }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            title: { display: true, text: 'Number of Jobs' }
                        },
                        x: {
                            title: { display: true, text: 'Skills' }
                        }
                    }
                }
            });
        })
        .catch(error => console.error("Error fetching skill demand data:", error));

    // Top 10 Companies with Most Job Postings Chart
    fetch("/api/top-companies")
        .then(response => response.json())
        .then(data => {
            const labels = data.map(item => item.company);
            const counts = data.map(item => item.job_count);

            const ctx = document.getElementById('topCompaniesChart').getContext('2d');
            new Chart(ctx, {
                type: 'horizontalBar',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Top Companies with Most Job Postings',
                        data: counts,
                        backgroundColor: 'rgba(153, 102, 255, 0.2)',
                        borderColor: 'rgba(153, 102, 255, 1)',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    indexAxis: 'y',
                    scales: {
                        x: { beginAtZero: true, title: { display: true, text: 'Number of Jobs' } },
                        y: { title: { display: true, text: 'Companies' } }
                    }
                }
            });
        });

    // Job Distribution by Role Chart
    fetch("/api/job-distribution")
        .then(response => response.json())
        .then(data => {
            const labels = data.map(item => item.role);
            const counts = data.map(item => item.count);

            const ctx = document.getElementById('jobDistributionChart').getContext('2d');
            new Chart(ctx, {
                type: 'pie',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Job Distribution by Role',
                        data: counts,
                        backgroundColor: [
                            'rgba(255, 99, 132, 0.2)',
                            'rgba(54, 162, 235, 0.2)',
                            'rgba(255, 206, 86, 0.2)',
                            'rgba(75, 192, 192, 0.2)',
                            'rgba(153, 102, 255, 0.2)',
                            'rgba(255, 159, 64, 0.2)'
                        ],
                        borderColor: [
                            'rgba(255, 99, 132, 1)',
                            'rgba(54, 162, 235, 1)',
                            'rgba(255, 206, 86, 1)',
                            'rgba(75, 192, 192, 1)',
                            'rgba(153, 102, 255, 1)',
                            'rgba(255, 159, 64, 1)'
                        ],
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: { position: 'top' },
                        tooltip: { enabled: true }
                    }
                }
            });
        })
        .catch(error => console.error("Error fetching job distribution data:", error));

    // Average Salary by Work Type Chart
    fetch("/api/average-salary")
        .then(response => response.json())
        .then(data => {
            const labels = data.map(item => item.work_type);
            const averages = data.map(item => item.average_salary);

            const ctx = document.getElementById('averageSalaryChart').getContext('2d');
            new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Average Salary by Work Type',
                        data: averages,
                        backgroundColor: [
                            'rgba(54, 162, 235, 0.2)',
                            'rgba(255, 206, 86, 0.2)',
                            'rgba(75, 192, 192, 0.2)',
                            'rgba(153, 102, 255, 0.2)',
                            'rgba(255, 159, 64, 0.2)'
                        ],
                        borderColor: [
                            'rgba(54, 162, 235, 1)',
                            'rgba(255, 206, 86, 1)',
                            'rgba(75, 192, 192, 1)',
                            'rgba(153, 102, 255, 1)',
                            'rgba(255, 159, 64, 1)'
                        ],
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: { position: 'top' },
                        tooltip: { 
                            callbacks: {
                                label: function(context) {
                                    const value = context.raw.toFixed(2);
                                    return `Average Salary: $${value}`;
                                }
                            }
                        }
                    }
                }
            });
        })
        .catch(error => console.error("Error fetching average salary data:", error));
});
