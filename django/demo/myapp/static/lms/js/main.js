/**
 * The Archive — University Research Library & Intelligence
 * Emerald Folio & Slate Grey Interactive UI & Chart.js Theme
 */

document.addEventListener('DOMContentLoaded', () => {
  // 1. Mobile Sidebar Navigation Toggle
  const mobileToggle = document.getElementById('mobileNavToggle');
  const sidebar = document.querySelector('.app-sidebar');

  if (mobileToggle && sidebar) {
    mobileToggle.addEventListener('click', (e) => {
      e.stopPropagation();
      sidebar.classList.toggle('mobile-open');
    });

    document.addEventListener('click', (e) => {
      if (sidebar.classList.contains('mobile-open') && !sidebar.contains(e.target)) {
        sidebar.classList.remove('mobile-open');
      }
    });
  }

  // 2. Modal Management (Data-Modal triggers)
  const modalTriggers = document.querySelectorAll('[data-modal-target]');
  const modalClosers = document.querySelectorAll('[data-modal-close]');

  modalTriggers.forEach(btn => {
    btn.addEventListener('click', () => {
      const targetId = btn.getAttribute('data-modal-target');
      const modal = document.getElementById(targetId);
      if (modal) {
        const loanId = btn.getAttribute('data-loan-id');
        const bookTitle = btn.getAttribute('data-book-title');
        const studentName = btn.getAttribute('data-student-name');

        const bookTitleEl = modal.querySelector('.modal-book-title');
        const studentNameEl = modal.querySelector('.modal-student-name');
        const returnForm = modal.querySelector('form.return-form');

        if (loanId && returnForm) {
          returnForm.action = `/circulation/return/${loanId}/`;
        }
        if (bookTitle && bookTitleEl) bookTitleEl.textContent = bookTitle;
        if (studentName && studentNameEl) studentNameEl.textContent = studentName;

        modal.classList.add('active');
      }
    });
  });

  modalClosers.forEach(btn => {
    btn.addEventListener('click', () => {
      const modal = btn.closest('.modal-backdrop');
      if (modal) {
        modal.classList.remove('active');
      }
    });
  });

  // Close modal when clicking backdrop
  document.querySelectorAll('.modal-backdrop').forEach(modal => {
    modal.addEventListener('click', (e) => {
      if (e.target === modal) {
        modal.classList.remove('active');
      }
    });
  });

  // 3. Dismiss Alerts
  const alertCloseButtons = document.querySelectorAll('.alert-close');
  alertCloseButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      const alert = btn.closest('.alert');
      if (alert) {
        alert.style.opacity = '0';
        setTimeout(() => alert.remove(), 200);
      }
    });
  });

  // 4. Chart.js Initializations with Emerald Green & Slate Grey Palette
  initializeCharts();

  // 5. Initialize Lucide Icons
  if (window.lucide) {
    lucide.createIcons();
  }
});

