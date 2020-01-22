// bind click event for all calendar widgets
var calendarOpts = {
    type: 'date',
    formatter: {
        date: function (date, settings) {
            if (!date) return '';
            var day = date.getDate() + '';
            if (day.length < 2) {
                day = '0' + day;
            }
            var month = (date.getMonth() + 1) + '';
            if (month.length < 2) {
                month = '0' + month;
            }
            var year = date.getFullYear();
            return year + '/' + month + '/' + day;
        }
    }
};
$(".ui.calendar").calendar(calendarOpts);
