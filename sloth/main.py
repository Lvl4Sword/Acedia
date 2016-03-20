#!/usr/bin/env python3
#
# Autocomplete taken from
# https://stackoverflow.com/questions/7821661/how-to-code-autocompletion-in-python
#
from dateutil.relativedelta import relativedelta

import bisect
import datetime
import readline
import sys

from sloth import cardio
from sloth import physical
from sloth import userinput
from sloth.store import LogEntry
from sloth.workouts import workouts


def initial_questions(settings):
    """
    Settings file will be overwritten if all the data is gathered from
    the user successfully.
    """

    name = userinput.first_name_prompter.prompt()
    age = userinput.age_prompter.prompt()
    sex = userinput.sex_prompter.prompt()
    measurement_system = userinput.measurement_system_prompter.prompt()

    if measurement_system == 'M':
        weight = userinput.metric_body_weight_prompter.prompt()
        height = userinput.metric_body_height_prompter.prompt()
    elif measurement_system == 'I':
        weight = userinput.imperial_body_weight_prompter.prompt()
        height = userinput.imperial_body_height_prompter.prompt()

    goal = userinput.goal_prompter.prompt()

    initial_stats(settings, name, age, sex, measurement_system, weight,
                  height, goal)


def initial_stats(settings, name, age, sex, measurement_system, weight,
                  height, goal):

    print('You have 26 points to place into 6 stats.')
    print('Press \'b\' to go back after agility')

    # This is to ensure that the "back" functionality works
    back = 0
    agility = charisma = defense = endurance = intelligence = strength = 0
    while back != 6:
        all_stats = [agility, charisma, defense,
                     endurance, intelligence, strength]
        if back == 0:
            all_stats[0] = 0
            agi_prompter = userinput.stats_agi_prompter(activity=all_stats)
            agility, back = agi_prompter.prompt()
        elif back == 1:
            all_stats[1] = 0
            chr_prompter = userinput.stats_chr_prompter(activity=all_stats)
            charisma, back = chr_prompter.prompt()
        elif back == 2:
            all_stats[2] = 0
            def_prompter = userinput.stats_def_prompter(activity=all_stats)
            defense, back = def_prompter.prompt()
        elif back == 3:
            all_stats[3] = 0
            end_prompter = userinput.stats_end_prompter(activity=all_stats)
            endurance, back = end_prompter.prompt()
        elif back == 4:
            all_stats[4] = 0
            int_prompter = userinput.stats_int_prompter(activity=all_stats)
            intelligence, back = int_prompter.prompt()
        elif back == 5:
            str_prompter = userinput.stats_str_prompter(activity=all_stats)
            strength, back = str_prompter.prompt()
        elif back == 6:
            break
        else:
            raise Exception('Unexpected "back" variable {0!r}'.format(back))

    settings.agility = agility
    settings.charisma = charisma
    settings.defense = defense
    settings.endurance = endurance
    settings.intelligence = intelligence
    settings.strength = strength
    settings.name = name.capitalize()
    settings.age = age
    settings.sex = sex.upper()
    settings.measuring_type = measurement_system
    settings.weight = weight
    settings.height = height
    settings.goal = goal
    settings.xp = 0

    settings.commit()

    print('Please re-run the game to get started.')


# Custom completer
class MyCompleter(object):

    def __init__(self, options):
        self.options = sorted(options)

    def complete(self, text, state):
        # on first trigger, build possible matches
        if state == 0:
            # cache matches (entries that start with entered text)
            if text:
                self.matches = [s for s in self.options
                                if s and s.startswith(text.capitalize())]
            # no text entered, all matches possible
            else:
                self.matches = self.options[:]
        try:
            # return match indexed by state
            return self.matches[state]
        except IndexError:
            return None


def body_checks(settings, logs):

    # check if imperial
    if settings.measuring_type == 'I':
        # height_format = '''{0:.0f}'{1:.0f}"'''.format(
        #                    *divmod(int(settings.height), 12))

        # bmi
        bmi = round((settings.weight / settings.height ** 2) * 703.0, 2)
        if not 50 < settings.weight < 1000:
            raise Exception("Pretty sure {}'s not your real weight.".format(
                             settings.weight))

    # check if metric
    elif settings.measuring_type == 'M':
        # height_format = '''{0}m'''.format(settings.height)

        # bmi
        bmi = round(settings.weight / (settings.height ** 2), 2)
        if not 22.679 < settings.weight < 453.592:
            raise Exception("Pretty sure {}'s not your real weight.".format(
                             settings.weight))
    # type isn't imperial or metric
    else:
        raise Exception('Unexpected units type {0!r}'.format(
                         settings.measuring_type))

    personal_checks(settings, logs, bmi)


