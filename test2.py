import datetime as dt
three_months_approx = dt.datetime.today() - dt.timedelta(days=90)
formattedDate_3m_ago =  three_months_approx.strftime("%Y%m%d")

print(formattedDate_3m_ago)