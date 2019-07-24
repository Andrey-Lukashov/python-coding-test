"""
Please write you name here: Andrej Lukasov (andrey.lukashov@gmail.com)
"""
import csv
from datetime import datetime, timedelta
import re
from collections import OrderedDict
from operator import itemgetter


def _check_correct_time_format(time):
    """
    Checks if time string is in the correct format

    :param time: time string to be checked for formatting
    :type time: str
    :return: True if date is in correct format and vice-versa
    :rtype: bool
    """
    pattern = re.compile("^[0-9][0-9]:[0-9][0-9]$")

    if pattern.match(time):
        return True
    else:
        return False


def _format_time(time):
    """
    Formats alleged time strings into the correct format

    :param time: str time string to be formatted
    :type time: str
    :return: datetime object or Fail if failed to format
    :rtype: datetime, bool
    """
    time = re.sub('[^0-9:]', '', time)

    if ":" not in time:
        time = time + ":00"
    pattern = re.compile("^[0-9]:[0-9][0-9]$")
    if pattern.match(time):
        time = "0" + time

    try:
        if _check_correct_time_format(time):
            return datetime.strptime(time, "%H:%M")
        else:
            raise ValueError("Cannot format date. Date formatted doesn't match the %H:%M pattern")
    except ValueError as ve:
        # print(ve)
        return False


def _process_working_time(start_time, end_time):
    """
    Processes shift times, calculates overall shift time

    :param start_time: shift start time
    :type start_time: str
    :param end_time:  shift end time
    :type end_time: str
    :return: shifts start time, end time and shift overall time
    :rtype: list
    """
    start_time = _format_time(start_time)
    end_time = _format_time(end_time)

    if (start_time is False) | (end_time is False):
        return False

    shift = end_time - start_time

    return [start_time, end_time, shift]


def _process_break_time(break_notes, shift_start_time):
    """
    Processes break notes, converts them to correct time format

    :param break_notes: break notes that were manually typed in by employee
    :type break_notes: str
    :param shift_start_time: object of when shift has started
    :type shift_start_time: datetime
    :return: break start, break end and overall break time
    :rtype: list
    """
    if "-" in break_notes:
        break_hours = break_notes.replace(" ", "").replace(".", ":").split('-')
    else:
        return False

    break_start = _format_time(break_hours[0])
    break_end = _format_time(break_hours[1])

    if (break_start is False) | (break_end is False):
        return False

    # check if we need to convert am to pm
    # break can't start and end  before the shift starts
    if break_start < shift_start_time:
        break_start = break_start + timedelta(hours=12)

        if break_start < shift_start_time:
            return False
    if break_end < shift_start_time:
        break_end = break_end + timedelta(hours=12)

        if break_end < shift_start_time:
            return False

    break_time = break_end - break_start

    return [break_start, break_end, break_time]


def process_shifts(path_to_csv):
    """
    Processes shifts data

    :param path_to_csv: The path to the work_shift.csv
    :type: path_to_csv: str
    :return: A dictionary with time as key (string) with format %H:%M (e.g. "18:00") and cost as value (Number)
    :rtype: dict
    """
    processed = {}

    try:
        file = open(path_to_csv)
        reader = csv.DictReader(file)

        for row in reader:

            if _process_working_time(row['start_time'], row['end_time']) is not False:
                start_time, end_time, shift = _process_working_time(row['start_time'], row['end_time'])
            else:
                break

            if _process_break_time(row['break_notes'], start_time) is not False:
                break_start, break_end, break_time = _process_break_time(row['break_notes'], start_time)
            else:
                break

            break_time_taken = {}
            for i in range(0, int(break_time.seconds / 60), 1):
                break_time = (break_start + timedelta(minutes=i)).strftime("%H:%M")
                hour_starting = break_time.split(":")[0] + ":00"

                if hour_starting not in break_time_taken.keys():
                    break_time_taken[hour_starting] = 1
                else:
                    break_time_taken[hour_starting] = break_time_taken[hour_starting] + 1

            for i in range(0, int(shift.seconds / 60) + 60, 60):
                hour_starting_string = (start_time + timedelta(minutes=i)).strftime("%H:00")
                hour_starting_datetime = datetime.strptime(hour_starting_string, "%H:%M")
                pay_multiplier = 1

                # calculate how much employee going to get paid taking break into account
                if hour_starting_string in break_time_taken.keys():
                    pay_multiplier = 1 - (break_time_taken[hour_starting_string] / 60)

                # in case of not starting and ending shift at exactly :00 minutes
                if hour_starting_datetime < start_time:
                    delta = start_time - datetime.strptime(hour_starting_string, "%H:%M")
                    pay_multiplier = round(delta.seconds / 60 / 60, 2)

                if hour_starting_datetime.hour == end_time.hour:
                    if end_time.timestamp() > hour_starting_datetime.timestamp():
                        pay_multiplier = abs(hour_starting_datetime.timestamp() - end_time.timestamp()) / 3600

                if hour_starting_string not in processed.keys():
                    processed[hour_starting_string] = round(float(row['pay_rate']) * pay_multiplier, 2)
                else:
                    processed[hour_starting_string] = round(processed[hour_starting_string] + float(row['pay_rate']) *
                                                            pay_multiplier, 2)

        file.close()

        return processed
    except IOError:
        # print(f"Couldn't read the file {path_to_csv}")
        return False