function initializeCharts() {
  // Monthly Circulation Velocity Trend (Emerald Green & Slate Grey)
  const trendCanvas = document.getElementById('circulationTrendChart');
  if (trendCanvas && window.Chart) {
    const rawData = trendCanvas.getAttribute('data-chart-data');
    if (rawData) {
      try {
        const trendData = JSON.parse(rawData);
        const labels = trendData.map(d => d.label);
        const issues = trendData.map(d => d.issues);
        const returns = trendData.map(d => d.returns);

        new Chart(trendCanvas, {
          type: 'line',
          data: {
            labels: labels,
            datasets: [
              {
                label: 'Checkouts (Issued)',
                data: issues,
                borderColor: '#0D5C46', // Deep Emerald Green
                backgroundColor: 'rgba(13, 92, 70, 0.08)',
                borderWidth: 2.5,
                tension: 0.25,
                fill: true,
                pointBackgroundColor: '#0D5C46',
                pointRadius: 4,
                pointHoverRadius: 6,
              },
              {
                label: 'Restocked (Returned)',
                data: returns,
                borderColor: '#596B64', // Archival Slate Grey
                backgroundColor: 'transparent',
                borderWidth: 2,
                borderDash: [5, 5],
                tension: 0.25,
                pointBackgroundColor: '#596B64',
                pointRadius: 3,
              }
            ]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: {
                position: 'top',
                align: 'end',
                labels: {
                  boxWidth: 12,
                  font: { family: 'Public Sans', size: 12, weight: '600' },
                  color: '#596B64'
                }
              },
              tooltip: {
                backgroundColor: '#121815',
                titleFont: { family: 'Playfair Display', weight: '700', size: 13 },
                bodyFont: { family: 'Public Sans', size: 12 },
                padding: 10,
                cornerRadius: 6
              }
            },
            scales: {
              y: {
                beginAtZero: true,
                grid: { color: '#DCE5E0' },
                ticks: {
                  font: { family: 'Public Sans', size: 11 },
                  color: '#596B64',
                  precision: 0
                }
              },
              x: {
                grid: { display: false },
                ticks: {
                  font: { family: 'Public Sans', size: 11 },
                  color: '#596B64'
                }
              }
            }
          }
        });
      } catch (e) {
        console.error('Error rendering circulation trend chart:', e);
      }
    }
  }

  // Collection Distribution Chart (Emerald Green & Slate Grey Shades)
  const genreCanvas = document.getElementById('genreDistChart');
  if (genreCanvas && window.Chart) {
    const rawData = genreCanvas.getAttribute('data-chart-data');
    if (rawData) {
      try {
        const genreData = JSON.parse(rawData);
        const labels = genreData.map(d => d.name);
        const values = genreData.map(d => d.loan_count || d.total_copies || 1);

        const emeraldGreyPalette = [
          '#0D5C46', // Deep Emerald
          '#16A37F', // Sage Emerald
          '#37433E', // Slate Dark Grey
          '#3D7A68', // Academic Sage
          '#596B64', // Medium Slate Grey
          '#073B2C', // Forest Archival
          '#8E9F99', // Muted Grey
          '#B45309'  // Amber Accent
        ];

        new Chart(genreCanvas, {
          type: 'doughnut',
          data: {
            labels: labels,
            datasets: [{
              data: values,
              backgroundColor: emeraldGreyPalette.slice(0, labels.length),
              borderWidth: 2,
              borderColor: '#FFFFFF'
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '66%',
            plugins: {
              legend: {
                position: 'right',
                labels: {
                  boxWidth: 10,
                  font: { family: 'Public Sans', size: 11 },
                  color: '#161D1A',
                  padding: 10
                }
              }
            }
          }
        });
      } catch (e) {
        console.error('Error rendering genre distribution chart:', e);
      }
    }
  }

  // Department Usage Breakdown Horizontal Bar Chart (Emerald Green)
  const deptCanvas = document.getElementById('deptActivityChart');
  if (deptCanvas && window.Chart) {
    const rawData = deptCanvas.getAttribute('data-chart-data');
    if (rawData) {
      try {
        const deptJson = JSON.parse(rawData);
        const depts = deptJson.by_department || [];
        const labels = depts.map(d => d.department);
        const loans = depts.map(d => d.total_loans);

        new Chart(deptCanvas, {
          type: 'bar',
          data: {
            labels: labels,
            datasets: [{
              label: 'Active Loans',
              data: loans,
              backgroundColor: '#0D5C46',
              borderRadius: 4,
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            indexAxis: 'y',
            plugins: {
              legend: { display: false }
            },
            scales: {
              x: {
                beginAtZero: true,
                grid: { color: '#DCE5E0' },
                ticks: { precision: 0 }
              },
              y: {
                grid: { display: false },
                ticks: { font: { family: 'Public Sans', size: 11, weight: '500' } }
              }
            }
          }
        });
      } catch (e) {
        console.error('Error rendering department chart:', e);
      }
    }
  }
}
