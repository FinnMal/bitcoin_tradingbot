def should_buy(self):
    info_message = ""

    # conditions if should buy
    conditions = [{'v': False, 'text': 'positive change in last 2 ticks'},
                  {'v': False, 'text': 'high loss in last but no change in last 15 ticks'},
                  {'v': False, 'text': 'positive change at weekend'}]

    # high change
    conditions[0]['v'] = self.db.get_percentage_to_last() > 0 and self.db.get_percentage_to_before(1) > 0
    if conditions[0]['v']:
        print(conditions[0]['text'] + ' -> ' + str(self.db.get_percentage_to_last()))

    # high loss in last but no change in last 15 ticks
    """
    has_change = False
    for i in range(0, 16):
        if self.db.get_percentage_to_before(i, True) != 0:
            has_change = True
    conditions[1]['v'] = self.db.get_percentage_to_before(1) < -0.025 and not has_change
    if conditions[1]['v']:
        print(conditions[1]['text'])
    """

    # high change at weekend
    conditions[2]['v'] = self.db.get_percentage_to_last() > 0.001 and self.db.is_weekend()
    if conditions[2]['v']:
        print(conditions[2]['text'] + ' -> ' + str(self.db.get_percentage_to_last()))

    do_buy = False
    for condition in conditions:
        if condition['v']:
            info_message = info_message + '\n\n<b>BUY: </b>' + condition['text']
            do_buy = True

    if do_buy:
        # conditions if can buy
        can_conditions = [{'v': True, 'text': 'percentage to day high is to low, so price could go down'},
                          {'v': True,
                           'text': 'profit in last 100 ticks is to high and the percentage to low is to '
                                   'high, to the price would go down'},
                          {'v': True,
                           'text': 'profit in last 100 ticks is to low and the percenteage to high is to '
                                   'low, to the price would go down'},
                          {'v': True, 'text': 'trend of last 70 seconds is negative'},
                          {'v': True, 'text': ''}]
        """
        # percentage to day high is low enough, so price would not go down
        can_conditions[0]['v'] = self.db.get_percentage_to_high() > 0
        if not can_conditions[0]['v']:
            print(can_conditions[0]['text'] + ' -> ' + self.db.get_percentage_to_high(False, True))


        # profit in last 100 ticks is to high, to the price would go down
        can_conditions[1]['v'] = 0.07 > self.db.get_trend(
            100) or self.db.get_percentage_to_low() < 0.4 or self.db.get_percentage_to_high() > 1
        if not can_conditions[1]['v']:
            print(can_conditions[1]['text'] + ' -> ' + self.db.get_trend(100, False, True))

        # profit in last 100 ticks is to low, to the price would go down
        can_conditions[2]['v'] = self.db.get_trend(100) > -0.3 or self.db.get_percentage_to_high() > 1.5
        if not can_conditions[2]['v']:
            print(can_conditions[2]['text'] + ' -> ' + self.db.get_trend(100, False, True))
        """

        # trend of last 70 seconds is to low
        can_conditions[3]['v'] = self.db.get_trend_of_last_seconds(70) > 0 or (
                self.db.is_weekend() and self.db.get_trend_of_last_seconds(70) > -0.3)
        if not can_conditions[3]['v']:
            print(can_conditions[3]['text'] + ' -> ' + self.db.get_trend_of_last_seconds(60, True, True))

        can_buy = True
        for condition in can_conditions:
            if not condition['v']:
                info_message = info_message + '\n\n<b>CANNOT BUY: </b>' + condition['text']
                can_buy = False
        self.db.send_info_message(info_message)
        return can_buy
    return False