def process_sales(path_to_csv):
    """
    Processes sales data

    :param path_to_csv: The path to the transactions.csv
    :type: path_to_csv: str
    :return: A dictionary with time (string) with format %H:%M as key and sales as value (string)
    :rtype: dict
    """
    processed = {}
    try:
        file = open(path_to_csv)
        reader = csv.DictReader(file)
        for row in reader:
            try:
                amount = float(row['amount'])

                if _check_correct_time_format(row['time']):
                    hour_starting = row['time'].split(":")[0] + ":00"

                    if hour_starting not in processed.keys():
                        processed[hour_starting] = str(round(amount, 2))
                    else:
                        processed[hour_starting] = str(round(float(processed[hour_starting]) + amount, 2))
                else:
                    return False

            except ValueError:
                file.close()
                return False
        file.close()

        return processed
    except IOError:
        #print(f"Couldn't read the file {path_to_csv}")
        return False


def compute_percentage(shifts, sales):
    """
    Computes percentage hourly revenue/labour cost

    :param shifts: processed shifts
    :type shifts: dict
    :param sales: processed sales
    :type sales: dict
    :return: computed percentages
    :rtype: dict
    """
    percentages = {}

    for time, cost in shifts.items():
        try:
            if _check_correct_time_format(time) is True:
                if float(cost):
                    if time not in sales.keys():
                        percentages[time] = -cost
                    else:
                        if float(sales[time]):
                            percentages[time] = round((cost / sales[time]) * 100, 2)
                        else:
                            raise ValueError("Sales amount provided is invalid")
                else:
                    raise ValueError("Shift costs value provided is invalid")
            else:
                raise ValueError("Date provided doesn't match the %H:%M pattern")
        except ValueError as ve:
            #print(ve)
            return False

    return percentages


def best_and_worst_hour(percentages):
    """
    Find best and worst performing hours

    :param percentages: hourly percentages of revenue/labour cost
    :type percentages: dict
    :return: best and worst performing hours
    :rtype: list
    """
    try:
        if type(percentages) is dict:
            percentages = OrderedDict(sorted(percentages.items(), key=itemgetter(1)))
            worst_hour = list(percentages)[0]

            for key, value in percentages.items():
                if percentages[key] > 0:
                    best_hour = key
                    break
            if _check_correct_time_format(worst_hour) is True:
                if _check_correct_time_format(best_hour) is True:
                    return [best_hour, worst_hour]
                else:
                    raise ValueError("Wrong best hour format")
            else:
                raise ValueError("Wrong worst hour format")
        else:
            raise TypeError("Percentages must be provided with a dictionary (output of compute_percentage())")
    except TypeError as te:
        #print(te)
        return False
    except ValueError as ve:
        #print(ve)
        return False


def main(path_to_shifts, path_to_sales):
    shifts_processed = process_shifts(path_to_shifts)
    sales_processed = process_sales(path_to_sales)
    percentages = compute_percentage(shifts_processed, sales_processed)
    best_hour, worst_hour = best_and_worst_hour(percentages)
    return best_hour, worst_hour


if __name__ == '__main__':
    # You can change this to test your code, it will not be used
    path_to_sales = "transactions.csv"
    path_to_shifts = "work_shifts.csv"
    best_hour, worst_hour = main(path_to_shifts, path_to_sales)


# Please write you name here: Andrej Lukasov (andrey.lukashov@gmail.com)