def personal_checks(settings, logs, bmi):

    # make sure the stats total up to 26
    stat_list = [settings.agility, settings.charisma, settings.defense,
                 settings.endurance, settings.intelligence,
                 settings.strength]
    if sum(stat_list) != 26:
        raise Exception('Stat points do not equal 26.')

        # make sure the goal is 1, 2, 3 or 4
        # goal_dict = {1: 'power lifter', 2: 'become stronger',
        #             3: 'lose weight', 4: 'cardio'}
        # if settings.goal in [1, 2, 3 , 4]:
        #    goal_string = goal_dict[settings.goal]
        # else:
    if settings.goal not in [1, 2, 3, 4]:
        raise Exception('Unexpected goal ID {0!r}'.format(settings.goal))
    else:
        pass

    bday_ = settings.age.split('-')
    # [0] is year, [1] is month, [2] is day.
    year_, month_, day_ = int(bday_[0]), int(bday_[1]), int(bday_[2])

    try:
        birthday = datetime.datetime(year_, month_, day_)
    except ValueError:
        raise Exception('The birthday in your settings file is not possible.')

    birthday_total = relativedelta(datetime.datetime.today(), birthday)
    current_age = birthday_total.years

    # if log xp and settings.xp don't match, take the xp from the logs
    check_xp(logs, settings)

    total_xp = int(settings.xp)

    level_ = level(total_xp)

    # the only way this would happen is if only a DETERIORATE was in your log
    if total_xp < 0:
        raise Exception('Something is wrong with your log file.')
    # impressive, but not yet supported
    elif total_xp > 99749:
        raise Exception('XP is over 99749')

    hello(settings, logs, birthday_total, current_age, total_xp, level_)


def hello(settings, logs, birthday_total, current_age, total_xp, level_):

    # there are no days, and only years meaning it's YOUR BIRTHDAY, WOO!
    if birthday_total.days == 0 and birthday_total.months == 0:
        birthday_today = ' (HAPPY BIRTHDAY!)'
    else:
        birthday_today = ''
    print('{0}/{1}/{2}{3}'.format(
           settings.name,
           settings.sex,
           current_age,
           birthday_today))

    print('Lvl {0}/XP {1}'.format(level_, total_xp))

    # don't log for 7, 14, 21 days? you'll lose 20% for each 7 days.
    deteriorate(settings, logs)

    completer = MyCompleter([str(k) for k in workouts])
    readline.set_completer(completer.complete)
    readline.parse_and_bind('tab: complete')

    choose_check = False
    while not choose_check:
        # because windows has to be special
        if sys.platform.startswith('win'):
            choose_extra = "(Tab for options)"
        else:
            choose_extra = "(Double tab for options)"
        choose_ = input('What workout did you do? {0}: '.format(choose_extra))
        if choose_.capitalize() not in workouts.keys():
            choose_check = False
        else:
            if choose_.capitalize() == 'Cardio':
                choose_check = True
                cardio.main(choose_, settings, logs)
                body_checks(settings, logs)
            else:
                choose_check = True
                physical.main(choose_, settings)
                body_checks(settings, logs)


def deteriorate(settings, logs):
    last_entry = logs.load_last_entry()
    if last_entry is None:
        return

    last_date = datetime.datetime.strptime(last_entry.date, '%B %d, %Y')
    today = datetime.datetime.today()
    deteriorate = today - last_date
    multiple_remove = int(deteriorate.days / 7)

    if multiple_remove >= 1 and settings.xp * 0.8 > 199.20000000000002:
        previous_xp = settings.xp
        for each in range(multiple_remove):
            total_xp = int(settings.xp)
            total_lost = round(total_xp * 0.2)
            settings.xp = round(total_xp * 0.8)

            deter_entry = LogEntry()

            deter_entry.date = today.strftime("%B %d, %Y")
            deter_entry.exercise_type = "DETERIORATE"
            deter_entry.total = total_lost
            deter_entry.distance = 0
            deter_entry.average = 0
            deter_entry.points = 0

            logs.append_entry(deter_entry)
            settings.commit()
        xp_lost = previous_xp - settings.xp
        print('Due to not logging anything for at least 7 days...')
        print('You\'ve lost {0} (20%) XP. Your XP is now {1}'.format(
               xp_lost, settings.xp))


def check_xp(logs, settings):
    logpoints = logs.check_log()

    if logpoints is None:
        if settings.xp != 0:
            settings.xp = 0
            settings.commit()
        return
    else:
        total_points, losing_points = logpoints
        log_total = sum(total_points) - sum(losing_points)

    if settings.xp == log_total:
        pass
    else:
        settings.xp = log_total
        settings.commit()


def level(total_xp):
    breakpoints = [250, 500, 2000, 3750, 5750, 8250, 11000, 14250, 17750,
                   21750, 26000, 30750, 35750, 41250, 47000, 53250, 59750,
                   66750, 74000, 82250, 90750]
    i = bisect.bisect(breakpoints, total_xp)
    return i + 1