def should_sell(self):
    conditions = [{'v': False, 'text': 'high limit at weekend'},
                  {'v': False, 'text': 'low limit at weekend'},
                  {'v': False, 'text': 'much profit and high loss'},
                  {'v': False, 'text': 'no change in last 15 ticks and much profit'},
                  {'v': False, 'text': 'last percentage is negative and current is positive'},
                  {'v': False, 'text': 'high loss in cur tick'},
                  {'v': False, 'text': 'high profit in cur tick and positive percentage'},
                  {'v': False, 'text': 'no profit and no changes in last 15 ticks'},
                  {'v': False, 'text': 'percentage to high is very low, the price could go down'},
                  {'v': False, 'text': 'trend in last 30 is not positive and profit is low'},
                  {'v': False, 'text': 'no significant change in last 10 seconds and high profit'},
                  {'v': False, 'text': 'no significant change in last 25 seconds'}]
    if self.cur_trade.is_active():
        # high limit
        # conditions[0]['v'] = self.cur_trade.get_percentage() > 0.09 and self.db.is_weekend()
        # if conditions[0]['v']:
        # print(conditions[0]['text'])

        # low limit
        conditions[1]['v'] = self.cur_trade.get_percentage() < -0.009 and self.db.is_weekend()
        if conditions[1]['v']:
            print(conditions[1]['text'])

        # much profit and high loss
        conditions[2]['v'] = self.cur_trade.get_percentage() > 0.08 and self.db.get_percentage_to_last() < -0.04
        if conditions[2]['v']:
            print(conditions[2]['text'])

        # no change and much profit
        conditions[3]['v'] = self.cur_trade.get_percentage() > 0.08 and not self.db.has_change(15)
        if conditions[3]['v']:
            print(conditions[3]['text'])

        # last percentage is negative and current is positive
        conditions[4][
            'v'] = self.cur_trade.get_last_percentage() < 0 and self.cur_trade.get_percentage() >= 0 and self.db.is_weekend()
        if conditions[4]['v']:
            print(conditions[4]['text'])

        # high loss in cur tick and not much profit
        # conditions[5] = db.get_percentage_to_last() < -0.04 and cur_trade.get_percentage() > -0.04
        # if conditions[5]:
        # print(conditions[5]['text'])

        # high profit in cur tick and positive percentage
        conditions[6]['v'] = self.db.get_percentage_to_last() > 0.08 and self.cur_trade.get_percentage() > 0
        if conditions[6]['v']:
            print(conditions[6]['text'])

        """
        # no changes in last 15 ticks
        has_change = False
        for i in range(0, 15):
            if db.get_percentage_to_before(i, True) != 0:
                has_change = True
        conditions[7]['v'] = cur_trade.get_percentage() > -0.02 and not has_change
        if conditions[7]['v']:
            print(conditions[7]['text'])

        # percentage to high is very low, the price could go down
        conditions[8]['v'] = db.get_percentage_to_high() < 0.05 and cur_trade.get_percentage() > 0
        if conditions[8]['v']:
            print(conditions[8]['text'])
        """

        # trend in last 40 seconds is not positive and profit is low
        conditions[9]['v'] = self.db.get_trend_of_last_seconds(30) < -0.045 and self.cur_trade.get_percentage() > -1
        if conditions[9]['v']:
            print(conditions[9]['text'])

        # no significant change in last 10 seconds and high profit > 0.03
        conditions[10]['v'] = self.db.get_trend_of_last_seconds(
            10) < 0.004 and self.cur_trade.get_percentage() > 0.02
        if conditions[10]['v']:
            print(conditions[10]['text'])

        # no significant change in last 25 seconds
        conditions[11]['v'] = self.db.get_trend_of_last_seconds(
            25) < 0.01 and self.cur_trade.get_percentage() > -0.004 and not self.db.is_weekend()
        if conditions[11]['v']:
            print(conditions[11]['text'])

    do_sell = False
    info_message = ''
    for condition in conditions:
        if condition['v']:
            info_message = info_message + '\n\n<b>SELL:</b> ' + condition['text']
            do_sell = True
    self.db.send_info_message(info_message)
    return do_sell