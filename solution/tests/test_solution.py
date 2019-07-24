from unittest import TestCase
import solution
from datetime import datetime, timedelta


class MySolutionTests(TestCase):
    def test_check_format_time(self):
        time = "11:00"
        check = solution._check_correct_time_format(time)
        self.assertTrue(check)

        time = "123"
        check = solution._check_correct_time_format(time)
        self.assertFalse(check)

        time = "qwerty"
        check = solution._check_correct_time_format(time)
        self.assertFalse(check)

    def test_format_time(self):
        shift_time = "13:00"
        formatted_time = solution._format_time(shift_time)
        expected_time = datetime.strptime('13:00', '%H:%M')

        self.assertTrue(type(formatted_time) is datetime)
        self.assertEqual(formatted_time, expected_time)

        shift_time = "3pm"
        formatted_time = solution._format_time(shift_time)
        expected_time = datetime.strptime('03:00', '%H:%M')

        self.assertTrue(type(formatted_time) is datetime)
        self.assertEqual(formatted_time, expected_time)

        shift_time = "blablabla"
        formatted_time = solution._format_time(shift_time)
        self.assertFalse(formatted_time)

        shift_time = "123:123"
        formatted_time = solution._format_time(shift_time)
        self.assertFalse(formatted_time)

        shift_time = "14:15pmpmpm123"
        formatted_time = solution._format_time(shift_time)
        self.assertFalse(formatted_time)

        shift_time = "5pm3pm5pm"
        formatted_time = solution._format_time(shift_time)
        self.assertFalse(formatted_time)

    def test_process_working_time(self):
        shift_start = "09:00"
        shift_end = "15:00"
        processed_working = solution._process_working_time(shift_start, shift_end)
        self.assertTrue(type(processed_working[0]) is datetime)
        self.assertTrue(type(processed_working[1]) is datetime)
        self.assertTrue(type(processed_working[2]) is timedelta)
        self.assertEqual(datetime.strptime("09:00", "%H:%M"), processed_working[0])
        self.assertEqual(datetime.strptime("15:00", "%H:%M"), processed_working[1])
        self.assertEqual(timedelta(hours=6), processed_working[2])

        shift_start = "abcd"
        shift_end = "15:00"
        processed_working = solution._process_working_time(shift_start, shift_end)
        self.assertFalse(processed_working)

        shift_start = ""
        shift_end = "15:00"
        processed_working = solution._process_working_time(shift_start, shift_end)
        self.assertFalse(processed_working)

    def test_process_break_time(self):
        break_hours = '12-13pm'
        start_time = datetime.strptime("10:00", "%H:%M")
        processed_break = solution._process_break_time(break_hours, start_time)
        self.assertTrue(type(processed_break) is list)
        self.assertEqual(datetime.strptime("12:00", "%H:%M"), processed_break[0])
        self.assertEqual(datetime.strptime("13:00", "%H:%M"), processed_break[1])
        self.assertEqual(timedelta(hours=1), processed_break[2])

        break_hours = ''
        start_time = datetime.strptime("17:00", "%H:%M")
        processed_break = solution._process_break_time(break_hours, start_time)
        self.assertFalse(processed_break)

        break_hours = '1pm-2pm'
        start_time = datetime.strptime("17:00", "%H:%M")
        processed_break = solution._process_break_time(break_hours, start_time)
        self.assertFalse(processed_break)

    def test_process_shifts(self):
        processed_shifts = solution.process_shifts("tests/test_broken_shifts.csv")
        self.assertTrue(type(processed_shifts) is dict)
        self.assertEqual(len(processed_shifts), 0)

        processed_shifts = solution.process_shifts("tests/test_empty_shifts.csv")
        self.assertTrue(type(processed_shifts) is dict)
        self.assertEqual(len(processed_shifts), 0)

        processed_shifts = solution.process_shifts("blabla_not_a-file asd")
        self.assertFalse(processed_shifts)

        processed_shifts = solution.process_shifts("tests/test_good_shifts.csv")
        self.assertTrue(type(processed_shifts) is dict)
        self.assertNotEqual(len(processed_shifts), 0)
        self.assertEqual(processed_shifts['16:00'], 0.0)
        self.assertEqual(processed_shifts['23:00'], 19.0)
        self.assertEqual(processed_shifts['10:00'], 5.0)
        self.assertEqual(processed_shifts['15:00'], 24.0)

    def test_process_sales(self):
        processed_sales = solution.process_sales("tests/test_broken_transactions.csv")
        self.assertFalse(processed_sales)

        processed_sales = solution.process_sales("tests/test_empty_transactions.csv")
        self.assertFalse(processed_sales)

        processed_sales = solution.process_sales("tests/test_good_transactions.csv")
        self.assertTrue(type(processed_sales) is dict)
        self.assertEqual(processed_sales['10:00'], '150.75')
        self.assertEqual(processed_sales['11:00'], '30.0')
        self.assertEqual(processed_sales['13:00'], '250.5')

    def test_compute_percentage(self):
        shifts = {
            '11:00': 25
        }
        sales = {
            '10:00': 500
        }
        percentage = solution.compute_percentage(shifts, sales)
        self.assertTrue(type(percentage) is dict)
        self.assertEqual(percentage['11:00'], -25)

        shifts = {}
        sales = {}
        percentage = solution.compute_percentage(shifts, sales)
        self.assertTrue(type(percentage) is dict)
        self.assertEqual(len(percentage), 0)

        shifts = {
            '11:00': 10,
            '12:00': 10,
            '13:00': 10
        }
        sales = {
            '11:00': 20,
            '12:00': 30,
            '13:00': 40
        }
        percentage = solution.compute_percentage(shifts, sales)
        self.assertTrue(type(percentage) is dict)
        self.assertEqual(len(percentage), 3)
        self.assertEqual(percentage['11:00'], 50.0)
        self.assertEqual(percentage['12:00'], 33.33)
        self.assertEqual(percentage['13:00'], 25.0)

        shifts = {
            '1100': '123q'
        }
        sales = {}
        percentage = solution.compute_percentage(shifts, sales)
        self.assertFalse(percentage)

        shifts = {
            '11:00': 10
        }
        sales = {
            '11:00': '123q'
        }
        percentage = solution.compute_percentage(shifts, sales)
        self.assertFalse(percentage)

    def test_best_and_worst_hour(self):
        percentages = {
            '10:00': 16.2,
            '11:00': 27.4,
            '12:00': 74.3,
            '13:00': -24,
            '14:00': -45,
            '15:00': 28.4,
            '16:00': -44
        }
        best_and_worst = solution.best_and_worst_hour(percentages)
        best_hour, worst_hour = solution.best_and_worst_hour(percentages)
        self.assertTrue(type(best_and_worst) is list)
        self.assertTrue(type(best_hour) is str)
        self.assertTrue(type(worst_hour) is str)
        self.assertTrue(solution._check_correct_time_format(best_hour))
        self.assertTrue(solution._check_correct_time_format(worst_hour))

        percentages = {
            '1000': 16.2,
            '11:00': 27.4,
        }
        best_and_worst = solution.best_and_worst_hour(percentages)
        self.assertFalse(best_and_worst)

        percentages = {
            '11:00': 'qwerty'
        }
        best_and_worst = solution.best_and_worst_hour(percentages)
        self.assertFalse(best_and_worst)
