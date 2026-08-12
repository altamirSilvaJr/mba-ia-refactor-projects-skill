class FinancialReportService {
    constructor(reportRepository) { this.reportRepository = reportRepository; }

    async execute() {
        const rows = await this.reportRepository.rows();
        const courses = new Map();
        rows.forEach((row) => {
            if (!courses.has(row.course_id)) courses.set(row.course_id, { course: row.course, revenue: 0, students: [] });
            if (row.enrollment_id !== null) {
                const course = courses.get(row.course_id);
                if (row.status === 'PAID') course.revenue += row.amount;
                course.students.push({ student: row.student || 'Unknown', paid: row.amount || 0 });
            }
        });
        return Array.from(courses.values());
    }
}

module.exports = FinancialReportService;
